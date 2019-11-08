# Transcripting Guide

Requirements: pipenv

```
$ pipenv install
$ pipenv shell
$ python -m src.transcript scripts/YOUR_SCRIPT_FILE.txt \
    > scenarios/YOUR_SCENARIO_FILE.json
```

# Installing Guide

```
$ docker build -t simplethoth .
$ docker run -d -p 5000:5000 --name CONTAINER_NAME \
    -v $(pwd)/scenarios/YOUR_SCENARIO.json:/app/scenario.json \
    -e SCENARIO_PATH=scenario.json simplethoth
```
