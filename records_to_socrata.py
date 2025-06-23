#!/usr/bin/env python
import argparse
import os
import arrow
import utils
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
    filter_iso_date_str = format_filter_date(args.date)

    client_postgrest = Postgrest(PGREST_ENDPOINT, token=PGREST_TOKEN)

    datasets = {
        "Traffic incident": TRAFFIC_RESOURCE_ID,
        "Fire incident": FIRE_RESOURCE_ID,
    }

    for dataset in datasets:

        data = client_postgrest.select(
            resource="traffic_reports",
            params={
                "traffic_report_status_date_time": f"gte.{filter_iso_date_str}",
                "order": "traffic_report_status_date_time",
                "type": f"eq.{dataset}"
            },
        )

        logger.info(f"{len(data)} {dataset}s to process")

        if not data:
            return

        build_point_data(data)

        client_socrata = utils.socrata.get_client()
        utils.socrata.publish(
            method="upsert",
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
        required=True,
    )

    cli_args = parser.parse_args()
    main(cli_args)
