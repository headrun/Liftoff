import re
import json
import copy
import requests
from datetime import datetime
from selenium import webdriver
from pyvirtualdisplay import Display
from liftoff.settings import proxies

def vigranAtlantic(request_data):
    data = request_data
    display = Display(visible=0, size=(1400, 1000))
    display.start()
    driver = webdriver.Firefox()
    driver.get('https://www.virginatlantic.com')
    _abck = ''.join([item.get('value') for item in driver.get_cookies() if item.get('name') == '_abck'])
    display.stop()
    driver.quit()

    departureDate = data.get('departure_date', {}).get('when', '')
    arrivalDate = data.get('arrival_date', {}).get('when', '')
    tripStatus = 'ONE_WAY'
    if arrivalDate:
        tripStatus = 'ROUND_TRIP'
    else:
        arrivalDate = None    
     
    request_cabins = data.get('cabins', [])
    cabin_classes = []
    cabin_hierarchy = []
    cabinMapping = {'Economy':'Economy', 'Premium':'Premium Economy', 'Main Cabin':'Economy', 'Business Class':'Business', 'First Class':'First Class', 'Upper Class':'Business', 'Delta One':'First Class'}
    for cabin in request_cabins:
        if cabin.lower() == "first":
            cabin_classes.append("First Class")
            cabin_classes.append("Delta One")
            cabin_classes.append("Business Class")
            cabin_hierarchy = cabin_hierarchy + ["First Class", "Business", "Premium Economy", "Economy", "Main Cabin", "Upper Class", "Delta One", "Business Class"]
        if cabin.lower() == "business":
            cabin_classes.append("Upper Class")
            cabin_classes.append("Business Class")
            cabin_hierarchy = cabin_hierarchy + ["Business", "Premium Economy", "Economy", "Main Cabin", "Upper Class"]
        elif cabin.lower() == "premium_economy":
            cabin_classes.append("Premium")
            cabin_hierarchy = cabin_hierarchy + ["Premium Economy", "Economy", "Main Cabin"]
        elif cabin.lower() == "economy":
            cabin_classes.append("Economy")
            cabin_classes.append("Main Cabin")
            cabin_hierarchy = cabin_hierarchy + ["Economy", "Main Cabin"]
    cabin_classes = list(set(cabin_classes))
    cabin_hierarchy = list(set(cabin_hierarchy))

   
    maxStop = data.get('max_stops')
    cookies = {'_abck': _abck}
    headers = {
        'authority': 'www.delta.com',
        'pragma': 'no-cache',
        'cache-control': 'no-cache',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.92 Safari/537.36',
        'content-type': 'application/json; charset=UTF-8',
        'accept': 'application/json',
        'origin': 'https://www.delta.com',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'accept-language': 'en-US,en;q=0.9,fil;q=0.8,te;q=0.7',

    }

    data = {"bestFare":"VSLT",
            "action":"findFlights",
            "destinationAirportRadius":{"unit":"MI", "measure":100},
            "deltaOnlySearch":False,
            "meetingEventCode":"",
            "originAirportRadius":{"unit":"MI", "measure":100},
            "passengers":[{"type":"ADT", "count":data.get('passengers', 0)}],
            "searchType":"search",
            "segments":[{"origin":''.join(data.get('departures', '')), "destination":''.join(data.get('arrivals', '')), "departureDate":departureDate, "returnDate":arrivalDate}],
            "shopType":"MILES",
            #"tripType":"ONE_WAY",
            "tripType":tripStatus,
            "priceType":"Award",
            "priceSchedule":"PRICE",
            "awardTravel":True,
            "refundableFlightsOnly":False,
            "nonstopFlightsOnly":False,
            "datesFlexible":True,
            "flexCalendar":False,
            "flexAirport":False,
            "upgradeRequest":False,
            "pageName":"FLIGHT_SEARCH",
            "actionType":"flexDateSearch",
            "initialSearchBy":{"fareFamily":"VSLT", "meetingEventCode":"", "refundable":False, "flexAirport":False, "flexDate":True, "flexDaysWeeks":"FLEX_DAYS"},
            "vendorDetails":{},
            "sortableOptionId":"priceAward",
            "requestPageNum":"1"
            }
    response = requests.post('https://www.virginatlantic.com/shop/ow/search', headers=headers, cookies=cookies, data=json.dumps(data), proxies=proxies)
    if response.status_code == 403:
        response = requests.post('https://www.virginatlantic.com/shop/ow/search', headers=headers, cookies=cookies, data=json.dumps(data), proxies=proxies)
 
    final_dict = []
    data = json.loads(response.text)    
    error_msg = data.get('shoppingError', {}).get('error', {}).get('message', {}).get('reasonMsg', '')
    if error_msg:
        error_msg = 'No flights found'
        return final_dict, error_msg
    data = json.loads(response.text)
    itinerary = data.get('itinerary', [])
    for fare in itinerary:
        Flag = True
        fares = fare.get('fare', '')
        trips = fare.get('trip', '')
        for trip in trips:
            sample_dict = {}
            sample_dict["distance"] = None
            sample_dict["num_stops"] = trip.get('stopCount', '')
            if sample_dict["num_stops"] > maxStop:
                Flag = False
                break
            if sample_dict["num_stops"] <= maxStop:
                sample_dict["connections"] = []
                fare_classes = {}

                segments = trip.get('flightSegment', [])
                time, tot_time, lay_hours, lay_time = [], [], [], []
                for segment in segments:
                    legs = segment.get('flightLeg', [])
                    for leg in legs:
                        total_time = 0
                        lay_hour, lay_minut = 0, 0
                        hours, minuts = 0, 0
                        airlineDetails = {}
                        departureAirport = leg.get('originAirportCode', '')
                        arrivalAirport = leg.get('destAirportCode', '')
                        departureDateTime = leg.get('schedDepartLocalTs', '')
                        arrivalDateTime = leg.get('schedArrivalLocalTs', '')
                        aircraftModel = leg.get('aircraft', {}).get('fleetName', '')
                        flightNumber = leg.get('viewSeatUrl', {}).get('fltNumber', '')
                        airlineDetails["airline"] = leg.get('operatingCarrier', {}).get('code', '')
                        airlineDetails["departure"] = {"when": departureDateTime, "airport": departureAirport}
                        airlineDetails["arrival"] = {"when": arrivalDateTime, "airport": arrivalAirport}
                        airlineDetails["distance"] = None
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
                        flighttimes = str(leg.get('duration', {}).get('hour', '')) + ':' + str(leg.get('duration', {}).get('minute', ''))
                        hours = hours+leg.get('duration', {}).get('hour', '')
                        minuts = minuts+leg.get('duration', {}).get('minute', '')
                        tot_time.append(hours)
                        time.append(minuts)
                        minit = str(sum(tot_time))+":"+str(sum(time))
                        minite = sum(time)
                        if minite > 60:
                            hour = 1
                            minite1 = minite - 60
                            minit = str(sum(tot_time)+hour)+":"+str(minite1)
                        else:
                            minit = str(sum(tot_time))+":"+str(sum(time))
                        fight_time = datetime.strptime(minit, '%H:%M').strftime('%H:%M')
                        airlineDetails["redemptions"] = None
                        airlineDetails["payments"] = None
                        airlineDetails["tickets"] = None
                        totalAirTime = str(segment.get('totalAirTime', {}).get('hour', '')) + ':' + str(segment.get('totalAirTime', {}).get('minute', ''))
                        try:
                            totalAirTimes = datetime.strptime(totalAirTime, '%H:%M').strftime('%H:%M')
                        except:
                            layoverTimes = None

                        layoverTime = str(segment.get('layover', {}).get('duration', {}).get('hour', '')) + ':'+ str(segment.get('layover', {}).get('duration', {}).get('minute', ''))
                        try:
                            layoverTimes = datetime.strptime(layoverTime, '%H:%M').strftime('%H:%M')
                        except:
                            layoverTimes = None

                        airlineDetails["times"] = {'flight': totalAirTimes, 'layover': layoverTimes}
                        sample_dict["connections"].append(airlineDetails)
                        lay_hour = lay_hour+segment.get('layover', {}).get('duration', {}).get('hour', 0)
                        lay_minut = lay_minut+segment.get('layover', {}).get('duration', {}).get('minute', 0)
                        lay_hours.append(lay_hour)
                        lay_time.append(lay_minut)
                        lay_minite = str(sum(lay_hours))+":"+str(sum(lay_time))
                        lay_minute = sum(lay_time)
                        if lay_minute > 60:
                            hour = 1
                            lay_minite1 = minite - 60
                            lay_minute = str(sum(lay_hours)+hour)+":"+str(lay_minite1)
                        else:
                            lay_minite = str(sum(lay_hours))+":"+str(sum(lay_time))
                        layover_time = datetime.strptime(lay_minite,'%H:%M').strftime('%H:%M')
                        if layover_time == '00:00':
                            layover_time = None
                        sample_dict['times'] = {'flight':fight_time, 'layover': layover_time}
                        #sample_dict["site_key"] = 'VS' 
                        sample_dict["site_key"] = request_data['site_key']
                
        if not Flag:
            continue
        fares = fare.get('fare', '')            
        fare_classes = {}
        for flg_det in fares:
            programs = flg_det.get('miscFlightInfos', {})
            final_sub_dict = copy.deepcopy(sample_dict)
            for program in programs:
                program = program.get('airlineFltInfo', {}).get('airline', {}).get('airlineName', '')
            currency = flg_det.get('totalPrice', {}).get('currency', {}).get('code', '')
            taxes = flg_det.get('totalPrice', {}).get('currency', {}).get('formattedAmount', '')
            miles = flg_det.get('basePrice', {}).get('miles', {}).get('miles', '')
                
            details = flg_det.get('miscFlightInfos', '')
            cabinname = flg_det.get('brandByFlightLeg', '')
            index = 0
            award = []
            for name in cabinname:
                cabinName = name.get('brandName', '')
                if '&#' in cabinName:
                    cabinName = ''.join(re.findall('(.*)&#', cabinName))
                final_sub_dict["connections"][index]["cabin"] = cabinName
                award.append(cabinName)
                try:
                    award_type = award[0], award[1]
                    final_sub_dict["award_type"] = ','.join(award_type)
                except:
                    final_sub_dict["award_type"] = award[0]                
                index = index +1
            index = 0    
            for cabin in details:
                fare_class = cabin.get('displayBookingCode', '')
                final_sub_dict["connections"][index]["fare_class"] = fare_class
                index = index +1
            final_sub_dict["redemptions"] = [{"miles": miles, "program":"Virgin Atlantic"}]
            final_sub_dict["payments"] = [{"currency": currency, "taxes": taxes, "fees":None}]
            if len(cabinname) != 0:
                cabin_available = False
                for element in final_sub_dict["connections"]:
                    nameOfCabin = element["cabin"]
                    result_cabin = any(ele in nameOfCabin for ele in cabin_classes)
                    result_cabin_name = ''.join([ele for ele in cabin_classes if(ele.lower() in nameOfCabin.lower())])
                    if result_cabin:
                        element["cabin"] = cabinMapping[result_cabin_name]
                        cabin_available = True
                if cabin_available:
                    hierarchy_valid = True
                    for element in final_sub_dict["connections"]:
                        cabin_hierarchy_valid = any(ele.lower() in element["cabin"].lower() for ele in cabin_hierarchy)
                        if not cabin_hierarchy_valid:
                            hierarchy_valid = False
                    if hierarchy_valid:
                        final_dict.append(final_sub_dict)
    return final_dict, error_msg          



