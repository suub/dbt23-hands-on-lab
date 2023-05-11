# Nightwatch Workshop

This repository contains information that is needed to participate in the Nightwatch hands-on lab [Das Tool Nightwatch - Metadatenmanagement zum Anfassen](https://dbt2023.abstractserver.com/program/#/details/sessions/39) at BiblioCon2023.

Please complete the steps in [Preparation](#preparation) before the workshop.

[[_TOC_]]


## Prerequisites

* docker (e.g. https://docs.docker.com/desktop/)
* docker compose (included in docker desktop or https://docs.docker.com/compose/install/)


## Preparation

Clone this repository

```
git clone https://gitlab.suub.uni-bremen.de/public-projects/nightwatch-workshop.git
cd nightwatch-workshop
```

Pull all images (could take a few minutes, don't use mobile data)

```
docker compose pull
```

and check if you can start them on your computer with

```
docker compose up -d
```

The following webapps will we available after a few seconds:

* Nightwatch UI at [localhost:4000](http://localhost:4000)
* RabbitMQ Management console at [localhost:15672](http://localhost:15672) (Username: `guest`, Password: `guest`)
* Solr Admin at [localhost:8983](http://localhost:8983) (will be filled during the workshop)
* "Discovery" App at [localhost:5000](http://localhost:5000) (will be filled during the workshop) -- added in next version

Visit the Nightwatch UI, create a user and login. Try running the Sleep Pipeline from the Pipelines View. It's a simple Pipeline to check the connection between Nightwatch, RabbitMQ and the Metadata-Worker.

When the Sleep Pipeline succeeds, you are prepared for the workshop :tada:. 

More complex pipelines will be added (by you) during the workshop.


## Support

If you have any issues, please don't hesitate to contact us before the hands-on lab.

[Contact us](mailto:nitghtwatch@suub.uni-bremen.de)
