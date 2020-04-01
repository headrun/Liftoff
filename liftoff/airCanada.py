import requests
import json
import re
import copy
from datetime import datetime

def airCanadas(request_body):
    data = request_body
    headers = {
        'authority': 'book.aircanada.com',
        'accept': 'application/json, text/plain, */*',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://www.aircanada.com',
        'sec-fetch-site': 'same-site',
        'sec-fetch-mode': 'cors',
        'referer': 'https://www.aircanada.com/ca/en/aco/home.html',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    }
    departureDate = request_body.get('departure_date').get('when')
    try:
        departureDate = datetime.strptime(departureDate, "%Y-%m-%d").strftime("%d/%m/%Y")
    except:
        departureDate = ''
    arrivalDate = request_body.get('arrival_date').get('when')
    try:
        arrivalDate = datetime.strptime(arrivalDate, "%Y-%m-%d").strftime("%d/%m/%Y")
    except:
        arrivalDate = ''
    request_cabins = data.get('cabins', [])
    cabin_classes = []
    cabinMapping = {'ECONOMY':'ECONOMY','PREMIUM_ECONOMY':'PREMIUM_ECONOMY','BUSINESS':'BUSINESS','FIRST':'FIRST_CLASS'}
    for cabin in request_cabins:
        if cabin == "FIRST_CLASS":
            cabin_classes.append("FIRST")
        elif cabin == "BUSINESS":
            cabin_classes.append("BUSINESS")
        elif cabin.lower() == "PREMIUM_ECONOMY":
            cabin_classes.append("PREMIUM_ECONOMY")
        elif cabin.lower() == "ECONOMY":
            cabin_classes.append("COACH")
    tripStatus = 'O'
    if departureDate != arrivalDate:
        tripStatus = 'R'
    maxStop = data.get('max_stops')

    data = {
      'AH_EMAIL': '',
      'AH_IATA_NUMBER': '0005417',
      'AH_SOURCE_CODE': '04',
      'AH_URL_AGENCY': 'http://www.aimia.com',
      'AH_URL_PICTURE': '/content/dam/aircanada/portal/Legacy/Images/spacer.gif',
      'B_LOCATION_TYPE_1': 'A',
      'COUNTRY': 'CA',
      'EXTERNAL_ID': '',
      'E_LOCATION_TYPE_1': 'A',
      'IS_HOME_PAGE': 'TRUE',
      'LANGUAGE': 'US',
      'LANGUAGE_CHARSET': 'utf-8',
      'USERID': 'GUEST',
      'actionName': 'Override',
      'countryOfResidence': 'CA',
      'departure1': departureDate,
      'dest1': ''.join(request_body.get('arrivals','')).strip(),
      'numberOfAdults': str(request_body.get('passengers',0)),
      'numberOfChildren': '0',
      'numberOfInfants': '0',
      'numberOfYouth': '0',
      'org1': ''.join(request_body.get('departures','')).strip(),
      'requestedPage': 'AVAI',
      'tripType': 'O'
    }

    response = requests.post('https://book.aircanada.com/ACWebOnline/CreatePNRServlet', headers=headers,data=data)
    data = json.loads(response.text)
    res = data.get("DATA",{}).get("availResponse",[])
    final_dict=[]
    for results in res:
        result = results.get("results",'')
        for fares in result:
            segment = fares.get("LIST_SEGMENT",'')
            fare = fares.get("fares",'')
            fare_classes = {}
            for seg in segment:
                sample_dict  = {}
                sample_dict["connections"] = []
                flight_num = seg.get("FLIGHT_NUMBER",'')
                when_date = seg.get("E_DATE",'')

                when = ''.join(re.findall('(.*)T',when_date))
                date1 = seg.get("B_DATE",'')
                date = ''.join(re.findall('(.*)T',date1))
                arrival = seg.get("E_LOCATION",'')
                Duration = seg.get("SEGMENT_DURATION",'')
                hours = int(Duration/60)
                minutes = Duration%60
                times = str(hours)+":"+ str(minutes)
                connectiontime = datetime.strptime(times, "%H:%M").strftime('%H:%M')

                departure = seg.get("B_LOCATION",'')
                departure_airport = departure.get('LOCATION_CODE','')
                arrival_airport = arrival.get("LOCATION_CODE",'')

                sample_dict["distance"] = None
                sample_dict["num_stops"] = seg.get("NUMBER_OF_STOPS",'')

                total_time = 0
                airlineDetails = {}
                airlineDetails["airline"] = seg.get("AIRLINE",'').get("CODE",'')
                airlineDetails["departure"] = {"when": date1, "airport": departure_airport}
                airlineDetails["arrival"] = {"when": when_date, "airport": arrival_airport}
                airlineDetails["flight"] = [flight_num]

                airlineDetails["redemptions"] = None
                airlineDetails["payments"] = None
                airlineDetails["tickets"] = None
                sample_dict["connections"].append(airlineDetails)
                sample_dict["times"] = {"filght":connectiontime,"layover":"0:00"}
                sample_dict["site_key"] = "A"


            payments = []
            for products in fare:
                cabin = products.get("product",'').get('0','')
                cabin1 = cabin.get("fareProduct",'')
                fare_classes["cabin"] = cabin1
                amount = products.get("fare",'').get("0",'')
                currency = amount.get("currency",'')
                taxes = amount.get("recTaxOriginal",'')
                total_tax = amount.get("recTotalOriginal",'')
                bound_total = amount.get("boundTotalOriginal",'')
                #payment = {"currency":currency,"taxes":taxes,"fees":"0"}
                final_sub_dict = copy.deepcopy(sample_dict)
                final_sub_dict["redemptions"] = {"miles": '', "program": ''}
                for connection in final_sub_dict["connections"]:
                    connection["fare_class"] = cabin1
                    connection["cabin"] = cabinMapping[cabin1]

                final_sub_dict["payments"] = [{"currency":currency,"taxes":taxes,"fees":bound_total}]
                final_dict.append(final_sub_dict)
    return final_dict
