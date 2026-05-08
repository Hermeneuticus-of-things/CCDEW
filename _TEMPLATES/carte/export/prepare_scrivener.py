#!/usr/bin/env python3
"""
Prepare Karma Book for Scrivener 3 import.
Creates numbered .txt files with clean text (no markdown formatting).
Scrivener imports: File → Import → Files → select all .txt from output folder.
Structure mirrors the Binder hierarchy through folder naming.
"""
import os, re, sys

SRC = r"<WORKSPACE_DIR>/PROJECTS\Karma Book\04_CARTE"
OUT = r"<WORKSPACE_DIR>/PROJECTS\Karma Book\export\scrivener_import"

# Chapter titles for folder names
CHAPTERS = {
    'Cap0': '00 — Introducere',
    'Cap1': '01 — Vocabularul Operațional',
    'Cap2': '02 — Substanța și Suportul',
    'Cap3': '03 — Calitatea și Fundamentul',
    'Cap4': '04 — Arhitectura Matricei',
    'Cap5': '05 — Mecanismul Acumulării',
    'Cap6': '06 — Maturizarea și Rezultatele',
    'Cap7': '07 — Epuizarea și Transcendența',
}

def clean_md(text):
    """Remove markdown formatting, keep ALOGEN terms readable."""
    # Remove heading markers
    text = re.sub(r'^#{1,3}\s+', '', text, flags=re.MULTILINE)
    # Convert ***term*** 'alogen' to TERM (alogen)
    text = re.sub(r"\*\*\*([^*]+)\*\*\*\s*'([^']+)'", r'\1 (\2)', text)
    # Remove remaining bold/italic markers
    text = re.sub(r'\*\*\*([^*]+)\*\*\*', r'\1', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    # Keep single italic for narrative blocks
    text = re.sub(r'^\*([^*]+)\*$', r'\1', text, flags=re.MULTILINE)
    # Remove horizontal rules
    text = re.sub(r'^---+$', '', text, flags=re.MULTILINE)
    # Remove footnote lines (¹ Cap...)
    text = re.sub(r'^¹.*$', '', text, flags=re.MULTILINE)
    # Remove backtick lines
    text = re.sub(r'^`.*$', '', text, flags=re.MULTILINE)
    # Clean up excess blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def main():
    os.makedirs(OUT, exist_ok=True)
    total = 0

    for cap_dir in sorted(os.listdir(SRC)):
        cap_path = os.path.join(SRC, cap_dir)
        if not os.path.isdir(cap_path) or cap_dir not in CHAPTERS:
            continue

        # Create chapter folder
        chapter_name = CHAPTERS[cap_dir]
        chapter_out = os.path.join(OUT, chapter_name)
        os.makedirs(chapter_out, exist_ok=True)

        # Process .md files
        files = sorted([f for f in os.listdir(cap_path)
                       if f.endswith('.md') and not f.endswith('.bak') and f != 'CLAUDE.md'])

        for i, fname in enumerate(files, 1):
            fpath = os.path.join(cap_path, fname)
            text = open(fpath, encoding='utf-8').read()
            clean = clean_md(text)

            # Output filename: numbered for order
            out_name = f"{i:02d}_{os.path.splitext(fname)[0]}.txt"
            out_path = os.path.join(chapter_out, out_name)
            open(out_path, 'w', encoding='utf-8').write(clean)
            total += 1

    print(f"Pregatit {total} fisiere in {OUT}")
    print(f"\nPasi in Scrivener 3:")
    print(f"1. File > New Project > Blank")
    print(f"2. In Binder, creeaza 8 foldere (Cap 0-7)")
    print(f"3. Pentru fiecare folder: File > Import > Files")
    print(f"4. Selecteaza toate .txt din folderul corespunzator")
    print(f"5. Scrivener le importa ca documente separate in Binder")
    print(f"6. Redenumeste fiecare document cu titlul subcapitolului")

if __name__ == '__main__':
    main()
