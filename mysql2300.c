/*       mysql2300.c
 *
 *       Open2300 1.11 - mysql2300 1.6
 *
 *       Get data from WS2300 weather station
 *       and add them to MySQL database
 *
 *       Copyright 2003,2004, Kenneth Lavrsen/Thomas Grieder
 *
 *       This program is published under the GNU General Public license
 *
 *  0.1  2004 Feb 21  Thomas Grieder
 *       Creates mysql2300. A Rewrite of log2300.
 *       Logline is now comma delimited for added support to write
 *       to MySQL
 *       (see also http://www.unixreview.com/documents/s=8989/ur0401a/)
 *
 *  1.2  2004 Mar 07  Kenneth Lavrsen
 *       Complete rewrite of the code to support the new rw2300 library.
 *       Logfile feature removed to make it a clean MySQL program.
 *       Added support for config file and program should be able to
 *       compile under Windows with the right MySQL client headers
 *       and libraries installed.
 *
 *  1.3  As 1.2
 *
 *  1.4  2006 Feb 24  Emiliano Parasassi
 *       Enhancement of mysql2300 program. It removes 2 redundant fields
 *       and let you to perform custom query more easily.
 *
 *  1.5  2006 Jul 19  Kenneth Lavrsen
 *       Replaced a risky use of sprintf with safer strcat
 *
 *  1.6  2007 Jul 19  Emiliano Parasassi
 *       http://www.lavrsen.dk/twiki/bin/view/Open2300/MysqlPatch2
 *       Plus updates in ALTER TABLE to match patch from Rolan Yang
 *
 *  1.7  2009 Dec 21  Ales Zeleny
 *       id weather table column changed.
 *       Logging added to be able to resolv some operational issues.
 *       Changed logic of wind data capture:
 *         - current speed
 *         - min speed
 *         - max speed
 *       values are recorded now (table change) and min&max reset is done
 *       each time data are captured - wind peaks are more important (for me)
 *       than a value taken at the time of measurement.
 *       All Wind angles retrieved from WS are recored, where wind_angle0
 *       is angle at measurement time and past 5 values are recorded.
 *
 *  1.8  2012 Apr 16  Ales Zeleny
 *       update to weather table columns
 *       - WS time value is added, so table now contain time information
 *         obtained by mysql now() function and meteostation value
 *       - supplemental columns used on data merge from several older tables
 *         source data identification and source data ID column, for later data
 *         verification if necessary, column for Revison tag taken form RCS
 *         keyword in mysql2300.c
 *       - other small changes I've forogot to mentioned
 *
 */

#include <mysql.h>
#include "rw2300.h"
// Extend logging with PID
#include <sys/types.h>

 
/********** MAIN PROGRAM ************************************************
 *
 * This program reads current weather data from a WS2300
 * and writes the data to a MySQL database.
 *
 * The open2300.conf config file must contain the following parameters
 * 
 * Table structure for table `weather` is shown in mysql2300.sql file
 * 
 * If you already have the 'weather' table of the previous
 * release(<=1.3), launch these SQL commands to modify it correctly:

ALTER TABLE `open2300`.`weather` MODIFY COLUMN `timestamp` DATETIME DEFAULT '0000-00-00 00:00:00' NOT NULL;
ALTER TABLE `open2300`.`weather` DROP COLUMN `rec_date`;
ALTER TABLE `open2300`.`weather` DROP COLUMN `rec_time`;
ALTER TABLE `open2300`.`weather` CHANGE COLUMN `timestamp`    `datetime`     DATETIME NOT NULL DEFAULT 0;
ALTER TABLE `open2300`.`weather` CHANGE COLUMN `windspeed`    `wind_speed`   DECIMAL(3,1) NOT NULL DEFAULT 0;
ALTER TABLE `open2300`.`weather` CHANGE COLUMN `rel_pressure` `rel_pressure` DECIMAL(5,1) NOT NULL;
ALTER TABLE `open2300`.`weather` CHANGE COLUMN `rain_total`   `rain_total`   DECIMAL(5,1) NOT NULL;
ALTER TABLE `open2300`.`weather` CHANGE COLUMN `wind_angle`   `wind_angle`   DECIMAL(4,1) NOT NULL;
ALTER TABLE `open2300`.`weather` CHANGE COLUMN `temp_in`      `temp_in`      DECIMAL(4,1) NOT NULL DEFAULT 0;
ALTER TABLE `open2300`.`weather` CHANGE COLUMN `temp_out`     `temp_out`     DECIMAL(4,1) NOT NULL DEFAULT 0;
ALTER TABLE `open2300`.`weather` CHANGE COLUMN `dewpoint`     `dewpoint`     DECIMAL(4,1) NOT NULL DEFAULT 0;
ALTER TABLE `open2300`.`weather` CHANGE COLUMN `wind_chill`   `wind_chill`   DECIMAL(4,1) NOT NULL DEFAULT 0;

 * It takes one parameters. The config file name with path
 * If this parameter is omitted the program will look at the default paths
 * See the open2300.conf-dist file for info
 *
 ***********************************************************************/
	static char const rcsid[] =
		"$Id: mysql2300.c,v 1.8 2012/04/16 14:37:07 ales Exp $";

	static char const rcsver[] =
		"$Revision: 1.8 $";

