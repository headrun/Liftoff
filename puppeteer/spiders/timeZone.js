var airportTimezone = require('airport-timezone');
module.exports = { timeZoneCode }
async function timeZoneCode(request_date){
	var timeZone = await airportTimezone.filter(function(airport){
	  return airport.code === request_date.code;
	})[0];
	return timeZone
}