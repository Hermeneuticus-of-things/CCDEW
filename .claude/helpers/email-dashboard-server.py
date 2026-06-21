#!/usr/bin/env python3
"""Email Dashboard Server v2 — WebSocket + live push + doar acțiuni."""
import json, os, sys, http.server, urllib.parse, time, re, threading, queue
import mailbox, email.utils, email.header

MEMORY = os.path.expanduser('~/CCDEW/_MEMORY')
PREFILTER = os.path.expanduser('~/.local/state/ccdew-email-prefilter.json')
ALERTS_FILE = os.path.expanduser('~/.local/state/ccdew-impact-alerts.json')
ACCOUNTS_REGISTRY = os.path.expanduser('~/CCDEW/_MEMORY/email-accounts-registry.json')

def _build_account_map():
    """Mapare 'Gmail' / 'Gmail 1' / 'GMX' / 'imap.gmail-1.com' → adresa reală.

    BetterBird numește conturile după provider:
      primul cont Gmail  → 'Gmail'
      al doilea          → 'Gmail 1'
      al treilea         → 'Gmail 2'  etc.
      primul cont GMX    → 'GMX'  (sau 'Gmx')
      al doilea GMX      → 'GMX 1' etc.
    """
    m = {}
    try:
        reg = json.load(open(ACCOUNTS_REGISTRY, encoding='utf-8'))
        accounts = reg.get('accounts', [])
        # grupăm după provider pentru a calcula indexul per provider
        from collections import defaultdict
        provider_idx = defaultdict(int)
        for a in accounts:
            email = a.get('email', '')
            cache_dir = a.get('cache_dir', '')
            provider = (a.get('provider') or '').lower()
            if not email:
                continue
            # mapare după cache_dir exact (fallback intern)
            if cache_dir:
                m[cache_dir] = email
            # mapare după numele BetterBird
            # provider label cu majusculă: gmail→Gmail, gmx→GMX, proton→Proton etc.
            label = {'gmail': 'Gmail', 'gmx': 'GMX', 'proton': 'Proton',
                     'outlook': 'Outlook', 'yahoo': 'Yahoo',
                     'icloud': 'iCloud'}.get(provider, provider.capitalize())
            idx = provider_idx[provider]
            if idx == 0:
                m[label] = email          # ex: 'Gmail' → primul cont Gmail
            else:
                m[f'{label} {idx}'] = email   # ex: 'Gmail 1', 'Gmail 2' ...
            # și variante cu majuscule diferite
            m[label.lower()] = m.get(label.lower(), email)
            m[label.upper()] = m.get(label.upper(), email)
            provider_idx[provider] += 1
    except Exception:
        pass
    return m

_ACCOUNT_MAP = _build_account_map()

def resolve_account(raw_account):
    """Înlocuiește 'Gmail N' sau 'imap.gmail-N.com' cu adresa reală."""
    if not raw_account:
        return raw_account
    resolved = _ACCOUNT_MAP.get(raw_account)
    if resolved:
        return resolved
    # fallback: caută parțial (ex: 'gmail-1' în cheie)
    lower = raw_account.lower()
    for k, v in _ACCOUNT_MAP.items():
        if k.lower() in lower or lower in k.lower():
            return v
    return raw_account

MBOX_DAEMON_CONFIG = os.path.expanduser('~/.local/state/ccdew-mbox-daemon.json')

_SKIP_FOLDERS = {'drafts', 'trash', 'sent', 'spam', 'brouillons', 'corbeille', 'junk', 'outbox'}

def _get_text_snippet(msg, max_len=150):
    """Extrage primul fragment text/plain din mesaj."""
    try:
        if msg.is_multipart():
            for part in msg.walk():
                try:
                    if part.get_content_type() == 'text/plain':
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or 'utf-8'
                            text = payload.decode(charset, errors='replace')
                            return text.strip()[:max_len]
                except Exception:
                    continue
        else:
            if msg.get_content_type() == 'text/plain':
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or 'utf-8'
                    text = payload.decode(charset, errors='replace')
                    return text.strip()[:max_len]
    except Exception:
        pass
    return ''

def _parse_date_iso(date_str):
    """Parses email date header to ISO string; fallback to original string."""
    if not date_str:
        return ''
    try:
        dt = email.utils.parsedate_to_datetime(date_str)
        return dt.isoformat()
    except Exception:
        return str(date_str)

def _resolve_path_to_account(mbox_path):
    """Derivă adresa de email din calea mbox folosind _ACCOUNT_MAP."""
    # Încearcă să găsească un fragment din cale care corespunde unui cont cunoscut
    for key, email_addr in _ACCOUNT_MAP.items():
        if key and key in mbox_path:
            return email_addr
    # Fallback: caută imap.* în cale
    import re as _re
    m = _re.search(r'imap[._-][a-zA-Z0-9._-]+', mbox_path)
    if m:
        fragment = m.group(0)
        resolved = resolve_account(fragment)
        if resolved != fragment:
            return resolved
    return ''

_inbox_cache = {'data': None, 'ts': 0}
_INBOX_CACHE_TTL = 300  # 5 minute — mai rar = mai puțin RAM

def load_inbox_emails(max_per_folder=10):  # redus de la 20 → 10 per folder
    """Citește emailurile INBOX din fișierele mbox configurate în daemon. Cache 60s."""
    global _inbox_cache
    if _inbox_cache['data'] is not None and (time.time() - _inbox_cache['ts']) < _INBOX_CACHE_TTL:
        return _inbox_cache['data']
    emails = []
    try:
        with open(MBOX_DAEMON_CONFIG, encoding='utf-8') as f:
            daemon_cfg = json.load(f)
    except Exception:
        return emails

    # daemon_cfg e un dict {path: timestamp} — extragem cheile
    if isinstance(daemon_cfg, dict):
        mbox_paths = list(daemon_cfg.keys())
    else:
        mbox_paths = daemon_cfg.get('mbox_paths', []) or daemon_cfg.get('paths', [])

    for mbox_path in mbox_paths:
        try:
            # Filtrează foldere excluse
            folder_lower = os.path.basename(mbox_path).lower()
            if any(skip in folder_lower for skip in _SKIP_FOLDERS):
                continue
            # Acceptă doar INBOX
            if 'inbox' not in folder_lower and 'inbox' not in mbox_path.lower():
                continue

            if not os.path.exists(mbox_path):
                continue

            folder_name = os.path.basename(mbox_path)
            account_addr = _resolve_path_to_account(mbox_path)

            try:
                mbox = mailbox.mbox(mbox_path, create=False)
            except Exception:
                continue

            try:
                all_msgs = []
                for idx, msg in enumerate(mbox):
                    try:
                        date_str = msg.get('Date', '')
                        date_iso = _parse_date_iso(date_str)
                        all_msgs.append((date_iso, idx, msg))
                    except Exception:
                        continue

                # Sortează descendent după dată, ia ultimele max_per_folder
                all_msgs.sort(key=lambda x: x[0], reverse=True)
                recent = all_msgs[:max_per_folder]

                for date_iso, msg_index, msg in recent:
                    try:
                        subject = ''
                        try:
                            raw_subj = msg.get('Subject', '')
                            if raw_subj:
                                decoded_parts = email.header.decode_header(raw_subj)
                                parts = []
                                for part, enc in decoded_parts:
                                    if isinstance(part, bytes):
                                        parts.append(part.decode(enc or 'utf-8', errors='replace'))
                                    else:
                                        parts.append(str(part))
                                subject = ''.join(parts)
                        except Exception:
                            subject = str(msg.get('Subject', ''))

                        from_addr = str(msg.get('From', ''))
                        snippet = _get_text_snippet(msg)

                        emails.append({
                            'subject': subject,
                            'from': from_addr,
                            'date': date_iso,
                            'snippet': snippet,
                            'account': account_addr,
                            'folder': folder_name,
                            'mbox_path': mbox_path,
                            'msg_index': msg_index,
                            'alert': None,
                        })
                    except Exception:
                        continue
            finally:
                try:
                    mbox.close()
                except Exception:
                    pass

        except Exception:
            continue

    # Sortare globală descendent după dată
    emails.sort(key=lambda e: e.get('date', ''), reverse=True)
    _inbox_cache['data'] = emails
    _inbox_cache['ts'] = time.time()
    return emails


