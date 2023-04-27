import psycopg2
from psycopg2.sql import Identifier, SQL
from psycopg2.extras import DictCursor, Json, execute_values
from datetime import datetime
import time
from worker.nw.utils import Result
from worker.nw.log import get_logger

logger = get_logger(__name__)


LOCAL_TZ = datetime.now().astimezone().tzinfo
IGNORED_COMPARISON_KEYS = {
    "created",
    "id"
}
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
JSONB_COLUMNS = [
    "access_options",
    "contributors",
    "identifiers"
]


def run(opts):
    db, table = get_params(opts.get("params"))

    con = psycopg2.connect(db, cursor_factory=DictCursor)
    metrics = insert(opts["data"], con, table)
    con.close()

    return Result(metrics=metrics)


def get_params(params):
    db = params.get("db")
    table = params.get("table")

    if not db:
        raise ValueError('"db" parameter missing')
    if not table:
        raise ValueError('"table" parameter missing')

    return db, table


def insert(records, con, table, no_update):
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


def get_db_records(record_ids, con, table):
    cur = con.cursor()
    cur.execute(
        SQL("SELECT * FROM {} WHERE id = ANY(%s);").format(Identifier(table)),
        [record_ids],
    )
    record_map = {record["id"]: dict(record) for record in cur.fetchall()}
    con.commit()
    cur.close()
    return record_map


def prepare_inserts(records, db_record_map):
    inserts = []
    for record in records:
        db_record = db_record_map.get(record["id"])
        if not db_record:
            record["created"] = datetime.now(LOCAL_TZ)
            inserts.append(record)
            continue

    return inserts


def insert_records(records, con, table):
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


def prepare_for_db(record):
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
