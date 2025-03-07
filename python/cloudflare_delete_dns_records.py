#!/usr/bin/env python3
"""
Deletes one DNS A record pointing to a mentioned server using
Cloudflare API v4. Edit places necessary.

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
    Deletes DNS A records using Cloudflare API v4.

     USAGE
    =======
    python3 delete_dns_records.py [Zone Name] [Sub doman]

     EXAMPLE (deletes sub.example.com)
    =======================================
    python3 delete_dns_records.py example.com sub
    """
    print(help_string)


def return_zone_info(cf, get_zone_name):
    try:
        zone_info = cf.zones.get(params={"name": get_zone_name})[0]
    except IndexError:
        print("Zone does not exist in this token.")
        sys.exit(-1)
    return zone_info


def delete_record(zone_name, dns_name):
    token = getenv("CLOUDFLARE_API_TOKEN", default=None)
    if token is None:
        print("Cloudflare API token not present.")
        sys.exit(-1)
    cf = CloudFlare.CloudFlare(token=token)
    zone_info = return_zone_info(cf, zone_name)
    zone_id = zone_info["id"]
    dns_records = cf.zones.dns_records.get(
        zone_id, params={"name": dns_name + "." + zone_name}
    )
    if len(dns_records) < 1:
        print("Records do not exist")
        sys.exit(-1)
    print(
        len(dns_records),
        "DNS (A) Records will be deleted. Type 'YES' to proceed: ",
        end="",
    )
    confirm_text = str(input())
    if confirm_text not in ["YES", "yes"]:
        print("User Aborted...")
        sys.exit(0)
    for dns_record in dns_records:
        dns_record_id = dns_record["id"]
        cf.zones.dns_records.delete(zone_id, dns_record_id)
    print("Record(s) successfully deleted.")
    sys.exit(0)


if __name__ == "__main__":
    try:
        a_zone_name = sys.argv[1]
        a_dns_name = sys.argv[2]
    except IndexError:
        print_help()
    delete_record(a_zone_name, a_dns_name)
