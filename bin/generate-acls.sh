#!/bin/sh

# Copyright 2017-2024 Stephen Warren <swarren@wwwdotorg.org>
# Copyright 2018-2021 Steve Undy <steve@roseundy.net>

script_dir="$(realpath $(dirname "$0"))"
root_dir="$(realpath "${script_dir}/..")"
lib_python_dir="${root_dir}/lib/python"

acl_new_dir="$1"
if [ -z "${acl_new_dir}" ]; then
    echo "ERROR: acl_new_dir arg missing"
    exit 1
fi

acl_orig_dir="${root_dir}/var/acls-orig"
log_dir="${root_dir}/var/log"
acl_dl_log="${log_dir}/acl-download.log"
acl_diff_log="${log_dir}/acl-diff.log"
mkdir -p "${acl_new_dir}"
mkdir -p "${log_dir}"

export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
export PYTHONPATH="${lib_python_dir}${PYTHONPATH:+:${PYTHONPATH}}"

if [ -z "${GEN_ACLS_MAIL_WRAP}" ]; then
  acl_report="${log_dir}/acl-report.log"
  GEN_ACLS_MAIL_WRAP=1 "$0" "$@" > "${acl_report}" 2>&1
  ret=$?
  mail -s "FCCH ACL update @$(hostname)" sysadmin@fortcollinscreatorhub.org < "${acl_report}"
  cat "${acl_report}"
  exit ${ret}
fi

rm -rf "${acl_orig_dir}"
cp -ar "${acl_new_dir}" "${acl_orig_dir}"

"${root_dir}/bin/generate-acls.py" "${acl_new_dir}" > "${acl_dl_log}" 2>&1
ret=$?
if [ ${ret} -ne 0 ]; then
  echo DOWNLOAD LOG:
  cat "${acl_dl_log}"
  exit ${ret}
fi

diff -urN "${acl_orig_dir}" "${acl_new_dir}" > "${acl_diff_log}" 2>&1
ret=$?
echo ACL DIFF:
cat "${acl_diff_log}"
echo
echo
echo
echo
echo DOWNLOAD LOG:
cat "${acl_dl_log}"
exit 0
