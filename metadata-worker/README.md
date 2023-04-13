# Metadata Worker

This project is a submodule of [Nightwatch Deployment](https://gitlab.suub.uni-bremen.de/public-projects/nightwatch-deployment) and contains the scripts to process metadata. It can also be used for local development.

## Local development and testing

1. Install necessary python libraries:
    ```
    poetry install
    ```
2. Define the process you want to test in `local_test.py`
3. Execute with 
    ```
    poetry run python -m local_test
    ```

## Usage

Every library or other information service probably needs specialised scripts for processing metadata. To customise the worker, this repository can be forked and scripts can be added or removed there. To change the [Nightwatch Deployment](https://gitlab.suub.uni-bremen.de/public-projects/nightwatch-deployment) to point to the correct scripts, correct the address given in the [.gitmodules file](https://gitlab.suub.uni-bremen.de/public-projects/nightwatch-deployment/-/blob/main/.gitmodules#L3) and synchronise: 
```
git submodule sync
```

When the worker(s) is/are already running and scripts were changed here, the worker(s) need(s) to be restarted to acknowledge the changes (Python caches modules, so the interpreter has to be restarted). The easiest way to restart all workers is

```
docker compose restart worker
```

## Support

If you find a bug or have ideas for features and improvement, please don't hesitate to create an issue.

[Contact us](mailto:nightwatch@suub.uni-bremen.de)