def _normalize_subject(subject):
    """Normalizează subiectul pentru matching: elimină Re:/Fwd:, lowercase."""
    s = re.sub(r'^(re|fwd?|tr|aw)[\s:]+', '', subject.strip(), flags=re.IGNORECASE)
    s = re.sub(r'\s+', ' ', s).strip().lower()
    return s


def enrich_with_alerts(emails):
    """Adaugă câmpul 'alert' fiecărui email dacă există un alert matching."""
    try:
        with open(ALERTS_FILE, encoding='utf-8') as f:
            alerts_data = json.load(f)
        alerts = alerts_data.get('alerts', [])
    except Exception:
        return emails

    for email_entry in emails:
        try:
            email_subj_norm = _normalize_subject(email_entry.get('subject', ''))
            email_from = (email_entry.get('from', '') or '').lower()
            matched_alert = None
            for alert in alerts:
                try:
                    alert_subj_norm = _normalize_subject(alert.get('subject', ''))
                    alert_from = (alert.get('from', '') or alert.get('account', '') or '').lower()
                    # Match pe subiect normalizat
                    subj_match = (email_subj_norm and alert_subj_norm and
                                  (email_subj_norm == alert_subj_norm or
                                   email_subj_norm in alert_subj_norm or
                                   alert_subj_norm in email_subj_norm))
                    # Match parțial pe from/account
                    from_match = False
                    if alert_from and email_from:
                        from_match = alert_from in email_from or email_from in alert_from
                    if subj_match or from_match:
                        matched_alert = alert
                        break
                except Exception:
                    continue
            email_entry['alert'] = matched_alert
        except Exception:
            email_entry['alert'] = None
    return emails


PREFILTER_MAP = {}
PREFILTER_MTIME = 0
_INDEX_LOCK = threading.Lock()
_SSE_LOCK = threading.Lock()
MAX_POST_BODY = 65_536  # 64KB max pentru orice POST body
_STATIC_WRITE_TIME = 0
_STATIC_WRITE_TTL = 60  # scrie hermes-dashboard.html max o dată pe minut

def load_prefilter():
    global PREFILTER_MAP, PREFILTER_MTIME
    try:
        cur = os.path.getmtime(PREFILTER)
        if cur <= PREFILTER_MTIME: return
        with open(PREFILTER, encoding='utf-8') as f:
            data = json.load(f)
        mapping = {}
        for acct_name, acct_data in data.get('accounts', {}).items():
            for msg in acct_data.get('keep_list', []):
                ref = f"{acct_name}-{msg.get('id','?')}".lower()
                mapping[ref] = {
                    'subject': msg.get('subject', ''),
                    'from': msg.get('from', ''),
                    'date': msg.get('date', ''),
                }
        PREFILTER_MAP = mapping
        PREFILTER_MTIME = cur
    except Exception as e:
        pass

load_prefilter()

LIVE_EVENTS = queue.Queue()

NATURE_PRIORITY = {
    'security': 1, 'financial': 2, 'legal': 3,
    'medical': 4, 'health': 5, 'account': 6,
    'personal': 7, 'administrative': 8, 'technical': 9,
    'business': 10, 'other': 99
}

URGENCY_ORDER = ['immediate', 'today', 'this_week', 'this_month', 'no_deadline']

def _age_days(entry):
    """Vârsta emailului în zile față de azi.
    Suportă: ISO ('2026-05-12'), RFC 2822 ('Tue, 12 May 2026 15:24:49 GMT'),
             timestamp Unix seconds (int/float).
    """
    import datetime as _dt, calendar as _cal
    from email.utils import parsedate as _pd

    d = entry.get('date') or entry.get('email_date') or ''
    if d:
        # Format ISO: '2026-05-12' sau '2026-05-12T...'
        try:
            age = (_dt.date.today() - _dt.datetime.strptime(str(d)[:10], '%Y-%m-%d').date()).days
            return max(0, age)
        except Exception:
            pass
        # Format RFC 2822: 'Tue, 12 May 2026 15:24:49 GMT'
        try:
            t = _pd(str(d))
            if t:
                ts = _cal.timegm(t)
                age = int((time.time() - ts) / 86400)
                return max(0, age)
        except Exception:
            pass
        # Format timestamp numeric în câmpul date
        try:
            ts = float(d)
            if ts > 1e9:  # Unix seconds
                age = int((time.time() - ts) / 86400)
                return max(0, age)
        except Exception:
            pass

    # Fallback: timestamp Unix seconds din câmpul 'timestamp'
    ts_field = entry.get('timestamp', 0)
    if ts_field and isinstance(ts_field, (int, float)) and ts_field > 1e9:
        age = int((time.time() - ts_field) / 86400)
        return max(0, age)

    # Fallback final: createdAt (ms)
    created = entry.get('createdAt', 0)
    if created:
        age = int((time.time()*1000 - created) / 86400000)
        return max(0, age)

    return None

def effective_urgency(entry):
    """Urgență calculată DINAMIC pe baza vârstei reale a emailului azi.

    Logica: vârsta emailului dictează maximul posibil, importanța (nature)
    poate păstra emailul vizibil mai mult, dar nu poate face un email vechi "azi".

    AZI (today)        = email primit AZI sau IERI (max 1 zi)
    SĂPTĂMÂNĂ          = email primit în ultimele 7 zile
    LUNA ASTA          = email primit în ultimele 30 zile
    no_deadline (INFO) = email mai vechi de 30 zile
    """
    nature = entry.get('nature', '')
    base   = entry.get('urgency', 'no_deadline')
    CRITICAL = ('security', 'financial', 'legal', 'phishing')

    age = _age_days(entry)

    # Dacă nu avem dată → folosim urgency original (nu putem calcula)
    if age is None:
        return base

    # ── Plafon temporal absolut ──────────────────────────────────────────
    if age > 90:
        return 'no_deadline'

    # ── AZI: NUMAI emailuri din ultimele 24h ─────────────────────────────
    if age == 0:
        if nature in CRITICAL or base in ('immediate', 'today'):
            return 'today'
        return 'this_week'

    # ── IMEDIAT: doar emailuri recente (≤2 zile) și critice ─────────────
    if age <= 2 and nature in CRITICAL and base == 'immediate':
        return 'immediate'

    # ── Emailuri 1-7 zile ────────────────────────────────────────────────
    if age <= 7:
        if nature in CRITICAL:
            return 'today' if age <= 1 else 'this_week'
        return 'this_week'

    # ── Emailuri 7-30 zile → LUNA ASTA ──────────────────────────────────
    if age <= 30:
        if nature in CRITICAL:
            return 'this_week'   # critical rămân în SĂPT
        return 'this_month'      # restul → LUNA ASTA

    # Orice altceva mai vechi de 30 zile → INFO
    return 'no_deadline'

