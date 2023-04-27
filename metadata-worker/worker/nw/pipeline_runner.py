import queue
import nanoid
import json
import base64
from importlib import import_module
from datetime import date, datetime
from .utils import Many, Partial, is_module_available
from .log import get_logger

__author__ = "Daniel Opitz"
__copyright__ = "Copyright 2022, SuUB"
__license__ = "GPL"
__maintainer__ = "Marie-Saphira Flug"


logger = get_logger(__name__)

current_tz = datetime.now().astimezone().tzinfo


class Pipeline:
    def __init__(self, blueprint, variables, working_dir):
        self.variables = variables
        self._variables = json.dumps(variables)
        self.working_dir = working_dir
        self._blueprint = json.dumps(blueprint)
        self.blueprint = self.fill_blueprint(blueprint)

        self.wq = queue.PriorityQueue()
        self.running_tasks = set()
        self.current_phase = 0

    def print(self):
        print("---blueprint---")
        print()
        print(self._blueprint)
        print()
        print("---vars---")
        print()
        print(self._variables)
        print()

    def fill_blueprint(self, blueprint):
        updated_vars = {}
        for k, v in self.variables.items():
            updated_vars[f"<{k}>"] = v

        job_vars = self.get_vars()

        for k in updated_vars.keys():
            for jvk, jvv in job_vars.items():
                updated_vars[k] = updated_vars[k].replace(jvk, jvv)

        for phase in blueprint["phases"]:
            for step in phase:
                if "params" in step:
                    for k in step["params"].keys():
                        for uvk, uvv in updated_vars.items():
                            if type(step["params"][k]) == str:
                                step["params"][k] = step["params"][k].replace(
                                    uvk, uvv
                                )

        return blueprint

    def get_vars(self):
        vars = {}
        if self.working_dir:
            vars["$WORKING_DIR"] = self.working_dir
        vars["$JOB_DATE"] = date.today().strftime("%Y-%m-%d")
        vars["$JOB_START"] = datetime.now().astimezone(current_tz).isoformat()
        vars["$LAST_SUCCESSFUL_RUN"] = ""
        return vars

    def is_completed(self):
        if len(self.running_tasks) > 0:
            return False

        if self.current_phase + 1 == len(self.blueprint["phases"]):
            return True

        self.current_phase += 1
        self.start_current_phase()
        return False

    def start_current_phase(self):
        current_phase = self.blueprint["phases"][self.current_phase]
        first_task = current_phase[0]
        task_unit = {
            "task": first_task,
            "next_tasks": current_phase[1:],
            "task_token": nanoid.generate(),
            "priority": 10,
        }
        self.running_tasks.add(task_unit["task_token"])
        self.queue_msg(task_unit)

    def process_msg(self, msg):
        module_name = msg["task"]["id"]
        logger.debug(f"in task with id {module_name}")
        print(module_name)
        if not is_module_available(module_name):
            raise ValueError(f"module {module_name} is not available")

        module = import_module(module_name)
        params = msg["task"].get("params")
        data = msg.get("data")
        if type(data) == dict:
            if "enc" in data and "raw" in data:
                data = base64.b64decode(data["raw"])

        opts = {}
        if params:
            opts["params"] = params

        if data:
            opts["data"] = data

        if msg["task"].get("passSentinel") and self.sentinel:
            opts["data"] = self.sentinel

        result = module.run(opts)
        if not result:
            raise ValueError(f"Got no Result from {module_name}!")

        next_step = (
            msg["next_tasks"][0]
            if "next_tasks" in msg
            and msg["next_tasks"]
            and msg["next_tasks"][0]
            else None
        )

        further_steps = (
            msg["next_tasks"][1:]
            if "next_tasks" in msg and msg["next_tasks"]
            else None
        )

        skip_id = msg["task"].get("skip_to")

        skip_id = msg["task"].get("skip_to")
        skip_step = None
        further_skip_steps = None
        if skip_id and "next_tasks" in msg and msg["next_tasks"]:
            for i, j in enumerate(msg["next_tasks"]):
                if skip_id == j["id"]:
                    skip_step = j
                    further_skip_steps = msg["next_tasks"][(i + 1):]

        priority = (
            msg["priority"] - 1 if msg["priority"] > 0 else msg["priority"]
        )

        new_tasks = []

        if next_step:
            if type(result.data) == Partial:
                for r in result.data.partial:
                    if type(r) == bytes:
                        r = {
                            "enc": "b64",
                            "raw": base64.b64encode(r).decode("utf-8"),
                        }
                    task_token = nanoid.generate()
                    self.running_tasks.add(task_token)
                    self.queue_msg(
                        {
                            "task": next_step,
                            "next_tasks": further_steps,
                            "task_token": task_token,
                            "priority": priority,
                            "data": r,
                        }
                    )

            elif result.data:
                rd = []
                if type(result.data) == Many:
                    rd += result.data.items
                else:
                    rd.append(result.data)
                for r in rd:
                    if type(r) == bytes:
                        r = {
                            "enc": "b64",
                            "raw": base64.b64encode(r).decode("utf-8"),
                        }
                    task_token = nanoid.generate()
                    new_tasks.append(
                        {
                            "task": next_step,
                            "next_tasks": further_steps,
                            "task_token": task_token,
                            "priority": priority,
                            "data": r,
                        }
                    )

        if skip_step:
            if result.skip:
                rd = []
                if type(result.skip) == Many:
                    rd += result.skip.items
                else:
                    rd.append(result.skip)
                for r in rd:
                    if type(r) == bytes:
                        r = {
                            "enc": "b64",
                            "raw": base64.b64encode(r).decode("utf-8"),
                        }
                    task_token = nanoid.generate()
                    new_tasks.append(
                        {
                            "task": skip_step,
                            "next_tasks": further_skip_steps,
                            "task_token": task_token,
                            "priority": priority,
                            "data": r,
                        }
                    )

        for task in new_tasks:
            self.running_tasks.add(task["task_token"])

        self.running_tasks.remove(msg["task_token"])
        if result.sentinel:
            if type(result.sentinel) != list:
                raise ValueError("Sentinel must be a list!")
            self.sentinel = result.sentinel[0]

        for task in new_tasks:
            self.queue_msg(task)

    def queue_msg(self, msg):
        priority = msg["priority"]
        self.wq.put(
            (
                priority,
                json.dumps(
                    msg, ensure_ascii=False, default=ext_json_serializer
                ),
            )
        )

    def run(self):
        self.start_current_phase()
        while True:
            try:
                msg = self.wq.get(timeout=5)
                msg = json.loads(msg[1])
                self.process_msg(msg)
                self.wq.task_done()
            except queue.Empty:
                if self.is_completed():
                    break
                continue
            except KeyboardInterrupt:
                break


def ext_json_serializer(obj):
    return str(obj)
