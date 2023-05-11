from flask import Flask, render_template, request
import httpx
import json
import psycopg2
from psycopg2.extras import DictCursor
from psycopg2.sql import SQL, Identifier

app = Flask(__name__)

BASE_PATH='http://solr:8983/solr/workshop/select?wt=json&df=name&rows=250&q='
DB_CONN='postgresql://nw:nw@nightwatch-db:5432/nw'

SOLR_STRING_FIELDS = ["title", "author", "title_authors"]
SOLR_INT_FIELDS = ["year"]
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
DB_QUERY = "SELECT * FROM records WHERE id = $1);"

@app.route('/', methods=["GET","POST"])
def index():
    query = None
    numresults = None
    results = None
    db_results = None

    # get the search term if entered, and attempt
    # to gather results to be displayed
    if request.method == "POST":
        query_term = request.form["searchTerm"]

        # return all results if no data was provided
        if query_term is None or query_term == "":
            query = "*:*"
        else:
            query = buildQuery(query_term)

        # query for information and return results
        connection = httpx.get("{}{}".format(BASE_PATH, query))
        response = json.load(connection)
        numresults = response['response']['numFound']
        results = response['response']['docs']
        if numresults > 0:
            db_results = queryDBforFullRecords(results)

    return render_template('index.html', query=query, numresults=numresults, results=db_results)


def buildQuery(query_term):
    query = ""
    search_terms = []
    for field in SOLR_STRING_FIELDS:
        search_terms.append(u"{}:{}".format(field, query_term))
    for field in SOLR_INT_FIELDS:
        try:
            search_terms.append(u"{}:{}".format(field, int(query_term)))
        except:
            continue
    query = "%20OR%20".join(search_terms)
    return query


def queryDBforFullRecords(records):
    id_list = [r["id"] for r in records]
    id_list = tuple(e for e in id_list)
    query = "SELECT * FROM {} WHERE id in %(id_list)s"
    table = "records"

    with psycopg2.connect(DB_CONN, cursor_factory=DictCursor) as db_con:
        with db_con.cursor() as cur:
            cur.execute(SQL(query).format(Identifier(table)), {"id_list": id_list})
            db_records = cur.fetchall()

    db_records = [dict(r) for r in db_records]
    return db_records


if __name__ == '__main__':
    app.run(host='0.0.0.0')