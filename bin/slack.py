import sys
import requests

url_fname = '/home/acl/acl-server/etc/slack_url'
with open(url_fname, 'r') as url_file:
	url = url_file.read()

outdata = ''
for line in sys.stdin:
	outdata += line

url = 'https://hooks.slack.com/services/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'

data = {'text': outdata}

rval = requests.post(url, json = data)
print(rval)
