import json
import copy
from datetime import datetime
import requests

def americanAirlines(request_data):
    data = request_data
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
    departureDate = data.get('departure_date', {}).get('when', '')
    arrivalDate = data.get('arrival_date', {}).get('when', '')
    request_cabins = data.get('cabins', [])
    cabin_classes = []
    cabinMapping = {
        'COACH':'economy',
        'PREMIUM_ECONOMY':'premium_economy',
        'BUSINESS':'business',
        'FIRST':'first_class'
    }
    for cabin in request_cabins:
        if cabin.lower() == "first_class":
            cabin_classes.append("FIRST")
        elif cabin.lower() == "business":
            cabin_classes.append("BUSINESS")
        elif cabin.lower() == "premium_economy":
            cabin_classes.append("PREMIUM_ECONOMY")
        elif cabin.lower() == "economy":
            cabin_classes.append("COACH")
    tripStatus = 'RoundTrip' if arrivalDate else 'OneWay'
    maxStop = data.get('max_stops', 0)
    data = {
        "allCarriers": True,
        "departureDate": departureDate,
        "destination": ''.join(data.get('arrivals', [])),
        "errorCode": "",
        "locale": "en_US",
        "loyaltyInfo": {"loyaltyId": "", "eliteLevel": "", "loyaltyBalance": ""},
        "origin": ''.join(data.get('departures', [])),
        "passengers": [{"type": "adult", "count": data.get('passengers', 0)}],
        "selectedProducts": [],
        "returnDate": arrivalDate,
        "searchType": "Award",
        "sessionId": "",
        "sliceIndex": 0,
        "solutionId": "",
        "solutionSet": "",
        "tripType": tripStatus,
        "cabinType": "",
        "maxStopCount": None
    }
    final_dict = []
    data = json.dumps(data)
    response = requests.post('https://www.americanairlines.in/booking/api/search/v2/itinerary', headers=headers, data=data)
    json_data = json.loads(response.text)
    errorMsg = json_data.get('message', '')
    if errorMsg:
        print("Invalid Request")
        return final_dict, errorMsg

    slice_list = json_data.get('slices', [])
    final_dict = []
    for ele in slice_list:
        sample_dict = {}
        sample_dict["distance"] = None
        sample_dict["num_stops"] = ele.get('stops', 0)
        if sample_dict["num_stops"] <= maxStop:
            segments = ele.get('segments', [])
            sample_dict["connections"] = []
            ele_arrival = ele.get('destination', {}).get('code', '')
            ele_departure = ele.get('origin', {}).get('code', '')

            request_arrivals = request_data.get('arrivals', '')
            request_departures = request_data.get('departures', '')

            if (ele_arrival not in request_arrivals) or (ele_departure not in request_departures):
                continue

            fare_classes = {}
            for segment_element in segments:
                total_time = 0
                airlineDetails = {}
                airLine = segment_element.get('flight', {}).get('carrierCode', '')
                flightNo = segment_element.get('flight', {}).get('flightNumber', '')
                arrivalDateTime = segment_element.get('arrivalDateTime', '')
                arrivalAirport = segment_element.get('destination', {}).get('code', '')
                departureDateTime = segment_element.get('departureDateTime', '')
                departureAirport = segment_element.get('origin', {}).get('code', '')
                airlineDetails["airline"] = "AA"
                airlineDetails["departure"] = {"when": departureDateTime, "airport": departureAirport}
                airlineDetails["arrival"] = {"when": arrivalDateTime, "airport": arrivalAirport}
                aircraftModel = segment_element.get('legs', [{}])[0].get('aircraft', {}).get('shortName')
                airlineDetails["distance"] = None
                flightNumber = airLine + flightNo
                airlineDetails["flight"] = [flightNumber]
                try:
                    aircraftManufacturer = aircraftModel.split(' ')[0]
                except:
                    aircraftManufacturer = ''
                try:
                    aircraftModelType = aircraftModel.split(' ')[1]
                except:
                    aircraftModelType = ''
                airlineDetails["aircraft"] = {"model": aircraftModelType, "manufacturer": aircraftManufacturer}
                legs = segment_element.get('legs', [])
                for leg in legs:
                    productDetails = leg.get('productDetails', [])
                    for product in productDetails:
                        fare_classes.setdefault(aircraftModelType, {}).update({product.get('productType', ''): product.get('bookingCode', '')})
                    flightTotalTime = leg.get('durationInMinutes', 0)
                    fTime = None
                    if flightTotalTime != 0:
                        fTime = str(int(flightTotalTime / 60)) + ':' + str(flightTotalTime % 60)
                        fTime = datetime.strptime(fTime, "%H:%M").strftime('%H:%M')
                    total = leg.get('connectionTimeInMinutes', 0)
                    lTime = None
                    if total != 0:
                        total_time = total_time + total
                        lTime = str(int(total / 60)) + ':' + str(total % 60)
                        try:
                            lTime = datetime.strptime(lTime, "%H:%M").strftime('%H:%M')
                        except:
                            lTime = lTime
                    airlineDetails["times"] = {"flight": fTime, "layover": lTime}
                airlineDetails["redemptions"] = None
                airlineDetails["payments"] = None
                airlineDetails["tickets"] = None
                sample_dict["connections"].append(airlineDetails)

            connectionTimeInMinutes = str(int(total_time / 60)) + ':' + str(total_time % 60)
            layoverTime = datetime.strptime(connectionTimeInMinutes, "%H:%M").strftime('%H:%M')
            if layoverTime == '00:00':
                layoverTime = None
            durationInMinutes = ele.get('durationInMinutes', 0)
            duration = str(int(durationInMinutes / 60)) + ':' + str(durationInMinutes % 60)
            try:
                flightTime = datetime.strptime(duration, "%H:%M").strftime('%H:%M')
            except:
                flightTime = duration
            sample_dict["times"] = {'flight': flightTime, 'layover': layoverTime}
            sample_dict["site_key"] = request_data['site_key']
            webSpecial = []
            pricingDetails = ele.get('pricingDetail', [])
            for price in pricingDetails:
                final_sub_dict = copy.deepcopy(sample_dict)
                if price.get('productAvailable') == True:
                    cabin = price.get('productType')
                    if cabin in cabin_classes:
                        productBenifits = price.get('productBenefits', '')
                        miles = price.get('perPassengerAwardPoints', 0)
                        final_sub_dict["redemptions"] = [{"miles": miles, "program": "American Airlines AAdvantage"}]
                        final_sub_dict["award_type"] = productBenifits
                        for connection in final_sub_dict["connections"]:
                            model = connection.get('aircraft', {}).get('model', '')
                            connection["fare_class"] = fare_classes.get(model, {}).get(cabin, '')
                            connection["cabin"] = cabinMapping[cabin]
                        currency = price.get('perPassengerDisplayTotal', {}).get('currency', '')
                        taxes = price.get('perPassengerDisplayTotal').get('amount', '')
                        final_sub_dict["payments"] = [{"currency": currency, "taxes": taxes, "fees":None}]
                        final_dict.append(final_sub_dict)
                        webSpecial.append(price.get('productType'))

    return final_dict, errorMsg
