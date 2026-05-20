const fs = require('fs');
const path = require('path');

const HERMES_SESSIONS = path.join(process.env.HOME, '.hermes/sessions');
const HERMES_STATE = path.join(process.env.HOME, '.hermes/state.db');
const CCDEW_MEMORY = path.join(__dirname, '../../_MEMORY/hermes-sync');
const CCDEW_CONTEXT = path.join(__dirname, '../../_MEMORY/hermes-context.json');

function ensureDir(dir) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

function syncHermesToCCDEW() {
  if (!fs.existsSync(HERMES_SESSIONS)) return [];
  
  const files = fs.readdirSync(HERMES_SESSIONS).filter(f => f.endsWith('.json'));
  const sessions = [];
  
  ensureDir(CCDEW_MEMORY);
  
  files.forEach(file => {
    const content = JSON.parse(fs.readFileSync(path.join(HERMES_SESSIONS, file), 'utf-8'));
    const dest = path.join(CCDEW_MEMORY, file);
    if (!fs.existsSync(dest)) {
      fs.writeFileSync(dest, JSON.stringify(content, null, 2));
      console.log(`[hermes-sync] Copiat: ${file}`);
    }
    sessions.push({ file, ...content });
  });
  
  return sessions;
}

function syncCCDEWToHermes() {
  const ccedwPrinciples = path.join(__dirname, '../../_MEMORY/semantic/principles.json');
  const hermesContext = path.join(process.env.HOME, '.hermes/context_from_ccdew.json');
  
  if (fs.existsSync(ccedwPrinciples)) {
    const principles = JSON.parse(fs.readFileSync(ccedwPrinciples, 'utf-8'));
    fs.writeFileSync(hermesContext, JSON.stringify(principles, null, 2));
    console.log(`[hermes-sync] Principii CCDEW → Hermes: ${hermesContext}`);
    return principles;
  }
  return null;
}

function extractConversations() {
  try {
    const content = fs.readFileSync(HERMES_STATE, 'utf-8');
    const conversations = [];
    const platforms = ['telegram', 'discord', 'slack'];
    
    platforms.forEach(platform => {
      const regex = new RegExp(`"${platform}"[^{]*{[^}]*"id":"([^"]+)"[^}]*"name":"([^"]+)"`, 'gi');
      let match;
      while ((match = regex.exec(content)) !== null) {
        conversations.push({
          platform,
          id: match[1],
          name: match[2]
        });
      }
    });
    
    return conversations;
  } catch (e) {
    return [];
  }
}

function syncToCCDEWContext() {
  const hermesConversations = extractConversations();
  const ccedwPrinciples = path.join(__dirname, '../../_MEMORY/semantic/principles.json');
  
  let principles = {};
  if (fs.existsSync(ccedwPrinciples)) {
    principles = JSON.parse(fs.readFileSync(ccedwPrinciples, 'utf-8'));
  }
  
  const context = {
    lastSync: new Date().toISOString(),
    hermesConversations,
    ccedwPrinciples: principles,
    source: 'hermes-sync bidirectional'
  };
  
  fs.writeFileSync(CCDEW_CONTEXT, JSON.stringify(context, null, 2));
  console.log(`[hermes-sync] CCDEW context actualizat: ${CCDEW_CONTEXT}`);
  return context;
}

function status() {
  const hermesCount = fs.existsSync(HERMES_SESSIONS) 
    ? fs.readdirSync(HERMES_SESSIONS).filter(f => f.endsWith('.json')).length 
    : 0;
  const ccedwCount = fs.existsSync(CCDEW_MEMORY)
    ? fs.readdirSync(CCDEW_MEMORY).filter(f => f.endsWith('.json')).length
    : 0;
  
  return { hermesSessions: hermesCount, ccedwSynced: ccedwCount };
}

function syncBidirectional() {
  console.log('=== Sincronizare Bidirecțională ===');
  console.log('1. Hermes → CCDEW');
  syncHermesToCCDEW();
  console.log('2. CCDEW → Hermes');
  syncCCDEWToHermes();
  console.log('3. Export context pentru CCDEW');
  syncToCCDEWContext();
  console.log('✅ Sincronizare completă!');
}

if (require.main === module) {
  const cmd = process.argv[2] || 'status';
  
  switch(cmd) {
    case 'sync-to-ccdew':
      console.log('=== Sincronizare Hermes → CCDEW ===');
      syncHermesToCCDEW();
      syncToCCDEWContext();
      break;
    case 'sync-to-hermes':
      console.log('=== Sincronizare CCDEW → Hermes ===');
      syncCCDEWToHermes();
      break;
    case 'sync':
    case 'bidirectional':
      syncBidirectional();
      break;
    case 'status':
    default:
      const s = status();
      console.log(`Hermes sesiuni: ${s.hermesSessions}`);
      console.log(`CCDEW sincronizate: ${s.ccedwSynced}`);
      if (fs.existsSync(CCDEW_CONTEXT)) {
        const ctx = JSON.parse(fs.readFileSync(CCDEW_CONTEXT, 'utf-8'));
        console.log(`Conversații Hermes: ${ctx.hermesConversations?.length || 0}`);
      }
  }
}

module.exports = { syncHermesToCCDEW, syncCCDEWToHermes, status };