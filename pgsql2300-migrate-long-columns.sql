/*
 * Rename columns from the legacy pgsql2300 schema to the descriptive
 * names used by pgsql2300.c and pgsql2300.sql.
 *
 * Run this once against an existing open2300.weather table before using
 * the refactored pgsql2300 logger.
 */

BEGIN;

ALTER TABLE open2300.weather RENAME COLUMN temp_in TO temperature_indoor;
ALTER TABLE open2300.weather RENAME COLUMN temp_out TO temperature_outdoor;
ALTER TABLE open2300.weather RENAME COLUMN rel_hum_in TO humidity_indoor;
ALTER TABLE open2300.weather RENAME COLUMN rel_hum_out TO humidity_outdoor;
ALTER TABLE open2300.weather RENAME COLUMN wind_angle0 TO wind_angle_current;
ALTER TABLE open2300.weather RENAME COLUMN wind_angle1 TO wind_angle_previous_1;
ALTER TABLE open2300.weather RENAME COLUMN wind_angle2 TO wind_angle_previous_2;
ALTER TABLE open2300.weather RENAME COLUMN wind_angle3 TO wind_angle_previous_3;
ALTER TABLE open2300.weather RENAME COLUMN wind_angle4 TO wind_angle_previous_4;
ALTER TABLE open2300.weather RENAME COLUMN wind_angle5 TO wind_angle_previous_5;
ALTER TABLE open2300.weather RENAME COLUMN ws_datetime TO station_datetime;
ALTER INDEX open2300.ws_datetime_idx RENAME TO station_datetime_idx;

COMMIT;
