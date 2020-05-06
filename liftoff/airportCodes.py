import requests;
import json;
from configparser import ConfigParser
import random
from json import dumps
def airportCodes():
	final_dict = {}
	cfg_obj = ConfigParser()
	cfg_obj.read('credentials.cfg')
	listofusers = eval(cfg_obj.get('AF', 'Accounts'))
	random_user = random.choice(listofusers)
	request_body = {"username":random_user.split('<>')[0],"password":random_user.split('<>')[1]}
	response = requests.post('http://127.0.0.1:5000/aiportCode', json=request_body)
	res_dict_string = response.text.split('pre-wrap;">')[1].split('<')[0]
	res_dict = json.loads(res_dict_string)
	airports_names = res_dict.get('stopoverLists',{}).get('stopoverLabels',{})
	airport_city = res_dict.get('stopoverLists',{}).get('cityLabels',{})
	count = 0
	for key, value in airports_names.items():
		if "AIRP" in key:
			iata_code = key.split('_')[0]
			try:
				city_name = airport_city[iata_code]
			except:
				city_name = ''
			re_data = {"code":iata_code}
			res = requests.post('http://127.0.0.1:5000/timeZone', json=re_data)
			try:
				time_res = json.loads(res.text)
			except:
				count = count + 1
				print(re_data)
				time_res = {}
			final_dict[iata_code]={"name":value,"city":city_name,"timeZone":time_res.get("timezone",'')}
	with open('airport_codes.txt', 'w+') as _file:
            _file.write(dumps(final_dict))




if __name__== "__main__":
	airportCodes()

