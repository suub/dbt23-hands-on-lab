"""
Script to open and read file contents for the next step.

Can be used with a file location specified in the blueprint
or a file location specified in the data recieved from the previous step,
without parameters in the blueprint.
(if both are given, the blueprint location will be used)

A convert flag can be set, if set to true the file content will be returned
converted to a dict, if set to false or not set the raw file content will
be returned.

================== Nightwatch usage ==================
{
    "id": "pipelines.tasks.importers.json",
    "name": "Read file contents"
    "params": {
        "path": str, optional
                -> path to a file
        "convert": bool, optional
                     false -> raw file content
                     true -> converted file content as dict
    }
}
======================================================
"""

import os
import json
from ...nightwatch.utils import Result
from pathlib import Path


def run(opts):
    """
    Opens the file in a specified location, if avaiable, and returns
    the content for the next step.

    Parameters
    ----------
    param opts: dict, required                           
        - opts["data"]: str, optional                   |
          the path to the file that should be opened    | one of these
        - opts["params"]["path"]: str, optional         | is requried
          the path to the file that should be opened    |

        - opts["params"]["convert"]: bool, optional
          if true a converted dict will be returned
          else the raw file content will be returned

    Returns
    ------
    Result:
        - A nightwatch Result with the parameters:
            - data dict or str
              a dict or a str containing the file content
    """

    subpath = opts.get("params", {}).get("path") or opts["data"]
    path = str(Path(os.environ["METADATA"]) / Path(subpath))
    with open(path, "r", encoding="utf8") as f:
        data = f.read()
        if opts.get("params", {}).get("convert"):
            data = json.loads(data)
        return Result(data=data)
