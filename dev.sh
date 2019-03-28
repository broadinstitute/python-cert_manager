#!/bin/bash

DOCKER_IMAGE='cert_manager:latest'
SUDO=

SCRIPT_DIR="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ "$TERM" != 'dumb' ] ; then
    TTY='-it'
fi

if [ "$( uname -s )" != 'Darwin' ]; then
    if [ ! -w "$DOCKER_SOCKET" ]; then
        SUDO='sudo'
    fi
fi

pushd "$SCRIPT_DIR" >/dev/null || exit 1

if ! $SUDO docker image ls | awk '{print $1":"$2}' | grep -q "$DOCKER_IMAGE"; then
    $SUDO docker build -t "$DOCKER_IMAGE" .
fi

$SUDO docker run $TTY --rm -v "$SCRIPT_DIR":/usr/src "$DOCKER_IMAGE" "$@"

popd >/dev/null || exit 1
