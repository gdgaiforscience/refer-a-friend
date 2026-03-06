var SHEET_ID = "YOUR_GOOGLE_SHEET_ID_HERE";

function doGet(e) {
  // If ?ref=XYZ is in the URL, track click and redirect
  if (e.parameter.ref) {
    return trackClickAndRedirect(e.parameter.ref);
  }
  
  // Otherwise, serve the UI
  return HtmlService.createHtmlOutputFromFile('Index')
    .setTitle('GDG Referral Tracker')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

function initializeSheets(ss) {
  // Create events sheet to control the active events dynamically
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
    referralsSheet.appendRow(['email', 'event_path', 'referral_code', 'created_at']);
    referralsSheet.setFrozenRows(1);
  }
  
  var clicksSheet = ss.getSheetByName('clicks');
  if (!clicksSheet) {
    clicksSheet = ss.insertSheet('clicks');
    clicksSheet.appendRow(['referral_code', 'clicked_at', 'event_name']);
    clicksSheet.setFrozenRows(1);
  }
}

function getEvents() {
  var ss;
  try {
    ss = SpreadsheetApp.openById(SHEET_ID);
  } catch(err) {
    return [];
  }
  
  var sheet = ss.getSheetByName('events');
  if (!sheet) return [];
  
  var data = sheet.getDataRange().getValues();
  var events = [];
  // Skip header row
  for (var i = 1; i < data.length; i++) {
    if (data[i][0]) { // Ensure event name isn't empty
      events.push({
        name: data[i][0],
        url: data[i][1]
      });
    }
  }
  return events;
}

function generateReferral(email, eventName) {
  if (!email || typeof email !== 'string' || !email.includes('@')) {
    return { success: false, error: "Invalid email" };
  }
  email = email.toLowerCase().trim();
  eventName = eventName || "Unknown Event";

  var ss;
  try {
    ss = SpreadsheetApp.openById(SHEET_ID);
  } catch(err) {
    return { success: false, error: "Error opening Spreadsheet. Check SHEET_ID in Code.gs" };
  }
  
  // Initialize sheets if they don't exist
  if (!ss.getSheetByName('events')) {
    initializeSheets(ss);
  }
  
  var referralsSheet = ss.getSheetByName('referrals');
  var data = referralsSheet.getDataRange().getValues();
  
  // Check if user already exists FOR THIS EVENT
  for (var i = 1; i < data.length; i++) {
    if (data[i][0].toLowerCase() === email && data[i][1] === eventName) {
      return { 
        success: true, 
        code: data[i][2], // Index 2 is referral_code
        message: "Welcome back! Here is your existing tracker for this event."
      };
    }
  }
  
  // Generate new code for new user/event combo
  var code = Math.random().toString(36).substring(2, 8).toUpperCase();
  var timestamp = new Date();
  
  referralsSheet.appendRow([email, eventName, code, timestamp]);
  
  return { 
    success: true, 
    code: code,
    message: "Tracker generated successfully!"
  };
}

function trackClickAndRedirect(code) {
  var ss;
  try {
    ss = SpreadsheetApp.openById(SHEET_ID);
  } catch(err) {
    return HtmlService.createHtmlOutput("Error: Could not open tracker database.");
  }
  
  if (!ss.getSheetByName('events')) {
    initializeSheets(ss);
  }
  
  var referralsSheet = ss.getSheetByName('referrals');
  var eventsSheet = ss.getSheetByName('events');
  var clicksSheet = ss.getSheetByName('clicks');
  
  var activeEventName = "Unknown Event";
  var activeEventUrl = "https://gdg.community.dev/"; // Fallback
  
  // 1. Find which event this code belongs to
  if (referralsSheet) {
    var refData = referralsSheet.getDataRange().getValues();
    for (var i = 1; i < refData.length; i++) {
      if (refData[i][2] === code) {
        activeEventName = refData[i][1];
        break;
      }
    }
  }
  
  // 2. Find the URL for that event
  if (eventsSheet && activeEventName !== "Unknown Event") { // only look if we found an event name
      var eventData = eventsSheet.getDataRange().getValues();
      for (var j = 1; j < eventData.length; j++) {
          if (eventData[j][0] === activeEventName) {
              activeEventUrl = eventData[j][1];
              break;
          }
      }
  }
  
  // Log the click with the name of the current event
  clicksSheet.appendRow([code, new Date(), activeEventName]);

  // Perform redirect using JavaScript to escape the Apps Script iframe
  var html = `
    <!DOCTYPE html>
    <html>
      <head>
        <title>Redirecting...</title>
        <script>
          window.top.location.href = "${activeEventUrl}";
        </script>
      </head>
      <body>
        <p>Redirecting to event page...</p>
        <p>If you are not redirected automatically, <a href="${activeEventUrl}">click here</a>.</p>
      </body>
    </html>
  `;
  return HtmlService.createHtmlOutput(html);
}

function getScriptUrl() {
  return ScriptApp.getService().getUrl();
}
