#!/usr/bin/python3

# Copyright 2017-2024 Stephen Warren <swarren@wwwdotorg.org>
# Copyright 2021 Steve Undy <steve@roseundy.net>

import argparse
import flask
import gunicorn.app.base
import os
import re
import subprocess
import sys
import time

parser = argparse.ArgumentParser(
    prog=sys.argv[0],
    description='FCCH ACL server')
parser.add_argument('--root-dir', required=True)
args = parser.parse_args()

bin_dir = os.path.join(args.root_dir, 'bin')
update_acls_bin = os.path.join(bin_dir, 'generate-acls.sh')
var_dir = os.path.join(args.root_dir, 'var')
acl_dir = os.path.join(var_dir, 'acls')
acl_fn_prefix = 'acl-'
log_dir = os.path.join(var_dir, 'log')
access_log_fn_template = os.path.join(log_dir, 'access-%Y-%m.log')
access_log_ts_template = '%Y%m%dT%H%M%S.'
http_log_fn = os.path.join(log_dir, 'http.log')
run_dir = os.path.join(var_dir, 'run')
pid_fn = os.path.join(run_dir, 'gunicorn.pid')
acl_update_pid_fn = os.path.join(run_dir, 'acl-update.pid')
acl_update_log_fn = os.path.join(log_dir, 'acl-update.log')
web_dir = os.path.join(args.root_dir, 'web')

app = flask.Flask(
    __name__,
    static_url_path='',
    static_folder=web_dir + '/static',
    template_folder=web_dir + '/templates',
)

re_acl_name = re.compile('^[a-z0-9_.-]+$')

def log_exception():
    import traceback
    traceback.print_exc(file=sys.stderr)

def acl_fn(acl):
    if not re_acl_name.match(acl):
        raise Exception('Invalid ACL ID', acl)
    return os.path.join(acl_dir, acl_fn_prefix + acl)

def show_file(fn, template, **extra):
    try:
        with open(fn, 'rt') as f:
            content=f.read()
    except:
        log_exception()
        content='Could not read log file'
    return flask.render_template(template, content=content, **extra)

class CantDetermineRunning(Exception):
    def __init__(self, seconds_left):
        self.seconds_left = seconds_left

def update_acls_running():
    if not os.path.exists(acl_update_pid_fn):
        return False
    try:
        with open(acl_update_pid_fn, 'rt') as pidf:
            pid_str = pidf.read().strip()
        if not pid_str:
            return False
        pid = int(pid_str)
        os.kill(pid, 0)
    except ProcessLookupError:
        running = False
    except:
        log_exception()
        pid_mtime = os.stat(acl_update_pid_fn).st_mtime
        when_assume_now_running = pid_mtime + 120
        now = time.time()
        time_left_until_assume_not_running = int(when_assume_now_running - now)
        if time_left_until_assume_not_running <= 0:
            running = False
        else:
            return time_left_until_assume_not_running
    else:
        running = True
    if not running:
        try:
            # Slightly racy if we happen to launch a new job exactly at this time.
            # We should really use a lockfile to manage the pidfile...
            os.unlink(acl_update_pid_fn)
        except:
            log_exception()
    return running

def update_acls_start():
    try:
        is_running = update_acls_running()
    except CantDetermineRunning as e:
        return f'Could not determine whether update is in progress; please wait {e.seconds_left} seconds and try again'
    if is_running:
        return 'Already running'
    try:
        with open(acl_update_log_fn, 'wt') as logf:
            sp = subprocess.Popen([update_acls_bin, acl_dir],
                stdout=logf, stderr=logf)
        pid = sp.pid
    except Exception as e:
        log_exception()
        import traceback
        return 'Could not start update process:\n' + '\n'.join(traceback.format_exception(e))
    try:
        with open(acl_update_pid_fn, 'wt') as pidf:
            pidf.write(str(pid))
    except Exception as e:
        log_exception()
        import traceback
        return 'Could not record update pid; please wait 1 minute before retrying:\n' + '\n'.join(traceback.format_exception(e))
    return None

def access_log_fn():
    return time.strftime(access_log_fn_template)

last_ts = None
ts_seq_num = 0
def gen_ts():
    global ts_seq_num
    global last_ts
    ts = time.strftime(access_log_ts_template)
    if ts == last_ts:
        ts_seq_num += 1
    else:
        ts_seq_num = 0
    last_ts = ts
    return ts + str(ts_seq_num)

@app.route('/')
def index():
    return flask.render_template('index.html')

@app.route('/ui/update-acls')
def ui_update_acls():
    message = update_acls_start()
    if message:
        return flask.render_template('ui-update-acls.html', message=message), 409
    else:
        return flask.redirect('/ui/view-acl-update-log', code=302)

@app.route('/ui/view-acl-update-log')
def ui_view_acl_update_log():
    running = update_acls_running()
    return show_file(acl_update_log_fn, 'ui-view-acl-update-log.html', running=running)

@app.route('/ui/view-acls')
def ui_view_acls():
    fns = sorted(os.listdir(acl_dir))
    acls = [acl[len(acl_fn_prefix):] for acl in fns if acl.startswith(acl_fn_prefix)]
    return flask.render_template('ui-view-acls.html', acls=acls)

@app.route('/ui/view-acl/<acl>')
def ui_view_acl(acl):
    return show_file(acl_fn(acl), 'ui-view-acl.html', name=acl)

@app.route('/ui/view-access-check-log')
def ui_view_access_check_log():
    return show_file(access_log_fn(), 'ui-view-access-check-log.html')

@app.route('/ui/view-http-log')
def ui_view_http_log():
    return show_file(http_log_fn, 'ui-view-http-log.html')

@app.route('/api/check-access-0/<acl>/<rfid>')
def api_check_access_0(acl, rfid):
    result = False
    with open(acl_fn(acl), 'rt') as f:
        for l in f.readlines():
            if l.strip() == rfid:
                result = True
                break
    with open(access_log_fn(), 'at+') as f:
        print('%s,check,%s,%s,%s' % (gen_ts(), acl, rfid, repr(result)), file=f)
    return flask.Response(repr(result), mimetype='text/plain')

@app.route('/api/log-remote-access-check-0/<acl>/<rfid>/<result>')
def api_log_remote_access_check_0(acl, rfid, result):
    with open(access_log_fn(), 'at+') as f:
        print('%s,check,%s,%s,%s' % (gen_ts(), acl, rfid, result), file=f)

@app.route('/api/get-acl-0/<acl>')
def api_get_acl_0(acl):
    with open(acl_fn(acl), 'rt') as f:
        return flask.Response(f.read(), mimetype='text/plain')

class GUnicornApp(gunicorn.app.base.BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {key: value for key, value in self.options.items()
            if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application

# A GUnicorn worker launches the ACL update process.
# This signal handler is installed in each worker to reap any such process.
# It does not get installed in the main GUnicorn master process.
# If the worker dies before the ACL update process exits, the ACL update
# process will be reparented to PID 1, which will also reap it.
def on_sig_child(signum, frame):
    while True:
        try:
            (pid, status) = os.waitpid(-1, os.WNOHANG)
            if pid == 0:
                break
        # Docs say (0, 0) is returned with WNOHANG, but in practice we get
        # this exception.
        except ChildProcessError:
            break

def post_worker_init(worker):
    import signal
    orig = signal.signal(signal.SIGCHLD, on_sig_child)

options = {
    'bind': '%s:%s' % ('', '8080'),
    'workers': 2,
    'accesslog': http_log_fn,
    'pidfile': pid_fn,
    'post_worker_init': post_worker_init,
}
GUnicornApp(app, options).run()
