// CCDEW Background — deschide dashboard-ul la startup Betterbird
// și gestionează deep-link către email-uri specifice
(function() {
  var DASHBOARD_URL = 'http://localhost:8766/';

  // Deschide dashboardul ca tab in Betterbird; daca exista deja, doar il focuseaza.
  function openDashboard() {
    return browser.tabs.query({}).then(function(tabs) {
      var existing = tabs.find(function(t) {
        return t.url && t.url.indexOf('localhost:8766') !== -1;
      });
      if (existing) {
        return browser.tabs.update(existing.id, { active: true });
      }
      return browser.tabs.create({ url: DASHBOARD_URL, active: true, index: 0 });
    });
  }

  // Click pe butonul din toolbar → deschide/focuseaza dashboardul (in Betterbird, nu in browser)
  browser.browserAction.onClicked.addListener(openDashboard);

  // La pornirea Betterbird, deschide tab-ul CCDEW
  browser.runtime.onStartup.addListener(openDashboard);

  // Si cand extensia e instalata/reincarcata
  browser.runtime.onInstalled.addListener(openDashboard);

  // Handler pentru mesaje din sidebar — deschide email direct
  browser.runtime.onMessage.addListener(function(request, sender, sendResponse) {
    if (request.action === 'openEmail') {
      openEmailBySubject(request.subject, request.fromAddr, request.date)
        .then(function(result) {
          sendResponse({success: true, result: result});
        })
        .catch(function(err) {
          sendResponse({success: false, error: err.message || String(err)});
        });
      return true; // async response
    }
    if (request.action === 'getAccounts') {
      browser.accounts.list().then(function(accts) {
        sendResponse({success: true, accounts: accts.map(function(a){ return a.name; })});
      }).catch(function(e){ sendResponse({success: false, error: String(e)}); });
      return true;
    }
  });

  // Funcție de căutare și deschidere email după subject
  async function openEmailBySubject(subject, fromAddr, date) {
    // Normalizează subject pentru căutare (elimină Re:/Fwd:)
    var searchSubject = subject.replace(/^(Re:|Fwd:|FW:)\s*/i, '').trim();

    // Ia toate conturile
    var accounts = await browser.accounts.list();
    var allFolders = [];
    for (var acct of accounts) {
      if (acct.folders) {
        for (var folder of acct.folders) {
          allFolders.push(folder);
        }
      }
    }

    // Caută în fiecare folder (prioritate: Inbox, Sent, Archive)
    var priorityOrder = function(name) {
      var n = name.toLowerCase();
      if (n.indexOf('inbox') !== -1) return 0;
      if (n.indexOf('sent') !== -1) return 1;
      if (n.indexOf('archive') !== -1) return 2;
      return 3;
    };
    allFolders.sort(function(a,b){ return priorityOrder(a.name) - priorityOrder(b.name); });

    for (var folder of allFolders) {
      try {
        var page = await browser.messages.query({
          folder: folder,
          subject: searchSubject
        });
        // Filtrează după from și date pentru acuratețe
        var matches = page.messages.filter(function(msg){
          var subjMatch = msg.subject && msg.subject.replace(/^(Re:|Fwd:|FW:)\s*/i,'').trim() === searchSubject;
          var fromMatch = !fromAddr || (msg.author && msg.author.toLowerCase().indexOf(fromAddr.toLowerCase()) !== -1);
          return subjMatch && fromMatch;
        });

        if (matches.length > 0) {
          // Deschide primul match într-un tab nou
          await browser.messageDisplay.open({
            messageId: matches[0].id,
            active: true
          });
          return {opened: true, folder: folder.name, subject: matches[0].subject};
        }
      } catch (e) {
        // Folder fără suport pentru query, continuă
      }
    }

    // Fallback: deschide Betterbird search
    return {opened: false, message: 'Email not found locally. Open search.'};
  }
})();
