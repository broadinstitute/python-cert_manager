#!/usr/bin/env bash

declare -g CHECKSUM_APP
declare -g CONTAINER_APP
declare -g CONTAINER_IMAGE='cert_manager:dev'
declare -g LABEL_PREFIX='org.broadinstitute.cert-manager'
declare -g SCRIPT_DIR
declare -ga TRACK_FILES=( Dockerfile poetry.lock pyproject.toml )
declare -ga SUDO
declare -ag TTY

SCRIPT_DIR="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if hash sha256sum 2>/dev/null; then
    CHECKSUM_APP='sha256sum'
elif hash shasum 2>/dev/null; then
    CHECKSUM_APP='shasum -a 256'
elif hash md5sum 2>/dev/null; then
    CHECKSUM_APP='md5sum'
else
    echo 'Could not find a checksumming program. Exiting!'
    exit 1
fi

if hash docker 2>/dev/null; then
    CONTAINER_APP='docker'
elif hash podman 2>/dev/null; then
    CONTAINER_APP='podman'
else
    echo 'Container environment cannot be found. Exiting!'
    exit 2
fi

if [[ "${TERM}" != 'dumb' ]]; then
    TTY=( -it )
fi

if [[ "${CONTAINER_APP}" = 'docker' ]] && [[ "$( uname -s )" != 'Darwin' ]]; then
    if [[ ! -w "${DOCKER_SOCKET}" ]]; then
        SUDO=( sudo )
    fi
fi

function build() {
    if [[ -z "$1" ]]; then
        echo 'Image name not provided to build. Exiting!'
        exit 1
    fi
    CONTAINER_IMAGE=$1

    if ! git diff --quiet; then
        echo 'Branch is dirty.  The build can only happen on an unmodified branch.'
        exit 2
    fi

    local -a labels
    for tfile in "${TRACK_FILES[@]}"; do
        label="$( "${CHECKSUM_APP}" "${tfile}" | awk -v PREFIX="${LABEL_PREFIX}" '{print PREFIX"."$2"="$1}' )"
        labels+=( --label "${label}" )
    done

    "${SUDO[@]}" "${CONTAINER_APP}" build --pull -t "${CONTAINER_IMAGE}" "${labels[@]}" .
}

pushd "${SCRIPT_DIR}" >/dev/null || exit 1
if ! "${SUDO[@]}" "${CONTAINER_APP}" image ls | awk '{print $1":"$2}' | grep --quiet -E "^(localhost\/)*${CONTAINER_IMAGE}"; then
    build "${CONTAINER_IMAGE}"
fi

rebuild='0'
for tfile in "${TRACK_FILES[@]}"; do
    current="$( "${CHECKSUM_APP}" "${tfile}" | cut -d' ' -f1 )"
    stored="$( "${CONTAINER_APP}" image inspect --format="{{index .Config.Labels \"${LABEL_PREFIX}.${tfile}\"}}" "${CONTAINER_IMAGE}" )"

    if [[ "${current}" != "${stored}" ]]; then
        echo "${tfile} changed.  Rebuilding."
        rebuild='1'
    fi
done

if [[ "${rebuild}" == '1' ]]; then
    build "${CONTAINER_IMAGE}"
fi

"${SUDO[@]}" "${CONTAINER_APP}" run "${TTY[@]}" --rm \
    -v "${SCRIPT_DIR}:/working" \
    "${CONTAINER_IMAGE}" "$@"

popd >/dev/null || exit 1
