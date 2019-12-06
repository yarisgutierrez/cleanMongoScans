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
    ./curse.py
"""
import os
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


class tcolors:
    """Define colors
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
      "Clean Up Residual Scanned Errors  =======================\n"
      + tcolors.ENDC)
print("Press Ctl+c to quit at any time.")


def mongoConn():
    """Define the Mongo connection details
        Syntax: hostname:port_number
    """
    print(tcolors.BOLD + "\n[ MONGODB CONNECTION INFORMATION ]" + tcolors.ENDC)
    mongo_server = input("Enter Mongo DB Server Hostname (Press Enter for "
                         "default: bigid-mongo): ")
    if len(mongo_server) == 0:
        mongo_server = "bigid-mongo"
    mongo_user = input("Enter Mongodb User (Press Enter for default): ")
    if len(mongo_user) == 0:
        mongo_user = "bigid"
    mongo_pass = getpass.getpass("Enter Password for user '%s' (Press "
                                 "Enter for default: password): "
                                 % mongo_user)
    if len(mongo_pass) == 0:
        mongo_pass = "password"

    return mongo_server, mongo_user, mongo_pass


mongo_server, mongo_user, mongo_pass = mongoConn()
# Check if SSL is being used with Mongo
mongo_ssl_check = input("\nIs Mongodb using SSL (y/n)? ").lower()
if mongo_ssl_check == "y":
    mongo_client_cert = input("Are you using Client Certificates "
                              "(y/n): ").lower()
    if mongo_ssl_check and mongo_client_cert == "y":
        while True:
            ssl_ca = input("Path to CA Certificate (e.g. /path/to/ca.pem): ")
            if os.path.isfile(ssl_ca):
                print(tcolors.GREEN + ssl_ca + " found\n" + tcolors.ENDC)
                break
            else:
                print(ssl_ca + " not found! Please check your path.\n ")
                pass
        while True:
            ssl_cert = input("Path to Client Certificate "
                             "(e.g. /path/to/client.pem): ")
            if os.path.isfile(ssl_cert):
                print(tcolors.GREEN + ssl_cert + " found\n" + tcolors.ENDC)
                break
            else:
                print(ssl_cert + " not found! Please check your path.\n ")
                pass
        while True:
            ssl_key = input("Path to key (e.g. /path/to/client.key): ")
            if os.path.isfile(ssl_key):
                print(tcolors.GREEN + ssl_key + " found\n" + tcolors.ENDC)
                break
            else:
                print(ssl_key + " not found! Please check your path.\n ")
                pass
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
        while True:
            ssl_ca = input("Path to CA Certificate (e.g. /path/to/ca.pem: ")
            if os.path.isfile(ssl_ca):
                print(tcolors.GREEN + ssl_ca + " found\n" + tcolors.ENDC)
                break
            else:
                print(ssl_ca + " not found! Please check your path.\n ")
                pass
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
              "Successul ***\n" + tcolors.ENDC)
except OperationFailure:
    print("Authentication failed! Please check that your username and "
          "password combination is correct\n")
    sys.exit()
except ServerSelectionTimeoutError:
    print("Timeout Error. Connection closed")
    sys.exit()

# Create the connection to the user-defined Mongo DB and quit if
# database is not found
while True:
    try:
        mongo_db = input("Enter the database name: ")
        dbcheck = client.list_database_names()
        if mongo_db in dbcheck:
            print(tcolors.GREEN + tcolors.BOLD + "Successfully connected "
                  "to '" + mongo_db + "'\n" + tcolors.ENDC)
            db = client[mongo_db]
            break
        else:
            print("Database '" + mongo_db + "' not found. "
                  "Please enter a valid database.\n")
            pass
    except Exception:
        print(Exception)

# Define the collection to use
scans_collection = db["scans"]

# Scan Profile Details
cont_loop = True
while cont_loop:
    scan_name = input("Enter Scan Profile Name (Case Sensitive): ")
    if len(scan_name) == 0:
        print("Scan Profile cannot be blank\n")
        pass
    for scan in scans_collection.find({"name": scan_name}):
        if scan_name in scan["name"]:
            print(tcolors.GREEN + "'" + scan_name + "' has been found\n"
                  + tcolors.ENDC)
            cont_loop = False
            break
        else:
            pass

scan_date = input("Enter date of scan (e.g. 2019-12-31): ")

# Only print certain values from the returned dict
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

            # Delete sub-scans for above Primary Scan
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
