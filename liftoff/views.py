from time import time
from rest_framework.decorators import api_view
from rest_framework.status import HTTP_400_BAD_REQUEST,\
HTTP_404_NOT_FOUND, HTTP_200_OK
from rest_framework.response import Response
from americanAirline import americanAirlines
from aeroplan import aeroplanselnium

SCRAPERS_DICT = {
    "AA": [americanAirlines, "https://www.aa.com"], "AC": [aeroplanselnium, "https://www.aeroplan.com/"]
    }

@api_view(['POST'])
def runscraper(request):
    if request.method == 'POST':
        start = time()
        final, length = {}, 0
        values = request.data
        valid = validateRequest(values)

        airline = ''.join(values.get('airlines', ''))
        if not airline or not valid:
            status = "Error"
            description = "Please provides all mandatory fields"
            res_status = HTTP_400_BAD_REQUEST
        else:
            res_status = HTTP_200_OK

        if airline in SCRAPERS_DICT.keys():
            scraper_class, url = SCRAPERS_DICT.get(airline, [])
            final_dict, error_message = scraper_class(values)

        else:
            final_dict = {}
            error_message = 'invalid airlines'

        if not error_message:
            final = {"routes": final_dict}
            status, description = "OK","OK"

        elif error_message == "invalid airlines":
            status = "Error"
            description = "invalid airlines"

        else:
            status = "Error"
            description = "invalid airlines"

        end = time()
        res_time = end - start
        final["metrics"] = {
            "url": url, "status": status, "description": description,
            "response_time": round(res_time, 2), "airline": airline, "results": len(final_dict)}
        return Response(final, status=res_status)


def validateRequest(data):
    airline = ''.join(data.get('airlines', []))
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

