FROM debian:11-slim AS build
RUN apt-get update
RUN apt-get install --no-install-suggests --no-install-recommends --yes python3-venv libpython3-dev git
RUN python3 -m venv /venv
RUN /venv/bin/pip install "poetry==1.5.1"

FROM build AS build-venv
COPY pyproject.toml poetry.lock /
RUN /venv/bin/poetry export --without-hashes --format requirements.txt --output /requirements.txt
RUN /venv/bin/pip install --disable-pip-version-check -r /requirements.txt

FROM gcr.io/distroless/python3-debian11
COPY --from=build-venv /venv /venv
COPY . /app
WORKDIR /app
ENTRYPOINT ["/venv/bin/python3", "main.py"]