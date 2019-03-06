FROM python:3.6-alpine

COPY Pipfile* /usr/src/

WORKDIR /usr/src

RUN apk update \
    && apk add bash gcc git musl-dev \
    && pip install pipenv==2018.11.26 --upgrade \
    && pipenv install --dev --system \
    && rm -rf /tmp/* \
    && rm -rf /var/cache/apk/* \
    && rm -rf /var/tmp/*

CMD ["bash"]
