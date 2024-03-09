#!/bin/sh

# Copyright 2023-2024 Stephen Warren <swarren@wwwdotorg.org>
# SPDX-License-Identifier: MIT

script_dir="$(realpath $(dirname "$0"))"
root_dir="$(realpath "${script_dir}/..")"
lib_python_dir="${root_dir}/lib/python"

export PYTHONPATH="${lib_python_dir}${PYTHONPATH:+:${PYTHONPATH}}"
exec "${script_dir}/fcch-acl-server.py" \
    --root-dir "${root_dir}"
