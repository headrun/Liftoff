import json
from copy import deepcopy
from datetime import datetime, timedelta
import requests

def americanAirlines(request_data):
    max_stops = request_data.get('max_stops', 0)
    passengers_count = request_data.get('passengers', 0)
    departure_date = request_data.get('departure_date', {}).get('when', '')
    arrival_date = request_data.get('arrival_date', {}).get('when', '')
    departures = request_data.get('departures', [])
    arrivals = request_data.get('arrivals', [])
    trip_status = 'RoundTrip' if arrival_date else 'OneWay'

    award_mapping = {
        'Economy': 'AAnytime Main Cabin',
        'Premium Economy': 'AAnytime Premium Economy',
        'Business': 'AAnytime Business',
        'First Class': 'AAnytime First'
    }

    cabin_mapping = {
        'COACH': 'Economy',
        'PREMIUM_ECONOMY': 'Premium Economy',
        'BUSINESS': 'Business',
        'FIRST': 'First Class'
    }

    cabin_classes = []
    request_cabins = request_data.get('cabins', [])
    for cabin in request_cabins:
        if cabin.lower() == "first_class":
            cabin_classes.append("FIRST")
        elif cabin.lower() == "business":
            cabin_classes.append("BUSINESS")
        elif cabin.lower() == "premium_economy":
            cabin_classes.append("PREMIUM_ECONOMY")
        elif cabin.lower() == "economy":
            cabin_classes.append("COACH")

    headers = {
        'authority': 'www.americanairlines.co.uk',
        'accept': 'application/json, text/plain, */*',
        'sec-fetch-dest': 'empty',
        'x-cid': 'a79b052d-04fd-4c4c-810e-72a1eec4f712',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.106 Safari/537.36',
        'content-type': 'application/json',
        'origin': 'https://www.americanairlines.co.uk',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'referer': 'https://www.americanairlines.co.uk/booking/choose-flights',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8,te;q=0.7,ta;q=0.6',
    }

    data = {
        "allCarriers": True,
        "departureDate": departure_date,
        "destination": ''.join(arrivals),
        "errorCode": "",
        "locale": "en_US",
        "loyaltyInfo": {"loyaltyId": "", "eliteLevel": "", "loyaltyBalance": ""},
        "origin": ''.join(departures),
        "passengers": [{"type": "adult", "count": passengers_count}],
        "selectedProducts": [],
        "returnDate": arrival_date,
        "searchType": "Award",
        "sessionId": "",
        "sliceIndex": 0,
        "solutionId": "",
        "solutionSet": "",
        "tripType": trip_status,
        "cabinType": "",
        "maxStopCount": None
    }

    final_dict = []
    url = 'https://www.americanairlines.in/booking/api/search/v2/itinerary'
    response = requests.post(url, headers=headers, data=json.dumps(data))
    json_data = json.loads(response.text)

    error_msg = json_data.get('message', '')
    if error_msg:
        return final_dict, error_msg

    final_dict = []
    result_slices = json_data.get('slices', [])
    for result_slice in result_slices:
        final_flight_times, final_layover_times = [], []
        _dict, fare_classes, connections = {}, {}, []

        total_duration = result_slice.get('durationInMinutes', 0)
        _arrival = result_slice.get('destination', {}).get('code', '')
        _departure = result_slice.get('origin', {}).get('code', '')

        if (_arrival not in arrivals) or (_departure not in departures):
            continue

        stops = result_slice.get('stops', 0)
        if stops <= max_stops:
            segments = result_slice.get('segments', [])
            for segment_element in segments:
                aircraft_manufacturer, aircraft_model_type, airline_details = '', '', {}
                airline = segment_element.get('flight', {}).get('carrierCode', '')
                flight_no = '%s%s' % (airline, segment_element.get('flight', {}).get('flightNumber', ''))
                arrival = segment_element.get('destination', {}).get('code', '')
                departure = segment_element.get('origin', {}).get('code', '')
                arrival_datetime = segment_element.get('arrivalDateTime', '')
                departure_datetime = segment_element.get('departureDateTime', '')

                legs = segment_element.get('legs', [])
                for leg in legs:
                    aircraft_details = leg.get('aircraft', {}).get('shortName', '')
                    if aircraft_details:
                        aircraft_manufacturer = aircraft_details.split(' ')[0]
                        aircraft_model_type = aircraft_details.split(' ')[-1]

                    fare_classes.setdefault(aircraft_model_type, {})
                    product_details = leg.get('productDetails', [])
                    for product in product_details:
                        fare_classes.get(aircraft_model_type, {}).update(
                            {product.get('productType', ''): product.get('bookingCode', '')})

                    flight_time = leg.get('durationInMinutes', '00:00')
                    if ':' not in str(flight_time):
                        final_flight_times.append(flight_time)
                        flight_time = str(flight_time // 60).zfill(2) + ':' + str(flight_time % 60).zfill(2)

                    layover_time = leg.get('connectionTimeInMinutes', '00:00')
                    if ':' not in str(layover_time):
                        final_layover_times.append(layover_time)
                        layover_time = str(layover_time // 60).zfill(2) + ':' + str(layover_time % 60).zfill(2)

                airline_details.update({
                    "airline": airline,
                    "flight": [flight_no],
                    "departure": {"when": departure_datetime, "airport": departure},
                    "arrival": {"when": arrival_datetime, "airport": arrival},
                    "distance": None,
                    "aircraft": {"model": aircraft_model_type, "manufacturer": aircraft_manufacturer},
                    "times": {"flight": flight_time, "layover": layover_time},
                    "redemptions": None,
                    "payments": None,
                    "tickets": None
                })
                connections.append(airline_details)

            total_layover_time = sum(final_layover_times)
            total_flight_time = total_duration - total_layover_time
            total_layover_time = str(total_layover_time // 60).zfill(2) + ':' + str(total_layover_time % 60).zfill(2)
            total_flight_time = str(total_flight_time // 60).zfill(2) + ':' + str(total_flight_time % 60).zfill(2)
            _dict.update({
                "distance": None,
                "num_stops": stops,
                "connections": connections,
                "times": {'flight': str(total_flight_time), 'layover': str(total_layover_time)},
                "site_key": request_data['site_key']
            })

            pricing_details = result_slice.get('pricingDetail', [])
            for price_details in pricing_details:
                final_sub_dict = deepcopy(_dict)
                if price_details.get('productAvailable', False):
                    cabin = price_details.get('productType', '')
                    if cabin in cabin_classes:
                        map_cabin = cabin_mapping.get(cabin, '')
                        award_type = award_mapping.get(map_cabin, '')
                        miles = price_details.get('perPassengerAwardPoints', 0)
                        currency = price_details.get('perPassengerDisplayTotal', {}).get('currency', '')
                        taxes = price_details.get('perPassengerDisplayTotal').get('amount', '')

                        for connection in final_sub_dict["connections"]:
                            model = connection.get('aircraft', {}).get('model', '')

                            connection.update({
                                "fare_class": fare_classes.get(model, {}).get(cabin, ''),
                                "cabin": map_cabin
                            })

                        final_sub_dict.update({
                            "redemptions": [{"miles": miles, "program": "American AAdvantage"}],
                            "award_type": award_type,
                            "payments": [{"currency": currency, "taxes": taxes, "fees": None}]
                        })
                        final_dict.append(final_sub_dict)
    if len(final_dict) == 0:
        error_msg = "No flights found"
        return final_dict, error_msg
    else:
        return final_dict, error_msg