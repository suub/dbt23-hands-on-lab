"""
Script to set an imported flag at the end of an import-pipeline.
If a folder was imported successfully a file is created in the folder
named ".IMPORTED" in order to let the next jobs know that this folder
has already been imported.

================== Nightwatch usage ==================
Should be in an seperated phase at the end of an import-pipeline
The "passSentinal" parameter should be set to true, in order
to forward the other folder names from the "get_avaiable_imports.py"-task
to the next job.

[
    {
        "id": "pipelines.tasks.fs.set_imported_flag",
        "name": "Set imported flag",
        "passSentinel": true
    }
]
======================================================
"""

import os
from worker.nw.utils import Result
from pathlib import Path


def run(opts):
    """
    Set an imported-flag in a specified loaction.

    Parameters
    ----------
    param opts: dict, required
        - opts["data"]: str, required
          a path to the location where the flag should be created

    Returns
    ------
    Result:
        - An empty nightwatch Result

    """
    imported_dir = str(Path(os.environ["METADATA"]) / Path(opts["data"]))
    open(os.path.join(imported_dir, ".IMPORTED"), "w").close()

    return Result()
