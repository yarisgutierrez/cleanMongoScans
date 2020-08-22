#!/usr/bin/envpython3
# -*- coding: utf-8 -*-

import sys
from pymongo import MongoClient

mongo_server = "192.168.1.99"
mongo_user = "bigid"
mongo_password = "password"
mongo_authSource = "admin"

client = MongoClient(mongo_server,
                     username=mongo_user,
                     password=mongo_password,
                     authSource=mongo_authSource)

mongo_db = "bigid-server"
db = client[mongo_db]

scans = db["scans"]
pii_findings = db["pii_findings"]
prim_id = "5f3fff03b3f9e14f5cbb9e3c"


def checkFindings():
    child_ids = []
    for i in scans.find({"parent_scan_id": prim_id, "type": "sub_scan"},
                        {"_id": 1}):

        child_ids.append(i["_id"])

    for x in child_ids:
        findings_count = pii_findings.count_documents({"scan_id": str(x)})
        if findings_count:
            print("PII Findings exist!")
            print(findings_count)
        else:
            sys.exit()


checkFindings()
