#!/usr/local/bin/bash

# Re-spawn as a background process, if we haven't already.
if [[ "$1" != "-n" ]]; then
    nohup "$0" -n > /dev/null 2>&1 &
    exit $?
fi

set -e


script_dir="$(dirname "$0")"
app_dir="$(cd "${script_dir}"/.. && pwd)"

echo $$ > "${app_dir}/var/pid"

#export LC_ALL=C.UTF-8
#export LANG=C.UTF-8
export LC_ALL=am_ET.UTF-8
export LANG=am_ET.UTF-8

. "${app_dir}/venv/bin/activate"
export FLASK_APP="${app_dir}/auth-server/auth-server.py"
#export FLASK_DEBUG=1
exec flask run --host=0.0.0.0 --port=8080
