'use strict';
'--unhandled-rejections=strict';
const puppeteer = require('puppeteer-extra')
const StealthPlugin = require('puppeteer-extra-plugin-stealth')
module.exports = { franceAirline }
async function franceAirline(request_date)
{
    var bodyHTML
    await puppeteer.use(StealthPlugin())
    await puppeteer.launch({executablePath: '/usr/bin/google-chrome', headless: true }).then(async browser => {
    try {
      const page = await browser.newPage()
      await page.goto('https://www.airfrance.us/')
      const navigationPromise = page.waitForNavigation()
      await page.waitForSelector('#gdpr_popin > section > div > div.gdpr-agree > button')
      await page.click('#gdpr_popin > section > div > div.gdpr-agree > button')
      await page.waitForSelector('#idHeaderAsfcUserAccount')
      await page.click('#idHeaderAsfcUserAccount')
      await page.waitForSelector('#mat-input-0')
      await page.click('#mat-input-0')
      await page.type('#mat-input-0', request_date.username);
      await page.waitForSelector('#mat-input-1')
      await page.click('#mat-input-1')
      await page.type('#mat-input-1', request_date.password);
      await page.waitForSelector('.login-btn-container > button')
      await page.click('.login-btn-container > button')
      //let element =  await page.waitForSelector('.asfc-svg-content > span > svg');
      //await element.screenshot({path: "testresult.png"});
      //await page.keyboard.press('Enter');
      await page.waitForSelector('#minibe__tab--abt')
      await page.waitFor(2000)
      //await page.screenshot({ path: 'testresult.png', fullPage: true })
      await page.click('#minibe__tab--abt')
      await page.waitForSelector('#minibe__oneWay--label')
      await page.click('#minibe__oneWay--label')
      await page.waitForSelector('#minibe__od--out')
      await page.click('#minibe__od--out')
      await page.type('#minibe__od--out',request_date.departures);
      await page.waitForSelector('#minibe__od--in')
      await page.click('#minibe__od--in')
      await page.type('#minibe__od--in', request_date.arrivals)
      let date = request_date.departureDate
      let monthYear = request_date.departureMonthYear
      await page.$eval('#minibe__calendar__openerWrapper--out > input.calendar__selectedDay', (el, _uid) => el.value = _uid, date);
      await page.$eval('#minibe__calendar__openerWrapper--out > input.calendar__selectedYearMonth', (el, _uid) => el.value = _uid, monthYear);
      //await page.$eval('#minibe__calendar__openerWrapper--out > input.calendar__selectedDay', el => el.value = setValue(date));
      //await page.$eval('#minibe__calendar__openerWrapper--out > input.calendar__selectedYearMonth', el => el.value = setValue(monthYear));
      await page.click('#minibe__button--search');
      await navigationPromise
      await page.waitFor(10000)
      bodyHTML = await page.evaluate(() => document.body.innerHTML);
      await browser.close()
     } catch (e){
        await browser.close()
     }
    })
    return bodyHTML
}
