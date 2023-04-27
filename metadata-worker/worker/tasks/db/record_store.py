"""
Script to store converted records in a PostgreSQL DB

================== Nightwatch usage ==================
{
    "id": "worker.tasks.db.record_store",
        "name": "Put records in DB",
        "params": {
            "db": "<DB_CON>",
            "table": "records"
        }
    }
}
example for DB_CON:
    "DB_CON": "postgresql://nw:nw@nightwatch-db:5432/nw"
======================================================
"""

import psycopg2
from psycopg2.sql import Identifier, SQL
from psycopg2.extras import DictCursor, Json, execute_values
from datetime import datetime
import time
from worker.nw.utils import Result
from worker.nw.log import get_logger

logger = get_logger(__name__)

LOCAL_TZ = datetime.now().astimezone().tzinfo
# which columns should be stored
RECORDS_TABLE_COLUMNS = [
    "access_options",
    "contributors",
    "created",
    "id",
    "identifiers",
    "publication_date",
    "source",
    "title"
]
# JSONB columns need extra treatment
JSONB_COLUMNS = [
    "access_options",
    "contributors",
    "identifiers"
]


def run(opts) -> Result:
    """
    This method receives records, a db connection and a table name and inserts
    the records into the given db table

    Parameters
    ----------
    param opts: dict, required
        Contains data from the previous job and parameters given in the
        blueprint of the pipeline.

        opts["data"]: list(dict), contains converted records, ready to be
                      inserted

        Input parameters in opts["params"]:
        - param db: str, required
            connection detail to database in the following format:
            "postgresql://<user>:<password>@<host>:<port>/<database>"
            e.g.: postgresql://nw:nw@nightwatch-db:5432/nw"
        - param table: str, required
            name of the db table containing the records

    Returns
    ------
    Result:
        - Result
            A nightwatch Result with the parameters:
            - param dict metrics: statistics about inserted records

    """
    db, table = get_params(opts.get("params"))

    con = psycopg2.connect(db, cursor_factory=DictCursor)
    metrics = insert(opts["data"], con, table)
    con.close()

    return Result(metrics=metrics)


def get_params(params) -> (str, str):
    """
    Extract parameters from given params dict
    """
    db = params.get("db")
    table = params.get("table")

    if not db:
        raise ValueError('"db" parameter missing')
    if not table:
        raise ValueError('"table" parameter missing')

    return db, table


def insert(records, con, table, no_update) -> dict:
    """
    Insert new records into the db

    Returns
    ------
    Statistics about the insertion
    """
    record_ids = [record["id"] for record in records]
    db_record_map = get_db_records(record_ids, con, table)

    inserts = prepare_inserts(records, db_record_map)

    logger.debug(f"records to insert: {len(inserts)}")
    failed = insert_records(inserts, con, table)

    return {
        "total": len(records),
        "new": len(inserts),
        "failed": failed
    }


def get_db_records(record_ids, con, table) -> dict:
    """
    Get existing records with matching ids from the db

    Returns
    ------
    Existing records with matching ids
    """
    cur = con.cursor()
    cur.execute(
        SQL("SELECT * FROM {} WHERE id = ANY(%s);").format(Identifier(table)),
        [record_ids],
    )
    record_map = {record["id"]: dict(record) for record in cur.fetchall()}
    con.commit()
    cur.close()
    return record_map


def prepare_inserts(records, db_record_map) -> list(dict):
    """
    Filters for records that don't exist yet

    Returns
    ------
    Records to be inserted
    """
    inserts = []
    for record in records:
        db_record = db_record_map.get(record["id"])
        if not db_record:
            record["created"] = datetime.now(LOCAL_TZ)
            inserts.append(record)
            continue

    return inserts


def insert_records(records, con, table) -> int:
    """
    Insert records into given db table

    Returns
    ------
    Number of failed inserts
    """
    table = Identifier(table)
    query = SQL("INSERT INTO {} ({}) VALUES %s;").format(
        table, SQL(",").join([Identifier(c) for c in RECORDS_TABLE_COLUMNS])
    )

    records = [prepare_for_db(r) for r in records]
    record_tuples = [
        tuple(r[k] for k in RECORDS_TABLE_COLUMNS) for r in records
    ]
    retries = 0
    commited = False
    while not commited:
        try:
            cur = con.cursor()
            execute_values(cur, query, record_tuples)
            con.commit()
            commited = True
        except Exception:
            con.rollback()
            retries += 1
            if retries < 5:
                time.sleep(30)
                continue
            return len(records)
        finally:
            cur.close()
    return 0


def prepare_for_db(record) -> dict:
    """
    Prepare and clean the records for insertion in three steps
    1. Convert python dict to Json string for JSONB columns
    2. Remove entry in record if it's not a db column
    3. Add empty column data, if it doesn't exist yet in the record
    """
    for column in JSONB_COLUMNS:
        val = record.get(column)
        if val and len(val) > 0:
            record[column] = Json(record[column])
        else:
            record[column] = None

    for k in set(record.keys()):
        if k not in RECORDS_TABLE_COLUMNS:
            del record[k]

    for column in RECORDS_TABLE_COLUMNS:
        if column not in record:
            record[column] = None

    return record
