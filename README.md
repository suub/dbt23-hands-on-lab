# Nightwatch Workshop

## TODO Goal of this workshop

Maybe add a slide that contains crossref -> db -> solr -> search


![Nightwatch architecture diagram. The User Interface Nightwatch is bidirectionally connected to redis for supervising each job's status and to a PostgreSQL to store data.](docs/Nightwatch_architecture.png)


## Prerequisites

* docker (e.g. https://docs.docker.com/desktop/)
* docker compose (included in docker desktop or https://docs.docker.com/compose/install/)


## Preparation

Clone this repository

```
git clone https://gitlab.suub.uni-bremen.de/public-projects/nightwatch-workshop.git
```

Pull all images (could take a few minutes, don't use mobile data)

```
docker compose pull
```

and check if you can start them on your computer with

```
docker compose up -d
```

The nightwatch UI will be available at `localhost:4000` after a few seconds.


## Support

If you have issues, please don't hesitate to contact us before the hands-on lab.

[Contact us](mailto:nitghtwatch@suub.uni-bremen.de)
