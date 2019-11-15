#!/usr/bin/env python
# -*- coding: utf-8 -*-

import getpass
import pprint
from pymongo import MongoClient
from bson.objectid import ObjectId

__author__ = "Yaris Alex Gutierrez"
__email__ = "yarisg@bigid.com"
__license__ = ""

# mongo_server = input("Enter MongoDB Server Address: ")
# mongo_user = input("\nEnter MongoDB User: ")
# mongo_password = getpass.getpass("\nEnter Password for %s: " % mongo_user)
# mongo_db = input("\nEnter the database name: ")
scan_name = input("\nEnter the name of the scan: ")


client = MongoClient("192.168.1.230",
                     username="bigid",
                     password="password",
                     authSource="admin")

db = client["bigid-server"]
scans_collection = db["scans"]

counter = 0

class tcolors:
    """
    Define some colors to not make outputs look bland
    """
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


if scan_name not in scans_collection:
    print("Scan does not exist")

for scans in scans_collection.find({"name": scan_name}):
    counter += 1
    print("\n" + tcolors.BOLD + str(counter) + ": " + tcolors.ENDC, end="")
    print(tcolors.GREEN + scans["name"] + tcolors.ENDC)
    pprint.pprint(scans)
    print("\n")

prim_id = input("Enter the _id of the scan to remove: ")

for ids in scans_collection.find({"_id": ObjectId(prim_id)}):
    scans_collection.delete_many({"_id": ObjectId(prim_id)})

# Deletes Sub Scan for above Primary Scan
for ids in scans_collection.find({"parent_scan_id": prim_id}):
    scans_collection.delete_many({"parent_scan_id": prim_id})
