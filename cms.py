#!/usr/bin/env python
# -*- coding: utf-8 -*-

import getpass
from pymongo import MongoClient
from bson.objectid import ObjectId

__author__ = "Yaris Alex Gutierrez"
__email__ = "yarisg@bigid.com"
__license__ = ""

# Mongo Stuff
mongo_ssl_check = input("\nIs MongoDB using SSL (y/n)? ").lower()


if mongo_ssl_check == "y":
    ssl_cert = input("\nSpecify path to CA file (e.g. /path/to/ca.pem): ")

mongo_server = input("\nEnter MongoDB Server Address: ")
mongo_user = input("\nEnter MongoDB User: ")
mongo_password = getpass.getpass("\nEnter Password for %s: " % mongo_user)
mongo_db = input("\nEnter the database name: ")
scan_name = input("\nEnter the name of the scan: ")

# Create the connection
# TODO: Work with Morgan to understand how we connect to Mongo via SSL to
# ensure we are passing the correct paramaters in the logic
if mongo_ssl_check == "y":
    client = MongoClient(mongo_server,
                         username=mongo_user,
                         password=mongo_password,
                         ssl=True,
                         ssl_ca_certs=ssl_cert,
                         authSource="admin")
else:
    client = MongoClient(mongo_server,
                         username=mongo_user,
                         password=mongo_password,
                         authSource="admin")


db = client[mongo_db]
scans_collection = db["scans"]

counter = 0


class tcolors:
    # Define some colors to not make outputs look bland
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


# Only print the relevant information from the dict returned
for scans in scans_collection.find({"name": scan_name}):
    counter += 1
    print("\n" + tcolors.BOLD + str(counter) + ": " + tcolors.ENDC, end="")
    print(tcolors.GREEN + tcolors.BOLD + scans["name"] + tcolors.ENDC)
    print(tcolors.WARNING + tcolors.BOLD + "_id: " + tcolors.ENDC, end="")
    print(scans["_id"])
    print(tcolors.BOLD + "State: " + tcolors.ENDC, end="")
    print(scans["state"])
    print(tcolors.BOLD + "Type of Scan: " + tcolors.ENDC, end="")
    print(scans["type"])
    print(tcolors.BOLD + "Created: " + tcolors.ENDC, end="")
    print(scans["created_at"])
    print(tcolors.BOLD + "Started: " + tcolors.ENDC, end="")
    print(scans["scan_progress_status"]["Started"])
    if scans["scan_progress_status"]["Completed"]:
        print(tcolors.BOLD + "Completed: " + tcolors.ENDC, end="")
        print(scans["scan_progress_status"]["Completed"])
    print("\n")

prim_id = input("Enter the _id of the scan to remove: ")

# Delete Primary Scan
for ids in scans_collection.find({"_id": ObjectId(prim_id)}):
    scans_collection.delete_many({"_id": ObjectId(prim_id)})

# Delete sub-scans for above Primary Scan
for ids in scans_collection.find({"parent_scan_id": prim_id}):
    scans_collection.delete_many({"parent_scan_id": prim_id})
