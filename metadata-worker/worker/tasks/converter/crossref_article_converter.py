"""
Script to convert record metadata downloaded from crossref from json format
into the internal db-schema

================== Nightwatch usage ==================
Requires a previous NW step that returns a NW Result containing
a list with a dict for each record in the field 'data'

{
    "id": "worker.tasks.converter.crossref_article_converter",
        "name": "Convert crossref records",
    }
}

======================================================
"""

import re
import json
from datetime import datetime
from worker.nw.utils import Result
from worker.nw.log import get_logger

logger = get_logger(__name__)

ORCID_RE = re.compile(r"(\d{4}-\d{4}-\d{4}-(\d{3}X|\d{3}x|\d{4}))")


def run(opts):
    """
    Convert crossref data to internal db-schema.

    Parameters
    ----------
    param opts: dict, required
        Contains data from the previous step.

        opts["data"]: list[dict], contains one crossref response,
        containing several raw records

    Returns
    ------
    Result:
        - A nightwatch Result with the parameters:
            - param records: list[dict]
                contains converted records
            - param metrics: dict
                contains metrics about the number of converted records
            - param logs: list[str]
                contains logs about failed conversions
    """

    file_contents = json.loads(opts["data"])
    converted = {}
    logs = []
    metrics = {}
    try:
        raw_records = file_contents["message"]["items"]
        for raw_record in raw_records:
            try:
                article = convert(raw_record)
            except Exception as e:
                logs.append(f"conversion failed for {get_id(raw_record)}: {e}")
                continue
            else:
                if article:
                    converted[article.get("id")] = article
        metrics["articles"] = len(converted)
        logger.debug(metrics)
        return Result(
            data=list(converted.values()),
            metrics=metrics,
            logs=logs
        )
    except KeyError:
        return Result(
            data=list(converted.values()),
            metrics={"articles": len(converted)},
            logs=logs
        )


def convert(raw_record):
    """
    Convert one raw crossref record to internal db-schema.

    Parameters
    ----------
    - param raw_record: dict, required
        One crossref record

    Returns
    ------
    - dict record:
        converted record
        with fields: id, access_options, title, contributors, publication_date,
        identifiers, source
    """
    record_title = get_title(raw_record)
    if not record_title:
        return None

    record = {}

    record["id"] = get_id(raw_record)
    record["access_options"] = get_access_options(raw_record)
    record["title"] = record_title
    record["contributors"] = get_contributors(raw_record)
    record["publication_date"] = get_publication_date(raw_record)
    record["identifiers"] = get_identifiers(raw_record)
    record["source"] = "crossref"

    return record


def get_id(raw_record):
    """
    Get DOI and build article ID

    Parameters
    ----------
    - param raw_record: dict, required
        raw crossref record

    Returns
    ------
    - string:
        article id, build like: "cr-" + doi
    """
    doi = raw_record.get("DOI")

    if not doi:
        return None

    return f"cr-{doi}"


def get_access_options(raw_record):
    """
    GEt access options from raw record, e.g. creative commons

    Parameters
    ----------
    - param raw_record: dict, required
        raw crossref record

    Returns
    ------
    - list[dict] access_options:
        contains the access options:
            - url: str
                url build with the doi
            - conditions: list[str]
                containing "oa" for open access articles
                or "ra" for restricted articles
    """
    doi = raw_record.get("DOI")
    url = f"https://doi.org/{doi}"

    access_options = []

    is_oa = check_license(raw_record)

    if is_oa:
        access_options.append(
            {"url": url, "conditions": ["oa"]}
        )
    else:
        access_options.append(
            {"url": url, "conditions": ["ra"]}
        )

    return access_options


def get_title(raw_record):
    """
    Get title from raw record

    Parameters
    ----------
    - param raw_record: dict, required
        raw crossref record

    Returns
    ------
    - title: str
       title and subtitle
    """
    title = raw_record.get("title")
    subtitle = raw_record.get("subtitle")
    if not title or len(title) == 0:
        return None

    title = "; ".join(title)
    if subtitle:
        subtitle = "; ".join(subtitle)
        if subtitle.lower() not in title.lower():
            title = f"{title}: {subtitle}"
    return title


