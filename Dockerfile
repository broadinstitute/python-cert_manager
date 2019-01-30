FROM python:3.6-alpine

COPY Pipfile* /usr/src/

RUN apk update \
    && apk add bash gcc git musl-dev \
    && pip install pipenv==2018.11.26 --upgrade \
    && cd /usr/src \
    && pipenv install --dev --system \
    && rm -rf /tmp/* \
    && rm -rf /var/cache/apk/* \
    && rm -rf /var/tmp/*

WORKDIR /usr/src

CMD ["bash"]
