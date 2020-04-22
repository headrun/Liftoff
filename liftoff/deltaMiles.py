import requests
import json
from pprint import pprint
import re
import copy
import json
from datetime import datetime
from selenium import webdriver
from pyvirtualdisplay import Display
from settings import proxies

def DeltaSkyMiles(request_data):
    display = Display(visible=0, size=(1400,1000))
    display.start()
    driver = webdriver.Firefox()
    driver.get('https://www.delta.com')
    _abck = ''.join([item.get('value') for item in driver.get_cookies() if item.get('name') == '_abck'])
    display.stop()
    driver.quit()
     
    cabin_classes = []
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

    cabinMapping = {'Economy':'Economy',
                    'Main Cabin':'Economy',
                    'Premium':'Premium Economy',
                    'Comfort+':'Premium Economy',
                    'First':'First Class', 
                    'Delta One':'First Class'}

    departureDate = request_data.get('departure_date', {}).get('when', '')
    arrivalDate = request_data.get('arrival_date', {}).get('when', '')
    tripStatus = 'ONE_WAY'
    if arrivalDate:
        tripStatus = 'ROUND_TRIP'
    else:
        arrivalDate = None

    request_cabins = request_data.get('cabins', [])
    for cabin in request_cabins:
        if cabin.lower() == "first_class":
            cabin_classes.append("First")
            cabin_classes.append("Delta One")
        elif cabin.lower() == "premium_economy":
            cabin_classes.append("Premium")
            cabin_classes.append("Comfort+")       
        elif cabin.lower() == "economy":
            cabin_classes.append("Economy")
            cabin_classes.append("Main Cabin")
    cabin_classes = list(set(cabin_classes))

    maxStop = request_data.get('max_stops')

    data = {"bestFare":"BE",
            "action":"findFlights",
            "destinationAirportRadius":{"unit":"MI","measure":100},
            "deltaOnlySearch":False,
            "originAirportRadius":{"unit":"MI","measure":100},
            "passengers":[{"type":"ADT","count":request_data.get('passengers', 0)}],    
            "searchType":"search",
            "segments":[{"origin":''.join(request_data.get('departures', '')),"destination":''.join(request_data.get('arrivals', '')),"departureDate":departureDate,"returnDate":arrivalDate}],
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
            "cacheKey":"b80b4b85-198c-4bfb-9c34-7da421b302d5",
            "actionType":"",
            "initialSearchBy":{"fareFamily":"BE","meetingEventCode":"","refundable":False,"flexAirport":False,"flexDate":True,"flexDaysWeeks":"FLEX_DAYS"},
            "sortableOptionId":"priceAward",
            "requestPageNum":"1"}

    response = requests.post('https://www.delta.com/shop/ow/search', headers=headers, cookies=cookies, data=json.dumps(data),proxies=proxies)
    data = json.loads(response.text)
    final_dict = []
    error_msg = data.get('shoppingError',{}).get('error',{}).get('message',{}).get('message','')
    if error_msg:
        print(error_msg)
        return final_dict,error_msg

    itinerary = data.get('itinerary',[])
    for fare in itinerary:
        fares = fare.get('fare','')
        for flg_det in fares:
            solutionId = flg_det.get('solutionId','')
        
    data = {"bestFare":"BE","action":"findFlights",
            "destinationAirportRadius":{"unit":"MI","measure":100},
            "deltaOnlySearch":False,
            "originAirportRadius":{"unit":"MI","measure":100},
            "passengers":[{"type":"ADT","count":request_data.get('passengers', 0)}],
            "searchType":"selectTripSearch",
            "segments":[{"returnDate":arrivalDate,"departureDate":departureDate,"destination":''.join(request_data.get('arrivals', '')),"origin":''.join(request_data.get('departures', ''))}],
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
            "cacheKey":"66fbe8ae-2a8c-4b2a-95ec-89af7a73954c",
            "requestPageNum":"1",
            "sortableOptionId":"priceAward",
            "selectedSolutions":[{"sliceIndex":1}],
            "actionType":"",
            "initialSearchBy":{"fareFamily":"BE","meetingEventCode":"","refundable":False,"flexAirport":False,"flexDate":True,"flexDaysWeeks":"FLEX_DAYS"},
            "currentSolution":{"solutionId":solutionId,"solutionIndex":0,"sliceIndex":1}}    
    res = requests.post('https://www.delta.com/shop/ow/search', headers=headers, cookies=cookies, data=json.dumps(data))
    data1 = json.loads(res.text)
    taxes = data1.get('selectedItinerary',[])
    for tax in taxes:
        fares1 = tax.get('fare','')
        for det in fares1:
            fees = det.get('tax',{})
            for fee in fees:
                tax_fee = fee.get('cost',{}).get('currency',{}).get('formattedAmount','')
    final_dict = []
    data = json.loads(response.text)
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
                        airlineDetails["airlines"] = "DL"
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
                        sample_dict['times'] = {'flight': flighttimes, 'layover': ltime}
                
                    totalAirTime = str(segment.get('totalAirTime',{}).get('hour','')) + ':' + str(segment.get('totalAirTime',{}).get('minute',''))
                    layoverTime = str(segment.get('layover',{}).get('duration',{}).get('hour','')) + ':'+ str(segment.get('layover',{}).get('duration',{}).get('minute',''))
                    if layoverTime == ':':
                        layoverTime = None
                    airlineDetails["times"] = {'flight': totalAirTime, 'layover': layoverTime}
                    #sample_dict["site_key"] = 'DL'    
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
            index = 0
            award = []
            for name in cabinname:
                cabinName = name.get('brandName','')
                if '&#' in cabinName:
                    cabinName =  ''.join(re.findall('(.*)&#',cabinName))
                final_sub_dict["connections"][index]["cabin"] = cabinName
                award.append(cabinName)
                try:
                    award_type = award[0] , award[1]
                    final_sub_dict["award_type"] = ', '.join(award_type)
                except:
                    final_sub_dict["award_type"] = award[0]
                index = index +1
            index = 0
            for cabin in details:
                #fare_class = cabin.get('displayBookingCode','')
                fare_class = cabin.get('bookingCode','')
                final_sub_dict["connections"][index]["fare_class"] = fare_class
                index = index +1
            final_sub_dict["redemptions"] = [{"miles": miles, "program":"Delta SkyMiles"}]
            final_sub_dict["payments"] = [{"currency": currency, "taxes": taxes, "fees":tax_fee}]
            if len(cabinname)!=0:
                cabin_available = False
                for element in final_sub_dict["connections"]:
                    nameOfCabin = element["cabin"]
                    result_cabin = any(ele in nameOfCabin for ele in cabin_classes)
                    result_cabin_name = ''.join([ele for ele in cabin_classes if(ele.lower() in nameOfCabin.lower())])
                    if result_cabin:
                        cabin_available = True
                        element["cabin"] = cabinMapping[result_cabin_name]
                if cabin_available:
                    final_dict.append(final_sub_dict)

    return final_dict , error_msg
