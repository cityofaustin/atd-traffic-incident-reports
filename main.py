#!/usr/bin/env python
# docker run -it --rm --env-file .env -v /path/to/folder/atd-traffic-incident-reports:/app \
# atddocker/atd-traffic-incident-reports:production bash

import os
import logging
import sys
import cx_Oracle


USER = os.getenv("USER")
PASSWORD = os.getenv("PASSWORD")
HOST = os.getenv("HOST")
PORT = os.getenv("PORT")
SERVICE = os.getenv("SERVICE")

QUERY = "SELECT * FROM QACT_USER.QACT"


def get_conn(host, port, service, user, password):
    # make connect descriptor string
    oracle_data_source_name = cx_Oracle.makedsn(host, port, service_name=service)
    # create and return oracle connection object
    return cx_Oracle.connect(user=user, password=password, dsn=oracle_data_source_name)


def main():
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

    print(rows)

    logging.info(f"{len(rows)} records received.")


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    main()
