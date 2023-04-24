"""
Script to update an existing solr index.
================== Nightwatch usage ==================
{
    "id": "worker.tasks.index.update_solr_index",
    "name": "update solr_index with latest db entries",
    "params": {
        "db": "<DB_CON>",
        "table": "records",
        "solr_url": "<SOLR_URL>",
        "last_index": "<LAST_INDEX>"
    }
}
======================================================
"""

import psycopg2
from datetime import datetime, timezone
from psycopg2.sql import SQL, Identifier
from psycopg2.extras import DictCursor

from worker.nw.utils import Result
from worker.tasks.utils import httpxClient
from worker.nw.log import get_logger

__maintainer__ = "Marie-Saphira Flug <nightwatch@suub.uni-bremen.de>"

logger = get_logger(__name__)
CHUNK_SIZE = 10_000


def run(opts):
    solr_url, db, table, last_index = get_params(opts["params"])

    db_con = psycopg2.connect(db, cursor_factory=DictCursor)

    updated_count, solr_count = update_records(
        solr_url, db_con, table, last_index
    )

    # count db entries for metrics
    cur = db_con.cursor()
    cur.execute(
        SQL(
            "SELECT count(*) AS count FROM {};"
        ).format(Identifier(table))
    )
    res = cur.fetchall()
    db_count = res[0]["count"]

    cur.close()
    db_con.close()

    return Result(
        metrics={
            "updated": updated_count,
            "total_db_count": db_count,
            "total_solr_count": solr_count,
        }
    )


def get_params(params) -> (str, str, str, datetime):
    """
    Extract parameters from given params dict
    """
    solr_url = params.get("solr_url")
    db = params.get("db")
    table = params.get("table")
    last_index = params.get("last_index", "2000-01-01T00:00:00+00:00")
    last_index = datetime.fromisoformat(last_index)

    if not solr_url:
        raise ValueError('"solr_url" parameter missing')
    if not db:
        raise ValueError('"db" parameter missing')
    if not table:
        raise ValueError('"table" parameter missing')
    logger.debug(type(last_index))
    return solr_url, db, table, last_index


def update_records(solr_url, db_con, table, last_index) -> (int, int):
    """
    Update solr index
    """
    updated_record_count = 0
    update_url = solr_url.rstrip("/") + "/update?commit=true,overwrite=true"
    # create a new db cursor called u(pdate)c(ount)
    cur = db_con.cursor(name="uc")
    cur.itersize = CHUNK_SIZE
    # Select all new db entries
    cur.execute(
        SQL(
            "SELECT * FROM {} WHERE created > %s;"
        ).format(Identifier(table)),
        [last_index],
    )
    db_records = cur.fetchmany(CHUNK_SIZE)
    # Iterate chunkwise over new db entries and add (=post) them
    # to the solr index
    while db_records:
        records = [dict(r) for r in db_records]
        records = [convert_db_record(r) for r in records]
        body = {"add": records}
        httpxClient.post(update_url, json=body)
        updated_record_count += len(records)
        db_records = cur.fetchmany(CHUNK_SIZE)
    cur.close()

    # count all solr entries for metrics
    query_url = solr_url.rstrip("/") + "/query?q=*:*&wt=json"
    result = httpxClient.get(query_url)

    return updated_record_count, result.json()["response"]["numFound"]


def convert_db_record(db_record):
    """
    Convert db entry to fit the solr schema
    """
    rec = {
        "id": db_record["id"],
        "created": datetime_to_iso(db_record["created"]),
        "title": db_record["title"],
        "author": get_authors(db_record),
        "year": get_year(db_record),
        "issn": get_identifiers(db_record, "issn"),
    }
    rec["title_authors"] = get_title_author(rec["title"], rec["author"])
    return rec


def datetime_to_iso(dt):
    """
    Convert date to iso format
    """
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def get_title_author(title, authors):
    """
    Have the title and first 3 authors on one string
    """
    return f'{title} {" ".join(authors[0::2])}'


def get_authors(db_record):
    """
    Create array with all kinds of combinations of given and family name
    """
    authors = []

    if db_record["contributors"]:

        for author in db_record["contributors"]:
            name_parts = [author.get("given_name"), author.get("family_name")]
            name_parts += (
                [part.strip() for part in author.get("name").split(",")]
                if author.get("name")
                else []
            )
            name_parts = list(filter(None.__ne__, name_parts))

            if len(name_parts) > 0:
                authors.append(" ".join(name_parts))
                authors.append(" ".join(reversed(name_parts)))

    return authors


def get_year(db_record):
    """
    Only the year of a publication gets indexed
    """
    if not db_record.get("publication_date"):
        return None

    return db_record["publication_date"][0]


def get_identifiers(db_record, identifier):
    """
    Identifiers of a specific type (= param identifier) should be searchable
    """
    identifiers = []

    if db_record["identifiers"]:
        identifiers += extract_identifiers(db_record["identifiers"],
                                           identifier)

    return identifiers


def extract_identifiers(identifiers, identifier_type):
    """
    Get identifiers of type identifier_type from list
    """
    filtered = filter(lambda i: i["type"] == identifier_type, identifiers)
    return list(map(lambda i: i["value"], filtered))
