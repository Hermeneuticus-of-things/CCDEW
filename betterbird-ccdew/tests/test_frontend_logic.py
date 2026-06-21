#!/usr/bin/env python3
"""
BB Email Dashboard — Frontend Static Tests
Nivel: HTML structure, JS logic, CSS, manifest, security
Nu necesită browser — analizează sursele direct.
Rulare: python3 tests/test_frontend_logic.py
"""

import sys, os, re, json, unittest

ROOT = os.path.join(os.path.dirname(__file__), '..')
SIDEBAR = os.path.join(ROOT, 'sidebar.html')
MANIFEST = os.path.join(ROOT, 'manifest.json')
BACKGROUND = os.path.join(ROOT, 'background.js')


def read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


class TestSidebarHTML(unittest.TestCase):
    """Validare structurală HTML + accesibilitate."""

    def setUp(self):
        self.html = read(SIDEBAR)

    def test_are_doctype(self):
        self.assertTrue(self.html.strip().startswith('<!DOCTYPE html'))

    def test_lang_ro(self):
        self.assertIn('lang="ro"', self.html)

    def test_charset_utf8(self):
        self.assertIn('charset="utf-8"', self.html.lower())

    def test_viewport_meta(self):
        self.assertIn('viewport', self.html)

    def test_aria_live_pe_alerts(self):
        self.assertIn('aria-live', self.html)

    def test_role_list_pe_alerts(self):
        self.assertIn('role="list"', self.html)

    def test_tabindex_pe_carduri(self):
        self.assertIn('tabindex="0"', self.html)

    def test_keyboard_handler_prezent(self):
        self.assertIn('onkeydown', self.html)
        self.assertIn('Enter', self.html)

    def test_toast_container_exista(self):
        self.assertIn('toast-container', self.html)

    def test_status_bar_exista(self):
        self.assertIn('status-bar', self.html)

    def test_refresh_buton_exista(self):
        self.assertIn('refreshBtn', self.html)

    def test_filtre_toate_prezente(self):
        for f in ['all', 'immediate', 'today', 'security', 'financial', 'phishing']:
            self.assertIn(f'data-filter="{f}"', self.html, f'Filtru lipsă: {f}')

    def test_server_url_localhost_8766(self):
        self.assertIn('localhost:8766', self.html)


class TestSidebarCSS(unittest.TestCase):
    """Validare CSS — fix-uri aplicate."""

    def setUp(self):
        self.html = read(SIDEBAR)

    def test_padding_bottom_pe_body(self):
        # Body trebuie să aibă padding-bottom pentru status-bar
        self.assertIn('padding-bottom', self.html)

    def test_refresh_bottom_suficient(self):
        # Butonul refresh trebuie să fie cel puțin la bottom:30px
        match = re.search(r'\.refresh\{[^}]+bottom:(\d+)px', self.html)
        if match:
            val = int(match.group(1))
            self.assertGreaterEqual(val, 30, f'Refresh bottom prea mic: {val}px')

    def test_prefers_reduced_motion_prezent(self):
        self.assertIn('prefers-reduced-motion', self.html)

    def test_focus_visible_prezent(self):
        self.assertIn('focus-visible', self.html)

    def test_hover_none_media_query(self):
        # Acțiunile trebuie să fie vizibile pe touch
        self.assertIn('hover:none', self.html)

    def test_meta_contrast_imbunatatit(self):
        # Culoarea veche #484f58 trebuie înlocuită cu ceva mai luminos
        self.assertNotIn('#484f58', self.html)

    def test_z_index_ierarhie(self):
        # toast z:200 > refresh z:100 > status-bar z:90
        toast_z = re.search(r'toast-container[^{]*\{[^}]*z-index:(\d+)', self.html)
        refresh_z = re.search(r'\.refresh\{[^}]+z-index:(\d+)', self.html)
        if toast_z and refresh_z:
            self.assertGreater(int(toast_z.group(1)), int(refresh_z.group(1)))


