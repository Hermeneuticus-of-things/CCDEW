#!/usr/bin/env python3
"""
BB Email Dashboard — Integration Tests (API HTTP live)
Nivel: toate endpoint-urile, CORS, response shape, edge cases
Cerință: serverul să ruleze pe localhost:8766
Rulare: python3 tests/test_api_integration.py
"""

import sys, os, json, time, unittest, urllib.request, urllib.error, urllib.parse, http.client

BASE = 'http://localhost:8766'
TIMEOUT = 10


def get(path, expect_json=True):
    url = BASE + path
    req = urllib.request.Request(url, headers={'Cache-Control': 'no-cache'})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        body = r.read().decode('utf-8')
        if expect_json:
            return r.status, r.headers, json.loads(body)
        return r.status, r.headers, body


def post(path, payload):
    url = BASE + path
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, method='POST',
                                  headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            body = r.read().decode('utf-8')
            return r.status, r.headers, json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        return e.code, e.headers, json.loads(body) if body else {}


def options(path):
    conn = http.client.HTTPConnection('localhost', 8766, timeout=TIMEOUT)
    conn.request('OPTIONS', path, headers={
        'Origin': BASE,
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'Content-Type',
    })
    r = conn.getresponse()
    headers = {k.lower(): v for k, v in r.getheaders()}
    conn.close()
    return r.status, headers


def server_is_up():
    try:
        get('/api/health')
        return True
    except Exception:
        return False


@unittest.skipUnless(server_is_up(), 'Server offline — pornește: python3 email-dashboard-server.py 8766')
class TestEndpointHealth(unittest.TestCase):

    def test_health_returneaza_ok(self):
        status, _, data = get('/api/health')
        self.assertEqual(status, 200)
        self.assertEqual(data.get('status'), 'ok')

    def test_health_are_entries(self):
        _, _, data = get('/api/health')
        self.assertIn('entries', data)
        self.assertIsInstance(data['entries'], int)
        self.assertGreaterEqual(data['entries'], 0)


@unittest.skipUnless(server_is_up(), 'Server offline')
class TestEndpointImpactAlerts(unittest.TestCase):
    """Endpoint principal consumat de sidebar.html."""

    def test_returneaza_200(self):
        status, _, _ = get('/api/impact-alerts')
        self.assertEqual(status, 200)

    def test_structura_corecta(self):
        _, _, data = get('/api/impact-alerts')
        self.assertIn('total_alerts', data)
        self.assertIn('alerts', data)
        self.assertIsInstance(data['alerts'], list)

    def test_fiecare_alerta_are_campuri_obligatorii(self):
        _, _, data = get('/api/impact-alerts')
        for alert in data.get('alerts', [])[:10]:
            self.assertIn('subject', alert, f'Lipsă subject în: {alert}')
            self.assertIn('urgency', alert, f'Lipsă urgency în: {alert}')

    def test_urgency_valori_valide(self):
        valid = {'immediate', 'today', 'this_week', 'no_deadline'}
        _, _, data = get('/api/impact-alerts')
        for alert in data.get('alerts', []):
            urg = alert.get('urgency', '')
            if urg:
                self.assertIn(urg, valid, f'Urgency invalidă: {urg}')

    def test_nu_contine_xss_in_subject(self):
        _, _, data = get('/api/impact-alerts')
        for alert in data.get('alerts', [])[:20]:
            subject = alert.get('subject', '')
            # Nu ar trebui să conțină tag-uri HTML neescapate
            self.assertNotIn('<script', subject.lower())


@unittest.skipUnless(server_is_up(), 'Server offline')
class TestEndpointActionable(unittest.TestCase):

    def test_returneaza_200(self):
        status, _, _ = get('/api/actionable')
        self.assertEqual(status, 200)

    def test_structura_paginare(self):
        _, _, data = get('/api/actionable')
        for key in ['total', 'page', 'limit', 'results']:
            self.assertIn(key, data)

    def test_paginare_functioneaza(self):
        _, _, p1 = get('/api/actionable?page=1&limit=5')
        _, _, p2 = get('/api/actionable?page=2&limit=5')
        self.assertIsInstance(p1['results'], list)
        self.assertLessEqual(len(p1['results']), 5)
        # Paginile nu trebuie să fie identice dacă există suficiente rezultate
        if p1['total'] > 5:
            self.assertNotEqual(p1['results'], p2['results'])

    def test_limit_maxim_respectat(self):
        # Limita maxima e 200
        _, _, data = get('/api/actionable?limit=9999')
        self.assertLessEqual(data['limit'], 200)


