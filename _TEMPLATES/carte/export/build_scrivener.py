#!/usr/bin/env python3
"""
Build a complete Scrivener 3 for Windows (.scriv) project.
Creates all required files: .scrivx, Files/Data/UUID/content.rtf, Settings/, version.txt
"""
import os, re, uuid, shutil
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, ElementTree, indent

SRC = r"<WORKSPACE_DIR>/PROJECTS\Karma Book\04_CARTE"
from datetime import datetime as _dt
_stamp = _dt.now().strftime('%Y-%m-%d_%H%M')
OUT = rf"<WORKSPACE_DIR>/PROJECTS\Karma Book\export\Karma_{_stamp}.scriv"

CHAPTERS = [
    ('Cap0', 'Introducere'),
    ('Cap1', 'Vocabularul Operational'),
    ('Cap2', 'Substanta si Suportul'),
    ('Cap3', 'Calitatea si Fundamentul'),
    ('Cap4', 'Arhitectura Matricei'),
    ('Cap5', 'Mecanismul Acumularii'),
    ('Cap6', 'Maturizarea si Rezultatele'),
    ('Cap7', 'Epuizarea si Transcendenta'),
]

BOOK_TITLE = "Karma: Arhitectura Subtila a Destinului"

def clean_md(text):
    text = re.sub(r'^#{1,3}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r"\*\*\*([^*]+)\*\*\*\s*'([^']+)'", r'\1 (\2)', text)
    text = re.sub(r'\*\*\*([^*]+)\*\*\*', r'\1', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'^\*([^*]+)\*$', r'\1', text, flags=re.MULTILINE)
    text = re.sub(r'^---+$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^`.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def text_to_rtf(text):
    result = []
    for ch in text:
        if ch == '\\': result.append('\\\\')
        elif ch == '{': result.append('\\{')
        elif ch == '}': result.append('\\}')
        elif ord(ch) > 127: result.append(f'\\u{ord(ch)}?')
        elif ch == '\n': result.append('\\par\n')
        else: result.append(ch)
    body = ''.join(result)
    return (
        '{\\rtf1\\ansi\\ansicpg1252\\deff0\n'
        '{\\fonttbl{\\f0\\froman\\fcharset0 Georgia;}}\n'
        '\\f0\\fs28\\sl360\\slmult1\\sa200\n'
        + body +
        '\n}'
    )

def make_uuid():
    return str(uuid.uuid4()).upper()

def now_str():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S +0200')

def build_project():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)

    # Create folder structure
    files_dir = os.path.join(OUT, 'Files')
    data_dir = os.path.join(files_dir, 'Data')
    settings_dir = os.path.join(OUT, 'Settings')
    os.makedirs(data_dir)
    os.makedirs(settings_dir)

    # version.txt — required
    with open(os.path.join(files_dir, 'version.txt'), 'w') as f:
        f.write('16\n')

    # Settings files — required
    with open(os.path.join(settings_dir, 'recents.txt'), 'w') as f:
        f.write('')
    with open(os.path.join(settings_dir, 'ui-common.xml'), 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<UICommon/>\n')
    with open(os.path.join(settings_dir, 'ui.ini'), 'w') as f:
        f.write('[General]\n')

    # Build .scrivx XML
    project_id = make_uuid()
    root = Element('ScrivenerProject', {
        'Version': '2.0',
        'Creator': 'SCRIV3-WIN-3.0.1',
        'Modified': now_str(),
        'Identifier': project_id,
    })

    # Binder
    binder = SubElement(root, 'Binder')

    # Draft folder
    draft_uuid = make_uuid()
    draft = SubElement(binder, 'BinderItem', {
        'UUID': draft_uuid,
        'Type': 'DraftFolder',
        'Created': now_str(),
        'Modified': now_str(),
    })
    SubElement(draft, 'Title').text = 'Manuscris'
    meta = SubElement(draft, 'MetaData')
    SubElement(meta, 'IncludeInCompile').text = 'Yes'
    draft_children = SubElement(draft, 'Children')

    # Create draft folder on disk
    os.makedirs(os.path.join(data_dir, draft_uuid), exist_ok=True)

    doc_counter = 0

    for cap_dir, cap_title in CHAPTERS:
        cap_path = os.path.join(SRC, cap_dir)
        if not os.path.isdir(cap_path):
            continue

        # Chapter folder in binder
        chap_uuid = make_uuid()
        chap = SubElement(draft_children, 'BinderItem', {
            'UUID': chap_uuid,
            'Type': 'Folder',
            'Created': now_str(),
            'Modified': now_str(),
        })
        SubElement(chap, 'Title').text = cap_title
        chap_meta = SubElement(chap, 'MetaData')
        SubElement(chap_meta, 'IncludeInCompile').text = 'Yes'
        chap_children = SubElement(chap, 'Children')

        # Chapter folder on disk
        os.makedirs(os.path.join(data_dir, chap_uuid), exist_ok=True)

        # Process .md files
        files = sorted([f for f in os.listdir(cap_path)
                       if f.endswith('.md') and not f.endswith('.bak') and f != 'CLAUDE.md'])

        for fname in files:
            fpath = os.path.join(cap_path, fname)
            text = open(fpath, encoding='utf-8').read()
            clean = clean_md(text)

            first_line = clean.split('\n')[0].strip()
            title = first_line if len(first_line) < 60 and first_line else os.path.splitext(fname)[0]

            # Document in binder
            doc_uuid = make_uuid()
            doc = SubElement(chap_children, 'BinderItem', {
                'UUID': doc_uuid,
                'Type': 'Text',
                'Created': now_str(),
                'Modified': now_str(),
            })
            SubElement(doc, 'Title').text = title
            doc_meta = SubElement(doc, 'MetaData')
            SubElement(doc_meta, 'IncludeInCompile').text = 'Yes'

            # Document on disk
            doc_data = os.path.join(data_dir, doc_uuid)
            os.makedirs(doc_data, exist_ok=True)
            rtf = text_to_rtf(clean)
            with open(os.path.join(doc_data, 'content.rtf'), 'w', encoding='utf-8') as f:
                f.write(rtf)

            doc_counter += 1

    # Research folder
    research_uuid = make_uuid()
    research = SubElement(binder, 'BinderItem', {
        'UUID': research_uuid,
        'Type': 'ResearchFolder',
        'Created': now_str(),
        'Modified': now_str(),
    })
    SubElement(research, 'Title').text = 'Research'
    os.makedirs(os.path.join(data_dir, research_uuid), exist_ok=True)

    # Trash folder
    trash_uuid = make_uuid()
    trash = SubElement(binder, 'BinderItem', {
        'UUID': trash_uuid,
        'Type': 'TrashFolder',
        'Created': now_str(),
        'Modified': now_str(),
    })
    SubElement(trash, 'Title').text = 'Trash'
    os.makedirs(os.path.join(data_dir, trash_uuid), exist_ok=True)

    # LabelSettings
    labels = SubElement(root, 'LabelSettings')
    SubElement(labels, 'Title').text = 'Label'
    label_list = SubElement(labels, 'Labels')
    for color, name in [('#FFFFFF', 'No Label'), ('#FF0000', 'Red'), ('#FFA500', 'Orange'),
                        ('#FFFF00', 'Yellow'), ('#00FF00', 'Green'), ('#0000FF', 'Blue'), ('#800080', 'Purple')]:
        l = SubElement(label_list, 'Label', {'Color': color})
        l.text = name

    # StatusSettings
    statuses = SubElement(root, 'StatusSettings')
    SubElement(statuses, 'Title').text = 'Status'
    status_list = SubElement(statuses, 'StatusItems')
    for s in ['No Status', 'To Do', 'In Progress', 'First Draft', 'Revised Draft', 'Final Draft', 'Done']:
        SubElement(status_list, 'Status').text = s

    # ProjectProperties
    props = SubElement(root, 'ProjectProperties')
    SubElement(props, 'ProjectTitle').text = BOOK_TITLE

    # Write .scrivx
    tree = ElementTree(root)
    indent(tree, space='  ')
    scrivx_path = os.path.join(OUT, 'Karma.scrivx')
    tree.write(scrivx_path, encoding='utf-8', xml_declaration=True)

    print(f"Scrivener project: {OUT}")
    print(f"Documents: {doc_counter} in 8 chapters")
    print(f"Open: {scrivx_path}")

if __name__ == '__main__':
    build_project()
