#!/usr/bin/env python
import argparse
import os
import arrow
import utils
import sys
from pypgrest import Postgrest

PGREST_ENDPOINT = os.getenv("PGREST_ENDPOINT")
PGREST_TOKEN = os.getenv("PGREST_TOKEN")
TRAFFIC_RESOURCE_ID = os.getenv("TRAFFIC_RESOURCE_ID")
FIRE_RESOURCE_ID = os.getenv("FIRE_RESOURCE_ID")


def format_filter_date(date_from_args):
    return "1970-01-01" if not date_from_args else arrow.get(date_from_args).isoformat()


def build_point_data(data):
    """
    formats location point column as expected by Socrata
    """
    for r in data:
        # handling missing lat and/or lon
        if r["longitude"] and r["latitude"]:
            r["location"] = f"POINT ({r['longitude']} {r['latitude']})"
        else:
            r["location"] = None


def main(args):
    if not args.date and not args.replace:
        raise ValueError("You must either provide a date or use the --replace flag.")
    if args.replace:
        confirmation = input(
            "Are you sure you want to replace all data stored in Socrata? Type 'yes' to confirm: "
        )
        if confirmation.strip().lower() != "yes":
            sys.exit(1)

    filter_iso_date_str = format_filter_date(args.date)

    client_postgrest = Postgrest(PGREST_ENDPOINT, token=PGREST_TOKEN)

    datasets = {
        "traffic_incident": TRAFFIC_RESOURCE_ID,
        "fire_incident": FIRE_RESOURCE_ID,
    }

    for dataset in datasets:
        data = client_postgrest.select(
            resource="public_safety_incidents",
            params={
                "select": "traffic_report_id,published_date,issue_reported,latitude,longitude,address,traffic_report_status,traffic_report_status_date_time,agency",
                "traffic_report_status_date_time": f"gte.{filter_iso_date_str}",
                "order": "traffic_report_status_date_time",
                "incident_type": f"eq.{dataset}",
            },
        )

        logger.info(f"{len(data)} {dataset}s to process")

        if not data:
            return

        build_point_data(data)

        client_socrata = utils.socrata.get_client()
        method = "replace" if args.replace else "upsert"
        utils.socrata.publish(
            method=method,
            resource_id=datasets[dataset],
            payload=data,
            client=client_socrata,
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
    parser.add_argument(
        "--replace", action="store_true", help="Replace all of the data"
    )

    cli_args = parser.parse_args()
    main(cli_args)
