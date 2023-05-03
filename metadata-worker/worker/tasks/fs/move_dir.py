"""
Script to move a folder to another location.
Requires a source and destination path as a string.

================== Nightwatch usage ==================
[
    {
        "id": "worker.tasks.fs.move_dir",
        "name": "Move downloaded files to import",
        "params": {
            "dst": "<IMPORT_DIR>",
            "src": "<DOWNLOAD_DIR>"
      }
    }
]

======================================================
"""

import os
import shutil
from worker.nw.utils import Result
from pathlib import Path


def run(opts):
    """
    This method moves a folder from one location to another.

    Parameters
    ----------
    param options: dict, required
        Contains parameters given in the blueprint of the pipeline
        Parameter keys in options:
        - param src: str, required
            the path of the folder to be moved
        - param dst: str, required
            the new path of the folder

    Returns
    ------
    - Result:
        A nightwatch result contaiing:
        - logs: list[str]
            A log indicating if the folder was moved

    """
    src = str(Path(os.environ["METADATA"]) / Path(opts["params"]["src"]))
    dst = str(Path(os.environ["METADATA"]) / Path(opts["params"]["dst"]))
    logs = []
    if os.path.isdir(src):
        logs.append(f"moved {src} to {dst}")
        shutil.move(src, dst)
    else:
        logs.append(f"nothing was moved, {src} does not exist")
    return Result(logs=logs)
