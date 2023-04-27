"""
Script to get avaiable files, with specific extensions, in a specified folder.


================== Nightwatch usage ==================
Should be the first step in a phase, after a phase with
the "get_avaiable_imports.py"-task.
The "passSentinal" parameter should be set to true, in order
to forward the other folder names from the "get_avaiable_imports.py"-task
to the next job.

[
      {
        "id": "pipelines.tasks.fs.get_file_list",
        "name": "Get list of files to import",
        "params": {
          "ext": ".json"
        },
        "passSentinel": true
      },

======================================================
"""

import os
from ...nightwatch.utils import Result, Many
from pathlib import Path


def run(opts):
    """
    Finds all files with s specified extension and
    returns the corresponding paths in a list.

    Parameters
    ----------
    param opts: dict, required
        - opts["data"]: str, required
          a path to the location which files should be retrieved from
        - opts["params"]["ext"]: str or list, required
          only files with this extensions will be considered
        - opts["params"]["single_output"]: bool, optional
          if set to true one list will be returned,
          otherwise the list will be returned with Many

    Returns
    ------
    Result:
        - A nightwatch Result with the parameters:
            - data list or Many(list):
              a list of all file paths as strings or Many lists
              with one file path each
            - metrics dict, metrics about the number of files found
    """
    import_dir = str(Path(os.environ["METADATA"]) / Path(opts["data"]))
    extensions = opts["params"]["ext"]
    if type(extensions) == str:
        extensions = [extensions]

    if type(extensions) != list:
        raise ValueError('"extensions" param must be a list or a string')

    import_files = []
    for path, subdirs, files in os.walk(import_dir):
        for name in files:
            if name.endswith(tuple(extensions)):
                import_files.append(
                    Path(
                        os.path.join(path, name).replace(
                            os.environ["METADATA"] + os.sep, ""
                        )
                    ).as_posix()
                )
    data = (
        import_files
        if opts["params"].get("single_output")
        else Many(import_files)
    )
    return Result(data=data, metrics={"file_count": len(import_files)})
