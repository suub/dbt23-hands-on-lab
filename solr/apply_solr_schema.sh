#!/bin/bash

# Applies the schema to Solr instance
curl -X POST -H 'Content-type:application/json' --data-binary '{    
    "add-field": [
        {
            "name": "title",
            "type": "text_de",
            "stored": true,
            "indexed": true
        },
        {
            "name": "author",
            "type": "text_general",
            "stored": true,
            "indexed": true,
            "multiValued": true
        },
        {
            "name": "title_authors",
            "type": "text_de",
            "indexed": true,
            "stored": true
        },
        {
            "name": "year",
            "type": "pint",
            "stored": true,
            "indexed": true
        },
        {
            "name": "issn",
            "type": "strings",
            "stored": true,
            "indexed": true
        },
        {
            "name": "abstract",
            "type": "text_de",
            "indexed": true,
            "stored": false
        }
    ]
}' http://nightwatch-solr:8983/solr/workshop/schema
