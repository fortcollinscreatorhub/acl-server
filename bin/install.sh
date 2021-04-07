#!/bin/bash

set -e
set -x

script_dir="$(dirname "$0")"
app_dir="$(cd "${script_dir}"/.. && pwd)"

cd "${app_dir}"

if [ ! -d venv ]; then
  python3 -m venv venv
fi
(. ./venv/bin/activate && pip install --upgrade -r etc/pip-requirements.txt)

mkdir -p "${app_dir}/.credentials"
