const puppeteer = require('puppeteer-extra')
const StealthPlugin = require('puppeteer-extra-plugin-stealth')
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
  //await page.click('#departurePoint')
  //await page.type('#departurePoint', 'LAX');
  //wait page.waitForSelector('#destChoices')
  //await page.click('#LAX')
  await page.waitForSelector('#destinationPoint')
  await page.$eval('#destinationPoint', el => el.value = 'LHR');
  //await page.click('#destinationPoint')
  //await page.type('#destinationPoint', 'LHR')
  //await page.waitForSelector('#destChoices')
  //await page.click('#LHR')
  await page.$eval('#departInputDate', el => el.value = '05/02/20');
  await page.waitForSelector('#oneWayBox')
  await page.click('#oneWayBox')
  await page.click('#submitBtn')
})

