--
-- This init file was generated from a postgreSQL database dump of the
-- production knack-serivces database in May 2025. It is for basic testing
-- purposes only and may not reflect the current production state
--
SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: api; Type: SCHEMA; Schema: -; Owner: -
--
CREATE SCHEMA api;


create table api.public_safety_incidents
(
    traffic_report_id               text not null primary key,
    published_date                  timestamp with time zone,
    address                         text,
    issue_reported                  text,
    latitude                        numeric,
    longitude                       numeric,
    traffic_report_status           text,
    traffic_report_status_date_time timestamp with time zone,
    agency                          varchar,
    incident_type                   text
);

alter table api.public_safety_incidents
    owner to postgres;

--
-- custom api_user role definition
--
CREATE ROLE api_user NOLOGIN;

GRANT USAGE ON SCHEMA api TO api_user;

GRANT SELECT ON ALL TABLES IN SCHEMA api TO api_user;

GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA api TO api_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA api
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO api_user;

GRANT USAGE ON ALL SEQUENCES IN SCHEMA api TO api_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA api
GRANT USAGE ON SEQUENCES TO api_user;
