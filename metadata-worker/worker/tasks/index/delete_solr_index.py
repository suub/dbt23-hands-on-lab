"""
Script to truncate existing solr index. All entries will be deleted, the
schema is kept.
================== Nightwatch usage ==================
{
    "id": "worker.tasks.index.delete_solr_index",
    "name": "delete index content",
    "params": {
        "solr_url": "<SOLR_URL>"
    }
}
======================================================
"""

from worker.nw.utils import Result
from worker.tasks.utils import httpxClient
from worker.nw.log import get_logger

__maintainer__ = "Marie-Saphira Flug <nightwatch@suub.uni-bremen.de>"

logger = get_logger(__name__)


def run(opts):
    """
    This method receives an url to a solr core and deletes all data from it

    Parameters
    ----------
    param opts: dict, required
        Contains parameters given in the blueprint of the pipeline
        Input parameters in opts["params"]:
        - param solr_url: str, required
            url to running solr core

    Returns
    ------
    Result:
        - Result
            A nightwatch Result with the parameters:
            - param logs: list
                information about successful deletion
    """
    solr_url = opts["params"]["solr_url"]
    update_url = solr_url.rstrip("/") + "/update?commit=true,overwrite=true"
    logs = []
    # delete everything. Could be changed to only delete certain things by
    # adding a filter here
    body = {"delete": {"query": "*:*"}}
    with httpxClient.httpxClient() as customClient:
        response = customClient.post(update_url, json=body)
        statusCode = customClient.checkStatusCodeOK(response.status_code)
    if statusCode:
        logger.debug("everything was deleted")
        logs.append("everything was deleted")
    else:
        raise ValueError(f"""something went wrong:
        response: {response}
        url: {update_url}
        body: {body}""")
    return Result(logs=logs)
