#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import getpass
import ssl

from pymongo import MongoClient
from bson.objectid import ObjectId

__author__ = "Yaris Gutierrez"
__email__ = "yarisg@bigid.com"
__license__ = "MIT"


class tcolors:
    """Define some colors to not make outputs look bland."""
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def main():
    # Check if SSL is being used with Mongo
    mongo_ssl_check = input("\nIs Mongodb using SSL (y/n)? ").lower()
    if mongo_ssl_check == "y":
        ssl_ca = input("\nPath to CA Certificate (e.g. /path/to/ca.pem: ")
        ssl_cert = input("\nPath to Client Certificate "
                         "(e.g. /path/to/client.pem): ")
        ssl_key = input("\nPath to key (e.g. /path/to/client.key): ")

    # Connection Details
    mongo_server = input("\nEnter Mongodb Server Address: ")
    mongo_user = input("\nEnter Mongodb User: ")
    mongo_pass = getpass.getpass("\nEnter Password for user '%s': "
                                 % mongo_user)
    mongo_db = input("\nEnter the database name: ")

    # Create the connection
    if mongo_ssl_check == "y":
        client = MongoClient(mongo_server,
                             username=mongo_user,
                             password=mongo_pass,
                             ssl=True,
                             ssl_ca_certs=ssl_ca,
                             ssl_certfile=ssl_cert,
                             ssl_keyfile=ssl_key,
                             authSource="admin")
    else:
        client = MongoClient(mongo_server,
                             username=mongo_user,
                             password=mongo_pass,
                             authSource="admin")
    db = client[mongo_db]

    # Test the connection and confirm successful authentication
    try:
        if client.server_info():
            print(tcolors.GREEN + "\nAuthentication successul!" + tcolors.ENDC)
        else:
            raise Exception
    except Exception:
        print("\nError: Could not connect to Mongo!\n")
        sys.exit()

    # Define the collection and search parameters
    scans_collection = db["scans"]
    while True:
        scan_name = input("\nEnter Scan Profile Name: ")
        if len(scan_name) == 0:
            print("\nScan Profile Name cannot be blank.")
            pass
        else:
            break
    scan_date = input("\nEnter date of scan (e.g. 2019-12-31): ")

    # Only print certain values from the returned dictionary in order to
    # make the output more legible. Additional keys can be added if needed
    # to expand on the details shown.
    # Example of some keys that may be useful: info, origin,
    # pii_summary_completed_dt, identities_scanned, etc.
    counter = 0
    try:
        for scans in scans_collection.find({"name": scan_name}):
            if str(scans["created_at"])[:10] == scan_date:
                counter += 1
                print("\n" + tcolors.BOLD + str(counter) + ") "
                      + tcolors.ENDC, end="")
                print(tcolors.GREEN + tcolors.BOLD + scans["name"] +
                      tcolors.ENDC)
                print(tcolors.WARNING + tcolors.BOLD + "_id: "
                      + tcolors.ENDC, end="")
                print(scans["_id"])
                print(tcolors.BOLD + "State: " +
                      tcolors.ENDC, end="")
                print(scans["state"])
                print(tcolors.BOLD + "Type of Scan: " +
                      tcolors.ENDC, end="")
                print(scans["type"])
                print(tcolors.BOLD + "Created: " +
                      tcolors.ENDC, end="")
                print(scans["created_at"])
                if scans["state"] == "Completed":
                    if scans["scan_progress_status"]["Completed"]:
                        print(tcolors.BOLD + "Completed: " +
                              tcolors.ENDC, end="")
                        print(scans["scan_progress_status"]["Completed"])
                print("\n")
            elif len(scan_date) == 0:
                raise ValueError
    except ValueError:
        print("\nA scan date is required!\n")

    if scan_date:
        auth_rem = input("Would you like to remove a scan (y/n)? ").lower()
        if auth_rem == "y":
            prim_id = input("Enter the _id of the scan to remove: ")
            print(tcolors.WARNING + "\nWARNING: THIS ACTION CANNOT BE UNDONE"
                  + tcolors.ENDC)
            confirm = input("\nAre you sure you want to remove "
                            "scan _id %s (y/n)? " % prim_id).lower()
            if confirm == "y":
                # Delete Primary Scan
                for ids in scans_collection.find({"_id": ObjectId(prim_id)}):
                    scans_collection.delete_many({"_id": ObjectId(prim_id)})

                # Delete sub-scans for above Primary Scan
                for ids in scans_collection.find({"parent_scan_id": prim_id}):
                    scans_collection.delete_many({"parent_scan_id": prim_id})
            elif confirm == "n":
                sys.exit()
        elif auth_rem == "n":
            print("\nExiting.\n")
            sys.exit()
    else:
        sys.exit()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nQuitting!\n")
        sys.exit()