@unittest.skipUnless(server_is_up(), 'Server offline')
class TestEndpointBB(unittest.TestCase):
    """Endpoint /bb — versiunea compactă pentru BetterBird."""

    def test_returneaza_html(self):
        status, headers, body = get('/bb', expect_json=False)
        self.assertEqual(status, 200)
        ct = headers.get('Content-Type', '')
        self.assertIn('text/html', ct)

    def test_contine_tabel_email(self):
        _, _, body = get('/bb', expect_json=False)
        self.assertIn('<table', body)

    def test_html_valid_incepe_cu_doctype(self):
        _, _, body = get('/bb', expect_json=False)
        self.assertTrue(body.strip().startswith('<!DOCTYPE'))

    def test_cache_control_no_cache(self):
        _, headers, _ = get('/bb', expect_json=False)
        cc = headers.get('Cache-Control', '')
        self.assertIn('no-cache', cc)


@unittest.skipUnless(server_is_up(), 'Server offline')
class TestEndpointAction(unittest.TestCase):
    """Endpoint /api/action — arhivare / amânare."""

    def test_archive_returneaza_ok(self):
        status, _, data = post('/api/action', {
            'action': 'archive',
            'subject': 'Test subject unitest',
            'from': 'test@example.com',
            'date': '2026-06-05'
        })
        self.assertEqual(status, 200)
        self.assertTrue(data.get('ok'))
        self.assertEqual(data.get('action'), 'archive')

    def test_snooze_returneaza_ok(self):
        status, _, data = post('/api/action', {
            'action': 'snooze',
            'subject': 'Test snooze',
        })
        self.assertEqual(status, 200)
        self.assertTrue(data.get('ok'))

    def test_body_gol_nu_crasha(self):
        # POST fără body — nu trebuie să crașeze serverul
        conn = http.client.HTTPConnection('localhost', 8766, timeout=TIMEOUT)
        conn.request('POST', '/api/action', body=b'',
                     headers={'Content-Type': 'application/json', 'Content-Length': '0'})
        r = conn.getresponse()
        self.assertIn(r.status, [200, 400])
        conn.close()

    def test_actiunea_se_logheza_in_fisier(self):
        log_file = os.path.expanduser('~/.local/state/ccdew-actions.jsonl')
        # Numărul de linii înainte
        before = 0
        if os.path.exists(log_file):
            with open(log_file) as f:
                before = sum(1 for _ in f)
        # Trimitem acțiune
        post('/api/action', {'action': 'archive', 'subject': 'LogTest-' + str(time.time())})
        time.sleep(0.1)
        # Numărul de linii după
        after = 0
        if os.path.exists(log_file):
            with open(log_file) as f:
                after = sum(1 for _ in f)
        self.assertGreater(after, before)


@unittest.skipUnless(server_is_up(), 'Server offline')
class TestCORS(unittest.TestCase):
    """Testează headerele CORS necesare pentru fetch din extension."""

    def test_get_are_acao_header(self):
        _, headers, _ = get('/api/health')
        acao = headers.get('Access-Control-Allow-Origin', '')
        self.assertTrue(acao in ['*', BASE], f'ACAO header lipsă sau greșit: {acao!r}')

    def test_options_preflight_returneaza_204(self):
        status, headers = options('/api/action')
        self.assertEqual(status, 204)

    def test_options_are_allow_methods(self):
        _, headers = options('/api/action')
        methods = headers.get('access-control-allow-methods', '')
        self.assertIn('POST', methods)
        self.assertIn('GET', methods)

    def test_options_are_allow_headers(self):
        _, headers = options('/api/action')
        ah = headers.get('access-control-allow-headers', '')
        self.assertIn('Content-Type', ah)


