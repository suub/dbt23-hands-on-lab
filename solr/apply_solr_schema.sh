#!/bin/bash

# Applies the schema to Solr instance

curl -X POST -H 'Content-type:application/json' --data-binary '@schema.json' http://localhost:8983/solr/workshop/schema