def is_actionable(entry):
    # Folosim eff_urgency (cu decay temporal) dacă e calculat, altfel urgency brut
    urgency = entry.get('eff_urgency') or entry.get('urgency', '')
    nature = entry.get('nature', '')
    return urgency in ('immediate', 'today') or (urgency == 'this_week' and nature in ('security', 'financial', 'legal', 'phishing'))

INDEX_CACHE = {}
INDEX_CACHE_TIME = 0
INDEX_CACHE_TTL = 300  # 5 min — loading 17k files e lent, nu reîncarca la fiecare 30s

def load_index(force=False):
    global INDEX_CACHE, INDEX_CACHE_TIME
    now = time.time()
    with _INDEX_LOCK:
        if not force and INDEX_CACHE and (now - INDEX_CACHE_TIME) < INDEX_CACHE_TTL:
            return list(INDEX_CACHE)  # returnăm copie pentru thread safety
    load_prefilter()
    index = []
    for layer, label in [('identity', 'L4'), ('semantic', 'L3')]:
        d = os.path.join(MEMORY, layer)
        if not os.path.isdir(d): continue
        for fn in os.listdir(d):
            if not fn.endswith('.json'): continue
            if not (fn.startswith('watch-') or fn.startswith('batch-') or fn.startswith('email-')): continue
            fp = os.path.join(d, fn)
            try:
                with open(fp, encoding='utf-8') as f:
                    data = json.load(f)
            except Exception:
                continue
            try:
                val = data.get('value', '')
                entry = {
                    'key': data.get('key', fn.replace('.json','')),
                    'layer': data.get('layer', label),
                    'createdAt': data.get('createdAt', 0),
                    'expiresAt': data.get('expiresAt', 0),
                    'source': data.get('source', ''),
                    'filename': fn,
                }
                email_ref = data.get('email_ref', '')
                if email_ref:
                    entry['email_ref'] = email_ref
                    pf = PREFILTER_MAP.get(email_ref.lower())
                    if pf:
                        entry['subject'] = pf['subject']
                        entry['from'] = pf['from']
                        entry['email_date'] = pf['date']
                if isinstance(val, str) and val.strip().startswith('{'):
                    try:
                        parsed = json.loads(val)
                        entry.update(parsed)
                        entry['value_raw'] = parsed
                    except json.JSONDecodeError:
                        entry['summary'] = val[:200]
                        parsed = {}
                elif isinstance(val, dict):
                    entry.update(val)
                    entry['value_raw'] = val
                    parsed = val
                else:
                    entry['summary'] = str(val)[:200]
                    parsed = {}
                # Completează subject/from din value_raw dacă lipsesc
                if not entry.get('subject') or entry.get('subject') == '?':
                    entry['subject'] = parsed.get('subject') or parsed.get('summary', '')[:80] or '(fără subiect)'
                if not entry.get('from') or entry.get('from') in ('?', '—', ''):
                    # încearcă: from > account > extras din summary
                    frm = parsed.get('from') or parsed.get('account', '')
                    if not frm:
                        # extrage "Cont: xxx@xxx" sau "contul xxx" din summary
                        import re as _re
                        m = _re.search(r'[Cc]ont[ul]*:?\s*([a-zA-Z0-9_.+\-]+@[a-zA-Z0-9_.+\-]+)', entry.get('subject',''))
                        frm = m.group(1) if m else ''
                    entry['from'] = frm or '—'
                if not entry.get('date'):
                    entry['date'] = parsed.get('date', '')
                entry['eff_urgency'] = effective_urgency(entry)
                entry['nature_priority'] = NATURE_PRIORITY.get(entry.get('nature', ''), 99)
                index.append(entry)
            except Exception:
                continue
    # Deduplicare pe (subject, from, date) — elimină duplicate exacte
    seen = set()
    deduped = []
    for e in index:
        sig = (e.get('subject','')[:60], e.get('from','')[:40], e.get('date','')[:10])
        if sig not in seen:
            seen.add(sig)
            deduped.append(e)
    index = deduped

    with _INDEX_LOCK:
        INDEX_CACHE = index
        INDEX_CACHE_TIME = now
    return index

def _calc_threat_score(alert):
    """Calculează threat score 1-4 pe baza urgency+nature+severity."""
    urgency_base = {'immediate':4,'today':3,'this_week':2,'this_month':1,'no_deadline':0.5}
    nat_mul = {'phishing':2.0,'account_security':1.8,'security':1.8,'financial':1.5,
               'legal':1.3,'medical':1.2,'subscription':0.8,'account':0.9,'general':0.7}
    sev_mul = {'high':1.5,'medium':1.0,'low':0.7,'critical':2.0}
    ub = urgency_base.get(alert.get('urgency',''), 1.0)
    nm = nat_mul.get(alert.get('nature',''), 1.0)
    sm = sev_mul.get(alert.get('severity',''), 1.0)
    raw = ub * nm * sm
    if raw >= 6: return 4
    if raw >= 3.5: return 3
    if raw >= 1.8: return 2
    return 1

