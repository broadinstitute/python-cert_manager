FROM python:3.8-alpine

COPY pyproject.toml README.md /usr/src/

WORKDIR /usr/src

RUN apk update \
    && apk add bash curl gcc git libffi-dev libxml2-dev libxslt-dev musl-dev openssl-dev \
    && pip install pip poetry --upgrade \
    && poetry install \
    && rm -f /etc/localtime \
    && ln -s /usr/share/zoneinfo/America/New_York /etc/localtime \
    && rm -rf /tmp/* \
    && rm -rf /var/cache/apk/* \
    && rm -rf /var/tmp/*

CMD ["bash"]
