#!/usr/bin/env python
import argparse
import os
import arrow
import utils
from pypgrest import Postgrest

PGREST_ENDPOINT = os.getenv("PGREST_ENDPOINT")
PGREST_TOKEN = os.getenv("PGREST_TOKEN")
SOCRATA_RESOURCE_ID = os.getenv("SOCRATA_RESOURCE_ID")


def format_filter_date(date_from_args):
    return "1970-01-01" if not date_from_args else arrow.get(date_from_args).isoformat()


def main(args):
    filter_iso_date_str = format_filter_date(args.date)

    client_postgrest = Postgrest(PGREST_ENDPOINT, token=PGREST_TOKEN)

    data = client_postgrest.select(
        resource="traffic_reports",
        params={
            "published_date": f"gte.{filter_iso_date_str}",
            "order": "traffic_report_status_date_time",
        },
    )

    logger.info(f"{len(data)} records to process")

    if not data:
        return

    client_socrata = utils.socrata.get_client()
    method = "replace" if not args.date else "upsert"

    utils.socrata.publish(method=method, resource_id=SOCRATA_RESOURCE_ID, payload=data, client=client_socrata
    )
    logger.info(f"{len(data)} records processed.")


if __name__ == "__main__":
    logger = utils.logging.getLogger(__file__)
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d",
        "--date",
        type=str,
        help=f"An ISO 8601-compliant date string which will be used to query records",
    )

    cli_args = parser.parse_args()
    main(cli_args)

