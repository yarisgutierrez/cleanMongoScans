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

from pymongo.errors import OperationFailure
from pymongo.errors import ServerSelectionTimeoutError
from pymongo import MongoClient
from bson.objectid import ObjectId

__author__ = "Yaris Gutierrez"
__copyright__ = "Copyright 2019, BigID"
__email__ = "yarisg@bigid.com"
__version__ = "0.1"

# TODO: Add the ability to rename scans. Example: In-Progress => Complete, and
# ensure that the script can be executed without the need to install Python
# and other dependencies.


class tcolors:
    """Define some colors to not make outputs look bland.
    """
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


print(tcolors.BOLD + "\n====================== "
      "Clear BigID Scan =======================\n" + tcolors.ENDC)
print("Press Ctl+c to quit at any time.")


def mongoConn():
    """Define the Mongo connection details
    The mongo_server variable can hold a port number if the non-standard
    Mongo DB port (27017) is not being used.
    For example, when entering the hostname, you can define the port number
    like so:

        Syntax: hostname:port_number

        Example: 'Enter Mongo DB Server Hostname: bigid-mongo:22314'
    """
    print(tcolors.BOLD + "\n[ MONGODB CONNECTION INFORMATION ]" + tcolors.ENDC)
    mongo_server = input("Enter Mongo DB Server Hostname: ")
    mongo_user = input("Enter Mongodb User: ")
    mongo_pass = getpass.getpass("Enter Password for user '%s': "
                                 % mongo_user)

    return mongo_server, mongo_user, mongo_pass


def certVerify(cert_name):
    """Verify the certificate path provided exists
    """
    try:
        f = open(cert_name)
        print(tcolors.GREEN + cert_name + " found!\n" + tcolors.ENDC)
        f.close
    except FileNotFoundError:
        print(cert_name + " not found! Please check your path.\n")
        sys.exit()


def main():
    # TODO: Consolidate and split code into more legible and reusable
    # functions. Add menu for "friendlier" interface

    mongo_server, mongo_user, mongo_pass = mongoConn()

    # Check if SSL is being used with Mongo and, if so, ask if
    # client certificates are also being used to determine
    # the proper connection parameters
    mongo_ssl_check = input("\nIs Mongodb using SSL (y/n)? ").lower()
    if mongo_ssl_check == "y":
        mongo_client_cert = input("Are you using Client Certificates "
                                  "(y/n): ").lower()
        if mongo_ssl_check and mongo_client_cert == "y":
            ssl_ca = input("Path to CA Certificate (e.g. /path/to/ca.pem): ")
            certVerify(ssl_ca)
            ssl_cert = input("Path to Client Certificate "
                             "(e.g. /path/to/client.pem): ")
            certVerify(ssl_cert)
            ssl_key = input("Path to key (e.g. /path/to/client.key): ")
            certVerify(ssl_key)
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

    # Test the connection and confirm successful authentication
    try:
        if client.server_info():
            print(tcolors.GREEN + tcolors.BOLD + "*** Authentication to Mongo "
                  "Successul! ***\n" + tcolors.ENDC)
    except OperationFailure:
        print("Authentication failed! Please check that your username and "
              "password combination is correct.\n")
        sys.exit()
    except ServerSelectionTimeoutError:
        print("Timeout Error. Connection closed.")
        sys.exit()

    # Create the connection to the user-defined Mongo DB and quit if
    # database is not found
    while True:
        try:
            mongo_db = input("Enter the database name: ")
            dbcheck = client.list_database_names()
            if mongo_db in dbcheck:
                print(tcolors.GREEN + tcolors.BOLD + "Successfully connected "
                      "to '" + mongo_db + "'!\n" + tcolors.ENDC)
                db = client[mongo_db]
                break
            else:
                print("Database '" + mongo_db + "' not found! "
                      "Please enter a valid database.\n")
                pass
        except Exception:
            print(Exception)

    # Define the collection and search parameters
    scans_collection = db["scans"]

    cont_loop = True
    while cont_loop:
        scan_name = input("Enter Scan Profile Name (Case Sensitive): ")
        if len(scan_name) == 0:
            print("Scan Profile cannot be blank!\n")
            pass
        for scan in scans_collection.find({"name": scan_name}):
            if scan_name in scan["name"]:
                print(tcolors.GREEN + "'" + scan_name + "' has been found.\n"
                      + tcolors.ENDC)
                cont_loop = False
                break
            else:
                pass

    scan_date = input("Enter date of scan (e.g. 2019-12-31): ")

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
            while auth_rem == "y":
                prim_id = input("Enter the _id of the scan to remove: ")
                if len(prim_id) == 0:
                    print("id cannot be blank!\n")
                    pass
                else:
                    break
            print(tcolors.FAIL + "\nWARNING: THIS ACTION CANNOT BE UNDONE"
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

                print("\n" + prim_id + " has been removed from the system")
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