def _gen_recommended_action(alert):
    """Generează o acțiune recomandată concretă bazată pe natura alertei."""
    nature = alert.get('nature', '')
    urgency = alert.get('urgency', '')
    subject = (alert.get('subject') or '').lower()
    hint = (alert.get('action_hint') or '').lower()
    from_addr = (alert.get('from') or '').lower()
    is_google = 'google' in from_addr or 'google' in hint or 'accounts.google' in from_addr

    # Securitate cont Google
    if nature in ('security', 'account_security') and is_google:
        if 'verification' in subject or 'verify' in subject:
            return 'Verifică dacă tu ai inițiat această acțiune. Dacă nu, schimbă parola imediat.'
        if '2-step' in subject or '2fa' in subject or 'two-step' in subject:
            return 'Confirmă că 2FA a fost activat de tine. Verifică sesiunile active pe myaccount.google.com/security'
        if 'security alert' in subject:
            return 'Deschide myaccount.google.com/security → verifică activitate recentă și dispozitive conectate.'
        if 'privacy' in subject:
            return 'Revizuiește setările de confidențialitate: myaccount.google.com/privacy'
        return 'Verifică activitatea contului pe myaccount.google.com/security'

    # Phishing / suspicious
    if nature == 'phishing':
        return 'NU da click pe linkuri. Marchează ca spam. Raportează phishing în clientul de email.'

    # Financial
    if nature == 'financial':
        if urgency in ('immediate', 'today'):
            return 'Verifică contul bancar direct (nu prin linkurile din email). Contactează banca dacă e suspect.'
        return 'Verifică direct pe site-ul oficial al băncii/serviciului.'

    # Legal
    if nature == 'legal':
        return 'Citește cu atenție termenul limită. Dacă e legal real, consultă un avocat sau răspunde în scris.'

    # Medical
    if nature == 'medical':
        return 'Confirmă programarea/informația direct cu furnizorul medical (telefon, nu email).'

    # Subscription / account changes
    if nature == 'subscription' or ('subscription' in subject):
        if urgency in ('immediate', 'today'):
            return 'Verifică dacă abonamentul este al tău. Dacă nu, anulează imediat de pe site-ul oficial.'
        return 'Notă pentru revizuire: verifică dacă mai ai nevoie de acest abonament.'

    # Account / verification codes
    if nature == 'account':
        if 'verification code' in subject or 'cod' in subject:
            return 'Cod de verificare primit — folosește-l în 10 minute sau ignoră dacă nu tu ai cerut.'
        if 'new account' in subject or 'cont nou' in hint:
            return 'Verifică că toate datele noului cont sunt corecte. Salvează credențialele în password manager.'
        if 'password' in subject or 'parola' in hint:
            return 'Schimbă parola dacă nu tu ai inițiat resetarea. Activează 2FA dacă nu e activat.'
        return 'Verifică activitatea contului și setările de securitate.'

    # Generic urgent
    if urgency == 'immediate':
        return 'Acțiune urgentă necesară — citește emailul complet și răspunde sau acționează azi.'
    if urgency == 'today':
        return 'Verifică și răspunde astăzi.'

    return 'Revizuiește emailul și decide dacă necesită acțiune.'

def build_api(index):
    accounts = set()
    natures = set()
    urgencies = set()
    for e in index:
        raw = e.get('value_raw', {})
        if isinstance(raw, dict):
            for a in raw.get('accounts', []):
                if isinstance(a, str) and len(a) > 2:
                    accounts.add(a.strip())
        if e.get('nature'): natures.add(e['nature'])
        if e.get('urgency'): urgencies.add(e['urgency'])
    natures = sorted(natures, key=lambda n: NATURE_PRIORITY.get(n, 99))
    urgencies = sorted(urgencies, key=lambda u: URGENCY_ORDER.index(u) if u in URGENCY_ORDER else 99)
    return {'total': len(index), 'accounts': sorted(accounts), 'natures': natures, 'urgencies': urgencies}

SSE_CLIENTS = []

def notify_sse_clients(data):
    msg = f"data: {json.dumps(data)}\n\n".encode()
    dead = []
    with _SSE_LOCK:
        clients = list(SSE_CLIENTS)
    for q in clients:
        try:
            q.put_nowait(msg)
        except Exception:
            dead.append(q)
    if dead:
        with _SSE_LOCK:
            for q in dead:
                try: SSE_CLIENTS.remove(q)
                except ValueError: pass

class SSEQueue:
    def __init__(self):
        self.q = queue.Queue()
    def get(self, timeout=1):
        try: return self.q.get(timeout=timeout)
        except queue.Empty: return None

def scapa_str(s):
    if s is None: return ''
    import html as _html
    return _html.escape(str(s))

