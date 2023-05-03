import json
import os
import time
from worker.tasks.utils import httpxClient
from worker.nw.log import get_logger

__maintainer__ = "Lena Klaproth <nightwatch@suub.uni-bremen.de>"

logger = get_logger(__name__)

BASE_URL = "https://api.crossref.org/"


def run(options):
    """
    This method calls the crossref api with specific filter values and
    downloads the corresponding crossref entries and saves them in json format
    to the specified location.

    Parameters
    ----------
    param options: dict, required
        Contains parameters given in the blueprint of the pipeline
        Parameter keys in options:
        - param filter: dict, required
            containing one or more filter key-value pairs for the crossref
            query
        - param download_dir: str, required
            the location were downloaded files will be saved
        - param user_agent: str, optional
            a user_agent containing contact information, should always be
            given in order to improve crossref performance

    Returns
    ------
    - records_downloaded: int
        indicating how many records have successfully been downloaded

    """
    download_dir = options["download_dir"]
    records_downloaded = 0
    for data in retrieve(**options):
        json_data, total, item_count, next_cursor = extract_data(data)
        records_downloaded += item_count
        if not os.path.exists(download_dir):
            try:
                os.makedirs(download_dir, exist_ok=True)
            except PermissionError:
                time.sleep(120)
                os.makedirs(download_dir, exist_ok=True)

        with open(f"{download_dir}/{time.time_ns()//1000000}.json", "w") as f:
            f.write(json.dumps(data))
    return records_downloaded


def retrieve(
    endpoint="works",
    filter=None,
    cursor="*",
    rows=None,
    user_agent="",
    **kwargs
):
    """
    Constructs filter parameters for the crossref query. Calls the crossref
    API with constructed parameters and a cursor, until all results have been
    retrieved, yields the result

    Parameters
    ----------
    - param endpoint: str, optional
        the endpoint of the crossref API, default value is "works", other
        endpoints are e.g. "journals" or "licenses"
    - param filter: dict, optional
        key-value pairs for the crossref query
    - param cursor: str, optional
        cursor parameter, if a cursor is used it should be "*" on the first
        API call and should be then set to the cursor value of the last
        received result
    - param rows: int, optional
        Should not be used! Gives the possibility to retrieve a specified
        amount of rows per API call, the crossref default value is 20 and
        crossref advises against changing it
    - param user_agent: str, optional
        a user_agent containing contact information, should always be given in
        order to improve crossref performance


    Returns
    ------
    - Generator:
        the method yields the data received from the API call and continues
        with the next API call until all records have been retrieved
    """

    if filter is None:
        filter = {}

    # There should always be a user-agent when using the crossref api
    headers = {"user-agent": user_agent}

    url = f"{BASE_URL}{endpoint}"

    total_results = 0
    done = 0

    r = get(headers, url, construct_params(filter, cursor, rows))
    data, total, item_count, next_cursor = extract_data(r)

    if next_cursor is not None:
        total_results = total
        done = item_count
        cursor = next_cursor
    logger.debug(f"Total item count: {total_results}")
    if total_results > 0:
        yield data

    while done < total_results:
        # slow down retrieval
        # time.sleep(1)
        r = get(headers, url, construct_params(filter, cursor, rows))
        data, total, item_count, next_cursor = extract_data(r)
        if item_count == 0:
            break
        if all([total_results, item_count, next_cursor]) is not None:
            done += item_count
            cursor = next_cursor
            logger.debug(f"Items retrieved: {done}")
            yield data


def get(headers, url, url_params, attempt=1):
    """
    Calls the given url with given headers and retries three times (with an
    increasing time interval between calls) if the call is unsuccessful

    Parameters
    ----------
    - param headers: dict, required
        headers, ({"user-agent": user_agent})
    - param url: str, required
        the url
    - param url_params: dict, optional
        contains url parameters (crossref filter values, rows, cursor)
    - param attempt: int, optional
        Counter for the number of attempts, defaults to 1

    Returns
    ------
    - HTTP response
        the response of the call
    """

    try:
        r = httpxClient.get(url,
                            headers=headers,
                            params=url_params,
                            timeout=60)
    except Exception as e:
        raise ValueError(f"Request Error for {url}: {e}")
    if httpxClient.checkStatusCodeOK(r.status_code):
        try:
            return r.json()
        except ValueError:
            raise ValueError(
                f"Response body is not JSON for {r.url}: {r.text}"
                )
    elif 400 <= r.status_code < 500:
        raise ValueError(
            f"Bad status code for {r.url}: {r.status_code}: {r.text}"
            )
    else:
        if attempt > 3:
            raise ValueError(f"Three unsuccessful attempts {r.url}")
        logger.warning(
            f"Server Error, wait {60*attempt} seconds to try again: {r.url}"
            )
        time.sleep(60*attempt)
        return get(headers, url, url_params, attempt+1)


def construct_params(filter, cursor, rows):
    """
    Prepares url parameters for httpx request

    Parameters
    ----------
    - param filter: dict, optional
        crossref filter key-value pairs
    - param cursor: str, optional
        crossref cursor
    - param rows: dict, optional
        crossref rows

    Returns
    ------
    - dict
        prepared url parameters
    """
    params = {}

    filter_param = create_filter_param(filter)
    if filter_param:
        params["filter"] = filter_param

    if cursor:
        params["cursor"] = cursor

    if rows:
        params["rows"] = rows

    return params


def create_filter_param(filter):
    """
    Prepares filter values for crossref query

    Parameters
    ----------
    - param filter: dict, optional
        crossref filter key-value pairs

    Returns
    ------
    - str
        prepared filter string for url parameters
    """
    if len(filter) == 0:
        return None

    filter_options = []
    for k, v in filter.items():
        if type(v) == list:
            for i in v:
                filter_options.append(f"{k}:{i}")
        else:
            filter_options.append(f"{k}:{v}")

    return ",".join(filter_options)


def extract_data(json_data):
    """
    Extracts specific data fields from a crossref json response

    Parameters
    ----------
    - param json_data: dict, required

    Returns
    ------
    - json_data: dict
        the original data
    - total_results: int
        number of records for the filter values
    - item_count: int
        number of records in this response
    - next_cursor: str
        next cursor value
    """
    total_results = json_data["message"].get("total-results", 0)
    item_count = len(json_data["message"].get("items", []))
    next_cursor = json_data["message"].get("next-cursor")

    return json_data, total_results, item_count, next_cursor
