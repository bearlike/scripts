#!/usr/bin/env python3
""" 
Adds DNS A records pointing to a mentioned server using Cloudflare API v4. Edit places necessary. 

Note:
For better codebase privacy/security, refer configuration file for
authentication in python-cloudflare docs. This is for internal usage.
"""
import CloudFlare  # pip3 install cloudflare
import sys


def print_help():
    help_string = """
    Adds DNS A records pointing to this server.
    
     USAGE
    =======
    python3 create-dns-record.py [ZONE_NAME] [SUBDOMAIN]

     EXAMPLE (creates subdomain.example.com)
    =======================================
    python3 create-dns-record.py example.com subdomain
    """
    print(help_string)


def return_zone_info(cf, zone_name):
    try:
        zone_info = cf.zones.get(params={'name': zone_name})[0]
    except IndexError:
        print("Zone does not exist in this token.")
        exit(-1)
    return zone_info


def add_record(zone_name, subdomain):
    cf = CloudFlare.CloudFlare(
        token='REPLACE THIS WITH THE CLOUDFLARE API TOKEN')
    zone_info = return_zone_info(cf, zone_name)
    zone_id = zone_info['id']
    dns_record = {'name': subdomain, 'type': 'A', 'content': 'XXX.XXX.XXX.XXX'}
    try:
        r = cf.zones.dns_records.post(zone_id, data=dns_record)
    except CloudFlare.exceptions.CloudFlareAPIError:
        print("Record already Exist.")
        exit(-1)
    if r['name'] == subdomain+'.'+zone_name:
        print(r['name'], "added successfully.")
    exit(0)


if __name__ == '__main__':
    try:
        zone_name = sys.argv[1]
        subdomain = sys.argv[2]
    except IndexError:
        print_help()
    add_record(zone_name, subdomain)
