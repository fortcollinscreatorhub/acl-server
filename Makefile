# Copyright 2023-2024 Stephen Warren <swarren@wwwdotorg.org>
# SPDX-License-Identifier: MIT

.PHONY: default
default: build

.PHONY: build
build:

.PHONY: install
install:
	install -D                               -d $(DESTDIR)/opt/fcch/acl-server/
	install -D                               -d $(DESTDIR)/opt/fcch/acl-server/bin/
	install -m 755 bin/fcch-acl-server.sh       $(DESTDIR)/opt/fcch/acl-server/bin/
	install -m 755 bin/fcch-acl-server.py       $(DESTDIR)/opt/fcch/acl-server/bin/
	install -m 755 bin/generate-acls.py         $(DESTDIR)/opt/fcch/acl-server/bin/
	install -m 755 bin/generate-acls.sh         $(DESTDIR)/opt/fcch/acl-server/bin/
	install -D                               -d $(DESTDIR)/opt/fcch/acl-server/etc/
	install -D                               -d $(DESTDIR)/opt/fcch/acl-server/lib/
	install -D                               -d $(DESTDIR)/opt/fcch/acl-server/lib/python/
	install -m 755 lib/python/WaApi.py          $(DESTDIR)/opt/fcch/acl-server/lib/python/
	install -D                               -d $(DESTDIR)/opt/fcch/acl-server/var/
	install -D                               -d $(DESTDIR)/opt/fcch/acl-server/var/log/
	install -D                               -d $(DESTDIR)/opt/fcch/acl-server/var/run/
	install -D                               -d $(DESTDIR)/opt/fcch/acl-server/var/acls/
	install -D                               -d $(DESTDIR)/opt/fcch/acl-server/web/templates/
	install -m 644 web/templates/*              $(DESTDIR)/opt/fcch/acl-server/web/templates/

	install -D                                     -d $(DESTDIR)/etc/logrotate.d
	install -m 644 etc/logrotate.d/fcch-acl-server    $(DESTDIR)/etc/logrotate.d

	# Must be in /lib not /opt/... for some reason?
	install -D -d $(DESTDIR)/lib/systemd/system/
	install -m 644 lib/systemd/system/fcch-acl-server.service $(DESTDIR)/lib/systemd/system/
