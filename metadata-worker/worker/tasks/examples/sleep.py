import time
from worker.nw.log import get_logger
from worker.nw.utils import Result

logger = get_logger(__name__)
logger.setLevel("DEBUG")


def run(args):
    seconds = args["params"].get("duration")
    logger.debug(f"Sleep for {seconds} seconds")
    time.sleep(seconds)
    logger.debug("Finished sleeping")
    return Result(logs=[[f"Slept for {seconds} seconds"]], metrics={"slept": 1})