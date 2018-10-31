# Notes

These instructions were tested on a Raspberry Pi 3 for speed. They should work
identically on a Raspberry Pi Zero W. Alternatively, set up the SD card on the
Pi 3, and transfer it to a Pi Zero W for production.

# Download the OS

https://www.raspberrypi.org/downloads/raspbian/

Raspbian Lite; not the "with desktop" variant since that's bigger, will be
slower to boot, and run more processes that take up precious RAM.

# Install OS to SD card

On your host PC:

    unzip 2018-03-13-raspbian-stretch-lite.zip
    # CAREFUL: Change /dev/sdc to the correct device in the command below!
    sudo dd if=2018-03-13-raspbian-stretch-lite.img of=/dev/sdc bs=32768

Now, insert the SD card into a Pi, connect an HDMI display, and USB keyboard
and mouse. Boot the system. If you're feeling fancy, you can perform the next
few steps using the serial console instead, but these instructions don't
describe that approach.

Pretty much all commands below are assumed to be run as root on the Raspberry
Pi. Once you've logged in as the `pi` user (via HDMI/USB or via ssh), run the
following command to get a root shell:

    sudo bash

# Localization configuration

Run:

    raspi-config

Use the menus to set:
- Localization -> Keyboard layout (US)
- Localization -> Timezone (America -> Denver)
- Localization -> Change WiFi Country -> US
- Network options -> Hostname: HAL
- Network options -> WiFi -> set SSID/password
- Interfacing options -> SSH -> Yes
- Interfacing options -> VNC -> No
- Interfacing options -> Serial -> Login over serial: No, Serial port HW enabled: Yes
- Advanced -> Expand Filesystem
- Finish -> reboot

# Set up SSH key-based access

On a system other than the Pi:

    ssh -oPubkeyAuthentication=no pi@192.168.63.200

(Here we assume that 192.168.63.200 is the Pi's IP address; you can obtain
this by running `ifconfig` on the Pi).

You will be prompted for the pi user's password on the Raspberry Pi.

Then, on the Pi:

    mkdir .ssh/
    vi .ssh/authorized_keys

In the editor, paste in your SSH public key. You can find sample content in
`backup/home-pi-ssh-authorized_keys`.

Set file permissions correctly:

    chmod -R og-rwx ~/.ssh

# Test SSH key-based access

On a system other than the Pi, in a different terminal to your existing SSH
session:

    ssh pi@192.168.63.200

You should not be prompted for the `pi` user's password, although you may be
prompted for your local SSH key password. If you are prompted for the `pi`
user's password, something is wrong with the authorized_keys file.

Exit the new SSH session, keeping the existing original session.

# Disable SSH password access

Edit `/etc/ssh/sshd_config` to edit the following lines:

from:

    #PubkeyAuthentication yes

to:

    PubkeyAuthentication yes

from:

    #HostbasedAuthentication no

to:

    HostbasedAuthentication no

from:

    #PasswordAuthentication yes

to:

    PasswordAuthentication no

from:

    #KerberosAuthentication no

to:

    KerberosAuthentication no

from:

    #GSSAPIAuthentication no

to:

    GSSAPIAuthentication no

Alternatively, you can copy `backup/etc-ssh-sshd_config` to
`/etc/ssh/sshd_config`.

Restart the SSH server:

    service ssh restart

On a system other than the Pi, in a different terminal to your existing SSH
session:

    ssh pi@192.168.63.200

You should still be able to log in, and should not be prompted for the `pi`
user's password.

    ssh -oPubkeyAuthentication=no pi@192.168.63.200

