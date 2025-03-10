# Installation instructions

This code is intended to run on Debian 12. It should run on any binary
architecture.

Update packages:

```shell
sudo apt update
sudo apt dist-upgrade
```

Install the fcch-acl-server package:

```shell
cd /tmp
wget https://www.fortcollinscreatorhub.org/rpi-packages/fcch-acl-server_6_all.deb
sudo apt install ./fcch-acl-server_6_all.deb
```

Create file `/opt/fcch/acl-server/etc/wa-credentials`:

```shell
touch                 /opt/fcch/acl-server/etc/wa-credentials
chown fcchacl:fcchacl /opt/fcch/acl-server/etc/wa-credentials
chmod 660             /opt/fcch/acl-server/etc/wa-credentials
vi                    /opt/fcch/acl-server/etc/wa-credentials
```

Place the relevant Wild Apricot credentials into this file.

# Usage

Visit `http://ip-address:8080/` to interact with the web interface.

# Troubleshooting

View service status:

```shell
service fcch-acl-server status
```

View service log:

```shell
journalctl -xeu fcch-acl-server
```

Restart service:

```shell
service fcch-acl-server restart
```
