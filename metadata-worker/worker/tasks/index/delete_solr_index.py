from worker.nw.utils import Result
from worker.tasks.utils import httpxClient
from worker.nw.log import get_logger

logger = get_logger(__name__)


def run(opts):
    solr_url = opts["params"]["solr_url"]
    update_url = solr_url.rstrip("/") + "/update?commit=true,overwrite=true"
    body = {"delete":{"query":"*:*"}}
    logger.debug("before post")
    httpxClient.post(update_url, json=body)
    logger.debug("after post")
    return Result()
