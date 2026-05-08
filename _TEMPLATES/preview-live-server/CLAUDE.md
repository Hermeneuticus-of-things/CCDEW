# Preview LIVE Server — Template

## Ce face
Server Python care randeaza fisiere .md ca HTML cu auto-refresh.
Cand editezi un fisier, pagina se reincarca singura in 2 secunde.

## Cand sa-l folosesti
- Orice proiect cu fisiere .md care vrei sa le vezi renderizate in browser
- Carti, glosare, documentatie, note — orice text Markdown
- Cand lucrezi in Claude Code si vrei sa vezi rezultatul live

## Cum sa-l folosesti

### Pas 1 — Copiaza serve_md.py in proiect
```
cp _TEMPLATES/preview-live-server/serve_md.py PROJECTS/NumeProiect/
```

### Pas 2 — Modifica BASE (optional)
Deschide serve_md.py si schimba `BASE` daca vrei sa servesti alt folder decat cel curent.

### Pas 3 — Adauga in launch.json
Pune in `.claude/launch.json` al workspace-ului:
```json
{
  "version": "0.0.1",
  "configurations": [
    {
      "name": "md-viewer",
      "runtimeExecutable": "python",
      "runtimeArgs": ["PROJECTS/NumeProiect/serve_md.py"],
      "port": 8766
    }
  ]
}
```

### Pas 4 — Porneste
Din Claude Code:
```
preview_start("md-viewer")
```

Sau din terminal:
```
python serve_md.py
```

## Dependente
- Python 3
- `pip install markdown` (optional — fara el, afiseaza text brut)

## Functionalitati
- Browsing pe foldere si fisiere .md
- Renderizare Markdown → HTML cu font Georgia, stil carte
- Auto-refresh la 2 secunde cand fisierul se schimba pe disc
- Navigare prev/next intre fisiere cu sageti
- Breadcrumb (Radacina / Folder / Fisier)
- Badge verde LIVE in coltul dreapta-sus
- Multi-threaded (nu se blocheaza)
- Exclude .bak, CLAUDE.md, foldere ascunse

## Port default
8766 — schimba in serve_md.py daca e ocupat
