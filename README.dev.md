# Development

On an x86 Linux PC (e.g. running Debian 12, Ubuntu 22.04, e.g. the NAS
itself...):

```shell
cd fcch-acl-server/
dpkg-buildpackage -us -uc && \
    scp ../fcch-acl-server_1_all.deb root@10.1.10.146:/tmp && \
    ssh root@10.1.10.146 sudo apt -y install --reinstall /tmp/fcch-acl-server_1_all.deb
```

Once testing is comlete, upload the package to our website, for easy access
from machines during setup:

```shell
scp ../fcch-acl-server_1_all.deb fcch-web:/home/u930-v2vbn3xb6dhb/www/fortcollinscreatorhub.org/public_html/rpi-packages
```
