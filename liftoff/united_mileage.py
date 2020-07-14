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
from scrapy.selector import Selector


def UnitedMileagePlus(request_data):
    final_dict = []
    # processing the input data
    arrivalAirport = ''.join(request_data.get('arrivals', ''))
    departureAirport = ''.join(request_data.get('departures', ''))
    departureDate = request_data.get('departure_date', {}).get('when', '')
    arrivalDate = request_data.get('arrival_date', {}).get('when', '')
    passengers = request_data.get('passengers', 0)
    max_request_stops = request_data.get('max_stops', 0)
    departure_date = datetime.strptime(departureDate, "%Y-%m-%d").strftime('%d %b, %Y')
    departure_week = datetime.strptime(departureDate, "%Y-%m-%d").strftime('%a, %d %b, %Y')
    if arrivalDate:
        arrival_date = datetime.strptime(arrivalDate, "%Y-%m-%d").strftime('%d %b, %Y')
        arrival_week = datetime.strptime(arrivalDate, "%Y-%m-%d").strftime('%a, %d %b, %Y')
    tripStatus = 'oneWay'
    if arrivalDate:
        tripStatus = 'roundTrip'
    else:
        arrival_date = departure_date
        arrival_week = departure_week
        arrivalDate = departureDate

    # cabin mappings
    cabin_classes = []
    cabin_mapping = {"First Saver Award": "First Class", "Business Saver Award": "Business",
                     "Business Everyday Award": "Business", "Premium Economy (lowest award)": "Premium Economy",
                     "Economy (lowest award)": "Economy"}
    mixed_cabin_mapping = {"First":"First Class", "Business":"Business", "Premium":"Premium Economy", "Economy":"Economy"}
    cabins = ["First", "Business", "Premium", "Economy"]
    request_cabin_detail = []
    request_cabins = request_data.get('cabins', [])
    cabin_hierarchy = []
    for cabin in request_cabins:
        if cabin.lower() == "first_class":
            cabin_classes.append("First Saver Award")
            request_cabin_detail.append("First Class")
            cabin_hierarchy = cabin_hierarchy + ["First Class", "Business", "Premium Economy", "Economy"]
        elif cabin.lower() == "business":
            cabin_classes.append("Business Saver Award")
            cabin_classes.append("Business Everyday Award")
            request_cabin_detail.append("Business")
            cabin_hierarchy = cabin_hierarchy + ["Business", "Premium Economy", "Economy"]
        elif cabin.lower() == "premium_economy":
            cabin_classes.append("Premium Economy (lowest award)")
            request_cabin_detail.append("Premium Economy")
            cabin_hierarchy = cabin_hierarchy + ["Premium Economy", "Economy"]
        elif cabin.lower() == "economy":
            cabin_classes.append("Economy (lowest award)")
            request_cabin_detail.append("Economy")
            cabin_hierarchy = cabin_hierarchy + ["Economy"]
    cabin_classes = list(set(cabin_classes))
    cabin_hierarchy = list(set(cabin_hierarchy))

    # login using selenium
    display = Display(visible=0, size=(1400, 1000))
    display.start()
    driver = webdriver.Firefox()
    driver.get('https://www.united.com/en/us')
    # getting cookies from selenium driver
    cookies = {}
    cookies_string = ''
    cookies_data = driver.get_cookies()
    for ele in cookies_data:
        cookies[ele["name"]] = ele["value"]
        cookies_string = cookies_string + ele["name"] + '=' + ele["value"] + ";"
    display.stop()
    driver.quit()
    # python request for getting flight details
    headers = {
        'authority': 'www.united.com',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-user': '?1',
        'sec-fetch-dest': 'document',
        'referer': 'https://www.united.com/en/us',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    }
    params = (
        ('f', departureAirport),
        ('t', arrivalAirport),
        ('d', departureDate),
        ('tt', '1'),
        ('at', '1'),
        ('sc', '7'),
        ('px', '1'),
        ('taxng', '1'),
        ('newHP', 'True'),
    )
    import pdb;pdb.set_trace()
    response = requests.get('https://www.united.com/ual/en/US/flight-search/book-a-flight/results/awd', headers=headers, params=params, cookies=cookies)
    sel = Selector(response)
    request_payload_script = ''.join(sel.xpath('//script[contains(text(),"FlightSearch.currentResults.appliedSearch")]/text()').extract()).strip().replace('\r\n','').replace(';','')
    request_payload = re.findall('appliedSearch =(.*)UA.Booking.FlightSearch.currentResults.appliedSearch.SearchFilters',request_payload_script)[0].replace('\t','').strip()
    data = json.loads(request_payload)
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
    response = requests.post('https://www.united.com/ual/en/US/flight-search/book-a-flight/flightshopping/getflightresults/awd', headers=headers, cookies=cookies, data=json.dumps(data)) #proxies=proxies)
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
            flight_origin = flight.get('Origin','')
            flight_destination = flight.get('LastDestination', {}).get('Code', '')
            if (flight_origin not in departureAirport) or (flight_destination not in arrivalAirport):
                continue
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
                        final_sub_dict = copy.deepcopy(sample_dict)
                        cabin_availablity = False
                        cabin_details = fare.get("FlightDetails", [])
                        if cabin_details:
                            cabin_availablity = True
                            for (cabin_data, con) in zip(cabin_details, final_sub_dict["connections"]):
                                cabin = cabin_data.get('ClassDescription', '')
                                for ele in cabins:
                                    if ele.lower() in cabin.lower():
                                        cabin_valid_name = ele
                                        break
                                con["cabin"] = mixed_cabin_mapping[cabin_valid_name]
                                con["fare_class"] = cabin_data.get('CabinType', '')
                        else:
                            cabin = fare.get('ProductTypeDescription', '')
                            for ele in cabins:
                                if ele.lower() in cabin.lower():
                                    cabin_availablity = True
                                    cabin_valid_name = ele
                                    break
                            for con in final_sub_dict["connections"]:
                                con["cabin"] = mixed_cabin_mapping[cabin_valid_name]
                            for (con, fare_class_name) in zip(final_sub_dict["connections"], fareclass_mapping[cabin.strip()]):
                                con["fare_class"] = fare_class_name
                        if cabin_availablity:
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
                            final_sub_dict["award_type"] = cabin.strip()
                            cabinValid = False
                            hierarchy_valid = True
                            for ele_con in final_sub_dict["connections"]:
                                result = any(ele.lower() in ele_con["cabin"].lower() for ele in request_cabin_detail)
                                if result:
                                    cabinValid = True
                                cabin_hierarchy_valid = any(ele.lower() == ele_con["cabin"].lower() for ele in cabin_hierarchy)
                                if not cabin_hierarchy_valid:
                                    hierarchy_valid = False
                            if cabinValid and hierarchy_valid:
                                final_dict.append(final_sub_dict)

    if len(final_dict) == 0:
        errorMsg = "No flights found"
        return final_dict, errorMsg
    else:
        return final_dict, errorMsg