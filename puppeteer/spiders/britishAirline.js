const puppeteer = require('puppeteer-extra')
const StealthPlugin = require('puppeteer-extra-plugin-stealth')
async function britishAirline(){
    puppeteer.use(StealthPlugin())
    puppeteer.launch({executablePath: '/usr/bin/google-chrome', headless: false }).then(async browser => {
        const page = await browser.newPage()
        await page.goto('https://www.britishairways.com/travel/home/execclub/_gf/en_us/')
        const navigationPromise = page.waitForNavigation()
        await page.waitForSelector('#loginid')
        await page.click('#loginid')
        await page.type('#loginid', 'mattrobertsm@gmail.com');
        await page.waitForSelector('#password')
        await page.click('#password')
        await page.type('#password', 'Roberts@11');
        await page.click('#navLoginForm > div:nth-child(5) > div > button')
        await page.waitFor(5000)
        await page.goto('https://www.britishairways.com/travel/redeem/execclub/_gf/en_us?eId=106019&tab_selected=redeem&redemption_type=STD_RED')
        await page.waitForSelector('#departurePoint')
        await page.$eval('#departurePoint', el => el.value = 'LAX');
        await page.waitForSelector('#destinationPoint')
        await page.$eval('#destinationPoint', el => el.value = 'LHR');
        await page.$eval('#departInputDate', el => el.value = '09/15/20');
        await page.waitForSelector('#oneWayBox')
        await page.click('#oneWayBox')
        await page.click('#submitBtn')
        await page.waitForSelector('#journey0RadioButton0CabinCodeM')


        const flight_single_connection = await page.evaluate(() => Array.from(document.querySelectorAll('.flight-details')));
        const connection_flight = await page.evaluate(() => Array.from(document.querySelectorAll('.connecting-flights')));
        console.log(flight_single_connection.length);
        console.log(connection_flight.length);
        final_dict = []
        const result = await page.evaluate(() => {
        const flights = document.querySelectorAll('.flight-details');
            return Array.from(flights, flight => {
                let final_sub_dict = {}
                let sample_dict = {}
                sample_dict["departureDate"] = flight.querySelector(".departdate ").textContent;
                sample_dict["departureTime"] = flight.querySelector(".departtime >strong").textContent;
                sample_dict["departureAirport"] = flight.querySelector(".airportCodeLink").textContent;
                sample_dict["arrivalDate"] = flight.querySelector(".arrivaldate ").textContent;
                sample_dict["arrivalTime"] = flight.querySelector(".arrivaltime >strong").textContent;
                sample_dict["arrivalAirport"] = flight.querySelector(".arrival >div >p >a").textContent;
                sample_dict["jurneyTime"] = flight.querySelector(".journeyTime").textContent;
                sample_dict["airline"] = flight.querySelector(".career-and-flight > a > span:nth-child(1)").textContent;
                sample_dict["flightNumber"] = flight.querySelector(".career-and-flight > a > span:nth-child(2)").textContent;
                sample_dict["model"] = flight.querySelector(".career-and-flight > a").href;
                sample_dict["cabins_details"] = flight.querySelector('.cabinSelector')
                let mona = flight.querySelector('.cabinSelector')
                console.log(mona)
                final_sub_dict["connections"] = sample_dict
                return final_sub_dict
            });
        });

        const result1 = await page.evaluate(() => {
            const rows = document.querySelectorAll('.connecting-flights');
                return Array.from(rows, row => {
                let sample_dict = {}
                const columns = row.querySelectorAll('.travel-time-detail');
                Array.from(columns, column => {
                    sample_dict["departureDate"] = column.querySelector(".departdate ").textContent;
                    sample_dict["departureTime"] = column.querySelector(".departtime >strong").textContent;
                    sample_dict["departureAirport"] = column.querySelector(".airportCodeLink").textContent;
                    sample_dict["arrivalDate"] = column.querySelector(".arrivaldate ").textContent;
                    sample_dict["arrivalTime"] = column.querySelector(".arrivaltime >strong").textContent;
                    sample_dict["arrivalAirport"] = column.querySelector(".arrival >div >p >a").textContent;
                    sample_dict["airline"] = column.querySelector(".career-and-flight > a > span:nth-child(1)").textContent;
                    sample_dict["flightNumber"] = column.querySelector(".career-and-flight > a > span:nth-child(2)").textContent;
                    sample_dict["model"] = column.querySelector(".career-and-flight > a").href;
                });
                let mona = row.querySelector('.cabinSelector')
                console.log(mona)
                sample_dict["cabins_details"] = row.querySelector('.cabinSelector')
                return sample_dict
            });
        });
        //console.log(result)
        //for await(const element of result){
        //    let href_data = await url_extraction(page,element.connections.model)
        //    console.log(href_data)
        //    element.connections.model_data = href_data
        //}
        //console.log(result1)
        //const cabins = await page.evaluate(() => Array.from(document.querySelectorAll('.cabinSelector')))
        const business = await page.$x("//div[contains(@class,'number-of-seats-available')]//div//*[text()='Business Class']");
        let business_element= await text_extraction (page, business)
        const economy = await page.$x("//div[contains(@class,'number-of-seats-available')]//div//*[text()='Economy']");
        let economy_element = await text_extraction(page,economy)
        console.log(economy_element)
        for await(const element of result){
           element["modelData"] = await url_extraction(page,element.connections.model)
           console.log(data)
        }
    })

}
britishAirline()


async function text_extraction (page, elements) {
   let data  = []
   index =0
   for await(const element of elements){
      await page.evaluate((element) => element.click(),element)
      await page.waitFor(10000)
      await page.waitForSelector('.totalPriceAviosTxt')
      let element1 = await page.$(".totalPriceAviosTxt");
      let text1 = await (await element1.getProperty('textContent')).jsonValue();
      data[index] = text1
      console.log(text1)
      index = index+1
   }
   return data
}

async function url_extraction (page, url) {
    await page.goto(url);
    await page.waitForSelector('#flightDetailsModalTable > div:nth-child(7) > p:nth-child(2) > span.text')
    let element1 = await page.$("#flightDetailsModalTable > div:nth-child(7) > p:nth-child(2) > span.text");
    let text1 = await (await element1.getProperty('textContent')).jsonValue();
    return text1
}