def make_app(api_info):
    last_webhook_data = {}
    webhook_lock = threading.Lock()

    def rebuild_index():
        return load_index(force=True)

    def handler(req):
        nonlocal last_webhook_data
        path = urllib.parse.urlparse(req.path).path
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(req.path).query)

        # CORS preflight
        if req.command == 'OPTIONS':
            return (204, {
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Max-Age': '86400',
            }, b'')

        if path == '/':
            idx = load_index()
            actionable = [e for e in idx if is_actionable(e)]
            actionable.sort(key=lambda e: (URGENCY_ORDER.index(e.get('eff_urgency', 'no_deadline')) if e.get('eff_urgency') in URGENCY_ORDER else 99, e.get('nature_priority', 99)))
            tpl_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'email-dashboard.html')
            try:
                with open(tpl_path, 'r', encoding='utf-8') as _f:
                    html_template = _f.read()
            except FileNotFoundError:
                return (404, {'Content-Type': 'text/plain'}, b'email-dashboard.html not found next to server script')
            light = []
            cards_html = ''
            for e in actionable[:50]:
                raw = e.get('value_raw', {}) or {}
                _sub = raw.get('subject') or e.get('subject') or raw.get('summary','') or e.get('summary','') or '(fără subiect)'
                _frm = raw.get('from') or e.get('from') or raw.get('account','') or e.get('account','') or '—'
                light.append({'key': e.get('key',''), 'summary': e.get('summary',''),
                    'subject': _sub,
                    'from': _frm,
                    'nature': raw.get('nature', e.get('nature','')),
                    'urgency': raw.get('urgency', e.get('urgency','')),
                    'account': raw.get('account', e.get('account','')),
                    'email_ref': e.get('email_ref',''),
                    'date': raw.get('date', e.get('date',''))})
                urg = raw.get('urgency', e.get('urgency', ''))
                nat = raw.get('nature', e.get('nature', ''))
                sub = scapa_str(_sub)
                frm = scapa_str(_frm)
                nat_ro = {'security':'securitate','financial':'financiar','legal':'legal','medical':'medical','personal':'personal','business':'business','technical':'tehnic','commercial':'comercial','travel':'calatorii','admin':'administrativ'}.get(nat, 'generala')
                urg_cls = {'immediate':'urgent','today':'today','this_week':'week','week':'week'}.get(urg, '')
                df = ''
                d = raw.get('date', e.get('date', ''))
                if d:
                    try: df = d[:10]
                    except: pass
                key_esc = scapa_str(e.get('key', ''))
                cards_html += f'''<div class="item {urg_cls}" data-key="{key_esc}" onclick="d(this.dataset.key)">
<div class="top"><div class="left">{"<div class=\"from\">"+frm+"</div>" if frm else ""}<div class="text">{sub[:120]}</div></div></div>
<div class="bottom"><span class="tag tag-{nat_ro}">{nat_ro}</span>{f"<span class=\"date\">{df}</span>" if df else ""}</div></div>'''
            safe_data = json.dumps({'results': light, 'actionable_count': len(actionable),
                'total_all': len(idx)}, ensure_ascii=False).replace('</script>', '<\\/script>')
            safe_accounts = json.dumps(build_api(idx).get('accounts', []), ensure_ascii=False)
            safe_alerts = json.dumps({'total_alerts': 0}, ensure_ascii=False)
            try:
                with open(ALERTS_FILE, encoding='utf-8') as f:
                    al = json.load(f)
                    safe_alerts = json.dumps(al, ensure_ascii=False)
            except: pass
            html = html_template.replace('<!--CARDS-->', cards_html).replace('/*__DATA_INJECT__*/', f'window.__DATA__={safe_data};window.__ACCOUNTS__={safe_accounts};window.__ALERTS__={safe_alerts};')
            global _STATIC_WRITE_TIME
            if time.time() - _STATIC_WRITE_TIME > _STATIC_WRITE_TTL:
                try:
                    static_path = os.path.expanduser('~/CCDEW/_MEMORY/hermes-dashboard.html')
                    with open(static_path, 'w', encoding='utf-8') as f:
                        f.write(html)
                    _STATIC_WRITE_TIME = time.time()
                except Exception:
                    pass
            return (200, {'Content-Type': 'text/html; charset=utf-8'}, html.encode('utf-8'))

        if path == '/bbtest':
            ts = __import__('time').strftime('%H:%M:%S')
            body = f'<!DOCTYPE html><html><body><h1>TEST BB</h1><p>La ora {ts} - daca vezi asta, BB poate incarca http://localhost!</p></body></html>'
            return (200, {'Content-Type': 'text/html; charset=utf-8'}, body.encode('utf-8'))

        if path == '/bb':
            """Versiune BB - compacta cu JS minim pentru deschidere in Betterbird"""
            idx = load_index()
            actionable = [e for e in idx if is_actionable(e)]
            actionable.sort(key=lambda e: (URGENCY_ORDER.index(e.get('eff_urgency', 'no_deadline')) if e.get('eff_urgency') in URGENCY_ORDER else 99, e.get('nature_priority', 99)))
            rows = ''
            for e in actionable[:50]:
                raw = e.get('value_raw', {}) or {}
                # Folosim aceeași logică de fallback ca load_index()
                sub = raw.get('subject') or e.get('subject') or raw.get('summary','') or e.get('summary','') or '(fără subiect)'
                frm = raw.get('from') or e.get('from') or raw.get('account','') or e.get('account','') or '—'
                sub = scapa_str(str(sub)[:80])
                frm = scapa_str(str(frm)[:40])
                urg = raw.get('urgency', e.get('urgency', ''))
                date = str(raw.get('date', e.get('date', '')))[:10]
                nat = raw.get('nature', e.get('nature', 'generala'))
                key = scapa_str(e.get('key', ''))
                has_ref = 'y' if e.get('email_ref') else 'n'
                open_btn = f'<td class="o"><button onclick="bb(\'{key}\')" title="Deschide în Betterbird">✉</button></td>' if e.get('email_ref') else '<td class="o"></td>'
                rows += f'<tr class="{urg}" data-key="{key}"><td class="d">{date}</td><td class="f">{frm}</td><td class="s">{sub}</td><td class="n">{nat}</td>{open_btn}</tr>'
            cc = '*{margin:0;padding:0;box-sizing:border-box}body{font-family:system-ui,sans-serif;background:#f8f9fa;color:#333;font-size:13px;padding:8px}h1{font-size:16px;color:#1a237e;margin-bottom:8px}table{width:100%;border-collapse:collapse}td,th{padding:5px 6px;border-bottom:1px solid #eee;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:12px}th{background:#e8eaf6;color:#3949ab;font-weight:600;font-size:11px}.d{width:75px;color:#888;font-size:11px}.f{width:150px}.s{max-width:260px;overflow:hidden;text-overflow:ellipsis}.n{width:70px;text-align:center;color:#888;font-size:10px}.o{width:32px;text-align:center}.o button{background:#1a237e;color:#fff;border:none;border-radius:3px;padding:2px 5px;cursor:pointer;font-size:11px}.o button:hover{background:#3949ab}.urgent td{background:#fff0f0}.today td{background:#fff8e1}.this_week td{background:#f1f8e9}tr:hover td{background:#e3f2fd!important}.stats{display:flex;gap:8px;margin-bottom:8px;flex-wrap:wrap}.stat{background:#fff;padding:4px 10px;border-radius:6px;font-size:11px;box-shadow:0 1px 2px rgba(0,0,0,0.06)}.stat b{font-size:14px;color:#1a237e}#status{position:fixed;bottom:8px;right:8px;background:#333;color:#fff;padding:4px 10px;border-radius:4px;font-size:11px;display:none}'
            js = '''<script>
function bb(key){
  var s=document.getElementById('status');
  s.textContent='Se deschide...';s.style.display='block';
  fetch('/api/bb-open?q='+encodeURIComponent(key))
    .then(function(r){return r.json();})
    .then(function(d){
      if(d.ok===false){s.textContent='Nu s-a găsit fișierul .eml';s.style.background='#c62828';}
      else{s.textContent='Deschis în Betterbird ✓';s.style.background='#2e7d32';}
      setTimeout(function(){s.style.display='none';s.style.background='#333';},3000);
    })
    .catch(function(){s.textContent='Eroare conexiune';s.style.display='block';setTimeout(function(){s.style.display='none';},2000);});
}
</script>'''
            body = ('<!DOCTYPE html><html><head><meta charset="utf-8"><style>'+cc+'</style></head><body>'
                   +'<h1>📧 Hermes Email</h1>'
                   +'<div class="stats"><div class="stat"><b>'+str(len(actionable))+'</b> urgente</div>'
                   +'<div class="stat"><b>'+str(sum(1 for e in actionable if e.get("urgency","")=="immediate"))+'</b> imediate</div>'
                   +'<div class="stat"><b>'+str(len(idx))+'</b> total</div></div>'
                   +'<table><tr><th>Data</th><th>De la</th><th>Subiect</th><th>Tip</th><th>BB</th></tr>'
                   +rows+'</table>'
                   +'<div id="status"></div>'
                   +js+'</body></html>')
            return (200, {'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-cache'}, body.encode('utf-8'))


        if path == '/start' or path == '/s':
            """Pagina de start — vizibila si fara JS."""
            idx = load_index()
            actionable = [e for e in idx if is_actionable(e)]
            actionable.sort(key=lambda e: (URGENCY_ORDER.index(e.get('eff_urgency', 'no_deadline')) if e.get('eff_urgency') in URGENCY_ORDER else 99, e.get('nature_priority', 99)))
            accts = build_api(idx).get('accounts', [])
            rows = ''
            for e in actionable[:50]:
                raw = e.get('value_raw', {}) or {}
                sub = scapa_str(raw.get('subject', e.get('subject', e.get('summary', '')))) or scapa_str(e.get('summary', '(fără subiect)'))
                frm = scapa_str(raw.get('from', e.get('from', '')))
                urg = raw.get('urgency', e.get('urgency', ''))
                nat = raw.get('nature', e.get('nature', ''))
                icon = {'security': '🔒', 'financial': '💰', 'legal': '⚖', 'technical': '⚙️'}.get(nat, '📧')
                nat_cls = {'security':'sec','financial':'fin','legal':'leg','medical':'med','health':'med','technical':'tech','account':'fin'}.get(nat, '')
                urg_cls = {'immediate':'acum','today':'azi','week':'sapt'}.get(urg, '')
                card_cls = {'immediate':'urgent','today':'today','week':'week'}.get(urg, '')
                rows += f'''<div class="card {card_cls}">
<div class="inner"><span class="ico">{icon}</span>
<div class="body"><span class="subj">{sub[:100]}</span>
<div class="meta"><span class="from">{frm[:50]}</span>
<span class="tag {nat_cls}">{nat}</span>
</div></div>
<span class="urgbadge {urg_cls}">{urg}</span>
</div></div>'''
            html = f'''<!DOCTYPE html>
<html lang="ro">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Hermes — Email</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f0f2f5;color:#1a1a2e;line-height:1.4}}
/* Header */
.hdr{{background:linear-gradient(135deg,#1a237e,#283593);color:#fff;padding:14px 18px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px}}
.hdr h1{{font-size:17px;font-weight:600}}
.hdr .hint{{font-size:11px;color:#aab0e0}}
/* Stats */
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(90px,1fr));gap:4px;padding:10px 14px;background:#fff;border-bottom:1px solid #e2e5ea}}
.stat{{text-align:center;padding:5px 8px;border-radius:6px;background:#f5f6fa}}
.stat .n{{font-size:19px;font-weight:700;color:#1a237e}}
.stat .l{{font-size:9px;color:#7a7a9a;text-transform:uppercase;letter-spacing:0.5px}}
.stat.warn .n{{color:#e65100}}
.stat.danger .n{{color:#c62828}}
/* Filter bar */
.fbar{{padding:8px 14px;background:#fff;border-bottom:1px solid #e2e5ea;display:flex;gap:6px;align-items:center;flex-wrap:wrap}}
.fbar .cta{{margin-left:auto;background:#1a237e;color:#fff;border:none;border-radius:5px;padding:6px 14px;font-size:12px;text-decoration:none;font-weight:500}}
.fbar .cta:hover{{background:#283593}}
/* Cards */
.list{{max-width:820px;margin:6px auto;padding:0 8px}}
.card{{background:#fff;border-radius:8px;margin-bottom:5px;border-left:4px solid #ccc;display:block;text-decoration:none;color:inherit;overflow:hidden}}
.card:hover{{box-shadow:0 2px 8px rgba(26,35,126,0.12)}}
.card.urgent{{border-left-color:#c62828}}
.card.today{{border-left-color:#e65100}}
.card.week{{border-left-color:#f9a825}}
.card .inner{{padding:10px 12px;display:flex;gap:10px;align-items:flex-start}}
.card .ico{{font-size:18px;margin-top:1px;flex-shrink:0}}
.card .body{{flex:1;min-width:0}}
.card .subj{{font-size:13px;font-weight:600;color:#1a237e;display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.card .meta{{display:flex;gap:8px;font-size:11px;color:#7a7a9a;margin-top:4px;flex-wrap:wrap}}
.card .meta span{{white-space:nowrap}}
.card .from{{color:#444;font-weight:500}}
.card .tag{{display:inline-block;font-size:10px;padding:1px 7px;border-radius:3px;background:#e8eaf6;color:#283593;text-transform:uppercase;letter-spacing:0.3px}}
.card .tag.sec{{background:#ffebee;color:#c62828}}
.card .tag.fin{{background:#e8f5e9;color:#2e7d32}}
.card .tag.leg{{background:#fff3e0;color:#e65100}}
.card .tag.med{{background:#fce4ec;color:#ad1457}}
.card .tag.tech{{background:#e3f2fd;color:#1565c0}}
.card .urgbadge{{font-size:10px;padding:1px 7px;border-radius:3px;font-weight:600;flex-shrink:0}}
.card .urgbadge.acum{{background:#c62828;color:#fff}}
.card .urgbadge.azi{{background:#e65100;color:#fff}}
.card .urgbadge.sapt{{background:#f9a825;color:#333}}
/* Empty */
.empty{{text-align:center;padding:40px 16px;color:#999;font-size:14px}}
.empty .eico{{font-size:32px;display:block;margin-bottom:8px}}
/* Footer */
.ftr{{text-align:center;padding:14px;font-size:11px;color:#999}}
.ftr a{{color:#283593;text-decoration:none}}
.ftr a:hover{{text-decoration:underline}}
</style>
</head>
<body>
<div class="hdr">
<h1>📧 Hermes — Email-uri importante</h1>
<span class="hint">{len(actionable)} de urmărit &middot; {len(accts)} conturi &middot; {len(idx)} arhivate</span>
</div>
<div class="stats">
<div class="stat danger"><div class="n">{sum(1 for e in actionable[:50] if (e.get("value_raw",{}) or {}).get("urgency","")=="immediate" or e.get("urgency","")=="immediate")}</div><div class="l">Urgente</div></div>
<div class="stat warn"><div class="n">{sum(1 for e in actionable[:50] if (e.get("value_raw",{}) or {}).get("urgency","")=="today" or e.get("urgency","")=="today")}</div><div class="l">Azi</div></div>
<div class="stat"><div class="n">{len(actionable)}</div><div class="l">Acționabile</div></div>
<div class="stat"><div class="n">{len(accts)}</div><div class="l">Conturi</div></div>
</div>
<div class="fbar">
<a href="http://localhost:8766/" class="cta">Deschide dashboard-ul interactiv &rarr;</a>
</div>
<div class="list">
{rows if rows else '<div class="empty"><span class="eico">📭</span>Nimic de arătat</div>'}
</div>
<div class="ftr">Powered by <a href="http://localhost:8766/">Hermes Email Dashboard</a></div>
</body></html>'''
            # Scrie static (throttled — max o dată pe minut)
            if time.time() - _STATIC_WRITE_TIME > _STATIC_WRITE_TTL:
                try:
                    static_path = os.path.expanduser('~/CCDEW/_MEMORY/hermes-dashboard.html')
                    with open(static_path, 'w', encoding='utf-8') as f:
                        f.write(html)
                    _STATIC_WRITE_TIME = time.time()
                except Exception:
                    pass
            return (200, {'Content-Type': 'text/html; charset=utf-8'}, html.encode('utf-8'))

        if path == '/api/health':
            idx = load_index()
            return (200, {'Content-Type': 'application/json'}, json.dumps({'status': 'ok', 'entries': len(idx)}).encode())

        if path == '/api/info':
            idx = load_index()
            return (200, {'Content-Type': 'application/json'}, json.dumps(build_api(idx)).encode())

        if path == '/api/events':
            client_q = SSEQueue()
            SSE_CLIENTS.append(client_q.q)
            def gen():
                yield "retry: 2000\n\n".encode()
                while True:
                    msg = client_q.get(timeout=30)
                    if msg:
                        yield msg
            return (200, {'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive'}, gen())

        if path == '/api/webhook':
            try:
                cl = min(int(req.headers.get('Content-Length', 0) or 0), MAX_POST_BODY)
                body = req.rfile.read(cl) if cl > 0 else b'{}'
                data = json.loads(body)
                with webhook_lock:
                    last_webhook_data = data
                notify_sse_clients({'type': 'new_emails', 'account': data.get('account', '?'), 'results': data.get('results', []), 'ts': time.time()})
                threading.Thread(target=rebuild_index, daemon=True).start()
                return (200, {'Content-Type': 'application/json'}, json.dumps({'ok': True}).encode())
            except Exception as e:
                return (200, {'Content-Type': 'application/json'}, json.dumps({'ok': False, 'error': str(e)}).encode())

        if path == '/api/actionable':
            idx = load_index()
            results = [e for e in idx if is_actionable(e)]
            results.sort(key=lambda e: (URGENCY_ORDER.index(e.get('eff_urgency', 'no_deadline')) if e.get('eff_urgency') in URGENCY_ORDER else 99, e.get('nature_priority', 99)))
            total = len(results)
            page = int(qs.get('page', ['1'])[0])
            limit = min(int(qs.get('limit', ['50'])[0]), 200)
            start = (page - 1) * limit
            page_results = results[start:start + limit]
            return (200, {'Content-Type': 'application/json'}, json.dumps({
                'total': total, 'page': page, 'limit': limit, 'results': page_results,
                'actionable_count': total, 'total_all': len(idx)
            }, ensure_ascii=False).encode())

        if path == '/api/accounts':
            idx = load_index()
            acct_counts = {}
            for e in idx:
                raw = e.get('value_raw') or {}
                acct_name = ''
                for src in [e.get('summary',''), json.dumps(raw.get('accounts',[])), e.get('source','')]:
                    for a in api_info['accounts']:
                        if a.lower() in src.lower():
                            acct_name = a
                            break
                    if acct_name: break
                if acct_name:
                    acct_counts[acct_name] = acct_counts.get(acct_name, 0) + 1
            for a in api_info['accounts']:
                acct_counts.setdefault(a, 0)
            return (200, {'Content-Type': 'application/json'},
                    json.dumps([{'name': k, 'count': v} for k, v in sorted(acct_counts.items(), key=lambda x: -x[1])], ensure_ascii=False).encode())

        NAME_KEYWORDS = ['matei', 'ionut', 'ionuț', 'catalin', 'cătălin', 'domin ic', 'dominic',
                         'themateiionutcatalin', 'ionutmateic', 'forsunriseverify', 'ombundetotdetot']

        if path == '/api/search':
            idx = load_index()
            urgency = qs.get('urgency', [None])[0]
            nature = qs.get('nature', [None])[0]
            search = qs.get('q', [None])[0]
            personal = qs.get('personal', [None])[0]
            page = int(qs.get('page', ['1'])[0])
            limit = min(int(qs.get('limit', ['50'])[0]), 200)
            # Dacă nu se filtrează explicit, arată doar actionable; altfel căutare în tot indexul
            if urgency or nature or search:
                results = list(idx)
            else:
                results = [e for e in idx if is_actionable(e)]
            if urgency:
                results = [e for e in results if e.get('urgency') == urgency]
            if nature:
                results = [e for e in results if e.get('nature') == nature]
            if personal == 'true':
                results = [e for e in results if any(k in json.dumps(e, ensure_ascii=False).lower() for k in NAME_KEYWORDS)]
            if search:
                sl = search.lower()
                results = [e for e in results if sl in json.dumps(e, ensure_ascii=False).lower()]
            total = len(results)
            start = (page - 1) * limit
            results = results[start:start + limit]
            return (200, {'Content-Type': 'application/json'},
                    json.dumps({'total': total, 'page': page, 'limit': limit, 'results': results}, ensure_ascii=False).encode())

        if path.startswith('/api/detail/'):
            idx = load_index()
            key = path.replace('/api/detail/', '')
            for e in idx:
                if e['key'] == key or e['filename'] == key:
                    return (200, {'Content-Type': 'application/json'}, json.dumps(e, ensure_ascii=False).encode())
            return (404, {}, b'{}')

        if path == '/api/classify':
            search_q = qs.get('q', [None])[0]
            # Acceptă și POST cu JSON body
            if not search_q:
                try:
                    cl = int(req.headers.get('Content-Length', 0))
                    if cl > 0:
                        body = json.loads(req.rfile.read(cl))
                        search_q = body.get('subject') or body.get('q') or body.get('query')
                except: pass
            if not search_q:
                return (200, {'Content-Type': 'application/json'}, json.dumps({'error': 'no query'}).encode())
            idx = load_index()
            match = None
            q_lower = search_q.lower()
            for e in idx:
                subj = e.get('subject', '') or ''
                frm = e.get('from', '') or ''
                key = e.get('key', '')
                if (subj and subj.lower() in q_lower) or (frm and frm.lower() in q_lower) or (key and key.lower() in q_lower):
                    if e.get('email_ref'):
                        match = e
                        break
            if match:
                parsed = match.get('value_raw', {}) or {}
                if not parsed:
                    val_str = match.get('val', '')
                    if isinstance(val_str, str) and val_str.strip().startswith('{'):
                        try: parsed = json.loads(val_str)
                        except: pass
                nature = parsed.get('nature', match.get('nature', ''))
                urgency = parsed.get('urgency', match.get('urgency', ''))
                base_score = {'immediate': 90, 'today': 70, 'this_week': 45, 'no_deadline': 15}.get(urgency, 30)
                nat_bonus = {'security': 10, 'phishing': 20, 'financial': 7, 'legal': 5, 'account': 3}.get(nature, 0)
                priority_score = parsed.get('priority_score', min(100, base_score + nat_bonus))
                attachments = parsed.get('attachments', [])
                result = {
                    'nature': nature,
                    'urgency': urgency,
                    'priority_score': priority_score,
                    'summary': parsed.get('summary', match.get('summary', parsed.get('subject', ''))),
                    'action': parsed.get('action', match.get('action', '')),
                    'account': parsed.get('account', match.get('account', '')),
                    'severity': parsed.get('severity', match.get('severity', '')),
                    'subject': match.get('subject', parsed.get('subject', '')),
                    'from': match.get('from', parsed.get('from', '')),
                    'date': match.get('email_date', parsed.get('date', '')),
                    'email_ref': match.get('email_ref', ''),
                    'key': match.get('key', ''),
                    'attachments': attachments if isinstance(attachments, list) else [],
                    'source': 'hermes'
                }
                return (200, {'Content-Type': 'application/json'}, json.dumps(result, ensure_ascii=False).encode())
            return (200, {'Content-Type': 'application/json'}, json.dumps({'source': 'index_only', 'subject': search_q}).encode())

        if path == '/api/feedback':
            try:
                cl = int(req.headers.get('Content-Length', 0))
                body = req.rfile.read(cl) if cl > 0 else b'{}'
                data = json.loads(body)
                fb_file = os.path.expanduser('~/.local/state/ccdew-feedback.jsonl')
                with open(fb_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(data, ensure_ascii=False) + '\n')
                return (200, {'Content-Type': 'application/json'}, json.dumps({'ok': True}).encode())
            except Exception as e:
                return (200, {'Content-Type': 'application/json'}, json.dumps({'ok': False, 'error': str(e)}).encode())

        if path == '/api/impact-alerts':
            if os.path.exists(ALERTS_FILE):
                try:
                    with open(ALERTS_FILE, encoding='utf-8') as f:
                        data = json.load(f)
                    for alert in data.get('alerts', []):
                        # Înlocuiește 'Gmail N' cu adresa reală de email
                        raw_acct = alert.get('account', '')
                        if raw_acct:
                            alert['account'] = resolve_account(raw_acct)
                        # Aplică decay temporal: urgența scade cu vârsta emailului
                        alert['urgency'] = effective_urgency(alert)
                        # Calculează threat_score (1-4) pentru plugin Mailspring
                        alert['threat_score'] = _calc_threat_score(alert)
                        # Generează recommended_action dacă lipsește
                        if not alert.get('recommended_action'):
                            alert['recommended_action'] = _gen_recommended_action(alert)
                    return (200, {'Content-Type': 'application/json'}, json.dumps(data, ensure_ascii=False).encode())
                except Exception:
                    pass
            return (200, {'Content-Type': 'application/json'}, json.dumps({'total_alerts': 0, 'alerts': []}).encode())

        if path == '/api/bb-open':
            import subprocess, glob as _glob
            search_q = qs.get('q', [None])[0]
            if not search_q:
                return (200, {'Content-Type': 'application/json'},
                        json.dumps({'ok': False, 'error': 'no query'}).encode())
            eml_path = None
            eml_debug = []
            idx = load_index()
            # Pasul 1: cauta prin email_ref exact
            for e in idx:
                if e.get('key') == search_q or e.get('filename') == search_q:
                    ref = e.get('email_ref', '')
                    if ref:
                        ref_clean = ref.replace('/', '-')
                        # încearcă: <ref>-*.eml și *<ref>*.eml
                        for pat_tmpl in [f'{ref_clean}-*.eml', f'*{ref_clean}*.eml']:
                            pat = os.path.expanduser(f'~/.cache/ccdew-eml/{pat_tmpl}')
                            matches = _glob.glob(pat)
                            eml_debug.append(f'pat={pat_tmpl} found={len(matches)}')
                            if matches:
                                eml_path = matches[0]
                                break
                    break
            # Pasul 2: cauta dupa sufixul cheii (fara fallback la ultimul modificat)
            if not eml_path and len(search_q) >= 8:
                suffix = search_q[-24:].replace('/', '-')
                pat = os.path.expanduser(f'~/.cache/ccdew-eml/*{suffix}*.eml')
                matches = _glob.glob(pat)
                eml_debug.append(f'suffix_pat found={len(matches)}')
                if matches:
                    eml_path = matches[0]
            # Pasul 3: NU deschidem un fișier aleatoriu — returnăm eroare clară
            if not eml_path:
                return (200, {'Content-Type': 'application/json'},
                        json.dumps({'ok': False, 'error': 'no .eml found', 'key': search_q,
                                    'debug': eml_debug,
                                    'hint': 'Emailul nu a fost exportat în ~/.cache/ccdew-eml/ — rulează ccdew-email-refresh'
                                    }).encode())
            # Verificare path traversal — eml_path trebuie să fie sub cache dir
            cache_dir = os.path.realpath(os.path.expanduser('~/.cache/ccdew-eml/'))
            real_eml = os.path.realpath(eml_path)
            if not real_eml.startswith(cache_dir):
                return (403, {'Content-Type': 'application/json'},
                        json.dumps({'ok': False, 'error': 'path not allowed'}).encode())
            try:
                subprocess.Popen(['bash', os.path.expanduser('~/.local/bin/bb-open'), real_eml],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return (200, {'Content-Type': 'application/json'},
                        json.dumps({'ok': True, 'eml': os.path.basename(real_eml)}).encode())
            except Exception as e:
                return (200, {'Content-Type': 'application/json'},
                        json.dumps({'ok': False, 'error': str(e)}).encode())

        if path == '/api/action':
            # Endpoint pentru arhivare / amânare din UI
            try:
                content_len = min(int(req.headers.get('Content-Length', 0) or 0), MAX_POST_BODY)
                body_raw = req.rfile.read(content_len) if content_len else b'{}'
                payload = json.loads(body_raw)
                action = payload.get('action', '')
                subject = payload.get('subject', '')
                # Log acțiunea în fișier pentru procesare asincronă
                log_file = os.path.expanduser('~/.local/state/ccdew-actions.jsonl')
                entry = {'ts': time.time(), 'action': action, 'subject': subject,
                         'from': payload.get('from', ''), 'date': payload.get('date', '')}
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + '\n')
                return (200, {'Content-Type': 'application/json'},
                        json.dumps({'ok': True, 'action': action}).encode())
            except Exception as e:
                return (200, {'Content-Type': 'application/json'},
                        json.dumps({'ok': False, 'error': str(e)}).encode())

        if path == '/api/inbox':
            inbox_emails = load_inbox_emails()  # folosește default max_per_folder=10
            inbox_emails = enrich_with_alerts(inbox_emails)
            body = json.dumps({'emails': inbox_emails, 'count': len(inbox_emails)}, ensure_ascii=False, default=str).encode('utf-8')
            # Eliberează lista locală imediat după serializare
            del inbox_emails
            return (200, {'Content-Type': 'application/json; charset=utf-8', 'Access-Control-Allow-Origin': '*'}, body)

        if path == '/inbox' or path == '/inbox.html':
            inbox_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'inbox.html')
            if os.path.exists(inbox_path):
                with open(inbox_path, 'rb') as f:
                    content = f.read()
                return (200, {'Content-Type': 'text/html; charset=utf-8'}, content)
            else:
                return (404, {'Content-Type': 'text/plain'}, b'inbox.html not found')

        if path == '/panel' or path == '/panel.html':
            panel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ccdew-panel.html')
            if os.path.exists(panel_path):
                with open(panel_path, 'rb') as f:
                    content = f.read()
                return (200, {'Content-Type': 'text/html; charset=utf-8'}, content)
            else:
                return (404, {'Content-Type': 'text/plain'}, b'ccdew-panel.html not found')

        return (404, {'Content-Type': 'text/plain'}, b'Not found')
    return handler

