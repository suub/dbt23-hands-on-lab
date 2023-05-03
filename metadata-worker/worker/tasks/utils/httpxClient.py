import httpx
from worker.nw.log import get_logger

logger = get_logger(__name__)
timeout = 30.0
customClient = httpx.Client(timeout=timeout)


def get(url, **params):
    if "attempt" in params:
        attempt = params.get("attempt")
        del params["attempt"]
    else:
        attempt = 0
    with customClient:
        try:
            r = customClient.get(url, **params)
        except httpx.ReadTimeout as e:
            if attempt < 3:
                params["attempt"] = attempt + 1
                params["timeout"] = params["timeout"] * 2 if "timeout" in params else timeout * 2
                r = get(url, **params)
            else:
                raise e
    return r


def post(url, **params):
    with customClient:
        logger.debug(f"posting to {url} in httpxClient")
        r = customClient.post(url, **params)
    return r


def stream(method, url):
    return customClient.stream(method, url)


def checkStatusCodeOK(statusCode):
    return statusCode == httpx.codes.OK
