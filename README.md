# atd-traffic-incident-reports

https://data.austintexas.gov/Transportation-and-Mobility/Real-Time-Traffic-Incident-Reports/dx9v-zd7x

This script replaces a [CTM](https://www.austintexas.gov/department/information-technology) created Cold Fusion app that connected to the public safety CAD database and published that information in the form of an RSS feed. The cold fusion app is slated to be retired by CTM.

DTS parsed the information from that RSS feed and saved it in one of our postgrest instances. The script that parsed the RSS feed is [here](https://github.com/cityofaustin/atd-data-publishing/blob/master/transportation-data-publishing/data_tracker/traffic_reports.py).

The script `main.py` contained in this repo bypasses the RSS feed and instead connects to the database directly and then proceeds to format and handle the data obtained in the same manner as the legacy script linked above. The oracle database only contains active traffic incidents.

### Automation

The `main.py` script is scheduled to run every 5 minutes by [Prefect](https://github.com/cityofaustin/atd-prefect/tree/main/flows/atd-traffic-incident-reports).

The data from the postgrest database is pushed to socrata [every 5 minutes as well](https://github.com/cityofaustin/atd-data-deploy/blob/production/config/scripts.yml#L279).

### Setup

The easiest path to running these utilities locally is to build this repo's Docker image, or pull it from `atddocker/atd-traffic-incident-reports`. This container builds on top of `atd-oracle-py`, which solves the headache of installing `cx_Oracle`. Any push to the main branch will trigger a docker build/push to Docker hub, updating the atd-traffic-incident-reports Docker image.

This repo has a `template.env` file, copy that file and rename as `.env`. The missing credentials can be found in the DTS 1Password vault, search "Austin-Travis County Traffic Report" for the username and password. The postgrest token is the legacy-scripts token.

Running `./main.py` will connect to the database, download and process the incidents and compare them to the active records in postgrest. Any records that differ will be upserted to postgrest.

