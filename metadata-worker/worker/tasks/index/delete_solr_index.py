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
    solr_url = opts["params"]["solr_url"]
    update_url = solr_url.rstrip("/") + "/update?commit=true,overwrite=true"
    # delete everything. Could be changed to only delete certain things by
    # adding a filter here
    body = {"delete": {"query": "*:*"}}
    httpxClient.post(update_url, json=body)
    return Result()
