/*	pgsql2300.c
 *
 *	Version 1.1 - with open2300 v 1.10
 *
 *	Get data from WS2300 weather station
 *	and add them to PostgreSQL database
 *
 *	Copyright 2004-2005, Kenneth Lavrsen/Thomas Grieder/Przemyslaw Sztoch
 *
 *	This program is published under the GNU General Public license
 *
 *	1.1  2004 Nov 25  Przemyslaw Sztoch
 *	Creates pgsql2300. A Rewrite of mysql2300.
 */

#include <libpq-fe.h>
#include "rw2300.h"
#include <stdarg.h>


/* fmt_alloc()
 *
 * Wrapper for vsnprintf() allocating memory as needed.
 *
 * */
char * fmt_alloc(const char *fmt, ...)
{
    int n;
    int size = 256;     /* Guess we need no more than 256 bytes */
    char *p, *np;
    va_list ap;

   if ((p = malloc(size)) == NULL)
        return NULL;

   while (1) {

       /* Try to print in the allocated space */

       va_start(ap, fmt);
       n = vsnprintf(p, size, fmt, ap);
       va_end(ap);

       /* Check error code */

       if (n < 0)
            return NULL;

       /* If that worked, return the string */

       if (n < size)
            return p;

       /* Else try again with more space */

       size = n + 1;       /* Precisely what is needed */

       if ((np = realloc (p, size)) == NULL) {
            free(p);
            return NULL;
        } else {
            p = np;
        }
    }
}

 
/********** MAIN PROGRAM ************************************************
 *
 * This program reads current weather data from a WS2300
 * and writes the data to a PgSQL database.
 *
 * The open2300.conf config file must contain the following parameters
 * 
 * It takes one parameters. The config file name with path
 * If this parameter is omitted the program will look at the default paths
 * See the open2300.conf-dist file for info
 *
 ***********************************************************************/
