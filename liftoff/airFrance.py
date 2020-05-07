from time import sleep, strptime
from scrapy.selector import Selector
import copy
from datetime import datetime, timedelta
import json
import requests
import re
import calendar
from pytz import country_timezones, timezone
import pytz
import random
from configparser import ConfigParser
def airFrance(request_data):
    cfg_obj = ConfigParser()
    cfg_obj.read('credentials.cfg')
    listofusers = eval(cfg_obj.get('AF', 'Accounts'))
    random_user = random.choice(listofusers)
    final_dict = []
    cabin_classes = []
    errorMsg = ''

    request_body = {
        "arrivals": ''.join(request_data.get('arrivals','')),
        "departures": ''.join(request_data.get('departures','')),
        "passengers":request_data.get('arrival_date', {}).get('when', ''),
        "username":random_user.split('<>')[0],
        "password":random_user.split('<>')[1]
    }
    departureDateTime = request_data.get('departure_date', {}).get('when', '')
    arrivalDateTime = request_data.get('arrival_date', {}).get('when', '')
    departureDate = datetime.strptime(departureDateTime, "%Y-%m-%d").strftime('%d')
    departureMonthYear = datetime.strptime(departureDateTime, "%Y-%m-%d").strftime('%Y%m')
    if arrivalDateTime:
        arrivalDate = datetime.strptime(departureDateTime, "%Y-%m-%d").strftime('%d')
        arrivalMonthYear = datetime.strptime(departureDateTime, "%Y-%m-%d").strftime('%Y%m')
    else:
        arrivalDate = departureDate
        arrivalMonthYear = departureMonthYear
    request_body["arrivalDate"] = arrivalDate
    request_body["arrivalMonthYear"] = arrivalMonthYear
    request_body["departureDate"] = departureDate
    request_body["departureMonthYear"] = departureMonthYear
    try:
        #change the IP according to Node js server
        response = requests.post('http://127.0.0.1:5000/airfrance', json=request_body)
    except:
        errorMsg = "Error occured while search the flight"
        return final_dict,errorMsg
    res = Selector(response)
    errorNode = ''.join(res.xpath('//div[contains(@class,"search__errors")]//text()').extract()).strip()
    if errorNode:
        return final_dict,errorNode
    num_stops = request_data.get('max_stops')
    cabin_mapping = {"Economy":"Economy","Premium Economy":"Premium Economy","Business":"Business","LA Premiere":"First Class"}
    request_cabins = request_data.get('cabins', [])
    cabin_hierarchy = []
    for cabin in request_cabins:
        if cabin.lower() == "first_class":
            cabin_classes.append('LA Premiere')
            cabin_hierarchy = cabin_hierarchy + ["First Class","Business","Premium Economy","Economy"]
        elif cabin.lower() == "business":
            cabin_classes.append('Business')
            cabin_hierarchy = cabin_hierarchy + ["Business", "Premium Economy", "Economy"]
        elif cabin.lower() == "premium_economy":
            cabin_classes.append("Premium Economy")
            cabin_hierarchy = cabin_hierarchy + ["Premium Economy", "Economy"]
        elif cabin.lower() == "economy":
            cabin_classes.append("Economy")
            cabin_hierarchy = cabin_hierarchy + ["Economy"]
    cabin_data_fetch = ['W','C','Y']
    cabin_classes = list(set(cabin_classes))
    cabin_hierarchy = list(set(cabin_hierarchy))

    miles_details = res.xpath('//tr[contains(@data-price-sort,"main")]')
    flight_Details = res.xpath('//tr[contains(@data-price-sort,"details")]')
    cabinDetailsJSON = ''.join(res.xpath('//script[8]//text()').extract()).split("JSON.parse(\'")[1].split("\')")[0]
    cabinDetails = json.loads(cabinDetailsJSON)

    file = open("airport_codes.txt","r")
    if file.mode == "r":
        contents = file.read()
    airport_code = json.loads(contents)
    list_getting_airportcode = {}

    for (miles_element,flight_element) in zip(miles_details,flight_Details):
        sample_dict = {}
        sample_dict["connections"] = []
        filightData = flight_element.xpath('td/div/div')
        layourTimeDict = []
        for flight in filightData:
            sub_dict = {}
            flight_number = ''.join(flight.xpath('div[@class="flight"]//text()').extract()).strip()
            if flight_number:
                sub_dict["distance"] = None
                sub_dict["departure"] = {
                    "when":''.join(flight.xpath('div[2]/div/div[1]/div[1]//text()').extract()).strip(),
                    "airport":''.join(flight.xpath('div[2]/div/div[1]/div[2]//text()').extract()).strip()
                }
                sub_dict["arrival"] = {
                    "when":''.join(flight.xpath('div[2]/div/div[2]/div[1]//text()').extract()).strip(),
                    "airport":''.join(flight.xpath('div[2]/div/div[2]/div[2]//text()').extract()).strip()
                }
                sub_dict["airline"] = flight_number[0:2]
                aircraft = ''.join(flight.xpath('div[4]/span[2]//text()').extract()).split(' ')
                if len(aircraft) == 2:
                    model = aircraft[1]
                    manufacturer = aircraft[0]
                else:
                    model = ''
                    manufacturer= ''.join(flight.xpath('div[4]/span[2]//text()').extract()).strip()
                sub_dict["aircraft"] = {
                    "model":model,
                    "manufacturer":manufacturer
                }
                sub_dict["cabin"]=''.join(flight.xpath('div[5]/span[2]//text()').extract()).replace('N/A','').strip()
                sub_dict["flight"]=[flight_number]
                sub_dict["times"]={"flight":0.0,"layover":None}
                sub_dict["redemptions"]=None
                sub_dict["payments"]=None
                sub_dict["tickets"]=None
                sub_dict["fare_class"]=None
                sample_dict["connections"].append(sub_dict)
            else:
                layourTime = ''.join(flight.xpath('div[contains(text(),"Connection")]//text()').extract()).split(':')[1].strip()
                layourTimeDict.append(layourTime.replace('h',":"))
        sample_dict["distance"] = None
        sample_dict["num_stops"] = len(sample_dict["connections"])-1
        if sample_dict["num_stops"] <= num_stops:
            # sample_dict["times"] = {
            #     "flight":''.join(miles_element.xpath('th/div/div/strong//text()').extract()).replace('h',':'),
            #     'layover':0.0
            # }
            tds = miles_element.xpath('td//button')
            for td in tds:
                onclick_data = ''.join(td.xpath('./@onclick').extract()).replace("'","")
                select_data = ''.join(re.findall('\((.*?)\)', onclick_data)).split(',')
                if select_data[2].strip() in cabin_data_fetch:
                    cabin_dict = cabinDetails[select_data[1].strip()][select_data[2].strip()]
                    cabin_valid = cabin_dict.get('cabinClassList', '')
                    totalFlightTime = 0
                    if cabin_valid:
                        final_sub_dict = copy.deepcopy(sample_dict)
                        for con in final_sub_dict["connections"]:
                            try:
                                airport_departure_name = con['departure']["airport"].split(',')[1].strip()
                                airport_departure_city = con['departure']["airport"].split(',')[0].strip()
                            except:
                                airport_departure_name = con['departure']["airport"]
                                airport_departure_city = con['departure']["airport"]
                            available = False
                            for key,value in airport_code.items():
                                if airport_departure_city.lower() in value["city"].lower():
                                    if airport_departure_name.lower() in value["name"].lower():
                                        available = True
                                        con['departure']["airport"] = key
                                        con['departure']["timezone"] = value["timeZone"]
                            if not available:
                                for key,value in airport_code.items():
                                    if airport_departure_name.lower() in value["name"].lower():
                                        con['departure']["airport"] = key
                                        con['departure']["timezone"] = value["timeZone"]
                        for con in final_sub_dict["connections"]:
                            try:
                                airport_arrival_name = con['arrival']["airport"].split(',')[1].strip()
                                airport_arrival_city = con['arrival']["airport"].split(',')[0].strip()
                            except:
                                airport_arrival_name = con['arrival']["airport"]
                                airport_arrival_city = con['arrival']["airport"]
                            available = False
                            for key,value in airport_code.items():
                                if airport_arrival_city.lower() in value["city"].lower():
                                    if airport_arrival_name.lower() in value["name"].lower():
                                        available = True
                                        con['arrival']["airport"] = key
                                        con['arrival']["timezone"] = value["timeZone"]
                            if not available:
                                for key,value in airport_code.items():
                                    if airport_arrival_name.lower() in value["name"].lower():
                                        con['arrival']["airport"] = key
                                        con['arrival']["timezone"] = value["timeZone"]

                        for (con, cabin_element) in zip(final_sub_dict["connections"], cabin_valid):
                            con["cabin"] = cabin_element
                            try:
                                recordDeparture = con['departure']["when"].replace('\xa0', '').split('+')
                                recordDepartureTime = recordDeparture[0]
                                recordDepartureDate = (datetime.strptime(departureDateTime, "%Y-%m-%d") + timedelta(days=int(recordDeparture[1]))).strftime('%Y-%m-%d')
                            except:
                                recordDepartureTime = con['departure']["when"]
                                recordDepartureDate = departureDateTime
                            recorddepartureDateTime = recordDepartureDate + ' ' + recordDepartureTime
                            con['departure']["when"] = datetime.strptime(recorddepartureDateTime, "%Y-%m-%d %I:%M %p").strftime('%Y-%m-%dT%H:%M')
                            try:
                                recordarrival = con['arrival']["when"].replace('\xa0', '').split('+')
                                recordarrivalTime = recordarrival[0]
                                recordarrivalDate = (datetime.strptime(departureDateTime, "%Y-%m-%d") + timedelta(days=int(recordarrival[1]))).strftime('%Y-%m-%d')
                            except:
                                recordarrivalTime = con['arrival']["when"]
                                recordarrivalDate = departureDateTime
                            recordarrivalDateTime = recordarrivalDate + ' ' + recordarrivalTime
                            con['arrival']["when"] = datetime.strptime(recordarrivalDateTime,"%Y-%m-%d %I:%M %p").strftime('%Y-%m-%dT%H:%M')
                            # departure_place = '_'.join(con['departure']["airport"].split(',')[0].split(' '))
                            # arrival_place = '_'.join(con['arrival']["airport"].split(',')[0].split(' '))
                            # for tz in find_city(departure_place):
                            #     departure_timezone = tz
                            # for tz1 in find_city(arrival_place):
                            #     arrival_timezone = tz1
                            departure_timezone = pytz.timezone(con["departure"]["timezone"])
                            arrival_timezone = pytz.timezone(con["arrival"]["timezone"])
                            timezone_departure = datetime.strptime(con['departure']["when"],"%Y-%m-%dT%H:%M")
                            con['departure']["when"] = departure_timezone.localize(timezone_departure).strftime('%Y-%m-%dT%H:%M:%S %Z%z')
                            timezone_departure_datetime = departure_timezone.localize(timezone_departure).astimezone(arrival_timezone)
                            timezone_arrival = datetime.strptime(con['arrival']["when"],"%Y-%m-%dT%H:%M")
                            con['arrival']["when"] = arrival_timezone.localize(timezone_arrival).strftime('%Y-%m-%dT%H:%M:%S %Z%z')
                            timezone_arrival_datetime = arrival_timezone.localize(timezone_arrival)
                            flightTimeMinites = (timezone_arrival_datetime - timezone_departure_datetime).seconds // 60
                            totalFlightTime = totalFlightTime+flightTimeMinites
                            con["times"]["flight"] = str(flightTimeMinites // 60).zfill(2) + ':' + str(flightTimeMinites % 60).zfill(2)
                            del con['arrival']["timezone"]
                            del con['departure']["timezone"]
                        final_sub_dict["redemptions"] = [{
                            "miles": cabin_dict["cost"],
                            "program": "Flying Blue"
                        }]
                        final_sub_dict["payments"] = [{
                            "currency": cabin_dict["currency"],
                            "taxes": cabin_dict["taxes"],
                            "fees": cabin_dict["taxes"]
                        }]
                        final_sub_dict["site_key"] = request_data.get('site_key','')
                        awardType = ''
                        for con_element in final_sub_dict["connections"]:
                            if con_element["cabin"] == None:
                                if select_data[2].strip() == "W":
                                    con_element["cabin"] = "Premium Economy"
                                elif select_data[2].strip() == "C":
                                    con_element["cabin"] = "Business"
                                else:
                                    con_element["cabin"] = "Economy"
                            else:
                                result_cabin = any(ele.lower() in con_element["cabin"].lower() for ele in cabin_classes)
                                try:
                                    result_cabin_name = ''.join([ele for ele in cabin_classes if (ele.lower() in con_element["cabin"].lower())][0])
                                except:
                                    result_cabin_name = ''
                                if result_cabin:
                                    con_element["cabin"] = cabin_mapping[result_cabin_name]
                            awardType = awardType+con_element["cabin"]+','
                        totalLayoverTime = 0
                        for (conn, layover) in zip(final_sub_dict["connections"][:-1], layourTimeDict):
                            conn["times"]["layover"] = layover
                            totalLayoverTime = totalLayoverTime + int(layover.split(':')[0])*60+int(layover.split(':')[1])
                        final_sub_dict["times"] = {"flight":None,"layover":None}
                        if totalLayoverTime != 0:
                            final_sub_dict["times"]["layover"] = str(totalLayoverTime // 60).zfill(2) + ':' + str(totalLayoverTime % 60).zfill(2)
                        else:
                            final_sub_dict["times"]["layover"] = None
                        final_sub_dict["times"]["flight"] = str(totalFlightTime // 60).zfill(2) + ':' + str(totalFlightTime % 60).zfill(2)
                        final_sub_dict["award_type"] = awardType[:-1]
                        cabinValid = False
                        hierarchy_valid = True
                        for ele_con in final_sub_dict["connections"]:
                            result = any(ele.lower() in ele_con["cabin"].lower() for ele in cabin_classes)
                            if result:
                                cabinValid = True
                            cabin_hierarchy_valid = any(ele.lower() in ele_con["cabin"].lower() for ele in cabin_hierarchy)
                            if not cabin_hierarchy_valid:
                                hierarchy_valid = False
                        if cabinValid and hierarchy_valid:
                            final_dict.append(final_sub_dict)
    return final_dict,errorMsg

def find_city(query):
    for country, cities in country_timezones.items():
        for city in cities:
            if query in city:
                yield timezone(city)

