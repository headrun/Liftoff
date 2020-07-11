from scrapy.selector import Selector
import copy
from datetime import datetime
import json
import requests
import pytz

def britishAirline(request_data):
    departure_date = request_data.get('departure_date').get('when')
    try:
        departure_date = datetime.strptime(departure_date, "%Y-%m-%d").strftime("%m/%d/%y")
    except:
        departure_date = ''
    cabins = [element.lower() for element in request_data.get('cabins', [])]
    request = {
        "username":"mattrobertsm@gmail.com",
        "password":"Roberts@11",
        "departures":''.join(request_data.get('departures', '')),
        "arrivals":''.join(request_data.get('arrivals', '')),
        "departureDate":departure_date,
        "cabins":cabins
        }
    max_stops = request_data.get('max_stops', 0)
    final_dict, error_msg = [], ''
    response = requests.post('http://127.0.0.1:5000/britishAirline', json=request)
    if response.status_code != 200:
        error_msg = "Error occured while search the flight"
        return final_dict, error_msg

    file = open("airport_codes.txt", "r")
    if file.mode == "r":
        contents = file.read()
    airport_code = json.loads(contents)

    res = json.loads(response.text)
    sel = Selector(text=res["sourcePage"])
    single_connections = sel.xpath('//div[@class="direct-flight-details"]')
    result_cabin_keys = {"Economy":"economy", "Premium Economy":"premium_economy", "Business Class":"business", "First Class":"first_class"}
    mapping_cabins = {"Economy":"Economy", "Premium Economy":"Premium Economy", "Business Class":"Business", "First Class":"First"}
    for flight in single_connections:
        sample_dict = {}
        flight_detail_url = ''.join(flight.xpath('div/div[@class="travel-time-detail"]/div[contains(@class,"operator")]/div/p[contains(@class,"career-and-flight")]/a/@href').extract()).strip()  
        flight_details = res.get('flight_model_data', {}).get(flight_detail_url, {})
        sample_dict["departure"] = {
            "when":datetime.strptime(flight_details.get('departure').split('\t')[-1], "%a %d %B %Y, %H:%M").strftime("%Y-%m-%dT%H:%M:%S"),
            "airport": ''.join(flight.xpath('div/div[@class="travel-time-detail"]/div[contains(@class,"departure")]/div[contains(@class,"airport-box")]/p/a/text()').extract()).strip()
        }
        sample_dict["arrival"] = {
            "when":datetime.strptime(flight_details.get('arrival').split('\t')[-1], "%a %d %B %Y, %H:%M").strftime("%Y-%m-%dT%H:%M:%S"),
            "airport":''.join(flight.xpath('div/div[@class="travel-time-detail"]/div[contains(@class,"arrival")]/div[contains(@class,"airport-box")]/p/a/text()').extract()).strip()
        }
        sample_dict["airline"] = flight_details.get('flight', '')[:2]
        sample_dict["flight"] = [flight_details.get('flight', '').replace(' ', '')]
        sample_dict["distance"] = None
        aircraft_list = flight_details.get('aircraft').split()
        if len(aircraft_list) > 1:
            aircraft, manufacturer = aircraft_list[:2]
        else:
            aircraft, manufacturer = aircraft_list[0], ''
        sample_dict["aircraft"] = {"aircraft":aircraft, "manufacturer":manufacturer}
        sample_dict["times"] = {
            "flight": ':'.join(flight_details.get('duration').replace('hrs', '').replace('mins', '').split()).strip(),
            "layover": '00:00'
        }
        sample_dict["redemptions"], sample_dict["payments"], sample_dict["tickets"], sample_dict["fare_class"] = None, None, None, None
        cabins = flight.xpath('div/div[@class="travel-class-detail"]/div/div[contains(@class,"number-of-seats-available")]/div/span/text()').extract()
        sub_dict = {
            "connections":[sample_dict],
            "distance":None,
            "num_stops":0,
            "site_key":request_data.get('site_key')
        }
        award_list = flight.xpath('div/div[@class="travel-class-detail"]/div/div[contains(@class,"number-of-seats-available")]/div/div/div/div/div/input[@class="cabinSelector"]/@aria-label').extract()
        award_types = [award.split('cabin')[1].strip() for award in award_list]
        for (cabin, award) in zip(cabins, award_types):
            final_sub_dict = copy.deepcopy(sub_dict)
            for con in final_sub_dict["connections"]:
                con["cabin"] = mapping_cabins[cabin]
            res_key = result_cabin_keys.get(cabin, '')
            result_array = res.get(res_key, [])
            if result_array:
                avios, tax = result_array[0].split('+')
                miles = float(avios.split()[0])
                tax_value = float(tax.split()[0].replace(',', ''))
                res[res_key].pop(0)
                final_sub_dict["redemptions"] = [{"miles": miles, "program": "British Airways Executive Club"}]
                final_sub_dict["payments"] = [{"currency": "USD", "taxes": tax_value, "fees":None}]
                final_sub_dict["times"] = final_sub_dict["connections"][0]["times"]
                final_sub_dict["award_types"] = award
                final_dict.append(final_sub_dict)
    if max_stops > 0:
        multi_connection = sel.xpath('//div[@class="conn-flight-details"]')
        for flight in multi_connection:
            sub_connections = flight.xpath('div/div[@class="travel-time-detail"]')
            connections = []
            for sub_flight in sub_connections:
                sample_dict = {}
                flight_detail_url = ''.join(sub_flight.xpath('div[contains(@class,"operator")]/div[contains(@class,"flight-detail")]/p[@class="career-and-flight"]/a/@href').extract()).strip()
                flight_details = res.get('flight_model_data', {}).get(flight_detail_url, {})
                sample_dict["departure"] = {
                    "when":datetime.strptime(flight_details.get('departure').split('\t')[-1], "%a %d %B %Y, %H:%M").strftime("%Y-%m-%dT%H:%M:%S"),
                    "airport": ''.join(sub_flight.xpath('div[contains(@class,"departure")]/div[@class="airport-box"]/p/a/text()').extract()).strip()
                }
                sample_dict["arrival"] = {
                    "when":datetime.strptime(flight_details.get('arrival').split('\t')[-1], "%a %d %B %Y, %H:%M").strftime("%Y-%m-%dT%H:%M:%S"),
                    "airport":''.join(sub_flight.xpath('div[contains(@class,"arrival")]/div[@class="airport-box"]/p/a/text()').extract()).strip()
                }
                sample_dict["airline"] = flight_details.get('flight', '')[:2]
                sample_dict["flight"] = [flight_details.get('flight', '').replace(' ', '')]
                sample_dict["distance"] = None
                aircraft_list = flight_details.get('aircraft').split()
                if len(aircraft_list) > 1:
                    aircraft, manufacturer = aircraft_list[:2]
                else:
                    try:
                        aircraft, manufacturer = aircraft_list[0], ''
                    except:
                        aircraft, manufacturer = '', ''

                sample_dict["aircraft"] = {"aircraft":aircraft, "manufacturer":manufacturer}
                sample_dict["times"] = {
                    "flight": ':'.join(flight_details.get('duration').replace('hrs', '').replace('mins', '').replace('hr', '').split()).strip(),
                    "layover": '00:00'
                }
                sample_dict["redemptions"], sample_dict["payments"], sample_dict["tickets"], sample_dict["fare_class"] = None, None, None, None
                connections.append(sample_dict)
            sub_dict = {
                "connections":connections,
                "num_stops":len(sub_connections),
                "distance":None,
                "site_key":request_data.get('site_key', '')
            }
            index = 0
            total_layover_time, total_flight_time = 0, 0
            for index, item in enumerate(sub_dict["connections"]):
                next = index + 1
                hrs, mins = item["times"]["flight"].split(':')
                total_flight_time = total_flight_time + ((int(hrs)*60) + int(mins))
                if next < len(sub_dict["connections"]):
                    layover_time_minutes = (datetime.strptime(sub_dict["connections"][next]["departure"]["when"], "%Y-%m-%dT%H:%M:%S") - datetime.strptime(item["arrival"]["when"], "%Y-%m-%dT%H:%M:%S")).seconds // 60
                    total_layover_time = total_layover_time + layover_time_minutes
                    item["times"]["layover"] = str(layover_time_minutes // 60).zfill(2) + ':' + str(layover_time_minutes % 60).zfill(2)


            cabins = flight.xpath('div/div[@class="travel-class-detail"]/div/div/div[contains(@class,"number-of-seats-available")]/div/span/text()').extract()
            award_list = flight.xpath('div/div[@class="travel-class-detail"]/div/div/div[contains(@class,"number-of-seats-available")]/div/div/div/div/div/input[@class="cabinSelector"]/@aria-label').extract()
            award_types = [award.split('cabin')[1].strip() for award in award_list]
            for (cabin, award) in zip(cabins, award_types):
                final_sub_dict = copy.deepcopy(sub_dict)
                for con in final_sub_dict["connections"]:
                    con["cabin"] = mapping_cabins[cabin]
                res_key = result_cabin_keys.get(cabin, '')
                result_array = res.get(res_key, [])
                if result_array:
                    avios, tax = result_array[0].split('+')
                    miles = float(avios.split()[0])
                    tax_value = float(tax.split()[0].replace(',', ''))
                    res[res_key].pop(0)
                    final_sub_dict["redemptions"] = [{"miles": miles, "program": "British Airways Executive Club"}]
                    final_sub_dict["payments"] = [{"currency": "USD", "taxes": tax_value, "fees":None}]
                    final_sub_dict["times"] = {
                        "flight": str(total_flight_time // 60).zfill(2) + ':' + str(total_flight_time % 60).zfill(2), 
                        "layover":str(total_layover_time // 60).zfill(2) + ':' + str(total_layover_time % 60).zfill(2)
                    }
                    final_sub_dict["award_type"] = award
                    final_dict.append(final_sub_dict)
    for flight_con in final_dict:
        connections = flight_con["connections"]
        for con in connections:
            departure_timezone_code = airport_code.get(con["departure"]["airport"], {}).get("timeZone", '')
            arrival_timezone_code = airport_code.get(con["arrival"]["airport"], {}).get("timeZone", '')
            departure_date_time = datetime.strptime(con["departure"]["when"], "%Y-%m-%dT%H:%M:%S")
            arrival_date_time = datetime.strptime(con["arrival"]["when"], "%Y-%m-%dT%H:%M:%S")
            departure_timezone = pytz.timezone(departure_timezone_code)
            arrival_timezone = pytz.timezone(arrival_timezone_code)
            con['departure']["when"] = departure_timezone.localize(departure_date_time).strftime('%Y-%m-%dT%H:%M:%S %Z%z')
            con['arrival']["when"] = arrival_timezone.localize(arrival_date_time).strftime('%Y-%m-%dT%H:%M:%S %Z%z')
    if len(final_dict) == 0:
        error_msg = "No flights found"
        return final_dict, error_msg
    else:
        return final_dict, error_msg