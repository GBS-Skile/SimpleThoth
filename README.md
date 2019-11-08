# Installing Guide

```
$ docker build -t simplethoth .
$ docker run -d -p 5000:5000 --name CONTAINER_NAME \
    -v $(pwd)/scenarios/YOUR_SCENARIO.json:/app/scenario.json \
    -e SCENARIO_PATH=scenario.json
```
