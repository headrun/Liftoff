import re
import copy
import json
from time import sleep, strptime
from datetime import datetime, timedelta
from selenium import webdriver
from pyvirtualdisplay import Display
import requests
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from liftoff.settings import proxies

def UnitedMileagePlus(request_data):
    final_dict = []
    # processing the input data
    arrivalAirport = ''.join(request_data.get('arrivals', ''))
    departureAirport = ''.join(request_data.get('departures', ''))
    departureDate = request_data.get('departure_date', {}).get('when', '')
    arrivalDate = request_data.get('arrival_date', {}).get('when', '')
    passengers = request_data.get('passengers', 0)
    max_request_stops = request_data.get('max_stops', 0)
    departure_date = datetime.strptime(departureDate, "%Y-%m-%d").strftime('%B %d, %Y')
    if arrivalDate:
        arrival_date = datetime.strptime(arrivalDate, "%Y-%m-%d").strftime('%B %d, %Y')
    tripStatus = 'oneWay'
    if arrivalDate:
        tripStatus = 'roundTrip'
    else:
        arrivalDate = departureDate

    # cabin mappings
    cabin_classes = []
    cabin_mapping = {"First Saver Award": "First Class", "Business Saver Award": "Business",
                     "Business Everyday Award": "Business", "Premium Economy (lowest award)": "Premium Economy",
                     "Economy (lowest award)": "Economy"}
    request_cabins = request_data.get('cabins', [])
    for cabin in request_cabins:
        if cabin.lower() == "first_class":
            cabin_classes.append("First Saver Award")
        elif cabin.lower() == "business":
            cabin_classes.append("Business Saver Award")
            cabin_classes.append("Business Everyday Award")
        elif cabin.lower() == "premium_economy":
            cabin_classes.append("Premium Economy (lowest award)")
        elif cabin.lower() == "economy":
            cabin_classes.append("Economy (lowest award)")
    cabin_classes = list(set(cabin_classes))

    # login using selenium
    options = FirefoxOptions()
    options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)
    driver.get('https://www.united.com/en/us')

    # getting cookies from selenium driver
    cookies = {}
    cookies_data = driver.get_cookies()
    for ele in cookies_data:
        cookies[ele["name"]] = ele["value"]
    driver.quit()
    # python request for getting flight details
    headers = {
        'Connection': 'keep-alive',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Sec-Fetch-Dest': 'empty',
        'X-Requested-With': 'XMLHttpRequest',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Safari/537.36',
        'Content-Type': 'application/json; charset=UTF-8',
        'Origin': 'https://www.united.com',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8'
    }
    data = {
        "searchTypeMain": tripStatus,
        "realSearchTypeMain": tripStatus,
        "Origin": departureAirport,
        "Destination": arrivalAirport,
        "DepartDate": None,
        "DepartDateBasicFormat": departureDate,
        "ReturnDate": None,
        "ReturnDateBasicFormat": arrivalDate,
        "awardTravel": True,
        "MaxTrips": None,
        "numberOfTravelers": passengers,
        "numOfAdults": passengers,
        "numOfSeniors": 0,
        "numOfChildren04": 0,
        "numOfChildren03": 0,
        "numOfChildren02": 0,
        "numOfChildren01": 0,
        "numOfInfants": 0,
        "numOfLapInfants": 0,
        "travelerCount": passengers,
        "Trips": [
            {
                "DepartDate": departure_date,
                "ReturnDate": None,
                "PetIsTraveling": False,
                "PreferredTime": "",
                "PreferredTimeReturn": None,
                "Destination": arrivalAirport,
                "Index": 1,
                "Origin": departureAirport,
            }
        ],
        "CartId": "CC48FE28-73B0-4B7E-A64C-669B94C6BABF",
        "cabinSelection": "ECONOMY",
        "IsChangeFeeWaived": True,
        "CurrencyDescription": "International POS Cuurency",
    }
    if "roundTrip" in tripStatus:
        data["Trips"].append({
            "DepartDate": arrival_date,
            "ReturnDate": None,
            "PetIsTraveling": False,
            "PreferredTime": "",
            "PreferredTimeReturn": None,
            "Destination": arrivalAirport,
            "Index": 2,
            "Origin": departureAirport,
        })
    response = requests.post('https://www.united.com/ual/en/in/flight-search/book-a-flight/flightshopping/getflightresults/awd', headers=headers, cookies=cookies, data=json.dumps(data)) #proxies=proxies)
    res = json.loads(response.text)
    errorstatus = res.get('status', '')
    errorMsg = ''
    if "fail" in errorstatus:
        error = res.get('data', {}).get('Errors', '')
        errorMsg = error[0].get('Message', '')
    data = res.get('data', {}).get('Trips', {})
    if not data: data = []
    for data_element in data:
        flight_details = data_element.get('Flights', [])
        for flight in flight_details:
            sample_dict = {}
            dateTime = []
            sample_dict["num_stops"] = flight.get('StopsandConnections', 0)
            if sample_dict["num_stops"] <= max_request_stops:
                sample_dict["connections"] = []
                dateTime.append({'departure': flight.get('DepartDateTime', ''), 'arrival': flight.get('DestinationDateTime', ''), 'flightTime': flight.get('TravelMinutes', '')})
                departureDateTime = flight.get('DepartDateTime', '')
                arrivalDateTime = flight.get('DestinationDateTime', '')
                flightsegment = flight['FlightSegmentJson']
                flighttimes = flight.get('TravelMinutes', '')
                segments = json.loads(flightsegment)
                fareclass_mapping = {"First Saver Award": [], "Business Saver Award": [], "Business Everyday Award": [],
                                     "Premium Economy (lowest award)": [], "Economy (lowest award)": [], "Business/First Saver Award" :[],
                                     "Business/First Everyday Award": []}
                for segment in segments:
                    sub_dict = {}
                    flightDate = segment.get('FlightDate', '')
                    sub_dict["departure"] = {"when": "", "airport": segment.get("Origin", '')}
                    sub_dict["arrival"] = {"when": "", "airport": segment.get("Destination", '')}
                    sub_dict["flight"] = [segment.get('CarrierCode', '') + "" + segment.get('FlightNumber', '')]
                    arriv = sub_dict["flight"][0]
                    sub_dict["airline"] = ''.join(re.findall('\D+', arriv))
                    sub_dict["distance"] = None
                    aircraftModel = segment.get('EquipmentDescription', '')
                    try:
                        aircraftManufacturer = aircraftModel.split(' ')[0]
                    except:
                        aircraftManufacturer = ''
                    try:
                        aircraftModelType = aircraftModel.split(' ')[1]
                    except:
                        aircraftModelType = ''
                    sub_dict["aircraft"] = {"model": aircraftModelType, "manufacturer": aircraftManufacturer}
                    sub_dict["redemptions"] = None
                    sub_dict["payments"] = None
                    sub_dict["tickets"] = None
                    try:
                        flightTime = flightDate.split(' ')[1]
                    except:
                        flightTime = ''
                    sub_dict["times"] = {'flight': "", 'layover':None}
                
                    product_data = segment.get('Products', '')
                    for product in product_data:
                        fareclass_connection = product.get('BookingCode', '')
                        cabin_connection = product.get('ProductTypeDescription', '')
                        fareclass_mapping[cabin_connection.strip()].append(fareclass_connection)
                    sample_dict["connections"].append(sub_dict)
                try:
                    getdateTime = flight.get('Connections', [])
                    layoutTime = []
                    for date_element in getdateTime:
                        dateTime.append({'departure': date_element.get('DepartDateTime', ''),
                                         'arrival': date_element.get('DestinationDateTime', ''),
                                         'flightTime': date_element.get('TravelMinutes', '')})
                        layoutTime.append(date_element.get('ConnectTimeMinutes', ''))
                except: pass
                sumOfFlightTimes = 0
                sumOfLayoverTimes = 0
                for (con, dateTime) in zip(sample_dict["connections"], dateTime):
                    con["departure"]["when"] = datetime.strptime(dateTime["departure"], "%m/%d/%Y %H:%M").strftime('%Y-%m-%dT%H:%M')
                    con["arrival"]["when"] = datetime.strptime(dateTime["arrival"], "%m/%d/%Y %H:%M").strftime('%Y-%m-%dT%H:%M')
                    con["times"]["flight"] = str(dateTime["flightTime"]//60).zfill(2) + ':' +str(dateTime["flightTime"]%60).zfill(2)
                    sumOfFlightTimes = sumOfFlightTimes + dateTime["flightTime"]
                for (con, layout) in zip(sample_dict["connections"][0:], layoutTime):
                    sumOfLayoverTimes = sumOfLayoverTimes + layout
                    con["times"]["layover"] = str(layout // 60).zfill(2) + ':' + str(layout % 60).zfill(2)
                fareDetails = flight.get('Products', [])
                for fare in fareDetails:
                    final_sub_dict = {}
                    fareclass = fare.get('BookingCode', '')
                    cabin = fare.get('ProductTypeDescription', '')
                    if fareclass:
                        cabin = fare.get('ProductTypeDescription', '')
                        final_sub_dict = copy.deepcopy(sample_dict)
                        if cabin.strip() in cabin_classes:
                            for con in final_sub_dict["connections"]:
                                con["cabin"] = cabin_mapping[cabin.strip()]
                            for (con, fare_class_name) in zip(final_sub_dict["connections"], fareclass_mapping[cabin.strip()]):
                                con["fare_class"] = fare_class_name

                            final_sub_dict["distance"] = None
                            final_sub_dict["times"] = {"flight": str(sumOfFlightTimes//60).zfill(2) + ':' +str(sumOfFlightTimes%60).zfill(2), "layover": str(sumOfLayoverTimes//60).zfill(2) + ':' +str(sumOfLayoverTimes%60).zfill(2)}
                            if final_sub_dict["times"]["layover"] == "00:00":
                                final_sub_dict["times"]["layover"] == None
                            miles_details = fare.get('Prices', [])
                            tax_details = fare.get('TaxAndFees')
                            miles, taxandfees, currency = 0, 0.0, "USD"
                            if miles_details:
                                miles = miles_details[0]["Amount"]
                            if tax_details:
                                taxandfees = tax_details.get("Amount", 0.0)
                                currency = tax_details.get("Currency", '')
                            final_sub_dict["redemptions"] = [{"miles": miles, "program": "MileagePlus"}]
                            final_sub_dict["payments"] = [{"currency": currency, "taxes": taxandfees, "fees": None}]
                            final_sub_dict["site_key"] = request_data['site_key']
                            #sample_dict["site_key"] = 'UA'
                            final_sub_dict["award_type"] = cabin
                            final_dict.append(final_sub_dict)

    return final_dict, errorMsg

