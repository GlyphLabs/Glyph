FROM python:3.11.4-slim-bullseye AS build
RUN python3 -m venv /venv
WORKDIR /app

FROM build AS install-poetry
RUN /venv/bin/pip install "poetry==1.5.1"

FROM install-poetry AS build-poetry
COPY pyproject.toml poetry.lock /
RUN /venv/bin/poetry export --without-hashes --format requirements.txt --output /requirements.txt

FROM build-poetry AS build-venv
RUN /venv/bin/pip install --disable-pip-version-check -r /requirements.txt

FROM gcr.io/distroless/python3-debian11
COPY --from=build-venv /venv /venv
COPY . /app
WORKDIR /app
ENTRYPOINT ["/venv/bin/python", "main.py"]