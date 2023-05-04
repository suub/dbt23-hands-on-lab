"""
Script to get available import folders from specified location,
all subfolders without an imported flag

================== Nightwatch usage ==================
Should be in a separated phase with sentinel set to "true",
the phase should be the first phase of an import-pipeline.
If more than one folder is found, the first folder will be imported
and a new job is created for the other folders. The job will be run
automatically after the first job is finished.
The first task in every following phase of the job should have
the "passSentinel" parameter set to "true", in order to pass the
folder's paths to the next job.

[
      {
        "id": "pipelines.tasks.fs.get_available_imports",
        "name": "Get list of directories to import",
        "params": {
          "dir": "<IMPORT_DIR>"
        },
        "sentinel": true
      }
]
example for IMPORT_DIR:
    "IMPORT_DIR": "data/crossref/import"


======================================================
"""

import os
from worker.nw.utils import Result
from pathlib import Path
from worker.nw.log import get_logger

logger = get_logger(__name__)


def run(opts):
    """
    Finds all subfolders without an imported-flag
    and gives them back as a sentinel value.

    Parameters
    ----------
    param opts: dict, required
        - opts["params"]["dir"]: str,
          the path to the location with folders that should be imported

    Returns
    ------
    Result:
        - A nightwatch Result with the parameters:
            - sentinel list unimported:
              all unimported subfolders in a sorted list
    """
    imports_dir = str(
        Path(os.environ["METADATA"]) / Path(opts["params"]["dir"])
    )
    logger.debug(f"Imports Directory: {imports_dir}")
    all_dirs = [
        os.path.join(imports_dir, d)
        for d in os.listdir(imports_dir)
        if os.path.isdir(os.path.join(imports_dir, d))
    ]
    unimported = []
    for d in all_dirs:
        if not os.path.exists(os.path.join(d, ".IMPORTED")):
            d = d.replace(os.environ["METADATA"], "").lstrip("/").lstrip("\\")
            unimported.append(d)
    logger.debug(f"Directories to import from: {str(sorted(unimported))}")
    return Result(sentinel=sorted(unimported))
