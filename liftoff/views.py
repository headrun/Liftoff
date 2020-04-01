from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
import datetime
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_200_OK
)
from rest_framework.response import Response
from . import americanAirline
from . import airCanada
from . import aeroplan

@csrf_exempt
@api_view(["POST"])
@permission_classes((AllowAny,))
def login(request):
    username = request.data.get("username")
    password = request.data.get("password")
    if username is None or password is None:
        return Response({'error': 'Please provide both username and password'},
                        status=HTTP_400_BAD_REQUEST)
    user = authenticate(username=username, password=password)
    if not user:
        return Response({'error': 'Invalid Credentials'},
                        status=HTTP_404_NOT_FOUND)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key},
                    status=HTTP_200_OK)

@csrf_exempt
@api_view(['POST'])
@permission_classes((AllowAny,))
def americanAirlines(request):
    if request.method == 'POST':
        value = request.data
        start = datetime.datetime.now()
        final = {}
        valid = validateRequest(value)
        length = 0
        if valid:
            final_dict = americanAirline.americanAirlines(value)
            if final_dict:
                length = len(final_dict)
                final = {"routes":final_dict}
                status, description = "OK","OK"
            else:
                status = "Error"
                description = "No flights available"
            res_status = HTTP_200_OK
        else:
            status = "Error"
            description = "Please provides all mandatory fields"
            res_status = HTTP_400_BAD_REQUEST
        end = datetime.datetime.now()
        res_time = end - start
        final["metrics"] = {"url":"https://www.aa.com","status":status,"description":description,"response_time":res_time.microseconds,"airline":"AA","results":length}
        return Response(final,status=res_status)

@csrf_exempt
@api_view(['POST'])
@permission_classes((AllowAny,))
def airCanadas(request):
    if request.method == 'POST':
        value = request.data
        start = datetime.datetime.now()
        final = {}
        valid = validateRequest(value)
        length = 0
        if valid:
            final_dict = airCanada.airCanadas(value)
            if final_dict:
                length = len(final_dict)
                final = {"routes":final_dict}
                status, description = "OK","OK"
            else:
                status = "Error"
                description = "No flights available"
            res_status = HTTP_200_OK
        else:
            status = "Error"
            description = "Please provides all mandatory fields"
            res_status = HTTP_400_BAD_REQUEST
        end = datetime.datetime.now()
        res_time = end - start
        final["metrics"] = {"url":"https://www.aircanada.com/","status":status,"description":description,"response_time":res_time.microseconds,"airline":"AC","results":length}
        return Response(final,status=res_status)

@csrf_exempt
@api_view(['POST'])
@permission_classes((AllowAny,))
def runscraper(request):
    if request.method == 'POST':
        final, length = {}, 0
        values = request.data
        start = datetime.datetime.now()
        valid = validateRequest(values)
        airline = values.get('airlines', '')
        if not airline or not valid:
            status = "Error"
            description = "Please provides all mandatory fields"
            res_status = HTTP_400_BAD_REQUEST
        else:
            res_status = HTTP_200_OK

        if airline == 'AA':
            final_dict = americanAirline.americanAirlines(values)
            url = 'https://www.aa.com'
        elif airline == 'AC':
            username = "mattrobertsm@gmail.com"
            password = "Roberts@11"
            values.update({'username': username, 'password': password})
            final_dict = aeroplan.aeroplanselnium(values)
            url =  'https://www.aeroplan.com/'
        else:
            final_dict, url = {}, ''

        if final_dict:
            length = len(final_dict)
            final = {"routes": final_dict}
            status, description = "OK","OK"
        else:
            status = "Error"
            description = "No flights available"

        end = datetime.datetime.now()
        res_time = end - start
        final["metrics"] = {"url": url, "status": status, "description": description, "response_time": res_time.microseconds, "airline":airline, "results":length}
        return Response(final,status=res_status)

def validateRequest(data):
    airline = data.get('airline', '')
    arrival =  data.get('arrival', '')
    cabins = data.get('cabins', '')
    departure_date = data.get('departure_date', {}).get('when', '')
    arrival_date = data.get('arrival_date', {}).get('when', '')
    departure = data.get('departure_date', '')
    arrival = data.get('arrival_date', '')
    departures = data.get('departure', '')
    max_stops = data.get('max_stops', '')
    passengers = data.get('passengers', '')
    valid = True
    if not airline: valid = False
    if not arrival: valid = False
    if not cabins: valid = False
    if not departure_date: valid = False
    if not arrival_date: valid = False
    if not departures: valid = False
    if not departures: valid = False
    if max_stops == '': valid = False
    if not passengers: valid = False
    return valid
