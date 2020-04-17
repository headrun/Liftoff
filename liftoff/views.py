from time import time
from rest_framework.decorators import api_view
from rest_framework.status import HTTP_400_BAD_REQUEST,\
HTTP_404_NOT_FOUND, HTTP_200_OK, HTTP_500_INTERNAL_SERVER_ERROR
from rest_framework.response import Response
from .americanAirline import americanAirlines
from .aeroplan import aeroplanselnium
from .virginatlantic import vigranAtlantic
from .deltaMiles import DeltaSkyMiles

SCRAPERS_DICT = {
    "AA": [americanAirlines, "https://www.aa.com"], "AC": [aeroplanselnium, "https://www.aeroplan.com"],
    "VS": [vigranAtlantic, "https://www.virginatlantic.com"], "DL":[DeltaSkyMiles, "https://www.delta.com"]
    }

@api_view(['POST'])
def runscraper(request):
    if request.method == 'POST':
        start = time()
        final, sites = {}, {}
        values = request.data
        valid = validateRequest(values)

        airlines = values.get('airlines', '')
        for idx, airline in enumerate(airlines):
            site_key = chr(97 + idx).upper()

            if not airline or not valid:
                status = "Error"
                description = "Please provides all mandatory fields"
                res_status = HTTP_400_BAD_REQUEST

            else:
                res_status = HTTP_200_OK

            crawler_start = time()
            if airline in SCRAPERS_DICT.keys():
                values.update({"site_key": site_key})
                scraper_class, url = SCRAPERS_DICT.get(airline, [])
                final_dict, error_message = scraper_class(values)

            else:
                final_dict = []
                error_message = 'invalid airlines'

            if not error_message:
                final = {"routes": final_dict}
                status, description = "OK","OK"

            elif error_message == "invalid airlines":
                status = "Error"
                description = "invalid airlines"
                res_status = HTTP_400_BAD_REQUEST

            else:
                status = "Error"
                description = "Temporarily resource not available"
                res_status = HTTP_500_INTERNAL_SERVER_ERROR

            crawler_end = time()
            crawler_res_time = int(round((crawler_end - crawler_start) * 1000))

            sites.update({
                site_key: {
                    "url": url, "status": status, "description": description,
                    "results": len(final_dict), "response_time": crawler_res_time,
                    "airline": airline
                    }
                })

        end = time()
        res_time = int(round((end - start) * 1000))
        final["metrics"] = {"response_time": res_time, "sites": sites}
        return Response(final, status=res_status)


def validateRequest(data):
    airline = data.get('airlines', [])
    arrival =  ''.join(data.get('arrivals', []))
    departure = ''.join(data.get('departures', []))
    cabins = data.get('cabins', '')
    departure_dict = data.get('departure_date', {})
    arrival_dict = data.get('arrival_date', {})
    max_stops = data.get('max_stops', '')
    passengers = data.get('passengers', '')

    valid = True
    if not airline: valid = False
    if not cabins: valid = False
    if departure_dict: valid = False if not departure_dict.get('when', '') else True
    if arrival_dict: valid = False if not arrival_dict.get('when', '') or not arrival else True
    if not departure: valid = False
    if max_stops == '': valid = False
    if not passengers: valid = False
    return valid