class TestSidebarJavaScript(unittest.TestCase):
    """Validare logică JavaScript."""

    def setUp(self):
        self.html = read(SIDEBAR)
        # Extrage scriptul
        m = re.search(r'<script>(.*?)</script>', self.html, re.DOTALL)
        self.js = m.group(1) if m else ''

    def test_iife_prezent(self):
        # Codul trebuie encapsulat în IIFE
        self.assertTrue(
            self.js.strip().startswith('(function()') or
            '(function(){' in self.js or
            '(function() {' in self.js
        )

    def test_iife_inchis(self):
        self.assertIn('})()', self.js.replace(' ', '').replace('\n', ''))

    def test_nu_window_lastData(self):
        # Variabila globală veche trebuie eliminată
        self.assertNotIn('window._lastData', self.js)

    def test_lastData_local(self):
        self.assertIn('lastData', self.js)

    def test_clearInterval_prezent(self):
        self.assertIn('clearInterval', self.js)

    def test_abortcontroller_prezent(self):
        self.assertIn('AbortController', self.js)

    def test_timeout_fetch(self):
        self.assertIn('setTimeout', self.js)
        self.assertIn('ctrl.abort', self.js)

    def test_esc_escapeaza_apostrofe(self):
        self.assertIn("&#39;", self.js)

    def test_api_action_endpoint(self):
        # Nu mai apelează bb-open pentru archive
        self.assertNotIn("'archive'", self.js.split('api/bb-open')[0] if 'api/bb-open' in self.js else self.js)
        self.assertIn('/api/action', self.js)

    def test_update_sticky_top_prezent(self):
        self.assertIn('updateStickyTop', self.js)

    def test_requestAnimationFrame_folosit(self):
        self.assertIn('requestAnimationFrame', self.js)

    def test_window_resize_listener(self):
        self.assertIn("'resize'", self.js)

    def test_show_toast_cu_type(self):
        # showToast trebuie să accepte param 'type'
        self.assertIn('function showToast', self.js)
        m = re.search(r'function showToast\(([^)]+)\)', self.js)
        if m:
            params = m.group(1)
            self.assertIn('type', params)


class TestManifest(unittest.TestCase):
    """Validare manifest.json."""

    def setUp(self):
        self.manifest = json.loads(read(MANIFEST))

    def test_manifest_version_2(self):
        self.assertEqual(self.manifest['manifest_version'], 2)

    def test_are_gecko_id(self):
        self.assertIn('applications', self.manifest)
        self.assertIn('gecko', self.manifest['applications'])
        self.assertIn('id', self.manifest['applications']['gecko'])

    def test_permisiuni_minime(self):
        perms = self.manifest.get('permissions', [])
        self.assertIn('tabs', perms)
        self.assertIn('messagesRead', perms)
        self.assertIn('http://localhost:8766/*', perms)

    def test_messages_update_eliminat(self):
        # messagesUpdate era inutilă — trebuie eliminată
        perms = self.manifest.get('permissions', [])
        self.assertNotIn('messagesUpdate', perms)

    def test_csp_prezent(self):
        self.assertIn('content_security_policy', self.manifest)
        csp = self.manifest['content_security_policy']
        self.assertIn("script-src 'self'", csp)

    def test_icons_definite(self):
        icons = self.manifest.get('icons', {})
        self.assertIn('48', icons)

    def test_icons_fisiere_exista(self):
        for size, path in self.manifest.get('icons', {}).items():
            full = os.path.join(ROOT, path)
            self.assertTrue(os.path.exists(full), f'Icon lipsă: {path}')

    def test_background_script_exista(self):
        scripts = self.manifest.get('background', {}).get('scripts', [])
        for s in scripts:
            full = os.path.join(ROOT, s)
            self.assertTrue(os.path.exists(full), f'Background script lipsă: {s}')

    def test_versiune_semver(self):
        v = self.manifest.get('version', '')
        parts = v.split('.')
        self.assertEqual(len(parts), 3)
        for p in parts:
            self.assertTrue(p.isdigit(), f'Versiune invalidă: {v}')


