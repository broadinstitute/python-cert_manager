FROM python:3.10-slim

COPY poetry.lock pyproject.toml README.md /working/

WORKDIR /working

RUN apt-get update \
    && apt-get upgrade -yq \
    && apt-get install -yq gcc libffi-dev \
    && pip install pip poetry --upgrade \
    && poetry install \
    && rm -f /etc/localtime \
    && ln -s /usr/share/zoneinfo/America/New_York /etc/localtime \
    && rm -rf /tmp/* \
    && rm -rf /var/cache/apt/* \
    && rm -rf /var/tmp/*

ENTRYPOINT ["poetry", "run"]

CMD ["bash"]
