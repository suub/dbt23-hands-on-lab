"""
Script to start a crossref download.
================== Nightwatch usage ==================
{
    "id": "worker.tasks.download.crossref_downloader",
    "name": "Download Crossref Metadata",
    "params": {
        "directory": "<DOWNLOAD_DIR>",
        "user_agent": "--email--",
        "filter_array": [
            {
            "issn": "1865-7648",
            "type": "journal-article",
            "from-update-date": 2023
            }
        ]
    }
}

======================================================
"""

import os
import uuid
from pathlib import Path
from worker.tasks.download import crossref_downloader_util
from worker.nw.utils import Result
from worker.nw.log import get_logger

__maintainer__ = "Lena Klaproth <nightwatch@suub.uni-bremen.de>"

logger = get_logger(__name__)


def run(opts):
    """
    This method receives a list with filter parameters, a path to a download
    location and a user_agent and starts a crossref download accordingly
    using crossref_downloader_util.py.

    Parameters
    ----------
    param opts: dict, required
        Contains parameters given in the blueprint of the pipeline
        Input parameters in opts["params"]:
        - param filter_list: list[dict], required
            list containing one or more filter dicts for crossref queries
        - param directory: str, required
            the location were downloaded files will be saved
        - param user_agent: str, required
            a user_agent containing contact information, should always be given
            in order to be polite and improve crossref performance


        Example filter_list:
        [
            {
            "issn": "1865-7648",
            "type": "journal-article",
            "from-update-date": 2023
            }
        ]

        Allowed filter keys:
            until-approved-date, has-assertion, from-print-pub-date,
            until-deposit-date, from-accepted-date, has-authenticated-orcid,
            from-created-date, relation.object, issn, ror-id, lte-award-amount,
            until-online-pub-date, group-title, full-text.application,
            until-created-date, license.version, from-deposit-date,
            has-abstract, from-awarded-date, has-event, from-approved-date,
            funder, assertion-group, from-online-pub-date, from-issued-date,
            directory, content-domain, license.url, from-index-date,
            full-text.version, full-text.type, until-posted-date, has-orcid,
            has-archive, type, has-ror-id, is-update, until-event-start-date,
            update-type, from-pub-date, has-license, funder-doi-asserted-by,
            isbn, has-full-text, doi, orcid, has-content-domain, prefix,
            until-event-end-date, has-funder, award.funder,
            clinical-trial-number, member, has-domain-restriction,
            until-accepted-date, container-title, license.delay,
            from-posted-date, has-affiliation, from-update-date, has-award,
            until-print-pub-date, from-event-start-date, gte-award-amount,
            has-funder-doi, until-index-date, has-update, until-update-date,
            until-issued-date, until-pub-date, award.number, has-references
            type-name, has-relation, alternative-id, archive, relation.type,
            updates, relation.object-type, category-name, until-awarded-date,
            has-clinical-trial-number, assertion, article-number,
            has-update-policy, from-event-end-date

    Returns
    ------
    Result:
        - Result
            A nightwatch Result with the parameters:
            - param metrics: dict
                statistics about successful and unsuccessful downloads
            - param logs: list
                information about unsuccessful downloads (e.g. error messages)

    """

    if opts["params"].get("filter_list"):
        filter_list = opts["params"]["filter_list"]
    else:
        return Result(
            logs=["Download skipped, since no filter values were given."]
            )

    if opts["params"].get("directory"):
        download_dir = str(
            Path(os.environ["METADATA"]) / Path(opts["params"]["directory"])
        )
    else:
        return Result(
            logs=["Download skipped, since no download directory was given."]
            )

    if opts["params"].get("user_agent"):
        user_agent = opts["params"]["user_agent"]
    else:
        return Result(
            logs=["Download skipped, since no user_agent was given. "]
            )

    metrics = {"downloaded_records": 0, "failed_downloads": 0}
    logs = []

    for filter_dict in filter_list:
        try:
            logger.debug(f"Retrieving data for filter values: {filter_dict}")
            # Start crossref download
            downloaded = download(filter_dict, download_dir, user_agent)
        except (ValueError, PermissionError) as e:
            logger.debug(
                f"Download failed for: {filter_dict}.  With exception: {e}"
                )
            metrics["failed_downloads"] += 1
            logs.append(
                f"Download failed for: {filter_dict}.  With exception: {e}"
                )
        else:
            metrics["downloaded_records"] += downloaded

    return Result(metrics=metrics, logs=logs)


def download(filter_dict, download_dir, user_agent):
    """Calls crossref_downloader_util's run method with given options

    Parameters
    ----------
    param filter_dict: dict, required
        Dict containing filter key-value pairs for one crossref query
    param download_dir: str, required
        Path to the location the query results will be saved to
    param user_agent: str, optional
        A string containing contact information for the crossref query,
        should always be given to be a 'polite' crossref user and
        recieve a more reliable crossref service

    Returns
    ------
    int
        Returns the result of the crossref_downloader_util's run method,
        which contains an int indicating how many records have been retrieved

    """
    opts = {"filter": filter_dict,
            "download_dir": f"{download_dir}/{uuid.uuid4()}",
            "user_agent": user_agent}
    return crossref_downloader_util.run(opts)