@unittest.skipUnless(server_is_up(), 'Server offline')
class TestSecurity(unittest.TestCase):
    """Testează securitatea endpoint-urilor."""

    def test_path_traversal_bb_open_blocat(self):
        # Încearcă să deschidă un fișier în afara cache-ului
        status, _, data = get('/api/bb-open?q=../../etc/passwd')
        # Nu trebuie să returneze success=True cu path traversal
        if isinstance(data, dict):
            self.assertNotEqual(data.get('ok'), True)

    def test_post_body_urias_nu_blocheaza_serverul(self):
        # Trimite exact MAX_POST_BODY+1 bytes — serverul trebuie să răspundă
        big_payload = 'x' * 70_000
        conn = http.client.HTTPConnection('localhost', 8766, timeout=TIMEOUT)
        body = json.dumps({'action': 'archive', 'subject': big_payload}).encode()
        conn.request('POST', '/api/action', body=body,
                     headers={'Content-Type': 'application/json',
                               'Content-Length': str(len(body))})
        r = conn.getresponse()
        r.read()  # consumăm răspunsul
        self.assertIn(r.status, [200, 400, 413])
        conn.close()

    def test_404_pentru_path_necunoscut(self):
        try:
            status, _, _ = get('/api/inexistent_endpoint_xyz', expect_json=False)
        except urllib.error.HTTPError as e:
            status = e.code
        self.assertEqual(status, 404)

    def test_search_injection_sigur(self):
        # Caractere speciale în search — nu trebuie să crașeze
        payload = urllib.parse.quote('<script>alert(1)</script>')
        try:
            status, _, data = get(f'/api/search?q={payload}')
            self.assertEqual(status, 200)
        except Exception as e:
            self.fail(f'Search cu XSS input a crăpat: {e}')


@unittest.skipUnless(server_is_up(), 'Server offline')
class TestSearch(unittest.TestCase):

    def test_search_fara_parametri_returneaza_actionabile(self):
        _, _, data = get('/api/search')
        self.assertIn('results', data)
        self.assertIn('total', data)

    def test_search_cu_query_returneaza_rezultate(self):
        _, _, data = get('/api/search?q=email')
        self.assertIn('results', data)
        self.assertIsInstance(data['results'], list)

    def test_search_paginare(self):
        _, _, data = get('/api/search?limit=3&page=1')
        self.assertLessEqual(len(data.get('results', [])), 3)

    def test_search_nature_filter(self):
        _, _, data = get('/api/search?nature=security')
        for r in data.get('results', []):
            self.assertEqual(r.get('nature'), 'security')

    def test_search_urgency_filter(self):
        _, _, data = get('/api/search?urgency=immediate')
        for r in data.get('results', []):
            self.assertIn(r.get('urgency'), ['immediate'])


@unittest.skipUnless(server_is_up(), 'Server offline')
class TestPerformanta(unittest.TestCase):
    """Testează că endpoint-urile răspund în timp rezonabil."""

    def _timp_raspuns(self, path):
        start = time.time()
        get(path)
        return time.time() - start

    def test_health_sub_500ms(self):
        t = self._timp_raspuns('/api/health')
        self.assertLess(t, 0.5, f'Health prea lent: {t:.2f}s')

    def test_impact_alerts_sub_2s(self):
        t = self._timp_raspuns('/api/impact-alerts')
        self.assertLess(t, 2.0, f'impact-alerts prea lent: {t:.2f}s')

    def test_bb_sub_3s(self):
        # /bb returnează HTML, nu JSON — măsurăm doar timpul
        start = time.time()
        url = BASE + '/bb'
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            r.read()
        t = time.time() - start
        self.assertLess(t, 3.0, f'/bb prea lent: {t:.2f}s')

    def test_requests_paralele_nu_blocheaza(self):
        """ThreadingHTTPServer trebuie să gestioneze 5 request-uri simultan."""
        import concurrent.futures
        def req(_):
            try:
                get('/api/health')
                return True
            except Exception:
                return False
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
            results = list(ex.map(req, range(5)))
        self.assertTrue(all(results), 'Unele request-uri paralele au eșuat')


if __name__ == '__main__':
    print('=' * 60)
    print('BB Email Dashboard — Integration Tests (API HTTP)')
    print(f'Target: {BASE}')
    print('=' * 60)
    if not server_is_up():
        print('\n⚠️  SERVERUL NU RULEAZĂ!')
        print('Pornește: python3 .claude/helpers/email-dashboard-server.py 8766\n')
        sys.exit(2)
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for cls in [TestEndpointHealth, TestEndpointImpactAlerts, TestEndpointActionable,
                TestEndpointBB, TestEndpointAction, TestCORS, TestSecurity,
                TestSearch, TestPerformanta]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
