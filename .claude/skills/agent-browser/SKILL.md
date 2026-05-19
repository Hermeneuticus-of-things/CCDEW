# Skill: agent-browser
# Trigger: /browser sau când task-ul implică web automation / scraping / screenshot

## Ce face
CLI Rust pentru browser automation AI-native. Daemon persistent → zero startup overhead între comenzi.
Install: `npm install -g agent-browser && agent-browser install`

## Pattern canonical (AI agent flow)

```bash
# 1. Deschide pagina
agent-browser open https://example.com

# 2. Snapshot refs — ÎNTOTDEAUNA înainte de click/fill
agent-browser snapshot -i          # -i = doar elemente interactive
# → - link "Login" [ref=e1]
# → - input "Email" [ref=e2]
# → - button "Submit" [ref=e3]

# 3. Acționează prin refs (stabile, nu CSS)
agent-browser fill @e2 "user@example.com"
agent-browser click @e3

# 4. Verifică rezultat
agent-browser get title
agent-browser get url
```

## Comenzi esențiale

| Comandă | Efect |
|---|---|
| `open <url>` | Navighează |
| `snapshot -i` | Refs interactive (pentru agenți) |
| `snapshot -c` | Compact (fără elemente goale) |
| `click @eN` | Click după ref |
| `fill @eN "text"` | Clear + fill |
| `type @eN "text"` | Type (fără clear) |
| `press Enter` | Tastă |
| `screenshot path.png` | Screenshot |
| `screenshot --annotate` | Screenshot cu labels (vision models) |
| `get text @eN` | Extrage text element |
| `get text body` | Tot textul paginii |
| `eval "document.title"` | JavaScript arbitrary |
| `wait 2000` | Delay ms |
| `wait @eN` | Așteptă element |
| `find role button click --name Submit` | Locator semantic |
| `tab new` | Tab nou |
| `session list` | Sesiuni active |
| `close` | Închide sesiunea curentă |

## Chaining (daemonul persistă între apeluri)

```bash
agent-browser open example.com && agent-browser snapshot -i
agent-browser fill @e1 "user" && agent-browser fill @e2 "pass" && agent-browser click @e3
```

## Patterns AI comune

### Web research / extragere date
```bash
agent-browser open "https://site.com/page"
agent-browser get text body          # tot textul
agent-browser eval "Array.from(document.querySelectorAll('h2')).map(e=>e.textContent)"
```

### Login flow
```bash
agent-browser open "https://site.com/login"
agent-browser snapshot -i
agent-browser fill @e1 "username"
agent-browser fill @e2 "password"
agent-browser click @e3
agent-browser wait 2000
agent-browser get url                # verifică redirect
```

### Screenshot pentru verificare
```bash
agent-browser screenshot --annotate  # labeled refs vizibili
```

### Multi-tab scraping
```bash
agent-browser open "https://site.com"
agent-browser tab new
agent-browser open "https://site2.com"
agent-browser tab 1                  # switch back
```

## Auth persistence
```bash
# Salvare stare după login
agent-browser open "https://site.com/login"
# ... login flow ...
agent-browser cookies get > auth-cookies.json

# Reîncărcare în sesiune nouă
agent-browser --session-name myapp open "https://site.com"
```

## Output JSON (pentru procesare programatică)
```bash
agent-browser --json snapshot -i
agent-browser --json get text body
```

## Dashboard (observabilitate)
```bash
agent-browser dashboard start        # http://localhost:4848
```

## Integrare cu Claude agenți
Folosește `Bash` tool pentru a rula comenzile. Daemonul persistă între tool calls.
Refs `@e1`, `@e2`... se resetează la fiecare `snapshot` — ia snapshot fresh înainte de fiecare acțiune pe o pagină nouă.
