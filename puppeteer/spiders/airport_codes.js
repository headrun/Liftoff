const puppeteer = require('puppeteer-extra')
const StealthPlugin = require('puppeteer-extra-plugin-stealth')
module.exports = { airportsCode }
async function airportsCode(request_data){
    var data
    await puppeteer.use(StealthPlugin())
    await puppeteer.launch({executablePath: '/usr/bin/google-chrome', headless: true, args: ['--no-sandbox', '--disable-setuid-sandbox','--lang=en-GB'] }).then(async browser => {
        const page = await browser.newPage()
        await page.goto('https://www.airfrance.us/')
        const navigationPromise = page.waitForNavigation()
        await page.waitForSelector('#gdpr_popin > section > div > div.gdpr-agree > button')
        await page.click('#gdpr_popin > section > div > div.gdpr-agree > button')
        await page.waitForSelector('#idHeaderAsfcUserAccount')
        await page.click('#idHeaderAsfcUserAccount')
        await page.waitForSelector('#mat-input-0')
        await page.click('#mat-input-0')
        await page.type('#mat-input-0', request_data.username);
        await page.waitForSelector('#mat-input-1')
        await page.click('#mat-input-1')
        await page.type('#mat-input-1', request_data.password);
        await page.waitForSelector('.login-btn-container > button')
        await page.click('.login-btn-container > button')
        await page.waitFor(3000)
        data = await text_extraction (page)
        await browser.close()
    })
    return data

}


async function text_extraction (page, elements) {
   await page.goto('https://www.airfrance.us/US/en/local/core/engine/stopover/LoadStopoverJsonAction.do')
   var content = await page.content(); 
   return content
}