class TestBackgroundJS(unittest.TestCase):
    """Validare background.js — logică extensie."""

    def setUp(self):
        self.js = read(BACKGROUND)

    def test_open_dashboard_functie_exista(self):
        self.assertIn('openDashboard', self.js)

    def test_browser_action_listener(self):
        self.assertIn('browserAction.onClicked', self.js)

    def test_message_listener_prezent(self):
        self.assertIn('runtime.onMessage', self.js)

    def test_open_email_handler_prezent(self):
        self.assertIn("'openEmail'", self.js)

    def test_return_true_pentru_async(self):
        # Esențial pentru răspunsuri asincrone în extensii
        self.assertIn('return true', self.js)

    def test_skip_spam_implementat(self):
        self.assertIn('spam', self.js.lower())
        self.assertIn('junk', self.js.lower())
        self.assertIn('trash', self.js.lower())

    def test_subfoldere_recursive(self):
        self.assertIn('subFolders', self.js)

    def test_collect_folders_functie(self):
        self.assertIn('collectFolders', self.js)

    def test_prioritate_inbox(self):
        self.assertIn('inbox', self.js.lower())
        self.assertIn('priorityOrder', self.js)

    def test_fallback_open_implementat(self):
        # Dacă emailul nu se găsește, trebuie să returneze mesaj clar
        self.assertIn('opened: false', self.js)

    def test_error_handling_pe_folder(self):
        # Foldere care nu suportă query trebuie prinse
        self.assertIn('catch', self.js)

    def test_iife_sau_use_strict(self):
        # Codul trebuie encapsulat
        self.assertTrue(
            '(function()' in self.js or
            "'use strict'" in self.js or
            self.js.strip().startswith('(')
        )


class TestSecuritateStatica(unittest.TestCase):
    """Analiză statică pentru probleme de securitate."""

    def setUp(self):
        self.sidebar = read(SIDEBAR)
        self.background = read(BACKGROUND)

    def test_nu_eval_in_sidebar(self):
        # eval() e periculos
        self.assertNotIn('eval(', self.sidebar)

    def test_nu_document_write_in_sidebar(self):
        self.assertNotIn('document.write(', self.sidebar)

    def test_innerHTML_foloseste_esc(self):
        # Orice valoare pusă în innerHTML trebuie escapată
        # Verificăm că funcția esc() e definită și apelată
        self.assertIn('function esc(', self.sidebar)
        # Numărăm apeluri esc() vs string-uri directe în innerHTML
        esc_calls = len(re.findall(r'esc\(', self.sidebar))
        self.assertGreater(esc_calls, 5, 'Prea puține apeluri esc() pentru innerHTML')

    def test_nu_innerHTML_cu_input_direct(self):
        # innerHTML='...' + string neescapat e periculos
        # Verificăm că nu există pattern-uri clare de injecție
        dangerous = re.findall(r'innerHTML\s*=\s*[^\'"]', self.sidebar)
        # Singurele innerHTML valide sunt cu string-uri construite sau constante
        self.assertLessEqual(len(dangerous), 3)

    def test_manifest_csp_no_unsafe_inline(self):
        manifest = json.loads(read(MANIFEST))
        csp = manifest.get('content_security_policy', '')
        self.assertNotIn("'unsafe-inline'", csp)
        self.assertNotIn("'unsafe-eval'", csp)

    def test_localhost_only_in_server(self):
        # Server-ul trebuie să asculte doar pe 127.0.0.1, nu 0.0.0.0
        server_path = os.path.join(ROOT, '..', '.claude', 'helpers', 'email-dashboard-server.py')
        if os.path.exists(server_path):
            src = read(server_path)
            # Verificăm că bind-ul e pe 127.0.0.1
            self.assertIn('127.0.0.1', src)
            # Nu trebuie să asculte pe 0.0.0.0 explicit
            self.assertNotIn("('0.0.0.0'", src)


if __name__ == '__main__':
    print('=' * 60)
    print('BB Email Dashboard — Frontend Static Tests')
    print('=' * 60)
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for cls in [TestSidebarHTML, TestSidebarCSS, TestSidebarJavaScript,
                TestManifest, TestBackgroundJS, TestSecuritateStatica]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
