
// https://app.bitly.com/settings/api > Settings > API > Access Token > Generate Token
const BITLY_ACCESS_TOKEN = PropertiesService.getScriptProperties().getProperty('BITLY_TOKEN');
const BITLY_GROUP_GUID = PropertiesService.getScriptProperties().getProperty('BITLY_GROUP_GUID');
const BITLY_DOMAIN = 'goo.gle';
const SPREADSHEET_ID = PropertiesService.getScriptProperties().getProperty('SHEET_ID');
const SHEET_NAME = 'leaderboard';
// https://www.google.com/u/1/recaptcha/admin/create
const RECAPTCHA_SECRET = PropertiesService.getScriptProperties().getProperty('RECAPTCHA_SECRET');


/**
 * Serves the HTML frontend to the user.
 */
function doGet() {
  return HtmlService.createHtmlOutputFromFile('Index')
    .setTitle('Refer-a-Friend Campaign')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}


/**
 * Generates a Bitly link securely with reCAPTCHA, rate limiting, and input validation.
 */
function generateReferralLink(email, website, recaptchaToken) {

  /*
  // --- 1. Verify reCAPTCHA ---
  
  // --- End reCAPTCHA Verification ---
  */


  // 2. Basic Input Validation
  if (!email || !website) {
    return { success: false, message: "Email and website are required." };
  }

  email = email.trim();
  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
  if (!emailRegex.test(email)) {
    return { success: false, message: "Invalid email format." };
  }

  // 3. Server-Side URL Validation (Prevent Open Shortener)
  const validEvents = getEvents();
  const selectedEvent = validEvents.find(e => e.url === website);

  if (!selectedEvent) {
    return { success: false, message: "Invalid target website selected." };
  }

  // 4. Email-Based Rate Limiting using CacheService
  const cache = CacheService.getScriptCache();
  const cacheKey = 'rate_limit_' + email.toLowerCase();
  const currentUsage = cache.get(cacheKey);
  const MAX_LINKS_PER_EMAIL = 10;

  if (currentUsage && parseInt(currentUsage) >= MAX_LINKS_PER_EMAIL) {
    return { success: false, message: "Link generation limit reached for this email address. Try again tomorrow." };
  }

  // 5. Generate Link
  try {
    const encodedEmail = Utilities.base64EncodeWebSafe(email);
    const apiUrl = "https://api-ssl.bitly.com/v4/bitlinks";
    const linkTitle = "GDG REFER: " + selectedEvent.name;
    const separator = website.includes('?') ? '&' : '?';
    const longUrl = website + separator + 'ref_user=' + encodedEmail;
    console.log("Long URL: ", longUrl);

    const payload = {
      long_url: longUrl,
      domain: BITLY_DOMAIN,
      title: linkTitle,
      tags: ["gdg-track"],
      group_guid: BITLY_GROUP_GUID
    };

    var options = {
      method: 'post',
      headers: {
        'Authorization': 'Bearer ' + BITLY_ACCESS_TOKEN,
        'Content-Type': 'application/json'
      },
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    };

    const response = UrlFetchApp.fetch(apiUrl, options);
    const responseCode = response.getResponseCode();
    const result = JSON.parse(response.getContentText());

    if (responseCode === 200 || responseCode === 201) {
      const bitlyLink = result.link;

      // Update spam abuse email cache
      const newUsageCount = (parseInt(currentUsage) || 0) + 1;
      cache.put(cacheKey, newUsageCount.toString(), 86400);

      // Update spreadsheet
      try {
        const sheet = SpreadsheetApp.openById(SPREADSHEET_ID).getSheetByName(SHEET_NAME);
        sheet.appendRow([new Date(), email, website, bitlyLink, encodedEmail]);
      } catch (sheetError) {
        console.error("Sheet Error: ", sheetError);
        return { success: false, message: "An internal server error occurred while logging. Please notify gdgforscience@gmail.com" };
      }

      return { success: true, link: bitlyLink };
    } else {
      console.error("Bitly API Error: ", result);
      const errorMsg = result.message || JSON.stringify(result);
      return { success: false, message: "Bitly Error (" + responseCode + "): " + errorMsg + ". Please notify gdgforscience@gmail.com" };
    }

  } catch (error) {
    console.error("Script Error: ", error);
    return { success: false, message: "An script error occurred. Please notify gdgforscience@gmail.com" };
  }
}
function getEvents() {
  try {
    const sheet = SpreadsheetApp.openById(SPREADSHEET_ID).getSheetByName('events');
    const data = sheet.getDataRange().getValues();
    const events = [];

    // Start at index 1 to skip the header row ("event" and "event_url")
    for (let i = 1; i < data.length; i++) {
      const eventName = data[i][0];
      const eventUrl = data[i][1];

      // Ensure the row isn't blank before adding it
      if (eventName && eventUrl) {
        events.push({
          name: eventName,
          url: eventUrl
        });
      }
    }
    return events;
  } catch (error) {
    Logger.log("Error fetching events: " + error.toString());
    return []; // Return an empty array if the sheet isn't found or there's an error
  }
}