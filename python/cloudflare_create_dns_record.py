#!/usr/bin/env python3
"""
Adds DNS A records pointing to a mentioned server using Cloudflare API v4.
Edit places necessary.

Note:
For better codebase privacy/security, refer configuration file for
authentication in python-cloudflare docs. This is for internal usage.
"""
import CloudFlare  # pip3 install cloudflare
import sys
from os import getenv
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.


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


def return_zone_info(cf, get_zone_name):
    try:
        zone_info = cf.zones.get(params={"name": get_zone_name})[0]
    except IndexError:
        print("Zone does not exist in this token.")
        sys.exit(-1)
    return zone_info


def add_record(zone_name, subdomain):
    c_token = getenv("CLOUDFLARE_API_TOKEN", default=None)
    c_ip = getenv("CLOUDFLARE_API_A_IP", default=None)
    if None in [c_token, c_ip]:
        print("Enviroinment variables not found.")
        sys.exit(-1)
    cf = CloudFlare.CloudFlare(token=c_token)
    zone_info = return_zone_info(cf, zone_name)
    zone_id = zone_info["id"]
    dns_record = {"name": subdomain, "type": "A", "content": c_ip}
    try:
        r = cf.zones.dns_records.post(zone_id, data=dns_record)
    except CloudFlare.exceptions.CloudFlareAPIError:
        print("Record already Exist.")
        sys.exit(-1)
    if r["name"] == subdomain + "." + zone_name:
        print(f"{r['name']}, added successfully.")
    sys.exit(0)


if __name__ == "__main__":
    try:
        a_zone_name = sys.argv[1]
        a_subdomain = sys.argv[2]
    except IndexError:
        print_help()
    add_record(a_zone_name, a_subdomain)
