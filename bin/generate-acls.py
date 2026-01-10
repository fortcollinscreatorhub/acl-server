#!/usr/bin/python3

# Copyright 2018-2022 Steve Undy <steve@roseundy.net>
# Copyright 2026 Stephen Warren <swarren@wwwdotorg.org>

__author__ = 'steve@roseundy.net'

import WaApi
import urllib.parse
import argparse
from filelock import FileLock
import os
import time
import sys
import datetime

# Configuration/policy

# Some ACLs get renamed
acl_mapping = {
    'blaser': 'big-laser-cutter',
    'mlaser': 'medium-laser-cutter',
    'slaser': 'small-laser-cutter',
}

# Everyone gets in the door and access to some basic tools
all_member_privs = [
    'door',
    'beltsander',
    'electronics-locker',
    'spindlesander'
]

apiKey_fname = 'wa-credentials'

# Implementation

bin_dir = os.path.dirname(__file__)
app_dir = os.path.dirname(bin_dir)
apiKey_fpath = os.path.join(
    app_dir,
    'etc',
    apiKey_fname)
acl_fname_prefix = 'acl-'

def get_apiKey(kpath):
    """Reads Wild Apricot API key from a file

    Returns: api key string
    """
    with open(kpath, 'r') as f:
        apiKey = f.readline().strip()
    return (apiKey)

def get_all_active_members(debug, contactsUrl):
    """Make an API call to Wild Apricot to retrieve
    contact info for all active members.

    Returns: list of contacts
    """

    # 7 days ago in yyyy-mm-dd format
    valid_date = str(datetime.date.today() - datetime.timedelta(days=7))

    pageSize = 100
    pageStart = 0
    contacts = []
    while True:
        params = {
            '$filter': "member eq true AND ( Status eq Active OR ( Status eq PendingRenewal AND 'Renewal due' ge " + valid_date + "))",
            '$async': 'false',
            '$top': pageSize,
            '$skip': pageStart,
        }
        request_url = contactsUrl + '?' + urllib.parse.urlencode(params)
        if debug: print('Making api call to get contacts')

        response = api.execute_request(request_url)
        thisPageContacts = response.Contacts
        contacts.extend(thisPageContacts)

        thisPageSize = len(thisPageContacts)
        if debug: print(f"pageStart {pageStart} thisPageSize {thisPageSize}")
        pageStart += thisPageSize
        if thisPageSize != pageSize:
            break
    return contacts

RFID_list = []
NAME_list = []

def grab_RFID(debug, contact):
    """Given a contact from Wild Apricot member database,
    pulls out list of RFIDs and privileges (ACLs)

    Adds to global RFID_list
    New: builds a name->rfid list (NAME_list)
    """
    global RFID_list
    global NAME_list

    privs = []
    privs.extend(all_member_privs)

    rfid_field = ''
    for field in contact.FieldValues:
        if (field.FieldName == 'RFID ID') and (field.Value is not None):
            rfid_field = field.Value
        if (field.FieldName == 'Privileges'):
            for privilege in field.Value:
                priv = privilege.Label.lower()
                privs.append(acl_mapping.get(priv, priv))
    rfids = []
    if rfid_field == '':
        return
    for rfid in rfid_field.split(','):
        rfid = int(rfid)
        RFID_list.append({'rfid':rfid, 'privs':privs})
        rfids.append(str(rfid))
        if debug: print ('Appending ACL - rfid:', rfid, 'privs:', privs)

    rfids_str = ','.join(rfids)
    NAME_list.append({'name':(contact.LastName + ',' + contact.FirstName), 'rfids':rfids_str})
    if debug: print ('Appending Name: ' + contact.LastName + ',' + contact.FirstName + ' rfids: ' + rfids_str)

def dump_RFIDs(debug, acl_dir, ts):
    """Reads stored list of RFID and writes
    ACL files with that data
    """

    # get existing list of acl files
    old_files = os.listdir(acl_dir)

    # sort RFIDs and generate list of privileges - we need the list to know what files to write
    privileges = set()
    RFID_list.sort(key=lambda x:x['rfid'])
    for e in RFID_list:
        for p in e['privs']:
            privileges.add(p)

    # open one file per privilege
    File = {}
    for f in privileges:
        fname = acl_fname_prefix + f
        fname_tmp = os.path.join(acl_dir, '.' + fname + '.tmp')
        File[f] = open (fname_tmp, 'w')
        if debug: print('Opened file:',fname_tmp)
        print('# Generated at', ts, file=File[f])
        try:
            old_files.remove(fname)
        except:
            pass

    # go back through list of RFIDs and write them to the appropriate file(s)
    for e in RFID_list:
        for p in e['privs']:
            File[p].write(str(e['rfid'])+'\n')

    # all done writing
    for f in File:
        File[f].close()

    # rename files just written
    for f in privileges:
        fname = os.path.join(acl_dir, acl_fname_prefix + f)
        fname_tmp = os.path.join(acl_dir, '.' + acl_fname_prefix + f + '.tmp')
        os.rename(fname_tmp, fname)

    # remove obsolete files
    for fname in old_files:
        if not fname.startswith(acl_fname_prefix):
            continue
        fpath = os.path.join(acl_dir, fname)
        os.unlink(fpath)

def dump_NAMEs(debug, acl_dir, ts):
    """Reads stored list of Names and writes
    Name file with that data
    """
    NAME_list.sort(key=lambda x:x['name'])

    fname_tmp = os.path.join(acl_dir, 'name_to_rfid')
    f = open (fname_tmp, 'w')
    if debug: print('Opened file:',fname_tmp)

    for e in NAME_list:
        f.write(e['name']+':'+str(e['rfids'])+'\n')

    f.close()

if __name__ == '__main__':
    ts = time.strftime('%Y%m%dT%H%M%S')
    parser = argparse.ArgumentParser(
        description='Download Access Control info (RFIDs) from Wild Apricot')
    parser.add_argument(
        '--debug', action='store_true', help='Turn on debugging prints')
    parser.add_argument(
        '--auth-only', action='store_true',
        help='Set up authentication, but don\'t download data')
    parser.add_argument(
        'output_dir', nargs='?',
        help='Directory to write RFID lists to')
    args = parser.parse_args()
    if args.debug: print(args)

    if not args.auth_only and not args.output_dir:
            parser.error('output_dir required if --auth-only not specified')

    # Start API and authenticate
    apiKey = get_apiKey(apiKey_fpath)

    api = WaApi.WaApiClient("CLIENT_ID", "CLIENT_SECRET")

    api.authenticate_with_apikey (apiKey, scope='account_view contacts_view')
    if args.debug: print('Authenticated')

    if args.auth_only:
        sys.exit(0)

    lock_fn = os.path.join(args.output_dir, ".lock")
    with FileLock(lock_fn):
        # Grab account details
        accounts = api.execute_request("/v2/accounts")
        account = accounts[0]
        contactsUrl = next(res for res in account.Resources if res.Name == 'Contacts').Url
        if args.debug: print('contactsUrl:', contactsUrl)

        # request contact details on all active members
        contacts = get_all_active_members(args.debug, contactsUrl)
        if args.debug: print ('Retrieved', len(contacts), 'contacts')

        # find the RFIDs and privileges and store them
        for contact in contacts:
            grab_RFID(args.debug, contact)

        # write the RFIDs to one or more files
        dump_RFIDs(args.debug, args.output_dir, ts)
        dump_NAMEs(args.debug, args.output_dir, ts)
        print('RFID lists generated OK at', ts)
