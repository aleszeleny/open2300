#
# Table structure for table containing weather data.
# Third version.
# Table name have to be configured in open2300.conf under MYSQL section 
# using key MYSQL_TABLENAME
#

CREATE TABLE `weather3` (
  `rec_id` bigint(20) unsigned NOT NULL auto_increment, # record ID
  `rec_datetime` datetime NOT NULL default '0000-00-00 00:00:00',   # record DateTime
  `temp_in` decimal(4,1),
  `temp_out` decimal(4,1),
  `dewpoint` decimal(4,1),
  `rel_hum_in` tinyint(3),
  `rel_hum_out` tinyint(3),
  `wind_speed` decimal(3,1),
  `wind_angle0` decimal(4,1),   # current wind angle
  `wind_angle1` decimal(4,1),   # last five wind angle values
  `wind_angle2` decimal(4,1),
  `wind_angle3` decimal(4,1),
  `wind_angle4` decimal(4,1),
  `wind_angle5` decimal(4,1),
  `wind_direction` char(3),
  `wind_speed_min` decimal(3,1),
  `wind_speed_max` decimal(3,1),
  `wind_speed_min_datetime` datetime,   # timestamp for mimimum wind speed
  `wind_speed_max_datetime` datetime,   # timestamp for maximum wind speed
  `wind_chill` decimal(4,1),
  `rain_1h` decimal(3,1),
  `rain_24h` decimal(3,1),
  `rain_total` decimal(5,1),
  `rel_pressure` decimal(5,1),
  `tendency` varchar(7),
  `forecast` varchar(6),
  `ws_datetime` datetime,
  `mysql2300_version` varchar(64),     # SW version ( RCS tag: Revision from mysql2300.c )
  `src_name` varchar(64),  # identify source data from historical tables
  `src_rec_id` bigint(20) unsigned,  # identify source data from historical tables
  PRIMARY KEY (`rec_id`)
) ENGINE=MyISAM;

create index rec_datetime_idx on weather3(rec_datetime);
create index ws_datetime_idx on weather3(ws_datetime);
