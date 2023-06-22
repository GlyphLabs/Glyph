FROM python:3.11-slim-bookworm AS build
# RUN python3 -m venv /venv
WORKDIR /app

FROM build AS install-poetry
RUN python3 -m pip install "poetry==1.5.1"

FROM install-poetry AS build-poetry
COPY pyproject.toml poetry.lock /
RUN python3 -m poetry export --without-hashes --format requirements.txt --output /requirements.txt

FROM build-poetry AS install-deps
RUN python3 -m pip install --disable-pip-version-check -r /requirements.txt

FROM install-deps AS runtime
COPY . /app
CMD ["python3", "main.py"]