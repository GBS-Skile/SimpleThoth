FROM python:3.7

RUN pip install pipenv
COPY Pipfile* /tmp/
RUN cd /tmp && pipenv lock --requirements > requirements.txt
RUN pip install -r /tmp/requirements.txt

COPY ./src/ /app/
WORKDIR /app

ENV FLASK_APP app
CMD flask run -h 0.0.0.0
