FROM python:3.7-alpine

COPY Pipfile* /usr/src/

WORKDIR /usr/src

RUN apk update \
    && apk add bash gcc git libxml2-dev libxslt-dev musl-dev \
    && pip install pipenv==2018.11.26 --upgrade \
    && pipenv lock \
    && pipenv sync --dev \
    && rm -rf /tmp/* \
    && rm -rf /var/cache/apk/* \
    && rm -rf /var/tmp/*

CMD ["bash"]