int main(int argc, char *argv[])
{
	WEATHERSTATION ws2300;
	MYSQL mysql;
	char logfields[1000] = "";
	char logvalues[3000] = "";
	char tempstring[1000] = "";
	const char *directions[]= {"N","NNE","NE","ENE","E","ESE","SE","SSE",
	                           "S","SSW","SW","WSW","W","WNW","NW","NNW"};
	double winddir[6];
	int tempint;
	char tendency[15];
	char forecast[15];
	double tempfloat_min, tempfloat_max;
	struct timestamp time_min, time_max;
	struct config_type config;
	char query[4096];

	get_configuration(&config, argv[1]);

	sprintf(tempstring,"Starting mysql2300 version %s", rcsver );
	LOG(LOG_MIN, tempstring);
//	LOG(LOG_MIN, "Starting mysql2300.");
//	LOG(LOG_MIN, rcsver);
	LOG(LOG_MED, rcsid);
	LOG(LOG_MED, "Reading data from weather station.");

	LOG(LOG_MAX, "Openning weather station.");
	ws2300 = open_weatherstation(config.serial_device_name);

	/* READ TEMPERATURE INDOOR */
	LOG(LOG_MAX, "READ TEMPERATURE INDOOR.");
	strcat(logfields, "temp_in, ");
	sprintf(logvalues,"\'%.1f\',", temperature_indoor(ws2300, config.temperature_conv) );
	
	/* READ TEMPERATURE OUTDOOR */
	LOG(LOG_MAX, "READ TEMPERATURE OUTDOOR.");
	strcat(logfields, "temp_out, ");
	sprintf(tempstring,"\'%.1f\',", temperature_outdoor(ws2300, config.temperature_conv) );
	strcat(logvalues, tempstring);
	
	/* READ DEWPOINT */
	LOG(LOG_MAX, "READ DEWPOINT.");
	strcat(logfields, "dewpoint, ");
	sprintf(tempstring,"\'%.1f\',", dewpoint(ws2300, config.temperature_conv) );
	strcat(logvalues, tempstring);
	
	/* READ RELATIVE HUMIDITY INDOOR */
	LOG(LOG_MAX, "READ RELATIVE HUMIDITY INDOOR.");
	strcat(logfields, "rel_hum_in, ");
	sprintf(tempstring,"\'%d\',", humidity_indoor(ws2300) );
	strcat(logvalues, tempstring);
	
	/* READ RELATIVE HUMIDITY OUTDOOR */
	LOG(LOG_MAX, "READ RELATIVE HUMIDITY OUTDOOR.");
	strcat(logfields, "rel_hum_out, ");
	sprintf(tempstring,"\'%d\',", humidity_outdoor(ws2300) );
	strcat(logvalues, tempstring);

	/* READ WIND SPEED MIN AND MAX */
	/* Do this before resetting min & max wind speed. */
	LOG(LOG_MAX, "READ WIND SPEED MIN AND MAX.");
	strcat(logfields, "wind_speed_min, wind_speed_max, ");
	wind_minmax(ws2300, config.wind_speed_conv_factor, &tempfloat_min,
	            &tempfloat_max, &time_min, &time_max);
	sprintf(tempstring,"\'%.1f\',\'%.1f\',", tempfloat_min, tempfloat_max);
	strcat(logvalues, tempstring);
	strcat(logfields, "wind_speed_min_datetime, wind_speed_max_datetime, ");
	sprintf(tempstring,
		"str_to_date(\'%d-%d-%d %d:%d\',\'%%Y-%%m-%%d %%H:%%i\'),",
		time_min.year, time_min.month, time_min.day, time_min.hour, time_min.minute);
	strcat(logvalues, tempstring);
	sprintf(tempstring,
		"str_to_date(\'%d-%d-%d %d:%d\',\'%%Y-%%m-%%d %%H:%%i\'),",
		time_max.year, time_max.month, time_max.day, time_max.hour, time_max.minute);
	strcat(logvalues, tempstring);

	/* READ DATE AND TIME FORM METEOSTATION */
	LOG(LOG_MAX, "READ DATE AND TIME FORM METEOSTATION.");
	strcat(logfields, "ws_datetime, ");
	ws_time(ws2300, &time_min);
	sprintf(tempstring,
		"str_to_date(\'%d-%d-%d %d:%d:%d\',\'%%Y-%%m-%%d %%H:%%i:%%s\'),",
		time_min.year, time_min.month, time_min.day, time_min.hour, time_min.minute, time_min.second);
	strcat(logvalues, tempstring);

	/* READ WIND SPEED (WITH WIND MIN_MAX RESET) AND DIRECTION AND WINDCHILL */
	LOG(LOG_MAX, "READ WIND SPEED (WITH WIND MIN_MAX RESET) AND DIRECTION AND WINDCHILL.");
	strcat(logfields, "wind_speed, wind_angle0, wind_angle1, wind_angle2, wind_angle3, wind_angle4, wind_angle5, wind_direction, ");
	sprintf(tempstring,"\'%.1f\',",
	        wind_all_reset(ws2300, config.wind_speed_conv_factor, &tempint, winddir, RESET_MIN + RESET_MAX) );
	strcat(logvalues, tempstring);
	sprintf(tempstring,
		"\'%.1f\',\'%.1f\',\'%.1f\',\'%.1f\',\'%.1f\',\'%.1f\',\'%s\',",
		winddir[0], winddir[1], winddir[2], winddir[3], winddir[4], winddir[5], directions[tempint]);
	strcat(logvalues, tempstring);

	/* READ WINDCHILL */
	LOG(LOG_MAX, "READ WINDCHILL.");
	strcat(logfields, "wind_chill, ");
	sprintf(tempstring,"\'%.1f\',", windchill(ws2300, config.temperature_conv) );
	strcat(logvalues, tempstring);

	/* READ RAIN 1H */
	LOG(LOG_MAX, "READ RAIN 1H.");
	strcat(logfields, "rain_1h, ");
	sprintf(tempstring,"\'%.1f\',", rain_1h(ws2300, config.rain_conv_factor) );
	strcat(logvalues, tempstring);
	
	/* READ RAIN 24H */
	LOG(LOG_MAX, "READ RAIN 24H.");
	strcat(logfields, "rain_24h, ");
	sprintf(tempstring,"\'%.1f\',", rain_24h(ws2300, config.rain_conv_factor) );
	strcat(logvalues, tempstring);
	
	/* READ RAIN TOTAL */
	LOG(LOG_MAX, "READ RAIN TOTAL.");
	strcat(logfields, "rain_total, ");
	sprintf(tempstring,"\'%.1f\',", rain_total(ws2300, config.rain_conv_factor) );
	strcat(logvalues, tempstring);

	/* READ RELATIVE PRESSURE */
	LOG(LOG_MAX, "READ RELATIVE PRESSURE.");
	strcat(logfields, "rel_pressure, ");
	sprintf(tempstring,"\'%.1f\',", rel_pressure(ws2300, config.pressure_conv_factor) );
	strcat(logvalues, tempstring);

	/* READ TENDENCY AND FORECAST */
	LOG(LOG_MAX, "READ TENDENCY AND FORECAST.");
	strcat(logfields, "tendency, forecast, ");
	tendency_forecast(ws2300, tendency, forecast);
	sprintf(tempstring,"\'%s\',\'%s\', ", tendency, forecast);
	strcat(logvalues, tempstring);

	/* CLOSE THE WEATHER STATION TO ENABLE OTHER PROGRAMS TO ACCESS */
	LOG(LOG_MAX, "CLOSE THE WEATHER STATION TO ENABLE OTHER PROGRAMS TO ACCESS.");
	close_weatherstation(ws2300);

	LOG(LOG_MED, "Weather station closed, connecting to MySQL...");

	/* ASSEMBLY SQL STATEMENT */
	strcat(logfields, "mysql2300_version");
	sprintf(tempstring,"\'%s\'", rcsver);
	strcat(logvalues, tempstring);
	//sprintf(query, "INSERT INTO weather VALUES ( NOW(), %s, null )", logvalues);
	sprintf(query, "insert into %s (rec_datetime, %s) values (now(), %s)", config.mysql_tablename, logfields, logvalues);
	LOG(LOG_MAX, "ASSEMBLED SQL STATEMENT:");
	LOG(LOG_MAX, query);

	/* INIT MYSQL AND CONNECT */
	LOG(LOG_MAX, "INIT MYSQL AND CONNECT.");
	if (!mysql_init(&mysql))
	{
		fprintf(stderr, "Cannot initialize MySQL");
		fprintf(stderr, "%s\n", query); 
		exit(EXIT_FAILURE);
	}

	if(!mysql_real_connect(&mysql, config.mysql_host, config.mysql_user,
	                       config.mysql_passwd, config.mysql_database,
	                       config.mysql_port, NULL, 0))
	{
		fprintf(stderr, "%d: %s \n",
		mysql_errno(&mysql), mysql_error(&mysql));
		fprintf(stderr, "%s\n", query); 
		exit(EXIT_FAILURE);
	}

	LOG(LOG_MAX, "INSERTING DATA.");
	if (mysql_query(&mysql, query))
	{
		fprintf(stderr, "Could not insert row. %s %d: \%s \n",
		        query, mysql_errno(&mysql), mysql_error(&mysql));
		fprintf(stderr, "%s\n", query); 
		mysql_close(&mysql);
		exit(EXIT_FAILURE);
	}

	LOG(LOG_MAX, "CLOSING MYSQL.");
	mysql_close(&mysql);

	LOG(LOG_MIN, "Finished successfully.");

	return(0);
}
