import os
import sodapy


def get_client(host="datahub.austintexas.gov", timeout=30):
    SOCRATA_APP_TOKEN = os.getenv("SOCRATA_APP_TOKEN")
    SOCRATA_API_KEY_ID = os.getenv("SOCRATA_API_KEY_ID")
    SOCRATA_API_KEY_SECRET = os.getenv("SOCRATA_API_KEY_SECRET")

    return sodapy.Socrata(
        host,
        SOCRATA_APP_TOKEN,
        username=SOCRATA_API_KEY_ID,
        password=SOCRATA_API_KEY_SECRET,
        timeout=timeout,
    )


def publish(*, method, resource_id, payload, client):
    """Just a sodapy wrapper that chunks payloads"""

    def chunks(lst, n):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i : i + n]

    for chunk in chunks(payload, 1000):
        if method == "replace":
            # replace the dataset with first chunk
            # subsequent chunks will be upserted
            client.replace(resource_id, chunk)
            method = "upsert"
        else:
            client.upsert(resource_id, chunk)
