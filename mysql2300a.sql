#
# Table structure for table `weather`
#

CREATE TABLE `weather2` (
  `id` bigint(20) unsigned NOT NULL auto_increment,
  `datetime` datetime NOT NULL default '0000-00-00 00:00:00',
  `temp_in` decimal(4,1),
  `temp_out` decimal(4,1),
  `dewpoint` decimal(4,1),
  `rel_hum_in` tinyint(3),
  `rel_hum_out` tinyint(3),
  `wind_speed` decimal(3,1),
  `wind_angle0` decimal(4,1),
  `wind_angle1` decimal(4,1),
  `wind_angle2` decimal(4,1),
  `wind_angle3` decimal(4,1),
  `wind_angle4` decimal(4,1),
  `wind_angle5` decimal(4,1),
  `wind_direction` char(3),
  `wind_speed_min` decimal(3,1),
  `wind_speed_max` decimal(3,1),
  `wind_speed_min_datetime` datetime,
  `wind_speed_max_datetime` datetime,
  `wind_chill` decimal(4,1),
  `rain_1h` decimal(3,1),
  `rain_24h` decimal(3,1),
  `rain_total` decimal(5,1),
  `rel_pressure` decimal(5,1),
  `tendency` varchar(7),
  `forecast` varchar(6),
  `datetime_ws` datetime,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM;

create index datetime_idx on weather2(datetime);
create index datetime_ws_idx on weather2(datetime_ws);
create index wind_speed_idx on weather2(wind_speed);
create index wind_speed_min_idx on weather2(wind_speed_min);
create index wind_speed_max_idx on weather2(wind_speed_max);
