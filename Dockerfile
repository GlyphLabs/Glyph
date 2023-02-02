FROM python:3.9.16-slim AS build
  RUN python3 -m venv /venv && \
  /venv/bin/pip install poetry

FROM build AS build-venv
COPY pyproject.toml poetry.lock /
RUN /venv/bin/poetry export --without-hashes --format requirements.txt --output /requirements.txt
RUN /venv/bin/pip install --disable-pip-version-check -r /requirements.txt

FROM gcr.io/distroless/python3-debian11
COPY --from=build-venv /venv /venv
COPY . /app
WORKDIR /app
ENTRYPOINT ["/venv/bin/python3", "src/main.py"]