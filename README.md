# Notes

This has been retargeted for a FreeNAS system (instead of the original Linux on Raspberry Pi).
This originally used Flask as the webserver, but has been moved to uwsgi

# Create Jail

Create a FreeNAS jail named "ACL", then shell into it

# System packages

            pkg install git
            pkg install python
            pkg install py37-pip
            pkg install links
            pkg install py37-flask
            pkg install wget
            pkg install uwsgi
            
# Create account

adduser acl

# Git clone

Download the door controller software.

    cd /home/acl
    git clone https://github.com/fortcollinscreatorhub/acl-server.git
    
# Install python dependencies and venv

    cd /home/acl/acl-server
    bash bin/install.sh

# Add to rc.d to start at boot

    cp etc/usr_local_etc_rc.d/aclserver /usr/local/etc/rc.d/aclserver
    chmod +x /usr/local/etc/rc.d/aclserver

# Set up cron jobs

Add to system crontab: (/etc/crontab)

    0   3   *   *   *  wget -O /dev/null 'http://localhost:8080/ui/update-acls' > /dev/null 2>&1
    
# Add api keys

- Get Wild Apriocot API key and add it to etc/client_secret
- Get Slack Webhook URL and add it to etc/slack_url
    
# Test

Reboot jail
Point web browser to http://<ACL JAIL IP>:8080 and make sure web pages are served

# Interacting with the web server from an SSH session

Use a text-mode/command-line web browser on the Pi:

    links http://127.0.0.1:8080/

Keyboard shortcuts:
- Arrows select links or scroll
- Enter follows a link
- Backspace goes back
- Ctrl-R refreshes
- q quits

# Debug logs

Log files are in `var/log/`

# TODO

- Mailing out no longer works. Needs to be converted to use Slack's API
- Logs are no longer backed up to the FCCH web site. Needs to be backed up somewhere.
