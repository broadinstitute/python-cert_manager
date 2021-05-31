FROM python:3.8-alpine

COPY Pipfile* /usr/src/

WORKDIR /usr/src

RUN apk update \
    && apk add bash gcc git libffi-dev libxml2-dev libxslt-dev musl-dev openssl-dev rust \
    && pip install pipenv==2018.11.26 --upgrade \
    && pipenv lock \
    && pipenv sync --dev \
    && rm -rf /tmp/* \
    && rm -rf /var/cache/apk/* \
    && rm -rf /var/tmp/*

CMD ["bash"]
