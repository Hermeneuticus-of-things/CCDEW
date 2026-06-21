// CCDEW Background v4.2 — pre-fetch + storage.local + badge + auto-refresh on new mail
(function() {
  var SERVER = 'http://127.0.0.1:8766';
  var FALLBACK = 'http://localhost:8766';
  var STORAGE_KEY = 'ccdew_alerts';
  var REFRESH_MS = 2 * 60 * 1000;  // 2 minute (polling de bază)
  var newMailTimer = null;           // debounce la email nou

  function bgFetch(path) {
    function tryUrl(url) {
      return fetch(url + path, {cache: 'no-cache'})
        .then(function(r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); });
    }
    return tryUrl(SERVER + path).catch(function() { return tryUrl(FALLBACK + path); });
  }

  function updateBadge(count, ok) {
    try {
      if (ok && count > 0) {
        browser.browserAction.setBadgeText({text: String(count)});
        browser.browserAction.setBadgeBackgroundColor({color: '#238636'});
        browser.browserAction.setTitle({title: '📧 Email Intelligence — ' + count + ' alerte'});
      } else if (!ok) {
        browser.browserAction.setBadgeText({text: '!'});
        browser.browserAction.setBadgeBackgroundColor({color: '#da3633'});
        browser.browserAction.setTitle({title: '📧 Email Intelligence — server offline'});
      } else {
        browser.browserAction.setBadgeText({text: ''});
        browser.browserAction.setTitle({title: '📧 Email Intelligence'});
      }
    } catch(e) {}
  }

  // Notificare desktop pentru emailuri urgente noi
  function notifyUrgent(newAlerts) {
    try {
      var urgent = newAlerts.filter(function(a) {
        return a.urgency === 'immediate' || a.urgency === 'today';
      });
      if (urgent.length === 0) return;
      var first = urgent[0];
      browser.notifications.create('ccdew-new-' + Date.now(), {
        type: 'basic',
        iconUrl: 'icons/ccdew-48.png',
        title: '📧 CCDEW — ' + urgent.length + ' alertă' + (urgent.length > 1 ? ' urgente noi' : ' urgentă nouă'),
        message: (first.nature_label || first.nature || '') + ': ' + (first.subject || '').substring(0, 60)
      }).catch(function(){});
    } catch(e) {}
  }

  var lastAlertCount = 0;
  var lastAlertIds = new Set();

  function refreshAlerts(fromNewMail) {
    bgFetch('/api/impact-alerts?v=' + Date.now())
      .then(function(data) {
        var alerts = data.alerts || [];

        // Detectează alerte noi față de ultima verificare
        if (fromNewMail && lastAlertIds.size > 0) {
          var newAlerts = alerts.filter(function(a) {
            var id = (a.subject || '') + '|' + (a.from || '') + '|' + (a.date || '');
            return !lastAlertIds.has(id);
          });
          if (newAlerts.length > 0) notifyUrgent(newAlerts);
        }

        // Salvează ID-urile curente
        lastAlertIds = new Set(alerts.map(function(a) {
          return (a.subject || '') + '|' + (a.from || '') + '|' + (a.date || '');
        }));
        lastAlertCount = alerts.length;

        browser.storage.local.set({
          [STORAGE_KEY]: { data: data, ts: Date.now(), ok: true }
        });
        updateBadge(alerts.length, true);

        // Daily digest — o singură dată pe zi la primul refresh
        var TODAY_KEY = 'ccdew_digest_' + new Date().toDateString();
        browser.storage.local.get(TODAY_KEY).then(function(r){
          if(!r[TODAY_KEY]){
            var urgent = alerts.filter(function(a){ return a.urgency==='immediate'||a.urgency==='today' })
            var week   = alerts.filter(function(a){ return a.urgency==='this_week' })
            var month  = alerts.filter(function(a){ return a.urgency==='this_month' })
            var msg = urgent.length+' urgente · '+week.length+' săpt · '+month.length+' lună'
            browser.notifications.create('ccdew-digest-'+Date.now(),{
              type:'basic',
              iconUrl:'icons/ccdew-48.png',
              title:'📧 CCDEW — Digest zilnic ('+alerts.length+' alerte)',
              message: msg
            }).catch(function(){})
            var obj={}; obj[TODAY_KEY]=true
            browser.storage.local.set(obj)
          }
        }).catch(function(){})
      })
      .catch(function(e) {
        browser.storage.local.set({
          [STORAGE_KEY]: { data: null, ts: Date.now(), ok: false, error: String(e) }
        });
        updateBadge(0, false);
      });
  }

  // ── Auto-refresh când BB primește email nou ──────────────────────────────
  try {
    browser.messages.onNewMailReceived.addListener(function(folder, messagelist) {
      // Debounce: dacă vin mai multe emailuri rapid, așteptăm 10s și facem un singur refresh
      if (newMailTimer) clearTimeout(newMailTimer);
      newMailTimer = setTimeout(function() {
        newMailTimer = null;
        // Badge pulsează temporar la "!" pentru a semnala activitate
        try {
          browser.browserAction.setBadgeText({text: '↺'});
          browser.browserAction.setBadgeBackgroundColor({color: '#8b949e'});
        } catch(e) {}
        // Așteptăm 15s ca serverul să proceseze noul email, apoi refresh
        setTimeout(function() { refreshAlerts(true); }, 15000);
      }, 10000); // debounce 10s
    });
  } catch(e) {
    // browser.messages.onNewMailReceived poate să nu fie disponibil în toate versiunile
  }

  // Handler mesaje din popup
  browser.runtime.onMessage.addListener(function(request, sender, sendResponse) {
    if (request.action === 'fetchAlerts') {
      bgFetch('/api/impact-alerts?v=' + Date.now())
        .then(function(data) { sendResponse({success: true, data: data}); })
        .catch(function(e) { sendResponse({success: false, error: String(e)}); });
      return true;
    }
    if (request.action === 'getStoredAlerts') {
      browser.storage.local.get(STORAGE_KEY).then(function(res) {
        sendResponse(res[STORAGE_KEY] || {ok: false, error: 'no data'});
      });
      return true;
    }
    if (request.action === 'refreshAlerts') {
      refreshAlerts(false);
      sendResponse({ok: true});
    }
    if (request.action === 'bgPost') {
      fetch(SERVER + request.path, {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(request.body)
      }).then(function() { sendResponse({success: true}); })
        .catch(function(e) { sendResponse({success: false, error: String(e)}); });
      return true;
    }
    if (request.action === 'openEmail') {
      openEmailBySubject(request.subject, request.fromAddr, request.date)
        .then(function(r) { sendResponse({success: true, result: r}); })
        .catch(function(e) { sendResponse({success: false, error: String(e)}); });
      return true;
    }
    if (request.action === 'matchAlert') {
      // Find alert matching the currently displayed email
      browser.storage.local.get('ccdew_alerts').then(function(res) {
        var stored = res['ccdew_alerts'];
        if (!stored || !stored.ok || !stored.data) {
          sendResponse({alert: null});
          return;
        }
        var alerts = stored.data.alerts || [];
        var subj = (request.subject || '').replace(/^(Re:|Fwd:|FW:)\s*/i, '').trim().toLowerCase();
        var from = (request.fromAddr || '').toLowerCase();
        var match = null;
        for (var i = 0; i < alerts.length; i++) {
          var a = alerts[i];
          var aSubj = (a.subject || '').replace(/^(Re:|Fwd:|FW:)\s*/i, '').trim().toLowerCase();
          var aFrom = (a.from || '').toLowerCase();
          if (aSubj === subj && (!from || aFrom.indexOf(from) !== -1 || from.indexOf(aFrom) !== -1)) {
            match = a;
            break;
          }
        }
        // Fuzzy fallback: subject contains
        if (!match) {
          for (var j = 0; j < alerts.length; j++) {
            var b = alerts[j];
            var bSubj = (b.subject || '').replace(/^(Re:|Fwd:|FW:)\s*/i, '').trim().toLowerCase();
            if (subj.length > 5 && (bSubj.indexOf(subj) !== -1 || subj.indexOf(bSubj) !== -1)) {
              match = b;
              break;
            }
          }
        }
        sendResponse({alert: match});
      }).catch(function() { sendResponse({alert: null}); });
      return true;
    }
  });

  // Auto-arhivare: curăță snoozed expirate o dată pe oră
  function cleanupOldDismissed(){
    browser.storage.local.get(['ccdew_dismissed','ccdew_snoozed']).then(function(r){
      // Curăță snoozed expirate
      var sn=r.ccdew_snoozed||{}
      var now=Date.now()
      Object.keys(sn).forEach(function(k){ if(sn[k]<now) delete sn[k] })
      browser.storage.local.set({ccdew_snoozed:sn})
    }).catch(function(){})
  }
  setInterval(cleanupOldDismissed, 60*60*1000) // la fiecare oră

  // Pre-fetch la startup + refresh periodic (2 min)
  browser.runtime.onStartup.addListener(refreshAlerts);
  browser.runtime.onInstalled.addListener(refreshAlerts);
  refreshAlerts(false); // imediat la încărcare
  setInterval(function() { refreshAlerts(false); }, REFRESH_MS);

  // Deschide email din BetterBird
  async function openEmailBySubject(subject, fromAddr, date) {
    var searchSubject = subject.replace(/^(Re:|Fwd:|FW:)\s*/i, '').trim();
    var accounts = await browser.accounts.list();
    var allFolders = [];
    function collectFolders(folders) {
      for (var f of (folders || [])) {
        var n = (f.name || '').toLowerCase();
        if (['spam','junk','trash','deleted','bulk mail','outbox','drafts'].includes(n)) continue;
        allFolders.push(f);
        if (f.subFolders && f.subFolders.length) collectFolders(f.subFolders);
      }
    }
    for (var acct of accounts) collectFolders(acct.folders);
    allFolders.sort(function(a,b){
      var p = function(n){ n=(n||'').toLowerCase(); return n.includes('inbox')?0:n.includes('sent')?1:n.includes('archive')?2:3; };
      return p(a.name)-p(b.name);
    });
    for (var folder of allFolders) {
      try {
        var page = await browser.messages.query({folder: folder, subject: searchSubject});
        var matches = page.messages.filter(function(msg){
          return msg.subject && msg.subject.replace(/^(Re:|Fwd:|FW:)\s*/i,'').trim() === searchSubject &&
                 (!fromAddr || (msg.author && msg.author.toLowerCase().includes(fromAddr.toLowerCase())));
        });
        if (matches.length > 0) {
          await browser.messageDisplay.open({messageId: matches[0].id, active: true});
          return {opened: true, folder: folder.name};
        }
      } catch(e) {}
    }
    return {opened: false};
  }
  // Context menu on messages
  try {
    browser.menus.create({
      id: 'ccdew-check',
      title: '🔍 CCDEW — Verifică alerta',
      contexts: ['message_list']
    });
    browser.menus.onClicked.addListener(function(info, tab) {
      if (info.menuItemId === 'ccdew-check') {
        browser.browserAction.openPopup().catch(function(){});
      }
    });
  } catch(e) {}
})();
