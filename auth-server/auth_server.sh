#!/usr/local/bin/bash

# Re-spawn as a background process, if we haven't already.
if [[ "$1" != "-n" ]]; then
    nohup "$0" -n > /dev/null 2>&1 &
    exit $?
fi

set -e


script_dir="$(dirname "$0")"
app_dir="$(cd "${script_dir}"/.. && pwd)"

echo $$ > "${app_dir}/var/pid2"


export LC_ALL=am_ET.UTF-8
export LANG=am_ET.UTF-8

cd $script_dir

. "${app_dir}/venv/bin/activate"
#/usr/local/bin/uwsgi --ini /usr/home/acl/acl-server/auth-server/auth_server.ini
exec /usr/local/bin/uwsgi --ini /usr/home/acl/acl-server/auth-server/auth_server.ini

