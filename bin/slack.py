import sys
import requests

url_fname = '/home/acl/acl-server/etc/slack_url'
with open(url_fname, 'r') as url_file:
	url = url_file.read()

outdata = ''
for line in sys.stdin:
	outdata += line

data = {'text': outdata}

rval = requests.post(url.rstrip(), json = data)
print(rval)
