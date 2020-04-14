import requests
import re
import json
from pprint import pprint
import re
import copy
from datetime import datetime


def vigranAtlantic(request_data):
    data = request_data

    headers = {
        'authority': 'www.virginatlantic.com',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36',
        'sec-fetch-user': '?1',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    }
    departureDate = data.get('departure_date', {}).get('when', '')
    dep_date = datetime.strptime(departureDate,"%Y-%m-%d").strftime('%m/%d/%Y')
    arrivalDate = data.get('arrival_date', {}).get('when', '')
    try:
        arr_date = datetime.strptime(arrivalDate,"%Y-%m-%d").strftime('%m/%d/%Y')    
    except:
        arr_date = ''
    tripStatus = 'ONE_WAY'
    if arrivalDate:
        tripStatus = 'ROUND_TRIP'
    else:
        arrivalDate = None
    
    params = (
        ('action', 'findFlights'),
        ('tripType', tripStatus),
        ('priceSchedule', 'PRICE'),
        ('originCity', ''.join(data.get('departures', ''))),
        ('destinationCity', ''.join(data.get('arrivals', ''))),
        ('departureDate', dep_date),
        ('departureTime', 'AT'),
        ('returnDate', arr_date),
        ('returnTime', ''),
        ('searchByCabin', 'true'),
        ('cabinFareClass', 'VSLT'),
        ('deltaOnlySearch', 'false'),
        ('deltaOnly', 'off'),
        ('Go', 'Find Flights'),
        ('meetingEventCode', ''),
        ('refundableFlightsOnly', 'false'),
        ('compareAirport', 'false'),
        ('awardTravel', 'true'),
        ('datesFlexible', 'true'),
        ('flexAirport', 'false'),
        ('passengerInfo', 'ADT:1'),
    )
    res = requests.get('https://www.virginatlantic.com/flight-search-2/search', headers=headers, params=params)
    ak_bmsc = ''.join(re.findall('ak_bmsc=(.*)',res.headers.get('Set-Cookie',''))).split(';')[0]
    ab_sk = ''.join(re.findall('_abck=(.*)',res.headers.get('Set-Cookie',''))).split(';')[0]
    tltu_id = ''.join(re.findall('TLTUID=(.*)',res.headers.get('Set-Cookie',''))).split(';')[0]
    tltu_sid = ''.join(re.findall('TLTSID=(.*)',res.headers.get('Set-Cookie',''))).split(';')[0]
    dt_cookie = ''.join(re.findall('dtCookie=(.*)',res.headers.get('Set-Cookie',''))).split(';')[0]
    bm_sz = ''.join(re.findall('bm_sz=(.*)',res.headers.get('Set-Cookie',''))).split(';')[0]

    cookies = {
        'TLTUID': tltu_id,
        'TLTSID': tltu_sid,
        'bm_sz': bm_sz,
        'ak_bmsc': ak_bmsc,
        #'_abck': 'C3B50BA645760D865B55BCB5BA35019C~0~YAAQyXbNFwozpRBxAQAAq1FCPwMho+7wheAe2bjfs92sasgv7qioa/Vm656W9W5ARfeiEn7daT/b0WzWKbOfqv4vksQzRQpRGBohGsEFL60L5HzC1B6CO3j67rFvsGgrUsLYl+SXfM0mRHF7SPfXYurXRJudQC+oeSWA7fbjYgqyWVE1beALTkTzj9T/xuuw0qqVljc/kUwqUcjMJKn/xh7GXU6kdRWG2Spr0pRIFvu2ggjvYrk8dF1zA0I8Qvu0eVkYtcRog22qFcAuufqovE/po+R8wi3KU33NGRbCEisslPgv44YZaYFu/EBl1do0D0zbYnPMUKjQN6Cyf17U~-1~-1~-1',
        'dtCookie': dt_cookie,
    }
    
    request_cabins = data.get('cabins', [])
    cabin_classes = []
    cabinMapping = {'Economy Classic':'economy','Premium':'premium_economy','Upper Class':'business','First Class':'first_class'}
    for cabin in request_cabins:
        if cabin.lower() == "first_class":
            cabin_classes.append("First Class")
        elif cabin.lower() == "business":
            cabin_classes.append("Upper Class")
        elif cabin.lower() == "premium_economy":
            cabin_classes.append("Premium")
        elif cabin.lower() == "economy":
            cabin_classes.append("Economy Classic")
    cabin_classes = list(set(cabin_classes))
    maxStop = data.get('max_stops')
    headers = {
        'authority': 'www.virginatlantic.com',
        'x-app-route': 'SL-RSB',
        'x-app-refresh': '',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36',
        'content-type': 'application/json; charset=UTF-8',
        'x-dtreferer': 'https://www.virginatlantic.com/flight-search-2/flexible-dates?cacheKeySuffix=92348bf5-1594-4388-8e13-66ae2d083a0e',
        'cachekey': '92348bf5-1594-4388-8e13-66ae2d083a0e',
        'origin': 'https://www.virginatlantic.com',
        'referer': 'https://www.virginatlantic.com/flight-search-2/search-results?cacheKeySuffix=92348bf5-1594-4388-8e13-66ae2d083a0e',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    }

    data = {"bestFare":"VSLT",
            "action":"findFlights",
            "destinationAirportRadius":{"unit":"MI","measure":100},
            "deltaOnlySearch":False,
            "meetingEventCode":"",
            "originAirportRadius":{"unit":"MI","measure":100},
            "passengers":[{"type":"ADT","count":data.get('passengers', 0)}],
            "searchType":"search",
            "segments":[{"origin":''.join(data.get('departures', '')),"destination":''.join(data.get('arrivals', '')),"departureDate":departureDate,"returnDate":arrivalDate}],
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
            "initialSearchBy":{"fareFamily":"VSLT","meetingEventCode":"","refundable":False,"flexAirport":False,"flexDate":True,"flexDaysWeeks":"FLEX_DAYS"},
            "vendorDetails":{},
            "sortableOptionId":"priceAward",
            "requestPageNum":"1"
            }
    response = requests.post('https://www.virginatlantic.com/shop/ow/search', headers=headers, cookies=cookies, data=json.dumps(data))
    if response.status_code == 403:
        response = requests.post('https://www.virginatlantic.com/shop/ow/search', headers=headers, cookies=cookies, data=json.dumps(data))
    
    final_dict = []
    data = json.loads(response.text)
    error_msg = data.get('shoppingError',{}).get('error',{}).get('message',{}).get('message','')
    if error_msg:
        print(error_msg)
        return final_dict,error_msg

    itinerary = data.get('itinerary',[])
    for fare in itinerary:
        Flag = True
        fares = fare.get('fare','')
        trips = fare.get('trip','')
        for trip in trips:
            sample_dict = {}
            sample_dict["distance"] = None
            sample_dict["num_stops"] = trip.get('stopCount','')
            if sample_dict["num_stops"] > maxStop:
                Flag = False
                break
            if sample_dict["num_stops"] <= maxStop:
                sample_dict["connections"] = []
                fare_classes = {}

                segments = trip.get('flightSegment',[])
                for segment in segments:
                    legs = segment.get('flightLeg',[])
                    for leg in legs:
                        total_time = 0
                        airlineDetails = {}
                        departureAirport = leg.get('originAirportCode','')
                        arrivalAirport = leg.get('destAirportCode','')
                        departureDateTime = leg.get('schedDepartLocalTs','')
                        arrivalDateTime = leg.get('schedArrivalLocalTs','')
                        aircraftModel = leg.get('aircraft',{}).get('fleetName','')
                        flightNumber = leg.get('viewSeatUrl',{}).get('fltNumber','')
                        airlineDetails["airlines"] = "VC"
                        airlineDetails["departures"] = {"when": departureDateTime, "airport": departureAirport}
                        airlineDetails["arrivals"] = {"when": arrivalDateTime, "airport": arrivalAirport}
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
                        flighttimes = str(leg.get('duration',{}).get('hour','')) + ':' + str(leg.get('duration',{}).get('minute',''))
                        ltime = None
                        airlineDetails["redemptions"] = None
                        airlineDetails["payments"] = None
                        airlineDetails["tickets"] = None
                        sample_dict["connections"].append(airlineDetails)
                        sample_dict["times"] = {'flight': flighttimes, 'layover': ltime}
                    totalAirTime = str(segment.get('totalAirTime',{}).get('hour','')) + ':' + str(segment.get('totalAirTime',{}).get('minute',''))
                    layoverTimes = str(segment.get('layover',{}).get('duration',{}).get('hour','')) + ':'+ str(segment.get('layover',{}).get('duration',{}).get('minute',''))
                    if layoverTimes == ':':
                        layoverTimes = None
                    airlineDetails['times'] = {'flight': totalAirTime, 'layover': layoverTimes}
                    #sample_dict["site_key"] = 'VC'    
                    sample_dict["site_key"] = request_data['site_key']
                
        if not Flag:
            continue
        fares = fare.get('fare','')            
        fare_classes = {}
        for flg_det in fares:
            programs = flg_det.get('miscFlightInfos',{})
            for program in programs:
                program = program.get('airlineFltInfo',{}).get('airline',{}).get('airlineName','')
            final_sub_dict = copy.deepcopy(sample_dict)
            currency = flg_det.get('totalPrice',{}).get('currency',{}).get('code','')
            taxes = flg_det.get('totalPrice',{}).get('currency',{}).get('formattedAmount','')
            miles = flg_det.get('basePrice',{}).get('miles',{}).get('miles','')
                
            details = flg_det.get('miscFlightInfos','')
            cabinname = flg_det.get('brandByFlightLeg','')
            for name in cabinname:
                cabinName = name.get('brandName','')
                result_cabin = any(ele in cabinName for ele in cabin_classes) 
                if result_cabin:
                    for cabin in details:
                        cabincode = cabin.get('displayBookingCode','')
                        fare_classes[cabinName] = cabin.get('displayBookingCode','') 
                        for connection in final_sub_dict["connections"]:
                            connection["fare_class"] = fare_classes[cabinName]
                            connection["cabin"] = cabinMapping[cabinName]
    
                        final_sub_dict["redemptions"] = [{"miles": miles, "program":program}]
                        final_sub_dict["payments"] = [{"currency": currency, "taxes": taxes, "fees":None}]
                        final_sub_dict["award_type"] = program
                    final_dict.append(final_sub_dict)
    
    return final_dict, error_msg
