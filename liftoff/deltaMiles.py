import re
import json
import copy
from datetime import datetime
import requests
from selenium import webdriver
from pyvirtualdisplay import Display
from liftoff.settings import proxies


def DeltaSkyMiles(request_data):
    display = Display(visible=0, size=(1400, 1000))
    display.start()
    driver = webdriver.Firefox()
    driver.get('https://www.delta.com')
    cookies = {item.get('name', ''): item.get('value', '') for item in driver.get_cookies() if item}
    display.stop()
    driver.quit()

    headers = {
        'authority': 'www.delta.com',
        'pragma': 'no-cache',
        'cache-control': 'no-cache',
        'x-app-route': 'SL-RSB',
        'x-app-refresh': '',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36',
        'content-type': 'application/json; charset=UTF-8',
        'accept': 'application/json',
        'x-app-channel': 'sl-sho',
        'cachekey': 'ac8f3c85-3418-4a10-803f-fa21499d7a15',
        'origin': 'https://www.delta.com',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'referer': 'https://www.delta.com/flight-search/search-results?cacheKeySuffix=dafba8ee-fb18-4e55-a3a4-859219dc567f',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        }

    departureDate = request_data.get('departure_date', {}).get('when', '')
    arrivalDate = request_data.get('arrival_date', {}).get('when', '')
    tripStatus = 'ONE_WAY'
    if arrivalDate:
        tripStatus = 'ROUND_TRIP'
    else:
        arrivalDate = None
    cabin_hierarchy, request_cabin_detail = [], []
    mixed_cabin_mapping = {"First":"First Class", "Delta One":"First Class", "Business":"Business", "Upper Class":"Business", "Premier":"Business", "Premium":"Premium Economy", "Comfort+":"Premium Economy", "Economy":"Economy", "Main Cabin":"Economy", "Main":"Economy", "Basic":"Economy", "Classic":"Economy"}
    cabins = ["First", "Delta One", "Business", "Upper Class", "Premier", "Premium", "Comfort+", "Economy", "Main", "Main Cabin", "Classic", "Basic"]
    request_cabins = request_data.get('cabins', [])
    for cabin in request_cabins:
        if cabin.lower() == "first":
            request_cabin_detail.append("First Class")
            cabin_hierarchy = cabin_hierarchy + ["First Class", "Business", "Premium Economy", "Economy"]
        elif cabin.lower() == "business":
            request_cabin_detail.append("Business")
            cabin_hierarchy = cabin_hierarchy + ["Business", "Premium Economy", "Economy"]
        elif cabin.lower() == "premium_economy":
            request_cabin_detail.append("Premium Economy")
            cabin_hierarchy = cabin_hierarchy + ["Premium Economy", "Economy"]
        elif cabin.lower() == "economy":
            request_cabin_detail.append("Economy")
            cabin_hierarchy = cabin_hierarchy + ["Economy"]
            
    #cabin_classes = list(set(cabin_classes))
    cabin_hierarchy = list(set(cabin_hierarchy))

    maxStop = request_data.get('max_stops')
    req_page = 0
    final_dict = []
    error_msg = ''
    while req_page >= 0:
        req_page = req_page + 1
        data = {"bestFare":"BE",
                "action":"findFlights",
                "destinationAirportRadius":{"unit":"MI", "measure":100},
                "deltaOnlySearch":False,
                "originAirportRadius":{"unit":"MI", "measure":100},
                "passengers":[{"type":"ADT", "count":request_data.get('passengers', 0)}],    
                "searchType":"search",
                "segments":[{"origin":''.join(request_data.get('departures', '')), "destination":''.join(request_data.get('arrivals', '')), "departureDate":departureDate, "returnDate":arrivalDate}],
                "shopType":"MILES",
                "tripType":tripStatus,
                "priceType":"Award",
                "priceSchedule":"AWARD",
                "awardTravel":True,
                "refundableFlightsOnly":False,
                "nonstopFlightsOnly":False,
                "datesFlexible":True,
                "flexCalendar":False,
                "flexAirport":False,
                "upgradeRequest":False,
                "corporateSMTravelType":"Personal",
                "pageName":"FLIGHT_SEARCH",
                "cacheKey":"dafba8ee-fb18-4e55-a3a4-859219dc567f",
                "actionType":"",
                "initialSearchBy":{"fareFamily":"BE", "meetingEventCode":"", "refundable":False, "flexAirport":False, "flexDate":True, "flexDaysWeeks":"FLEX_DAYS"},
                "sortableOptionId":"priceAward",
                #"requestPageNum":"2"}
                "requestPageNum":str(req_page)}
        if req_page > 1:
            data.update({"filter":filters, "searchType":"resummarizePaging", "selectedSolutions":[]})
            response = requests.post('https://www.delta.com/shop/ow/search', headers=headers, cookies=cookies, data=json.dumps(data), proxies=proxies)
        else:
            response = requests.post('https://www.delta.com/shop/ow/search', headers=headers, cookies=cookies, data=json.dumps(data), proxies=proxies)
        if response.status_code == 400:
            try:
                data = json.loads(response.text)
                error_msg = data.get('shoppingError', {}).get('error', {}).get('message', {}).get('message', '')
            except: data, error_msg = '', ''
            if error_msg:
                error_msg = 'invalid airlines'
                return final_dict, error_msg
            else:
                break
            
        data = json.loads(response.text)
        itinerary = data.get('itinerary', [])
        error_msg = data.get('shoppingError', {}).get('error', {}).get('message', {}).get('message', '')
        if error_msg:
            error_msg = 'No flights found'
            print(error_msg)
            return final_dict, error_msg
        filters = data.get('filter', {})
        if not filters:
            filters = data.get('searchCriteria', {}).get('request', {}).get('filter', '')
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
                            airlineDetails["departure"] = {"when": departureDateTime, "airport": departureAirport}
                            airlineDetails["arrival"] = {"when": arrivalDateTime, "airport": arrivalAirport}
                            airlineDetails["distance"] = None
                            airlineDetails["flight"] = [flightNumber]
                            airlineDetails["airline"] = ''.join(re.findall('\D+', flightNumber))
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
                            if minite >= 60:
                                hour = 1
                                minite1 = minite - 60
                                minit = str(sum(tot_time)+hour)+":"+str(minite1)
                            else:
                                minit = str(sum(tot_time))+":"+str(sum(time))
                            try: flight_time = datetime.strptime(minit, '%H:%M').strftime('%H:%M')
                            except: flight_time = minit
                            airlineDetails["redemptions"] = None
                            airlineDetails["payments"] = None
                            airlineDetails["tickets"] = None
                        
                            totalAirTime = str(segment.get('totalAirTime', {}).get('hour', '')) + ':' + str(segment.get('totalAirTime', {}).get('minute', ''))
                            try:
                                totalAirTimes = datetime.strptime(totalAirTime, '%H:%M').strftime('%H:%M')
                            except:
                                totalAirTimes = None
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
                            lay_minutes = sum(lay_time)
                            if lay_minutes >= 60:
                                hour = 1
                                lay_minite1 = lay_minutes - 60
                                lay_minite = str(sum(lay_hours)+hour)+":"+str(lay_minite1)
                            else:
                                lay_minite = str(sum(lay_hours))+":"+str(sum(lay_time))
                            try: layover_time = datetime.strptime(lay_minite, '%H:%M').strftime('%H:%M')
                            except: layover_time = lay_minite                             
                            if layover_time == '00:00':
                                layover_time = None
                            sample_dict['times'] = {'flight':flight_time, 'layover':layover_time}
                            #sample_dict["site_key"] = 'DL'    
                            sample_dict["site_key"] = request_data['site_key']

            if not Flag:
                continue
            fares = fare.get('fare', '')            
            fare_classes = {}
            for flg_det in fares:
                programs = flg_det.get('miscFlightInfos', {})
                for program in programs:
                    program = program.get('airlineFltInfo', {}).get('airline', {}).get('airlineName', '')
                final_sub_dict = copy.deepcopy(sample_dict)
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
                    #fare_class = cabin.get('displayBookingCode','')
                    fare_class = cabin.get('bookingCode', '')
                    final_sub_dict["connections"][index]["fare_class"] = fare_class
                    index = index +1
                final_sub_dict["redemptions"] = [{"miles": miles, "program":"Delta SkyMiles"}]
                final_sub_dict["payments"] = [{"currency": currency, "taxes": taxes, "fees":None}]
                if len(cabinname) != 0:
                    cabin_available = False
                    for element in final_sub_dict["connections"]:
                        nameOfCabin = element["cabin"]
                        for ele in cabins:
                            if ele.lower() in nameOfCabin.lower():
                                cabin_available = True
                                cabin_valid_name = ele
                                break
                        element["cabin"] = mixed_cabin_mapping[cabin_valid_name]
                    if cabin_available:
                        cabinValid = False
                        hierarchy_valid = True
                        for element in final_sub_dict["connections"]:
                            result = any(ele.lower() == element["cabin"].lower() for ele in request_cabin_detail)    
                            if result:
                                cabinValid = True
                            cabin_hierarchy_valid = any(ele.lower() == element["cabin"].lower() for ele in cabin_hierarchy)
                            if not cabin_hierarchy_valid:
                                hierarchy_valid = False
                        if cabinValid and hierarchy_valid:
                            final_dict.append(final_sub_dict)
    return final_dict, error_msg
