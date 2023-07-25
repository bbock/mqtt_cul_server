FROM python:3.10-slim

LABEL org.opencontainers.image.url="https://github.com/bbock/mqtt_cul_server"
LABEL org.opencontainers.image.authors="Bernhard Bock <bernhard@bock.nu>"
LABEL org.opencontainers.image.licenses="GPL-3.0"
LABEL org.opencontainers.image.title="MQTT CUL server"
LABEL org.opencontainers.image.description="Bridge to connect a CUL wireless transceiver with an MQTT broker"

ENV PYTHONUNBUFFERED 1
ENV POETRY_VIRTUALENVS_CREATE false

WORKDIR /mqtt_cul_server

COPY . .
RUN pip --no-cache-dir install poetry
COPY pyproject.toml poetry.lock /
RUN poetry install --only main

VOLUME /state

ENTRYPOINT [ "python", "server.py" ]
