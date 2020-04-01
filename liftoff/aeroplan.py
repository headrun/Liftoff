from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from scrapy.selector import Selector
from pyvirtualdisplay import Display
from time import sleep, strptime
from datetime import datetime, timedelta
import email
import imaplib
import re

def aeroplanselnium(request_data):
    routes = []
    username = request_data.get("username", '')
    password = request_data.get("password", '')
    departure_date = request_data.get('departure_date', {}).get('when', '')
    arrival_date = request_data.get('arrival_date', {}).get('when', '')
    departure_airport = request_data.get('departure', '')
    arrival_airport = request_data.get('arrival', '')

    passengers = request_data.get('passengers', 0)
    cabins = request_data.get('cabins', [])
    max_stops = request_data.get('max_stops', '')
    cabin_classes = []
    for cabin in cabins:
        if cabin.lower() == "economy":
            cabin_classes.append("ECONOMY")
        elif cabin.lower() == "premium_economy":
            cabin_classes.append("PREMIUM ECONOMY")
        elif cabin.lower() == "business":
            cabin_classes.append("BUSINESS")
        elif cabin.lower() == "first_class":
            cabin_classes.append("FIRST")
    cabin_classes = list(set(cabin_classes))

    display = Display(visible=1, size=(1400,1000))
    display.start()
    profile = webdriver.FirefoxProfile()
    profile.set_preference("browser.cache.disk.enable", False)
    profile.set_preference("browser.cache.memory.enable", False)
    profile.set_preference("browser.cache.offline.enable", False)
    profile.set_preference("network.http.use-cache", False)
    driver = webdriver.Firefox(profile)
    driver.delete_all_cookies()

    departure_date = datetime.strptime(departure_date, "%Y-%m-%d").strftime('%m/%d/%Y')
    arrival_date = datetime.strptime(arrival_date, "%Y-%m-%d").strftime('%m/%d/%Y')

    try:
        driver.get('https://www.aeroplan.com/landing/process.do?lang=E#/')
        driver.find_element_by_xpath("//button[@type='button']").click()
        driver.find_element_by_id("aeroplanNumber").clear()
        driver.find_element_by_id("aeroplanNumber").send_keys(username)
        driver.find_element_by_name("pin").click()
        driver.find_element_by_name("pin").clear()
        driver.find_element_by_name("pin").send_keys(password)
        driver.find_element_by_xpath("(//button[@type='submit'])[3]").click()
        sleep(10)
        driver.find_element_by_name("verification-code").click()
        driver.find_element_by_name("verification-code").clear()
        sleep(5)

        opt_check = 0
        while opt_check < 5:
            otp = get_otp(username, password)
            if otp:
                break
            opt_check += 1

        driver.find_element_by_name("verification-code").send_keys(otp)
        driver.find_element_by_xpath("//button[@type='button']").click()
        sleep(7)
        driver.find_element_by_link_text("English").click()
        sleep(5)
        driver.find_element_by_link_text("FLIGHTS").click()
        sleep(5)
        driver.find_element_by_id("tripTypeRoundTrip2").click()
        driver.find_element_by_id("OneWayAirCanadaCompare1").click()
        sleep(2)
        driver.find_element_by_id("city1FromOnewayCode-selectized").send_keys(departure_airport)
        sleep(2)
        driver.find_element_by_xpath('//fieldset[@class="form-group checkradio-style is-filled"]').click()
        sleep(2)
        driver.find_element_by_id("city1ToOnewayCode-selectized").send_keys(arrival_airport)
        sleep(2)
        driver.find_element_by_xpath('//span[@class="highlight"]').click()
        driver.find_element_by_id("l1Oneway").send_keys(departure_date)
        sleep(2)
        driver.find_element_by_xpath('//div[@data-automation="one-way-submit"]').click()

        sleep(20)

        windows = driver.window_handles
        if windows:
            results_page = windows[-1]
            driver.switch_to_window(results_page)

        year = departure_date.split('/')[-1]
        sel = Selector(text=driver.page_source)
        nodes = sel.xpath('//div[contains(@id, "prod0")][contains(@class, "flightRow")]') +\
                sel.xpath('//div[contains(@id, "prod1")][contains(@class, "flightRow")]')

        for node in nodes:
            award_type, record, conn = '', {}, []
            if 'prod0' in node.extract():
                award_type = 'Fixed Mileage'
            elif 'prod1' in node.extract():
                award_type = 'Market Fare'

            departure = ''.join(node.xpath('.//div[@class="from"]/text()').extract()).strip()
            arrival = ''.join(node.xpath('.//div[@class="to"]/text()').extract()).strip()
            miles = ''.join(node.xpath('.//div[@class="miles"]/text()').extract()) or 0
            if miles:
                miles = int(miles.replace(',', '').strip())
            stops = ''.join(node.xpath('.//div[@class="stops"]/text()').extract()) or 0
            if stops and 'direct' in stops.lower():
                stops = 0
            elif stops:
                stops = int(stops.split(' ')[0].strip())

            layover_hour, layover_min = 0, 0
            layover_list = node.xpath('.//div[@class="connection"]//span[@class="bold"]/text()').extract()
            for layover in layover_list:
                if 'h' not in layover:
                    lay_time = strptime(layover, "%M min")
                else:
                    lay_time = strptime(layover, "%Hh %M min")
                layover_hour = layover_hour + lay_time.tm_hour
                layover_min = layover_min + lay_time.tm_min

            lay_time = timedelta(hours=layover_hour, minutes=layover_min)

            try:
                layover_time = datetime.strptime(str(lay_time), "%H:%M:%S").strftime('%H:%M')
            except:
                layover_time = lay_time

            total_time = '00:00'
            total_travel_time = ''.join(node.xpath('.//div[@class="totalDurationRow"]/div[@class="totalDuration"]/text()').extract())
            if total_travel_time:
                total_time = total_travel_time.split(':')[-1].strip()
                if 'h' not in total_time:
                    total_time = total_time.replace('min', '').strip()
                    total_time = timedelta(minutes=int(total_time))
                else:
                    hours, minutes = total_time.split('h')
                    total_time = timedelta(hours=int(hours.strip()), minutes=int(minutes.replace('min', '').strip()))

                total_time = str(total_time - lay_time)
                total_time = datetime.strptime(total_time, "%H:%M:%S").strftime("%H:%M")

            record.update({
                "distance": None,
                "num_stops": stops,
                "times": {
                    "flight": total_time,
                    "layover": str(layover_time)
                    },
                "redemptions": [
                    {
                        "miles": miles,
                        }
                    ],
                "payments": [
                    {
                        "currency": "USD",
                        "taxes": "0.0",
                        "fees": None
                        }
                    ],
                "site_key": "AC"
                })
            if stops <= max_stops:
                inner_nodes = node.xpath('.//div[@class="middleColumn"]')
                if not inner_nodes: continue
                for inner_node in inner_nodes:
                    flight_no = ''.join(inner_node.xpath('./div[@class="line flighNo"]/@flighno').extract()).strip()
                    dep_airport = ''.join(inner_node.xpath('.//div[contains(text(), "Departs")]/../div[@class="airport"]/text()').extract()).strip()
                    arr_airport = ''.join(inner_node.xpath('.//div[contains(text(), "Arrives")]/../div[@class="airport"]/text()').extract()).strip()
                    dep_date = ''.join(inner_node.xpath('.//div[contains(text(), "Departs")]/../div[@class="date"]/text()').extract()).strip()
                    dep_time = ''.join(inner_node.xpath('.//div[contains(text(), "Departs")]/../div[@class="time"]/text()').extract()).strip()
                    arr_date = ''.join(inner_node.xpath('.//div[contains(text(), "Arrives")]/../div[@class="date"]/text()').extract()).strip()
                    arr_time = ''.join(inner_node.xpath('.//div[contains(text(), "Arrives")]/../div[@class="time"]/text()').extract()).strip()
                    flight_duration = ''.join(inner_node.xpath('./div[@class="line last"]/div[@class="duration"]/b/text()').extract()).strip()
                    cabin_class = ''.join(inner_node.xpath('.//div[@class="cabin"]/div/text()').extract()).strip()
                    book_class = ''.join(inner_node.xpath('.//div[@class="bookclass"]/text()').extract()).strip()
                    book_class = book_class.replace("Class", "").strip()
                    aircraft = ''.join(inner_node.xpath('.//div[@class="aircraft"]/text()').extract()).strip()

                    dep_datetime = datetime.strptime('%s %s %s' % (year, dep_date, dep_time), "%Y %a. %b %d %H:%M").strftime("%Y-%m-%dT%H:%M")
                    arr_datetime = datetime.strptime('%s %s %s' % (year, arr_date, arr_time), "%Y %a. %b %d %H:%M").strftime("%Y-%m-%dT%H:%M")

                    flight_dur, layover_dur = '00:00', '00:00'
                    if flight_duration:
                        flight_duration = flight_duration.split(':')[-1].replace('min', '').strip()
                        if 'h' not in flight_duration:
                            flight_dur = timedelta(minutes=int(flight_duration))
                        else:
                            hours, minutes = flight_duration.split('h')
                            flight_dur = timedelta(hours=int(hours.strip()), minutes=int(minutes.replace('min', '').strip()))

                    try:
                        flight_duration = datetime.strptime(str(flight_dur), "%H:%M:%S").strftime('%H:%M')
                    except:
                        flight_duration = flight_dur

                    conn_dict = {
                            "departure": {
                                "when": dep_datetime,
                                "airport": "".join(re.findall("\((.*?)\)", dep_airport)).strip()
                                },
                            "arrival": {
                                "when": arr_datetime,
                                "airport": "".join(re.findall("\((.*?)\)", arr_airport)).strip()
                                },
                            "airline": "".join(re.findall("[a-zA-Z]+", flight_no)).strip(),
                            "flight": [flight_no],
                            "cabin": cabin_class.title(),
                            "distance": None,
                            "aircraft": {
                                "model": aircraft.split(' ')[-1] if aircraft else '',
                                "manufacturer": aircraft.split(' ')[0] if aircraft else ''
                                },
                            "times": {
                                "flight": str(flight_duration),
                                "layover": str(layover_time),
                                },
                            "redemptions": [{
                                "miles": miles,
                                "program": "%s %s".strip() % (award_type, cabin_class.title())
                                }],
                            "payments": [{
                                "currency": "CAD",
                                "taxes": "",
                                "fees": "0"
                                }],
                            "tickets": None,
                            "fare_class": book_class
                            }

                    conn.append(conn_dict)
                cabin_available = False
                for ele in conn:
                    if ele["cabin"].upper() in cabin_classes:
                        cabin_available = True
                if cabin_available:
                    record.update({"connections": conn})
                    record["redemptions"][0].update({"program": "%s %s".strip() % (award_type, cabin_class.title())})
                    record["award_type"] = "%s %s".strip() % (award_type, cabin_class.title())
                    routes.append(record)

    except Exception as error:
        print (error)

    finally:
        display.stop()
        driver.quit()
        return routes

def get_otp(username, password):
    opt = ''
    imapSession = imaplib.IMAP4_SSL('imap.gmail.com', '993')
    typ, accountDetails = imapSession.login(username, password)
    if typ != 'OK':
        print('Not able to sign in!')
        raise

    imapSession.select('"[Gmail]/All Mail"')
    typ, data = imapSession.search(None, 'UnSeen')
    if typ != 'OK':
        print('Error searching Inbox.')
        raise

    for msgId in data[0].split():
        typ, messageParts = imapSession.fetch(msgId, '(RFC822)')
        if typ != 'OK':
            print('Error fetching mail.')
            raise

        emailBody = messageParts[0][1]
        mail = email.message_from_bytes(emailBody)
        mail_subject = mail['subject']
        mail_from = mail['from']

        if "info@communications.aeroplan.com" in mail_from:
            opt = ''.join(re.findall('VERIFICATION\sCODE:\s(\d{6})', emailBody.decode('utf8'))).strip()

    imapSession.close()
    imapSession.logout()
    print('Done')

    return opt