int main(int argc, char *argv[])
{
	WEATHERSTATION ws2300;
	PGconn *conn;
	PGresult *res;
	int retval = 1;
//	unsigned char logline[200] = "";
	const char *directions[]= {"N","NNE","NE","ENE","E","ESE","SE","SSE",
	                           "S","SSW","SW","WSW","W","WNW","NW","NNW"};
//	double winddir[6];
	int tempint;
//	char tendency[15];
//	char forecast[15];
	struct config_type config;
	char query[4096];
	char *sql_query;
	struct weather_dataset ws_data;

	get_configuration(&config, argv[1]);

	ws2300 = open_weatherstation(config.serial_device_name);

	/* READ TEMPERATURE INDOOR */

	ws_data.temperature_indoor = temperature_indoor(ws2300,
			config.temperature_conv);

//	sprintf(logline,"%s\'%.1f\',", logline, ws_data.temperature_indoor);


	/* READ TEMPERATURE OUTDOOR */

	ws_data.temperature_outdoor = temperature_outdoor(ws2300,
			config.temperature_conv);

//	sprintf(logline,"%s\'%.1f\',", logline, ws_data.temperature_outdoor);


	/* READ DEWPOINT */

	ws_data.dewpoint = dewpoint(ws2300, config.temperature_conv);

//	sprintf(logline,"%s\'%.1f\',", logline, ws_data.dewpoint );
	

	/* READ RELATIVE HUMIDITY INDOOR */

  ws_data.humidity_indoor = humidity_indoor(ws2300);

//	sprintf(logline,"%s\'%d\',", logline, ws_data.humidity_indoor);
	
	
	/* READ RELATIVE HUMIDITY OUTDOOR */

  ws_data.humidity_outdoor = humidity_outdoor(ws2300);

//  sprintf(logline,"%s\'%d\',", logline, ws_data.humidity_outdoor);


	/* READ WIND SPEED AND DIRECTION aND WINDCHILL */

  ws_data.wind_speed = wind_all(ws2300,
      config.wind_speed_conv_factor, &tempint, ws_data.wind_angle);

  ws_data.wind_direction = fmt_alloc("%s", directions[tempint]);

//	sprintf(logline,"%s\'%.1f\',", logline, ws_data.wind_speed);

//	sprintf(logline,"%s\'%.1f\',\'%s\',", logline,
//	        ws_data.wind_angle[0],
//          fmt_alloc("%s", directions[tempint]) );
	

	/* READ WINDCHILL */

  ws_data.wind_chill = windchill(ws2300, config.temperature_conv);

//	sprintf(logline,"%s\'%.1f\',", logline, ws_data.wind_chill);

	
	/* READ RAIN 1H */

  ws_data.rain_1h = rain_1h(ws2300, config.rain_conv_factor);

//	sprintf(logline,"%s\'%.1f\',", logline, ws_data.rain_1h);
	
	
	/* READ RAIN 24H */

  ws_data.rain_24h = rain_24h(ws2300, config.rain_conv_factor);

//	sprintf(logline,"%s\'%.1f\',", logline, ws_data.rain_24h);

	
	/* READ RAIN TOTAL */

  ws_data.rain_total = rain_total(ws2300, config.rain_conv_factor);

//	sprintf(logline,"%s\'%.1f\',", logline, ws_data.rain_total);

	
	/* READ RELATIVE PRESSURE */

  ws_data.rel_pressure = rel_pressure(ws2300, config.pressure_conv_factor);

//	sprintf(logline,"%s\'%.1f\',", logline,	ws_data.rel_pressure);


	/* READ TENDENCY AND FORECAST */
	
	tendency_forecast(ws2300, ws_data.tendency, ws_data.forecast);

//	sprintf(logline,"%s\'%s\',\'%s\'", logline, ws_data.tendency,
//      ws_data.forecast);


	/* CLOSE THE WEATHER STATION TO ENABLE OTHER PROGRAMS TO ACCESS */
	close_weatherstation(ws2300);

  sql_query = fmt_alloc(
        "INSERT INTO %s (\n"
        "     temperature_indoor\n"
        "   , temperature_outdoor\n"
        "   , dewpoint\n"
        "   , humidity_indoor\n"
        "   , humidity_outdoor\n"
        "   , wind_speed\n"
        "   , wind_angle\n"
        "   , wind_direction\n"
        "   , wind_chill\n"
        "   , rain_1h\n"
        "   , rain_24h\n"
        "   , rain_total\n"
        "   , tendency\n"
        "   , forecast\n"
        ") VALUES (\n"
        "     %.1f\n"
        "   , %.1f\n"
        "   , %.1f\n"
        "   , %d\n"
        "   , %d\n"
        "   , %.1f\n"
        "   , %.1f\n"
        "   , '%s'\n"
        "   , %.1f\n"
        "   , %.1f\n"
        "   , %.1f\n"
        "   , %.1f\n"
        "   , '%s'\n"
        "   , '%s'\n"
        ")\n",
      "table_name",
      ws_data.temperature_indoor, ws_data.temperature_outdoor, ws_data.dewpoint,
      ws_data.humidity_indoor, ws_data.humidity_outdoor, ws_data.wind_speed,
      ws_data.wind_angle[0], ws_data.wind_direction, ws_data.wind_chill,
      ws_data.rain_1h, ws_data.rain_24h, ws_data.rain_total,
      ws_data.tendency, ws_data.forecast);

  printf("%s", sql_query);

  free(ws_data.wind_direction);
  free(sql_query);

//	sprintf(query, "INSERT INTO %s VALUES ('%s', current_timestamp, %s)", config.pgsql_table, config.pgsql_station, logline);

	//printf("%s\n",query);  //disabled to be used in cron job
	//printf("%s\n",config.pgsql_connect); //debug

	/* INIT PQ AND EXECUTE QUERY */
	conn = PQconnectdb(config.pgsql_connect);

	if (PQstatus(conn) == CONNECTION_BAD)
	{
		fprintf(stderr, "Connection to PgSQL failed:\n%s\n", config.pgsql_connect);
		fprintf(stderr, "%s", PQerrorMessage(conn));
	}
	else
	{
		res = PQexec(conn, query);
	
		if (PQresultStatus(res) == PGRES_COMMAND_OK)
			retval = 0;
		else
			fprintf(stderr, "Could not insert row. %s:\n%s\n", PQresultErrorMessage(res), query);
				
		PQclear(res);
	}
		
	PQfinish(conn);

	return retval;
}