class Server(http.server.ThreadingHTTPServer):
    allow_reuse_address = True

def run(port=8766):
    print(f"Building index...", flush=True)
    index = load_index()
    api_info = build_api(index)
    handler = make_app(api_info)

    class ReqHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self._handle()
        def do_POST(self):
            self._handle()
        def do_OPTIONS(self):
            self._handle()
        def _handle(self):
            try:
                code, headers, body = handler(self)
                is_stream = headers.get('Content-Type') == 'text/event-stream'
                self.send_response(code)
                for k, v in headers.items():
                    self.send_header(k, v)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                if is_stream:
                    if hasattr(body, '__iter__') and not isinstance(body, (bytes, str)):
                        for chunk in body:
                            try:
                                self.wfile.write(chunk)
                                self.wfile.flush()
                            except:
                                break
                    else:
                        self.wfile.write(body)
                else:
                    self.wfile.write(body if isinstance(body, bytes) else body.encode())
            except Exception as e:
                try:
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': str(e)}).encode())
                except:
                    pass
        def log_message(self, fmt, *a):
            import sys
            print(f"[REQ] {self.address_string()} {fmt % a}", flush=True)

    actionable_count = sum(1 for e in index if is_actionable(e))
    srv = Server(('127.0.0.1', port), ReqHandler)
    print(f"CCDEW Email Dashboard v2 — live")
    print(f"  http://localhost:{port}")
    print(f"  {len(index)} intrari ({actionable_count} actionabile)")
    print(f"  {len(api_info['accounts'])} conturi | SSE live activ")
    print(f"  Index cache: {INDEX_CACHE_TTL}s TTL")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8766
    run(port)
