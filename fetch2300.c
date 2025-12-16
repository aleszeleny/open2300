/*  open2300 - fetch2300.c
 *  
 *  Version 1.11
 *  
 *  Control WS2300 weather station
 *  
 *  Copyright 2003-2006, Kenneth Lavrsen
 *  This program is published under the GNU General Public license
 */

#define DEBUG 1

#include "rw2300.h"

 
/********** MAIN PROGRAM ************************************************
 *
 * This program reads all current and min/max data from a WS2300
 * weather station and write it to standard out. This is the program that
 * the program weatherstation.php uses to display a nice webpage with
 * current weather data.
 *
 * It takes one parameter which is the config file name with path
 * If this parameter is omitted the program will look at the default paths
 * See the open2300.conf-dist file for info
 *
 ***********************************************************************/
int main(int argc, char *argv[])
{
	WEATHERSTATION ws2300;
	char logline[3000] = "";
	char tempstring[1000] = "";
	char datestring[50];     //used to hold the date stamp for the log file
	const char *directions[]= {"N","NNE","NE","ENE","E","ESE","SE","SSE",
	                           "S","SSW","SW","WSW","W","WNW","NW","NNW"};
	double winddir[6];
	char tendency[15];
	char forecast[15];
	struct config_type config;
	double tempfloat_min, tempfloat_max;
	int tempint, tempint_min, tempint_max;
	struct timestamp time_min, time_max;
	time_t basictime;

	if (DEBUG) printf("DEBUG:%s:%d\tget_configuration()\n", __FILE__, __LINE__);
	get_configuration(&config, argv[1]);

	if (DEBUG) printf("DEBUG:%s:%d\topen_weatherstation()\n", __FILE__, __LINE__);
	ws2300 = open_weatherstation(config.serial_device_name);


	/* READ TEMPERATURE INDOOR */

	if (DEBUG) printf("DEBUG:%s:%d\ttemperature_indoor()\n", __FILE__, __LINE__);
	sprintf(logline, "Ti %.1f\n", temperature_indoor(ws2300, config.temperature_conv) );

	if (DEBUG) printf("DEBUG:%s:%d\ttemperature_indoor_minmax()\n", __FILE__, __LINE__);
	temperature_indoor_minmax(ws2300, config.temperature_conv, &tempfloat_min,
	                          &tempfloat_max, &time_min, &time_max);

	sprintf(tempstring, "Timin %.1f\nTimax %.1f\n"
	                    "TTimin %02d:%02d\nDTimin %04d-%02d-%02d\n"
	                    "TTimax %02d:%02d\nDTimax %04d-%02d-%02d\n",
	        tempfloat_min, tempfloat_max,
	        time_min.hour, time_min.minute, time_min.year, time_min.month, time_min.day,
	        time_max.hour, time_max.minute, time_max.year, time_max.month, time_max.day);
	strcat(logline, tempstring);


	/* READ TEMPERATURE OUTDOOR */

	if (DEBUG) printf("DEBUG:%s:%d\ttemperature_outdoor()\n", __FILE__, __LINE__);
	sprintf(tempstring, "To %.1f\n", temperature_outdoor(ws2300, config.temperature_conv) );
	strcat(logline, tempstring);

	if (DEBUG) printf("DEBUG:%s:%d\ttemperature_outdoor_minmax()\n", __FILE__, __LINE__);
	temperature_outdoor_minmax(ws2300, config.temperature_conv, &tempfloat_min,
	                           &tempfloat_max, &time_min, &time_max);

	sprintf(tempstring, "Tomin %.1f\nTomax %.1f\n"
	                    "TTomin %02d:%02d\nDTomin %04d-%02d-%02d\n"
	                    "TTomax %02d:%02d\nDTomax %04d-%02d-%02d\n",
	        tempfloat_min, tempfloat_max,
	        time_min.hour, time_min.minute, time_min.year, time_min.month, time_min.day,
	        time_max.hour, time_max.minute, time_max.year, time_max.month, time_max.day);
	strcat(logline, tempstring);


	/* READ DEWPOINT */

	if (DEBUG) printf("DEBUG:%s:%d\tdewpoint()\n", __FILE__, __LINE__);
	sprintf(tempstring, "DP %.1f\n", dewpoint(ws2300, config.temperature_conv) );
	strcat(logline, tempstring);

	if (DEBUG) printf("DEBUG:%s:%d\tdewpoint_minmax()\n", __FILE__, __LINE__);
	dewpoint_minmax(ws2300, config.temperature_conv, &tempfloat_min,
	                &tempfloat_max, &time_min, &time_max);

	sprintf(tempstring, "DPmin %.1f\nDPmax %.1f\n"
	                    "TDPmin %02d:%02d\nDDPmin %04d-%02d-%02d\n"
	                    "TDPmax %02d:%02d\nDDPmax %04d-%02d-%02d\n",
	        tempfloat_min, tempfloat_max,
	        time_min.hour, time_min.minute, time_min.year, time_min.month, time_min.day,
	        time_max.hour, time_max.minute, time_max.year, time_max.month, time_max.day);
	strcat(logline, tempstring);


	/* READ RELATIVE HUMIDITY INDOOR */

	if (DEBUG) printf("DEBUG:%s:%d\thumidity_indoor_all()\n", __FILE__, __LINE__);
	sprintf(tempstring, "RHi %d\n", humidity_indoor_all(ws2300, &tempint_min, &tempint_max,
	                                                    &time_min, &time_max) );
	strcat(logline, tempstring);

	sprintf(tempstring, "RHimin %d\nRHimax %d\n"
	                    "TRHimin %02d:%02d\nDRHimin %04d-%02d-%02d\n"
	                    "TRHimax %02d:%02d\nDRHimax %04d-%02d-%02d\n",
	        tempint_min, tempint_max,
	        time_min.hour, time_min.minute, time_min.year, time_min.month, time_min.day,
	        time_max.hour, time_max.minute, time_max.year, time_max.month, time_max.day);
	strcat(logline, tempstring);


	/* READ RELATIVE HUMIDITY OUTDOOR */

	if (DEBUG) printf("DEBUG:%s:%d\thumidity_outdoor_all()\n", __FILE__, __LINE__);
	sprintf(tempstring, "RHo %d\n", humidity_outdoor_all(ws2300, &tempint_min, &tempint_max,
	                                                  &time_min, &time_max) );
	strcat(logline, tempstring);

	sprintf(tempstring, "RHomin %d\nRHomax %d\n"
	                    "TRHomin %02d:%02d\nDRHomin %04d-%02d-%02d\n"
	                    "TRHomax %02d:%02d\nDRHomax %04d-%02d-%02d\n",
	        tempint_min, tempint_max,
	        time_min.hour, time_min.minute, time_min.year, time_min.month, time_min.day,
	        time_max.hour, time_max.minute, time_max.year, time_max.month, time_max.day);
	strcat(logline, tempstring);


	/* READ WIND SPEED AND DIRECTION */

	if (DEBUG) printf("DEBUG:%s:%d\twind_all()\n", __FILE__, __LINE__);
	sprintf(tempstring,"WS %.1f\n",
	       wind_all(ws2300, config.wind_speed_conv_factor, &tempint, winddir));
	strcat(logline, tempstring);

	sprintf(tempstring,"DIRtext %s\nDIR0 %.1f\nDIR1 %0.1f\n"
	                   "DIR2 %0.1f\nDIR3 %0.1f\nDIR4 %0.1f\nDIR5 %0.1f\n",
	        directions[tempint], winddir[0], winddir[1],
	        winddir[2], winddir[3], winddir[4], winddir[5]);
	strcat(logline, tempstring);


	/* WINDCHILL */

	if (DEBUG) printf("DEBUG:%s:%d\twindchill()\n", __FILE__, __LINE__);
	sprintf(tempstring, "WC %.1f\n", windchill(ws2300, config.temperature_conv) );
	strcat(logline, tempstring);

	if (DEBUG) printf("DEBUG:%s:%d\twindchill_minmax()\n", __FILE__, __LINE__);
	windchill_minmax(ws2300, config.temperature_conv, &tempfloat_min,
	                 &tempfloat_max, &time_min, &time_max); 

	sprintf(tempstring, "WCmin %.1f\nWCmax %.1f\n"
	                    "TWCmin %02d:%02d\nDWCmin %04d-%02d-%02d\n"
	                    "TWCmax %02d:%02d\nDWCmax %04d-%02d-%02d\n",
	        tempfloat_min, tempfloat_max,
	        time_min.hour, time_min.minute, time_min.year, time_min.month, time_min.day,
	        time_max.hour, time_max.minute, time_max.year, time_max.month, time_max.day);
	strcat(logline, tempstring);


	/* READ WINDSPEED MIN/MAX */

	if (DEBUG) printf("DEBUG:%s:%d\twind_minmax()\n", __FILE__, __LINE__);
	wind_minmax(ws2300, config.wind_speed_conv_factor, &tempfloat_min,
	            &tempfloat_max, &time_min, &time_max);

	sprintf(tempstring, "WSmin %.1f\nWSmax %.1f\n"
	                    "TWSmin %02d:%02d\nDWSmin %04d-%02d-%02d\n"
	                    "TWSmax %02d:%02d\nDWSmax %04d-%02d-%02d\n",
	        tempfloat_min, tempfloat_max,
	        time_min.hour, time_min.minute, time_min.year, time_min.month, time_min.day,
	        time_max.hour, time_max.minute, time_max.year, time_max.month, time_max.day);
	strcat(logline, tempstring);


	/* READ RAIN 1H */

	if (DEBUG) printf("DEBUG:%s:%d\train_1h_all()\n", __FILE__, __LINE__);
	sprintf(tempstring, "R1h %.2f\n",
	        rain_1h_all(ws2300, config.rain_conv_factor,
	                    &tempfloat_max, &time_max));
	strcat(logline, tempstring);

	sprintf(tempstring, "R1hmax %.2f\n"
	                    "TR1hmax %02d:%02d\nDR1hmax %04d-%02d-%02d\n",
	        tempfloat_max,
	        time_max.hour, time_max.minute, time_max.year, time_max.month, time_max.day);
	strcat(logline, tempstring);


	/* READ RAIN 24H */

	if (DEBUG) printf("DEBUG:%s:%d\train_24h_all()\n", __FILE__, __LINE__);
	sprintf(tempstring,"R24h %.2f\n",
	        rain_24h_all(ws2300, config.rain_conv_factor,
	                     &tempfloat_max, &time_max));
	strcat(logline, tempstring);

	sprintf(tempstring,"R24hmax %.2f\n"
	                   "TR24hmax %02d:%02d\nDR24hmax %04d-%02d-%02d\n",
	        tempfloat_max,
	        time_max.hour, time_max.minute, time_max.year, time_max.month, time_max.day);
	strcat(logline, tempstring);


	/* READ RAIN TOTAL */

	if (DEBUG) printf("DEBUG:%s:%d\train_total_all()\n", __FILE__, __LINE__);
	sprintf(tempstring,"Rtot %.2f\n",
	        rain_total_all(ws2300, config.rain_conv_factor, &time_max));
	strcat(logline, tempstring);

	sprintf(tempstring,"TRtot %02d:%02d\nDRtot %04d-%02d-%02d\n",
	        time_max.hour, time_max.minute, time_max.year,
	        time_max.month, time_max.day);
	strcat(logline, tempstring);


	/* READ RELATIVE PRESSURE */

	if (DEBUG) printf("DEBUG:%s:%d\trel_pressure()\n", __FILE__, __LINE__);
	sprintf(tempstring,"RP %.3f\n",
	        rel_pressure(ws2300, config.pressure_conv_factor) );
	strcat(logline, tempstring);


	/* RELATIVE PRESSURE MIN/MAX */

	if (DEBUG) printf("DEBUG:%s:%d\trel_pressure_minmax()\n", __FILE__, __LINE__);
	rel_pressure_minmax(ws2300, config.pressure_conv_factor, &tempfloat_min,
	                    &tempfloat_max, &time_min, &time_max);

	sprintf(tempstring, "RPmin %.3f\nRPmax %.3f\n"
	                    "TRPmin %02d:%02d\nDRPmin %04d-%02d-%02d\n"
	                    "TRPmax %02d:%02d\nDRPmax %04d-%02d-%02d\n",
	        tempfloat_min, tempfloat_max,
	        time_min.hour, time_min.minute, time_min.year, time_min.month, time_min.day,
	        time_max.hour, time_max.minute, time_max.year, time_max.month, time_max.day);
	strcat(logline, tempstring);


	/* READ TENDENCY AND FORECAST */

	if (DEBUG) printf("DEBUG:%s:%d\ttendency_forecast()\n", __FILE__, __LINE__);
	tendency_forecast(ws2300, tendency, forecast);
	sprintf(tempstring, "Tendency %s\nForecast %s\n", tendency, forecast);
	strcat(logline, tempstring);


	/* GET DATE AND TIME FOR LOG FILE, PLACE BEFORE ALL DATA IN LOG LINE */

	time(&basictime);
	strftime(datestring, sizeof(datestring),"Date %Y-%b-%d\nTime %H:%M:%S\n",
	         localtime(&basictime));

	// Print out and leave

	if (DEBUG) printf("DEBUG:%s:%d\tPrint out and leave()\n", __FILE__, __LINE__);
	printf("%s%s", datestring, logline);

	if (DEBUG) printf("DEBUG:%s:%d\tclose_weatherstation()\n", __FILE__, __LINE__);
	close_weatherstation(ws2300);

	if (DEBUG) printf("DEBUG:%s:%d\treturn(0)\n", __FILE__, __LINE__);
	return(0);
}

