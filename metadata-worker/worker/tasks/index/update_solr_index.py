import psycopg2
from datetime import datetime, timezone
from psycopg2.sql import SQL, Identifier
from psycopg2.extras import DictCursor
from ...nightwatch.utils import Result
from ...nw.utils import httpxClient


CHUNK_SIZE = 10_000


def run(opts):
    solr_url, db, table, last_index = get_params(opts["params"])

    db_con = psycopg2.connect(db, cursor_factory=DictCursor)

    updated_count, solr_count = update_records(
        solr_url, db_con, table, last_index
    )

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


def get_params(params):
    solr_url = params.get("solr_url")
    db = params.get("db")
    table = params.get("table")
    last_index = params.get("last_index")

    if not solr_url:
        raise ValueError('"solr_url" parameter missing')
    if not db:
        raise ValueError('"db" parameter missing')
    if not table:
        raise ValueError('"table" parameter missing')
    if not last_index:
        last_index = "2000-01-01T00:00:00+00:00"

    last_index = datetime.fromisoformat(last_index)

    return solr_url, db, table, last_index


def update_records(solr_url, db_con, table, last_index):
    updated_record_count = 0
    update_url = solr_url.rstrip("/") + "/update?commit=true,overwrite=true"
    cur = db_con.cursor(name="uc")
    cur.itersize = CHUNK_SIZE
    cur.execute(
        SQL(
            "SELECT * FROM {} WHERE created > %s;"
        ).format(Identifier(table)),
        [last_index],
    )

    db_records = cur.fetchmany(CHUNK_SIZE)
    while db_records:
        records = [dict(r) for r in db_records]
        records = [convert_db_record(r) for r in records]
        body = {"add": records}
        httpxClient.post(update_url, json=body)
        updated_record_count += len(records)
        db_records = cur.fetchmany(CHUNK_SIZE)

    cur.close()
    query_url = solr_url.rstrip("/") + "/query?q=*:*&wt=json"
    result = httpxClient.get(query_url)

    return updated_record_count, result.json()["response"]["numFound"]


def convert_db_record(db_record):
    rec = {
        "id": db_record["id"],
        "created": datetime_to_iso(db_record["created"]),
        "title": db_record["title"],
        "author": get_authors(db_record),
        "year": get_year(db_record),
        "issn": get_identifiers(db_record, "issn"),
    }
    rec["title_authors"] = get_ta(rec["title"], rec["author"])
    return rec


def datetime_to_iso(dt):
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def get_ta(title, authors):
    return f'{title} {" ".join(authors[0::2])}'

def get_authors(db_record):
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
    if db_record["type"] == "journal":
        return get_first_publication_date(db_record)

    if not db_record.get("publication_date"):
        return None

    return db_record["publication_date"][0]


def get_identifiers(db_record, identifier):
    identifiers = []

    if db_record["identifiers"]:
        identifiers += extract_identifiers(db_record["identifiers"], identifier)

    if db_record["containers"]:
        for container in db_record["containers"]:

            if (
                container.get("type")
                and container["type"] not in INDEXED_CONTAINER_TYPES
            ):
                continue

            container_identifiers = container.get("identifiers")
            if container_identifiers:
                identifiers += extract_identifiers(
                    container_identifiers, identifier
                )

    return identifiers


def extract_identifiers(identifiers, identifier_type):
    filtered = filter(lambda i: i["type"] == identifier_type, identifiers)
    return list(map(lambda i: i["value"], filtered))