def get_contributors(raw_record):
    """
    Get contributors from raw record.

    Parameters
    ----------
    - param raw_record: dict, required
        raw crossref record

    Returns
    ------
    - list[dict] contributors:
        a list with contributor details,
        with a maximum of 30 contributors allowed
    """
    contributors = []

    for role in ["author", "editor", "chair", "translator"]:
        raw_contribs = raw_record.get(role)
        if raw_contribs:
            contribs = []
            for raw_contrib in raw_contribs:
                contrib = get_contributor_details(raw_contrib)

                if contrib:
                    contrib["role"] = role
                    if raw_contrib.get("sequence") == "first":
                        contribs.insert(0, contrib)
                    else:
                        contribs.append(contrib)
            contributors += contribs

    if len(contributors) > 30:
        contributors = contributors[0:30]

    return contributors


def get_contributor_details(contributor):
    """
    Get contributor details from one raw contributor.

    Parameters
    ----------
    - param contributor: dict, required
        raw information about one contributor

    Returns
    ------
    - dict c:
        contributor information, containing: given name, family name,
        suffix, name, identifiers (ORCID), affiliation
    """
    c = {}

    given = contributor.get("given")
    family = contributor.get("family")
    suffix = contributor.get("suffix")
    name = contributor.get("name")

    if family and family.strip():

        if suffix and suffix.strip():
            if "join" not in suffix:
                c["family_name"] = f"{family.strip()} {suffix}"
        else:
            c["family_name"] = family.strip()

    if given and given.strip():
        c["given_name"] = given.strip()

    if name and name.strip():
        c["name"] = name.strip()

    if not c:
        return None

    orcid_url = contributor.get("ORCID")
    if orcid_url:
        m = re.search(ORCID_RE, orcid_url)
        if m:
            c["identifiers"] = [
                {"value": m.group(1).strip().upper(), "type": "orcid"}
            ]

    affiliation = contributor.get("affiliation")
    if affiliation:
        c["affiliation"] = "; ".join(
            [a["name"].strip() for a in affiliation if a["name"].strip()]
        )

    return c


def get_publication_date(raw_record):
    """
    Get publication date from raw record.

    Parameters
    ----------
    - param raw_record: dict, required
        raw crossref record

    Returns
    ------
    - list publication_date:
        Date of publication, (publication_date[0]->year,
        publication_date[1]->month, publication_date[1]->day)
    """
    publication_date = None

    published_print = raw_record.get("published-print")
    if published_print:
        publication_date = published_print["date-parts"][0]

    published_online = raw_record.get("published-online")
    if published_online:
        online_publication_date = published_online["date-parts"][0]
        if datetime(*online_publication_date) < datetime(*publication_date):
            publication_date = online_publication_date

    if publication_date:
        return publication_date

    issued = raw_record.get("issued")
    if issued:
        return issued["date-parts"][0]

    return None


def get_identifiers(raw_record):
    """
    Get identifiers (doi)  from raw record.

    Parameters
    ----------
    - param raw_record: dict, required
        raw crossref record

    Returns
    ------
    - list[dict] identifiers:
        list containing a dict, with the doi, if raw record contains a doi
        empty list otherwise
    """
    identifiers = []

    doi = raw_record["DOI"]
    if doi:
        identifiers.append({"value": doi, "type": "doi", "source": "crossref"})

    return identifiers


def check_license(raw_record):
    """
    Check if a raw record contains an open access license.

    Parameters
    ----------
    - param raw_record: dict, required
        raw crossref record

    Returns
    ------
    - bool oa:
        indicates if a record is open access
    """
    oa = False
    license_infos = raw_record.get("license")
    if license_infos:
        for license_info in license_infos:
            oa_info = license_info.get("URL")
            if "creativecommons" in oa_info:
                oa_date_start = license_info.get("start")

                if oa_date_start:
                    date = []
                    date_parts = oa_date_start["date-parts"][0]

                    if len(date_parts) == 3:
                        date.append(str(date_parts[0]))
                        if len(str(date_parts[1])) == 1:
                            date.append(str(date_parts[1]).zfill(2))
                        else:
                            date.append(str(date_parts[1]))
                        if len(str(date_parts[2])) == 1:
                            date.append(str(date_parts[2]).zfill(2))
                        else:
                            date.append(str(date_parts[2]))

                date = "-".join(date)
                date = datetime.strptime(date, "%Y-%m-%d")
                now = date.today()
                if date < now:
                    oa = True
    return oa
