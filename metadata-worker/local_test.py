from worker.nw.pipeline_runner import Pipeline
from datetime import datetime
import os

blueprint = {
    "phases": [
        [
            {
                "id": "worker.tasks.examples.sleep",
                "name": "test",
                "params": {"duration": 6}
            }
        ],
    ]
}

working_dir = "test"
variables = {}

pipeline = Pipeline(blueprint, variables, working_dir)
pipeline.run()
