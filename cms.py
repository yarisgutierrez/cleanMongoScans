#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The current iteration of this script will allow users to list Scans
regardless of status (i.e. Completed, InProgress, Failed) and remove the
scan from the UI.

The script can be run on a user's desktop as long as they have remote access
to the Mongo DB and access to CA/Client Certificates, if SSL is being used.

Requirements:
    - Python 3.x
    - PyMongo (pip3 install pymongo)

Usage:
    ./cms.py
"""
import sys
import getpass

from pymongo import MongoClient
from bson.objectid import ObjectId

__author__ = "Yaris Gutierrez"
__copyright__ = "Copyright 2019, BigID"
__email__ = "yarisg@bigid.com"
__license__ = "MIT"
__version__ = "0.1"

# TODO: Add the ability to rename scans. Example: In-Progress => Complete, and
# ensure that the script can be executed without the need to install Python
# and other dependencies.
# Work on better error-handling logic


class tcolors:
    """Define some colors to not make outputs look bland."""
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    boLD = "\033[1m"
    UNDERLINE = "\033[4m"


def mongoConn():
    """Define the Mongo connection details"""
    print(tcolors.BOLD + "\n##### MONGO CONNECTION INFORMATION #####" +
          tcolors.ENDC)
    mongo_server = input("\nEnter Mongodb Server Address: ")
    mongo_user = input("Enter Mongodb User: ")
    mongo_pass = getpass.getpass("Enter Password for user '%s': "
                                 % mongo_user)
    mongo_db = input("Enter the database name: ")

    return mongo_server, mongo_user, mongo_pass, mongo_db


def main():
    # TODO: Consolidate and split code into mode legible and reusable
    # functions. Add menu for "friendlier" interface

    mongo_server, mongo_user, mongo_pass, mongo_db = mongoConn()

    # Check if SSL is being used with Mongo and, if so, ask if
    # client certificates are also being used to determine
    # the proper connection parameters
    mongo_ssl_check = input("\nIs Mongodb using SSL (y/n)? ").lower()
    if mongo_ssl_check == "y":
        mongo_client_cert = input("Are you using Client Certificates "
                                  "(y/n): ").lower()
        if mongo_ssl_check and mongo_client_cert == "y":
            ssl_ca = input("Path to CA Certificate (e.g. /path/to/ca.pem: ")
            ssl_cert = input("Path to Client Certificate "
                             "(e.g. /path/to/client.pem): ")
            ssl_key = input("Path to key (e.g. /path/to/client.key): ")
            print(mongo_server, mongo_user, mongo_pass, mongo_db)
            client = MongoClient(mongo_server,
                                 username=mongo_user,
                                 password=mongo_pass,
                                 ssl=True,
                                 ssl_ca_certs=ssl_ca,
                                 ssl_certfile=ssl_cert,
                                 ssl_keyfile=ssl_key,
                                 authSource="admin")
        # If client certificates are not being use but CA is, specify
        # the CA certificate only to initiate the connection
        elif mongo_ssl_check == "y":
            ssl_ca = input("Path to CA Certificate (e.g. /path/to/ca.pem: ")
            client = MongoClient(mongo_server,
                                 username=mongo_user,
                                 password=mongo_pass,
                                 ssl=True,
                                 ssl_ca_certs=ssl_ca,
                                 authSource="admin")
    # If SSL is not being used, use the standard Mongo connection
    else:
        client = MongoClient(mongo_server,
                             username=mongo_user,
                             password=mongo_pass,
                             authSource="admin")

    # Create the connection to the user-defined Mongo DB
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
        scan_name = input("\nEnter Scan Profile Name (Case Sensitive): ")
        if len(scan_name) == 0:
            print("\nScan Profile Name cannot be blank.")
            pass
        else:
            break
    scan_date = input("Enter date of scan (e.g. 2019-12-31): ")

    # Only print certain values from the returned dictionary in order to
    # make the output more legible. Additional keys can be added if needed
    # to expand on the details shown.
    # Example of some keys that may be useful: info, origin,
    # pii_summary_completed_dt, identities_scanned, etc.
    # Example of h
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

                # Delete sub-scans for above Primary Scan to remove any
                # artifacts from the primary scan collection
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
