# CCDEW Betterbird Extension

Dashboard de impact alerts **în** Betterbird — nu separat.

## Instalare

1. Deschide Betterbird
2. Meniu → **Add-ons and Themes** (sau `Ctrl+Shift+A`)
3. Click pe **⚙️** (roata dințată) → **Install Add-on From File...**
4. Selectează folderul `betterbird-ccdew/` (sau zip-u-l)
5. Restart Betterbird

## Alternativă: Load Temporary Extension

1. În Betterbird, mergi la `about:debugging`
2. Click **Load Temporary Add-on**
3. Selectează `manifest.json` din folderul `betterbird-ccdew/`

## Ce face

- **Sidebar panel** în Betterbird cu alertele de impact
- Click pe alertă → **deschide email-ul** direct în Betterbird
- Se refresh-ează automat la 60 secunde
- Arată **fapte reale**: cine, ce, cât, când — nu generalități

## Cerințe

- CCDEW email dashboard trebuie să ruleze pe `localhost:8766`
- Se pornește automat la `SessionStart` în opencode
