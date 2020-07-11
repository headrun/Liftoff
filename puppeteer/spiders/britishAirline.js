const puppeteer = require('puppeteer-extra')
const StealthPlugin = require('puppeteer-extra-plugin-stealth')
module.exports = { britishAirline }
async function britishAirline(request_data){
    var result
    await puppeteer.use(StealthPlugin())
    await puppeteer.launch({executablePath: '/usr/bin/google-chrome', headless: true, args: ['--no-sandbox', '--disable-setuid-sandbox','--lang=en-GB']}).then(async browser => {
        const page = await browser.newPage()
        await page.goto('https://www.britishairways.com/travel/home/execclub/_gf/en_us/')
        const navigationPromise = page.waitForNavigation()
        await page.waitForSelector('#membershipNumber')
        await page.click('#membershipNumber')
        await page.type('#membershipNumber', request_data.username);
        await page.waitForSelector('#input_password')
        await page.click('#input_password')
        await page.type('#input_password', request_data.password);
        await page.click('#ecuserlogbutton')
        await page.waitFor(5000)
        await page.goto('https://www.britishairways.com/travel/redeem/execclub/_gf/en_us?eId=106019&tab_selected=redeem&redemption_type=STD_RED')
        await page.waitForSelector('#departurePoint')
        let departure = request_data.departures
        let arrival = request_data.arrivals
        let departureDate = request_data.departureDate
        await page.$eval('#departurePoint', (el, _uid) => el.value = _uid, departure);
        await page.waitForSelector('#destinationPoint')
        await page.$eval('#destinationPoint', (el, _uid) => el.value = _uid, arrival);
        await page.$eval('#departInputDate', (el, _uid) => el.value = _uid, departureDate);
        await page.waitForSelector('#oneWayBox')
        await page.click('#oneWayBox')
        await page.click('#submitBtn')
        await page.waitForSelector('#journey0RadioButton0CabinCodeM')
        let business_element = []
        bodyHTML = await page.evaluate(() => document.body.innerHTML);
        if (request_data.cabins.includes("business")){
            const business = await page.$x("//div[contains(@class,'number-of-seats-available')]//div//*[text()='Business Class']");
            business_element= await text_extraction (page, business) 
        }
        let premium_economy_element = []
        if (request_data.cabins.includes("premium_economy")){
            const premium_economy = await page.$x("//div[contains(@class,'number-of-seats-available')]//div//*[text()='Premium Economy']");
            premium_economy_element = await text_extraction(page,premium_economy)
        }
        let economy_element = []
        if (request_data.cabins.includes("economy")){
            const economy = await page.$x("//div[contains(@class,'number-of-seats-available')]//div//*[text()='Economy']");
            economy_element = await text_extraction(page,economy)
        }
        let first_class_element = []
        if (request_data.cabins.includes("first_class")){
            const first_class = await page.$x("//div[contains(@class,'number-of-seats-available')]//div//*[text()='LA Premiere']");
            first_class_element = await text_extraction(page,economy)
        }
        const model_details = await page.$$eval('.career-and-flight > a', anchors => [].map.call(anchors, a => a.href));
        const model_list = {}
        for await(const element of model_details){
               model_list[element] = await url_extraction(page,element)
               // model_list.push(data)
        }
        result = {
            "economy":economy_element,
            "premium_economy":premium_economy_element,
            "business":business_element,
            "first_class":first_class_element,
            "flight_model_data":model_list,
            "sourcePage":bodyHTML
            }
        await browser.close()
    })
    return result
}


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
      index = index+1
   }
   return data
}

async function url_extraction (page, url) {
    await page.goto(url);
    await page.waitForSelector('#flightDetailsModalTable > div:nth-child(7) > p:nth-child(2) > span.text')
    const result = await page.evaluate(() => {
        let flight_info = {}
        flight_info["flight"] = document.querySelector('#flightDetailsModalTable > div:nth-child(1) > p:nth-child(2) > span.text').textContent;
        flight_info["operatedBy"] = document.querySelector('#flightDetailsModalTable > div:nth-child(2) > p:nth-child(2) > span.text').textContent;
        flight_info["departure"] = document.querySelector('#flightDetailsModalTable > div:nth-child(3) > p:nth-child(2) > span.text').textContent;
        flight_info["arrival"] = document.querySelector('#flightDetailsModalTable > div:nth-child(4) > p:nth-child(2) > span.text').textContent;
        flight_info["stops"] = document.querySelector('#flightDetailsModalTable > div:nth-child(5) > p:nth-child(2) > span.text').textContent;
        flight_info["duration"] = document.querySelector('#flightDetailsModalTable > div:nth-child(6) > p:nth-child(2) > span.text').textContent;
        flight_info["aircraft"] = document.querySelector('#flightDetailsModalTable > div:nth-child(7) > p:nth-child(2) > span.text').textContent;
        return flight_info
    });
    result["url"] = url
    return result
}