You should not be able to log in this way. You'll likely see error `Permission
denied (publickey)`.

Now, reboot the Pi and re-run the previous two tests.

From this point forward, you can connect to the Pi using SSH. So, disconnect
the HDMI monitor, keyboard, and mouse.

# System packages

    apt -y update
    apt -y dist-upgrade
    apt -y install \
        build-essential \
        git \
        python3-dev \
        virtualenv \
        postfix \
        mailutils \
        links

When prompted for the type of mail configuration to install, select "No
configuration"; we'll configure it manually later.

# Git clone

Download the door controller software. This will place a local copy of various
config files onto the Pi for use by later steps. DO NOT run the door
controller install script yet.

    cd /opt/
    git clone https://github.com/fortcollinscreatorhub/access-control.git fcch-access-control

# Mail Server

Install email configuration files:

    cp etc-aliases /etc/aliases
    cp etc-mailname /etc/mailname
    cp etc-postfix-main.cf /etc/postfix/main.cf
    cp etc-postfix-relay_passwords /etc/postfix/relay_passwords
    newaliases

Replace the password in the file with the real one (get the password from
bluehost or from swarren)

    cd /etc/postfix/
    vi relay_passwords
    postmap relay_passwords 

Restart postfix:

    service postfix restart

Test postfix:

    echo test|mail -s test sysadmin@fortcollinscreatorhub.org

Note: You could try sending a test email to your own personal email address.
However, I've found that Bluehost (FCCH's email hosting provider) eats email
sent from HAL to addresses other than mailing lists hosted on Bluehost:-(

# Install access control software

Copy the Google drive authentication file to the Pi:

On your host system:

    scp path/to/client_secret.json pi@192.168.63.200:/tmp/

Get that file from swarren. You can also get it from the Google application
console website.

On the Pi:

    cd /opt/fcch-access-control/
    mv /tmp/client_secret.json etc/
    chown 0:0 etc/client_secret.json 
    chmod 644 etc/client_secret.json 

Run the install script:

    ./bin/install.sh

... and follow the various instructions that it prints. The last thing the
script should print is shown below; if the script stops at any other time,
some error occurred, which must be debugged and fixed.

    + systemctl start fcch-access-control-door-controller

# Configure log backups

## Create an SSH key

Run the following to create a key. Don't create a passphrase.

    cd /opt/fcch-access-control/
    install -d /opt/fcch-access-control/.ssh -m 0770 -o root -g fcchaccess
    ssh-keygen -t rsa -b 4096 -f /opt/fcch-access-control/.ssh/id_rsa
    chown root:fcchaccess /opt/fcch-access-control/.ssh/id_rsa{,.pub}
    chmod ug+r /opt/fcch-access-control/.ssh/id_rsa{,.pub}

## Configure the FCCH webserver to accept backups

On the FCCH webserver (fortcon5@fortcollinscreatorhub.org), ensure that the
Pi's /opt/fcch-access-control/.ssh/id_rsa.pub is part of the web server's
/home2/fortcon5/.ssh/authorized_keys. The entry should include a force command
definition, as shown below:

    # HAL (door access control) backups
    command="rsync --server -re.iLsfxC . /home2/fortcon5/backup-hal-var/" ssh-rsa AAAA...Go0yhn91Q== root@HAL

# Set up cron jobs

    crontab -u fcchaccess /opt/fcch-access-control/backup/var-spool-cron-crontabs-fcchaccess

The crontab includes jobs for:
- Updating the ACLs each night.
- Backup up the log files each night.

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

The following commands can be useful when debugging any issues:

    systemctl enable $(pwd)/etc/systemd/fcch-access-control-auth-server.service
    systemctl disable fcch-access-control-auth-server.service
    systemctl start/stop/restart fcch-access-control-auth-server
    journalctl -u fcch-access-control-auth-server

    systemctl enable $(pwd)/etc/systemd/fcch-access-control-door-controller.service
    systemctl disable fcch-access-control-door-controller.service
    systemctl start/stop/restart fcch-access-control-door-controller
    journalctl -u fcch-access-control-door-controller

    # The correct port depends on which Pi HW you're running on. Use ttyS0 for
    # Pi 3 and Pi Zero W at least. These picocom commands rely on the main
    # access control software being stopped, since the serial port can't be
    # shared between the two applications. You may need to
    # `sudo apt install picocom`.
    picocom -b 9600 /dev/ttyS0
    picocom -b 9600 /dev/ttyAMA0

Log files are in `/opt/fcch-access-control/var/log/`.
