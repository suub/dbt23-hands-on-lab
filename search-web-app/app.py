from flask import Flask, render_template, request
from urllib.request import urlopen
import simplejson
import sys

app = Flask(__name__)

BASE_PATH='http://nightwatch-solr:8983/solr/workshop/select?wt=json&df=name&rows=250&q='

@app.route('/', methods=["GET","POST"])
def index():
    query = None
    numresults = None
    results = None

    # get the search term if entered, and attempt
    # to gather results to be displayed
    if request.method == "POST":
        query = request.form["searchTerm"]

        # return all results if no data was provided
        if query is None or query == "":
            query = "*:*"

        # query for information and return results
        print("{}{}".format(BASE_PATH, query), file=sys.stderr)
        connection = urlopen("{}{}".format(BASE_PATH, query))
        print(connection, file=sys.stderr)
        response = simplejson.load(connection)
        numresults = response['response']['numFound']
        results = response['response']['docs']

    return render_template('index.html', query=query, numresults=numresults, results=results)

if __name__ == '__main__':
    app.run(host='0.0.0.0')