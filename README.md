# atd-traffic-incident-reports

https://data.austintexas.gov/Transportation-and-Mobility/Real-Time-Traffic-Incident-Reports/dx9v-zd7x

This script replaces a [CTM](https://www.austintexas.gov/department/information-technology) created Cold Fusion app that connected to the public safety CAD database and published that information in the form of an RSS feed. The cold fusion app is slated to be retired by CTM.

DTS parsed the information from that RSS feed and saved it in one of our [postgrest](https://github.com/cityofaustin/atd-postgrest) instances. The script that parsed the RSS feed is [here](https://github.com/cityofaustin/atd-data-publishing/blob/master/transportation-data-publishing/data_tracker/traffic_reports.py).

The script `main.py` contained in this repo bypasses the RSS feed and instead connects to the database directly. It then proceeds to format and handle the data obtained in the same manner as the legacy script linked above. The oracle database only contains active traffic incidents.

### Automation

The `main.py` and `records_to_socrata.py` scripts are scheduled to run every 5 minutes by [Airflow](https://github.com/cityofaustin/atd-airflow/blob/production/dags/atd_traffic_incident_reports.py).

### Setup

The easiest path to running these utilities locally is to build this repo's Docker image, or pull it from `atddocker/atd-traffic-incident-reports`. Previous versions of this code depended on cx_Oracle, it now uses [oracledb](https://python-oracledb.readthedocs.io/en/latest/user_guide/appendix_c.html#steps-to-upgrade-to-python-oracledb). Any push to the main branch will trigger a docker build/push to Docker hub, updating the atd-traffic-incident-reports Docker image.

This repo has a `template.env` file, copy that file and rename as `.env`. The missing credentials can be found in the DTS 1Password vault, search "Austin-Travis County Traffic Report" for the username and password. The postgrest token is the legacy-scripts token.

Running `./main.py` will connect to the database, download and process the incidents and compare them to the active records in postgrest. Any records that differ will be upserted to postgrest.

Note: You must be on the COA network in order to connect to the oracle database.

### Local Dev

If you are interested in setting up a local copy of the postgres database and postgREST service then you can use the `docker-compose-local.yaml` file. 

```
docker compose -f docker-compose-local.yaml up
```

This will then create a postgres DB locally alongside the postgREST service to access it. To use it with the scripts, simply make these edits to a production `.env` file:

```
PGREST_ENDPOINT=http://0.0.0.0:3000
PGREST_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYXBpX3VzZXIifQ.z2R8GY8J23EBFWpyLQGqs8iJK1gsCm3Izg1Ez3qq5CQ
```
