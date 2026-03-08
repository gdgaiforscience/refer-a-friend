var SHEET_ID = "1WUscJ2uMKEXrEqSCZW5sUgHUM44b7djnekprEqoqZW4";

// Bitly config — set these in Script Properties (File → Project properties → Script properties)
// BITLY_TOKEN:      your Bitly API access token
// BITLY_GROUP_GUID: (optional) your Bitly group GUID for enterprise accounts

function doGet() {
  return HtmlService.createHtmlOutputFromFile('Index')
    .setTitle('GDG Referral Tracker')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

// ---------------------------------------------------------------------------
// Sheet setup
// ---------------------------------------------------------------------------

function initializeSheets(ss) {
  var eventsSheet = ss.getSheetByName('events');
  if (!eventsSheet) {
    eventsSheet = ss.insertSheet('events');
    eventsSheet.appendRow(['event_name', 'event_url']);
    eventsSheet.appendRow(['GDG AI for Science - Next Event', 'https://gdg.community.dev/']);
    eventsSheet.setFrozenRows(1);
    eventsSheet.autoResizeColumns(1, 2);
  }

  var referralsSheet = ss.getSheetByName('referrals');
  if (!referralsSheet) {
    referralsSheet = ss.insertSheet('referrals');
    referralsSheet.appendRow(['email', 'event_name', 'bitly_link', 'created_at']);
    referralsSheet.setFrozenRows(1);
  }
}

// ---------------------------------------------------------------------------
// Bitly API helpers
// ---------------------------------------------------------------------------

function getBitlyToken_() {
  var token = PropertiesService.getScriptProperties().getProperty('BITLY_TOKEN');
  if (!token) {
    throw new Error('BITLY_TOKEN not set. Go to File → Project properties → Script properties and add it.');
  }
  return token;
}

function callBitlyApi_(endpoint, method, payload) {
  var token = getBitlyToken_();
  var options = {
    method: method || 'get',
    headers: {
      'Authorization': 'Bearer ' + token,
      'Content-Type': 'application/json'
    },
    muteHttpExceptions: true
  };
  if (payload) {
    options.payload = JSON.stringify(payload);
  }

  var response = UrlFetchApp.fetch('https://api-ssl.bitly.com' + endpoint, options);
  var code = response.getResponseCode();
  var body = JSON.parse(response.getContentText());

  if (code >= 400) {
    Logger.log('Bitly API error: ' + JSON.stringify(body));
    throw new Error('Bitly API error (' + code + '): ' + (body.message || body.description || 'Unknown error'));
  }
  return body;
}

function createBitlyLink_(longUrl, title) {
  var payload = {
    long_url: longUrl,
    domain: 'go.gle',
    title: title || ''
  };

  // Include group_guid if set (required for some enterprise accounts)
  var groupGuid = PropertiesService.getScriptProperties().getProperty('BITLY_GROUP_GUID');
  if (groupGuid) {
    payload.group_guid = groupGuid;
  }

  var result = callBitlyApi_('/v4/bitlinks', 'post', payload);
  return result.link; // e.g. "https://go.gle/abc123"
}

// ---------------------------------------------------------------------------
// Events
// ---------------------------------------------------------------------------

function getEvents() {
  var ss;
  try {
    ss = SpreadsheetApp.openById(SHEET_ID);
  } catch (err) {
    return [];
  }

  var sheet = ss.getSheetByName('events');
  if (!sheet) return [];

  var data = sheet.getDataRange().getValues();
  var events = [];
  for (var i = 1; i < data.length; i++) {
    if (data[i][0]) {
      events.push({
        name: data[i][0],
        url: data[i][1]
      });
    }
  }
  return events;
}

// ---------------------------------------------------------------------------
// Referral generation
// ---------------------------------------------------------------------------

function generateReferral(email, eventName) {
  if (!email || typeof email !== 'string' || !email.includes('@')) {
    return { success: false, error: "Invalid email" };
  }
  email = email.toLowerCase().trim();
  eventName = eventName || "Unknown Event";

  var ss;
  try {
    ss = SpreadsheetApp.openById(SHEET_ID);
  } catch (err) {
    return { success: false, error: "Error opening Spreadsheet. Check SHEET_ID in Code.gs" };
  }

  // Initialize sheets if needed
  if (!ss.getSheetByName('events')) {
    initializeSheets(ss);
  }

  var referralsSheet = ss.getSheetByName('referrals');
  var data = referralsSheet.getDataRange().getValues();

  // Check if user already has a link for this event
  for (var i = 1; i < data.length; i++) {
    if (data[i][0].toString().toLowerCase() === email && data[i][1] === eventName) {
      return {
        success: true,
        link: data[i][2], // bitly_link column
        message: "Welcome back! Here is your existing referral link for this event."
      };
    }
  }

  // Look up the event URL
  var eventUrl = "https://gdg.community.dev/"; // fallback
  var eventsSheet = ss.getSheetByName('events');
  if (eventsSheet) {
    var eventData = eventsSheet.getDataRange().getValues();
    for (var j = 1; j < eventData.length; j++) {
      if (eventData[j][0] === eventName) {
        eventUrl = eventData[j][1];
        break;
      }
    }
  }

  // Create a unique Bitly link for this referrer + event
  var bitlyLink;
  try {
    var title = 'GDG Referral | ' + eventName + ' | ' + email;
    bitlyLink = createBitlyLink_(eventUrl, title);
  } catch (err) {
    return { success: false, error: "Failed to create short link: " + err.message };
  }

  // Store in sheet
  referralsSheet.appendRow([email, eventName, bitlyLink, new Date()]);

  return {
    success: true,
    link: bitlyLink,
    message: "Referral link generated successfully!"
  };
}

// ---------------------------------------------------------------------------
// Utility: retrieve Bitly group GUID (run manually if needed)
// ---------------------------------------------------------------------------

function listBitlyGroups() {
  var result = callBitlyApi_('/v4/groups', 'get');
  Logger.log('Bitly Groups: ' + JSON.stringify(result, null, 2));
  return result;
}
