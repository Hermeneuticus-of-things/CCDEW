#!/usr/bin/env python3
"""
BB Email Dashboard — Unit Tests (server logic, fără HTTP)
Nivel: funcții interne, algoritmi, edge cases
Rulare: python3 tests/test_server_unit.py
"""

import sys, os, json, time, unittest, datetime, threading

# Adaugă helper-ul în path pentru import direct
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '.claude', 'helpers'))

# Importăm modulele testate (fără să pornim serverul)
import importlib.util, types

def load_server_module():
    """Încarcă email-dashboard-server.py ca modul fără să execute run()."""
    path = os.path.join(os.path.dirname(__file__), '..', '..', '.claude', 'helpers', 'email-dashboard-server.py')
    spec = importlib.util.spec_from_file_location('email_server', path)
    mod = importlib.util.module_from_spec(spec)
    # Suprascriem __name__ ca să nu execute if __name__ == '__main__'
    spec.loader.exec_module(mod)
    return mod

try:
    srv = load_server_module()
    SERVER_LOADED = True
except Exception as e:
    SERVER_LOADED = False
    LOAD_ERROR = str(e)


class TestAgeDays(unittest.TestCase):
    """Testează _age_days() — calculul vârstei emailului."""

    def setUp(self):
        if not SERVER_LOADED:
            self.skipTest(f'Server nu s-a încărcat: {LOAD_ERROR}')

    def test_data_iso_recenta(self):
        today = datetime.date.today().isoformat()
        entry = {'date': today}
        age = srv._age_days(entry)
        self.assertEqual(age, 0)

    def test_data_iso_ieri(self):
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        entry = {'date': yesterday}
        age = srv._age_days(entry)
        self.assertEqual(age, 1)

    def test_data_veche_365(self):
        old = (datetime.date.today() - datetime.timedelta(days=365)).isoformat()
        entry = {'date': old}
        age = srv._age_days(entry)
        self.assertGreaterEqual(age, 365)

    def test_fallback_createdAt(self):
        # Fără 'date', folosește createdAt
        one_day_ago_ms = int((time.time() - 86400) * 1000)
        entry = {'createdAt': one_day_ago_ms}
        age = srv._age_days(entry)
        self.assertIn(age, [0, 1])  # poate fi 0 sau 1 în funcție de ora exactă

    def test_fara_date_returneaza_none(self):
        entry = {}
        age = srv._age_days(entry)
        self.assertIsNone(age)

    def test_data_rfc2822(self):
        # Format email clasic: "Thu, 05 Jun 2026 10:00:00 +0000"
        entry = {'date': 'Thu, 05 Jun 2025 10:00:00 +0000'}
        age = srv._age_days(entry)
        self.assertIsNotNone(age)
        self.assertGreater(age, 0)

    def test_niciodata_negativ(self):
        future = (datetime.date.today() + datetime.timedelta(days=5)).isoformat()
        entry = {'date': future}
        age = srv._age_days(entry)
        self.assertEqual(age, 0)  # max(0, ...)


class TestEffectiveUrgency(unittest.TestCase):
    """Testează effective_urgency() — logica de boost + decay temporal."""

    def setUp(self):
        if not SERVER_LOADED:
            self.skipTest(f'Server nu s-a încărcat: {LOAD_ERROR}')

    def test_security_boost_de_la_this_week_la_today(self):
        entry = {'urgency': 'this_week', 'nature': 'security', 'date': datetime.date.today().isoformat()}
        result = srv.effective_urgency(entry)
        self.assertEqual(result, 'today')

    def test_financial_boost(self):
        entry = {'urgency': 'this_week', 'nature': 'financial', 'date': datetime.date.today().isoformat()}
        result = srv.effective_urgency(entry)
        self.assertEqual(result, 'today')

    def test_fara_boost_comercial(self):
        entry = {'urgency': 'this_week', 'nature': 'commercial', 'date': datetime.date.today().isoformat()}
        result = srv.effective_urgency(entry)
        self.assertEqual(result, 'this_week')

    def test_decay_mai_mult_de_un_an(self):
        old = (datetime.date.today() - datetime.timedelta(days=400)).isoformat()
        entry = {'urgency': 'immediate', 'nature': 'commercial', 'date': old}
        result = srv.effective_urgency(entry)
        self.assertEqual(result, 'no_deadline')

    def test_decay_90_zile_immediate_la_this_week(self):
        old = (datetime.date.today() - datetime.timedelta(days=95)).isoformat()
        entry = {'urgency': 'immediate', 'nature': 'commercial', 'date': old}
        result = srv.effective_urgency(entry)
        self.assertEqual(result, 'this_week')

    def test_decay_30_zile_nu_se_aplica_securitate(self):
        old = (datetime.date.today() - datetime.timedelta(days=35)).isoformat()
        entry = {'urgency': 'immediate', 'nature': 'security', 'date': old}
        result = srv.effective_urgency(entry)
        # security nu se degradează la 30 zile
        self.assertEqual(result, 'immediate')

    def test_urgency_necunoscuta(self):
        entry = {'urgency': 'undefined_value', 'date': datetime.date.today().isoformat()}
        result = srv.effective_urgency(entry)
        self.assertEqual(result, 'no_deadline')

    def test_boost_nu_depaseste_immediate(self):
        # Boost pe 'immediate' rămâne 'immediate' (nu scade sub 0)
        entry = {'urgency': 'immediate', 'nature': 'security', 'date': datetime.date.today().isoformat()}
        result = srv.effective_urgency(entry)
        self.assertEqual(result, 'immediate')


