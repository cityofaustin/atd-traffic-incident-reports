#!/usr/bin/env python
# docker run -it --rm --env-file .env -v /path/to/folder/atd-traffic-incident-reports:/app \
# atddocker/atd-traffic-incident-reports:production bash

import os
import logging
import sys
import requests
import cx_Oracle
import hashlib
import arrow


USER = os.getenv("USER")
PASSWORD = os.getenv("PASSWORD")
HOST = os.getenv("HOST")
PORT = os.getenv("PORT")
SERVICE = os.getenv("SERVICE")
PGREST_ENDPOINT = os.getenv("PGREST_ENDPOINT")
PGREST_TOKEN = os.getenv("PGREST_TOKEN")

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {PGREST_TOKEN}",
    "Prefer": "return=representation, resolution=merge-duplicates",
}

QUERY = "SELECT * FROM QACT_USER.QACT"


def get_conn(host, port, service, user, password):
    """ Create oracle database connection """
    # make connect descriptor string
    oracle_data_source_name = cx_Oracle.makedsn(host, port, service_name=service)
    # create and return oracle connection object
    return cx_Oracle.connect(user=user, password=password, dsn=oracle_data_source_name)


def get_oracle_db_records():
    """
    connects to oracle db and executes query, converts rows retrieved into dicts
    :return: list of records (dict)
    """
    conn = get_conn(HOST, PORT, SERVICE, USER, PASSWORD)
    cursor = conn.cursor()
    cursor.execute(QUERY)

    # define row handler which returns each row as a dict
    # h/t https://stackoverflow.com/questions/35045879/cx-oracle-how-can-i-receive-each-row-as-a-dictionary
    cursor.rowfactory = lambda *args: dict(
        zip([d[0] for d in cursor.description], args)
    )
    rows = cursor.fetchall()
    conn.close()

    logging.info(f"{len(rows)} records in oracle database received.")
    return rows


def generate_record_id(call_number, timestamp):
    """
    the records from the oracle database do not have record ids associated with them
    the coldfusion app added IDs generated by Coldfusion using #hash(call_number,"SHA")#
    this function does the same using hashlib and appending our timestamp as before
    :param call_number: call_number
    :param timestamp:
    :return: traffic_incident_id string
    """
    # create coldfusion hash id
    cf_id = hashlib.sha1(str.encode(call_number)).hexdigest().upper()
    #  compose record id from entry identifier (which is not wholly unique) and publication timestamp
    return "{}_{}".format(cf_id, timestamp)


def get_active_records():
    """
    Query active records from postgrest endpoint
    :return: list of active records (dict)
    """
    active_records_endpoint = f"{PGREST_ENDPOINT}?traffic_report_status=eq.ACTIVE"

    active_records_response = requests.get(active_records_endpoint, headers=headers)
    active_records_response.raise_for_status()
    return active_records_response.json()


def format_record(incident):
    """
    Formats data from incident into record dict to upsert to postgrest
    :param incident: dict from oracle db
    :return: record dict
    """
    record = {}
    published_date = arrow.get(incident['CURR_DATE']).replace(tzinfo="US/Central")
    status_date = arrow.now().format()
    record["traffic_report_id"] = generate_record_id(incident['CALL_NUMBER'], published_date.timestamp)
    record["published_date"] = published_date.format()
    record["traffic_report_status"] = "ACTIVE"
    record["traffic_report_status_date_time"] = status_date
    record["address"] = incident['ADDRESS'].strip()
    record["issue_reported"] = incident['DESCRIPTION'].strip()
    record["latitude"] = incident['LATITUDE']
    record["longitude"] = incident['LONGITUDE']
    return record


def parse_records(traffic_incidents):
    """
    :param traffic_incidents: list of traffic incidents from oracle db
    :return: list of formatted incident records
    """
    records = []
    for incident in traffic_incidents:
        record = format_record(incident)
        records.append(record)

    return records


def apply_archive_status(records):
    """
    updates status to ARCHIVED and status_date_time to now
    :param records: list of records that are in postgrest but no longer in oracle db (no longer active)
    :return: list of records (dicts)
    """
    for record in records:
        record["traffic_report_status"] = "ARCHIVED"
        record["traffic_report_status_date_time"] = arrow.now().format()
    return records


def main():
    # get records from oracle db
    traffic_incident_records = get_oracle_db_records()
    traffic_incident_records = parse_records(traffic_incident_records)
    incident_record_ids = [record["traffic_report_id"] for record in traffic_incident_records]
    # get records with ACTIVE status from postgrest
    active_records = get_active_records()
    active_records_ids = [record["traffic_report_id"] for record in active_records]

    # records that are in oracle db but not postgrest
    new_records = [
        record
        for record in traffic_incident_records
        if record["traffic_report_id"] not in active_records_ids
    ]

    # records that are in postgrest but no longer in oracle db
    archive_records = [
        record
        for record in active_records
        if record["traffic_report_id"] not in incident_record_ids
    ]

    # change status to ARCHIVED and add timestamp
    archive_records = apply_archive_status(archive_records)

    payload = new_records + archive_records

    logging.info(f"{len(payload)} records to upsert into postgrest.")

    if payload:
        res = requests.post(PGREST_ENDPOINT, headers=headers, json=payload)
        return res.json()


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    main()
