/*
Script to create database, roles for inserting WS data and for retrieving them.
*/

create role open2300 password 'ws2300rw' login;

create role ws2300 password 'open2300ro' login;

create database open2300DB owner open2300 encoding 'UTF8';

\c open2300db;

create schema if not exists open2300 authorization open2300;

grant usage on schema open2300 to ws2300;

#
# Table structure for table containing weather data.
# Third version.
# Table name have to be configured in open2300.conf under PGSQL section 
# using key PGSQL_TABLE
#

CREATE TABLE open2300.weather (
  rec_id bigserial, -- record ID
  rec_datetime timestamp with time zone  NOT NULL default now(),   -- record DateTime
  temperature_indoor numeric(4,1),
  temperature_outdoor numeric(4,1),
  dewpoint numeric(4,1),
  humidity_indoor smallint,
  humidity_outdoor smallint,
  wind_speed numeric(3,1),
  wind_angle_current numeric(4,1),
  wind_angle_previous_1 numeric(4,1),
  wind_angle_previous_2 numeric(4,1),
  wind_angle_previous_3 numeric(4,1),
  wind_angle_previous_4 numeric(4,1),
  wind_angle_previous_5 numeric(4,1),
  wind_direction char(3),
  wind_speed_min numeric(3,1),
  wind_speed_max numeric(3,1),
  wind_speed_min_datetime timestamp,   -- timestamp for mimimum wind speed
  wind_speed_max_datetime timestamp,   -- timestamp for maximum wind speed
  wind_chill numeric(4,1),
  rain_1h numeric(3,1),
  rain_24h numeric(3,1),
  rain_total numeric(5,1),
  rel_pressure numeric(5,1),
  tendency varchar(7),
  forecast varchar(6),
  station_datetime timestamp,
  ws_datetime_local timestamp,
  ws_datetime_utc timestamp,
  pgsql2300_version varchar(64),     -- SW version ( RCS tag: Revision from pgsql2300.c )
  src_name varchar(64),  -- identify source historical table name from which data were imported
  src_rec_id bigint,  -- identify source data from historical tables
  PRIMARY KEY (rec_id)
) ;

alter table open2300.weather owner to open2300;

create index rec_datetime_idx on open2300.weather(rec_datetime);
create index station_datetime_idx on open2300.weather(station_datetime);
create index ws_datetime_local_idx on open2300.weather(ws_datetime_local);
create index ws_datetime_utc_idx on open2300.weather(ws_datetime_utc);

grant select on open2300.weather to ws2300;