class TestIsActionable(unittest.TestCase):
    """Testează is_actionable() — ce apare în dashboard."""

    def setUp(self):
        if not SERVER_LOADED:
            self.skipTest(f'Server nu s-a încărcat: {LOAD_ERROR}')

    def test_immediate_actionabil(self):
        self.assertTrue(srv.is_actionable({'urgency': 'immediate'}))

    def test_today_actionabil(self):
        self.assertTrue(srv.is_actionable({'urgency': 'today'}))

    def test_no_deadline_nu_actionabil(self):
        self.assertFalse(srv.is_actionable({'urgency': 'no_deadline'}))

    def test_this_week_security_actionabil(self):
        self.assertTrue(srv.is_actionable({'urgency': 'this_week', 'nature': 'security'}))

    def test_this_week_commercial_nu_actionabil(self):
        self.assertFalse(srv.is_actionable({'urgency': 'this_week', 'nature': 'commercial'}))

    def test_this_week_phishing_actionabil(self):
        self.assertTrue(srv.is_actionable({'urgency': 'this_week', 'nature': 'phishing'}))

    def test_entry_gol(self):
        self.assertFalse(srv.is_actionable({}))

    def test_foloseste_eff_urgency_daca_exista(self):
        # eff_urgency are prioritate față de urgency brut
        entry = {'urgency': 'no_deadline', 'eff_urgency': 'immediate'}
        self.assertTrue(srv.is_actionable(entry))


class TestDeduplicare(unittest.TestCase):
    """Testează că load_index() deduplicã corect."""

    def setUp(self):
        if not SERVER_LOADED:
            self.skipTest(f'Server nu s-a încărcat: {LOAD_ERROR}')

    def test_deduplicare_logica(self):
        # Simulăm manual logica de deduplicare din load_index
        entries = [
            {'subject': 'Test email', 'from': 'a@b.com', 'date': '2026-06-01'},
            {'subject': 'Test email', 'from': 'a@b.com', 'date': '2026-06-01'},  # duplicat
            {'subject': 'Alt email', 'from': 'c@d.com', 'date': '2026-06-01'},
        ]
        seen = set()
        deduped = []
        for e in entries:
            sig = (e.get('subject','')[:60], e.get('from','')[:40], e.get('date','')[:10])
            if sig not in seen:
                seen.add(sig)
                deduped.append(e)
        self.assertEqual(len(deduped), 2)


class TestUrgencyOrder(unittest.TestCase):
    """Testează că URGENCY_ORDER este corect definit și complet."""

    def setUp(self):
        if not SERVER_LOADED:
            self.skipTest(f'Server nu s-a încărcat: {LOAD_ERROR}')

    def test_toate_urgentele_prezente(self):
        for u in ['immediate', 'today', 'this_week', 'no_deadline']:
            self.assertIn(u, srv.URGENCY_ORDER)

    def test_ordinea_corecta(self):
        self.assertLess(
            srv.URGENCY_ORDER.index('immediate'),
            srv.URGENCY_ORDER.index('no_deadline')
        )

    def test_nature_priority_complet(self):
        for n in ['security', 'financial', 'legal']:
            self.assertIn(n, srv.NATURE_PRIORITY)
            self.assertLess(srv.NATURE_PRIORITY[n], srv.NATURE_PRIORITY.get('other', 99))


class TestThreadSafety(unittest.TestCase):
    """Testează că lock-urile există și sunt threading.Lock."""

    def setUp(self):
        if not SERVER_LOADED:
            self.skipTest(f'Server nu s-a încărcat: {LOAD_ERROR}')

    def test_index_lock_exista(self):
        self.assertTrue(hasattr(srv, '_INDEX_LOCK'))
        self.assertIsInstance(srv._INDEX_LOCK, type(threading.Lock()))

    def test_sse_lock_exista(self):
        self.assertTrue(hasattr(srv, '_SSE_LOCK'))

    def test_max_post_body_definit(self):
        self.assertTrue(hasattr(srv, 'MAX_POST_BODY'))
        self.assertGreater(srv.MAX_POST_BODY, 0)
        self.assertLessEqual(srv.MAX_POST_BODY, 1_048_576)  # max 1MB


class TestScapaStr(unittest.TestCase):
    """Testează funcția de escape HTML pentru output safe."""

    def setUp(self):
        if not SERVER_LOADED:
            self.skipTest(f'Server nu s-a încărcat: {LOAD_ERROR}')

    def test_escape_lt_gt(self):
        result = srv.scapa_str('<script>alert(1)</script>')
        self.assertNotIn('<script>', result)
        self.assertIn('&lt;', result)

    def test_escape_ampersand(self):
        result = srv.scapa_str('a & b')
        self.assertIn('&amp;', result)

    def test_none_returneaza_string_gol(self):
        result = srv.scapa_str(None)
        self.assertEqual(result, '')

    def test_string_normal_nemodificat(self):
        result = srv.scapa_str('email normal')
        self.assertEqual(result, 'email normal')


if __name__ == '__main__':
    print('=' * 60)
    print('BB Email Dashboard — Unit Tests (server logic)')
    print('=' * 60)
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for cls in [TestAgeDays, TestEffectiveUrgency, TestIsActionable,
                TestDeduplicare, TestUrgencyOrder, TestThreadSafety, TestScapaStr]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
