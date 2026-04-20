"""
tests/test_onboarding.py

Testy onboardingu agentów.
Nie wymagają kluczy LLM — mockują wywołanie LLM.

Uruchomienie:
    python tests/test_onboarding.py
    # lub:
    python -m pytest tests/test_onboarding.py -v
"""
import asyncio
import json
import sys
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


class TestPersonalities(unittest.TestCase):
    """Test 1 — słownik osobowości jest kompletny."""

    def test_all_personalities_present(self):
        from agents.onboarding import PERSONALITIES
        required = {"cautious", "aggressive", "neutral", "scalper", "swing"}
        self.assertEqual(set(PERSONALITIES.keys()), required)

    def test_personality_fields(self):
        from agents.onboarding import PERSONALITIES
        for name, cfg in PERSONALITIES.items():
            with self.subTest(personality=name):
                self.assertIn("description",        cfg)
                self.assertIn("risk_profile",        cfg)
                self.assertIn("max_risk_per_trade",  cfg)
                self.assertIsInstance(cfg["max_risk_per_trade"], float)
                self.assertGreater(cfg["max_risk_per_trade"], 0)
                self.assertLessEqual(cfg["max_risk_per_trade"], 0.05)

    def test_risk_order(self):
        """Cautious ma mniejsze ryzyko niż aggressive."""
        from agents.onboarding import PERSONALITIES
        self.assertLess(
            PERSONALITIES["cautious"]["max_risk_per_trade"],
            PERSONALITIES["aggressive"]["max_risk_per_trade"],
        )


class TestPromptBuilder(unittest.TestCase):
    """Test 2 — prompt zawiera wszystkie wymagane elementy."""

    def setUp(self):
        self.strategies = [
            {
                "id":       "mean_rev_v1",
                "text":     "## META\nName: Mean Reversion v1\nCategory: mean_reversion\n\nOpis: Test strategy",
                "metadata": {"category": "mean_reversion"},
            },
            {
                "id":       "momentum_v1",
                "text":     "## META\nName: Momentum v1\nCategory: momentum\n\nOpis: Test strategy",
                "metadata": {"category": "momentum"},
            },
        ]

    def test_prompt_contains_agent_id(self):
        from agents.onboarding import _build_onboarding_prompt
        prompt = _build_onboarding_prompt(
            "trader_test", "neutral", "Test summary", self.strategies
        )
        self.assertIn("trader_test", prompt)

    def test_prompt_contains_strategy_ids(self):
        from agents.onboarding import _build_onboarding_prompt
        prompt = _build_onboarding_prompt(
            "trader_test", "neutral", "Test summary", self.strategies
        )
        self.assertIn("mean_rev_v1", prompt)
        self.assertIn("momentum_v1", prompt)

    def test_prompt_contains_personality(self):
        from agents.onboarding import _build_onboarding_prompt
        prompt = _build_onboarding_prompt(
            "trader_test", "aggressive", "Test summary", self.strategies
        )
        self.assertIn("Agresywny", prompt)
        self.assertIn("high", prompt)

    def test_prompt_requests_json(self):
        from agents.onboarding import _build_onboarding_prompt
        prompt = _build_onboarding_prompt(
            "trader_test", "neutral", "Test summary", self.strategies
        )
        self.assertIn("selected_strategies", prompt)
        self.assertIn("primary_strategy", prompt)
        self.assertIn("risk_per_trade", prompt)

    def test_prompt_strategy_count(self):
        from agents.onboarding import _build_onboarding_prompt
        prompt = _build_onboarding_prompt(
            "trader_test", "neutral", "Test summary", self.strategies
        )
        self.assertIn("2 dokumentow", prompt)


class TestPreferredCategories(unittest.TestCase):
    """Test 3 — mapowanie osobowości na kategorie."""

    def test_cautious_prefers_mean_reversion(self):
        from agents.onboarding import _get_preferred_categories
        cats = _get_preferred_categories("cautious")
        self.assertIn("mean_reversion", cats)

    def test_aggressive_prefers_momentum(self):
        from agents.onboarding import _get_preferred_categories
        cats = _get_preferred_categories("aggressive")
        self.assertIn("momentum", cats)

    def test_unknown_personality_has_fallback(self):
        from agents.onboarding import _get_preferred_categories
        cats = _get_preferred_categories("unknown_personality")
        self.assertIsInstance(cats, list)
        self.assertGreater(len(cats), 0)


class TestRunOnboarding(unittest.IsolatedAsyncioTestCase):
    """Test 4 — pełny onboarding z mock LLM."""

    def setUp(self):
        """Ustaw tymczasowe środowisko testowe."""
        # Używamy istniejącej bazy testowej lub tworzymy tymczasową
        self._tmp_dir = tempfile.mkdtemp()
        self._tmp_db   = str(Path(self._tmp_dir) / "test_trading.db")
        self._tmp_chroma = str(Path(self._tmp_dir) / "chromadb")

    def tearDown(self):
        shutil.rmtree(self._tmp_dir, ignore_errors=True)

    async def test_agent_not_found(self):
        """Onboarding zwraca błąd gdy agent nie istnieje."""
        from agents.onboarding import run_onboarding

        with patch("agents.onboarding.get_agent", return_value=None), \
             patch("agents.onboarding.log_activity"):
            result = await run_onboarding("nonexistent_agent", "neutral")

        self.assertFalse(result["success"])
        self.assertIn("nie istnieje", result["error"])

    async def test_already_onboarded(self):
        """Drugi onboarding zwraca cache zamiast wywoływać LLM."""
        from agents.onboarding import run_onboarding

        mock_agent = {
            "id":               "trader_test",
            "onboarding_done":  1,
            "strategies":       json.dumps(["mean_rev_v1"]),
            "strategy_reasoning": "Test reasoning",
            "risk_per_trade":   0.007,
        }

        with patch("agents.onboarding.get_agent", return_value=mock_agent), \
             patch("agents.onboarding.log_activity"):
            result = await run_onboarding("trader_test", "neutral")

        self.assertTrue(result["success"])
        self.assertTrue(result.get("already_done"))
        self.assertEqual(result["strategies"], ["mean_rev_v1"])
        self.assertEqual(result["model_used"], "cached")

    async def test_successful_onboarding_mock(self):
        """Pełny onboarding z zamockowanym LLM i KB."""
        from agents.onboarding import run_onboarding

        mock_agent = {
            "id":              "trader_test",
            "onboarding_done": 0,
            "strategies":      None,
        }

        mock_strategies = [
            {
                "id":       "mean_rev_v1",
                "text":     "## META\nName: Mean Reversion\nCategory: mean_reversion\n\nOpis: test",
                "metadata": {"category": "mean_reversion"},
            }
        ]

        llm_response = json.dumps({
            "selected_strategies":  ["mean_rev_v1"],
            "reasoning":            "Strategia mean reversion pasuje do profilu cautious.",
            "primary_strategy":     "mean_rev_v1",
            "risk_per_trade":       0.006,
            "preferred_timeframes": ["15m", "1h"],
            "notes":                "Skupiam się na mean reversion.",
        })

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value.choices[0].message.content = llm_response

        with patch("agents.onboarding.get_agent",                        return_value=mock_agent), \
             patch("agents.onboarding.update_agent"), \
             patch("agents.onboarding.set_agent_strategies"), \
             patch("agents.onboarding.log_activity"), \
             patch("agents.onboarding._get_llm_client",                return_value=(mock_client, "test-model")), \
             patch("knowledge_base.query.get_all_strategies",          return_value=mock_strategies), \
             patch("knowledge_base.query.get_strategies_summary",      return_value="Test summary"):
            result = await run_onboarding("trader_test", "cautious")

        self.assertTrue(result["success"], f"Onboarding failed: {result.get('error')}")
        self.assertEqual(result["agent_id"],          "trader_test")
        self.assertIn("mean_rev_v1",                  result["strategies"])
        self.assertEqual(result["primary_strategy"],  "mean_rev_v1")
        self.assertAlmostEqual(result["risk_per_trade"], 0.006, places=4)
        self.assertEqual(result["model_used"],        "test-model")

    async def test_invalid_strategy_id_fallback(self):
        """LLM zwraca nieistniejące ID — system używa fallback."""
        from agents.onboarding import run_onboarding

        mock_agent = {"id": "trader_test", "onboarding_done": 0, "strategies": None}

        mock_strategies = [
            {
                "id":       "real_strategy_v1",
                "text":     "## META\nName: Real Strategy\nCategory: momentum\n\nOpis: test",
                "metadata": {"category": "momentum"},
            }
        ]

        # LLM zwraca nieistniejące ID
        llm_response = json.dumps({
            "selected_strategies":  ["nonexistent_strategy_xyz"],
            "reasoning":            "test",
            "primary_strategy":     "nonexistent_strategy_xyz",
            "risk_per_trade":       0.012,
            "preferred_timeframes": ["1h"],
            "notes":                "",
        })

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value.choices[0].message.content = llm_response

        with patch("agents.onboarding.get_agent",                        return_value=mock_agent), \
             patch("agents.onboarding.update_agent"), \
             patch("agents.onboarding.set_agent_strategies"), \
             patch("agents.onboarding.log_activity"), \
             patch("agents.onboarding._get_llm_client",                return_value=(mock_client, "test-model")), \
             patch("knowledge_base.query.get_all_strategies",          return_value=mock_strategies), \
             patch("knowledge_base.query.get_strategies_summary",      return_value="Test summary"):
            result = await run_onboarding("trader_test", "neutral")

        self.assertTrue(result["success"])
        # Powinien użyć fallback — prawdziwe ID
        self.assertIn("real_strategy_v1", result["strategies"])

    async def test_risk_per_trade_capped(self):
        """Ryzyko z LLM nie przekracza limitu osobowości."""
        from agents.onboarding import run_onboarding

        mock_agent = {"id": "trader_test", "onboarding_done": 0, "strategies": None}
        mock_strategies = [
            {"id": "s1", "text": "## META\nName: S1\nCategory: momentum", "metadata": {}}
        ]

        # LLM chce 10% ryzyka — za dużo dla "cautious" (max 0.7%)
        llm_response = json.dumps({
            "selected_strategies":  ["s1"],
            "reasoning":            "test",
            "primary_strategy":     "s1",
            "risk_per_trade":       0.10,
            "preferred_timeframes": ["15m"],
            "notes":                "",
        })

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value.choices[0].message.content = llm_response

        with patch("agents.onboarding.get_agent",                        return_value=mock_agent), \
             patch("agents.onboarding.update_agent"), \
             patch("agents.onboarding.set_agent_strategies"), \
             patch("agents.onboarding.log_activity"), \
             patch("agents.onboarding._get_llm_client",                return_value=(mock_client, "test-model")), \
             patch("knowledge_base.query.get_all_strategies",          return_value=mock_strategies), \
             patch("knowledge_base.query.get_strategies_summary",      return_value=""):
            result = await run_onboarding("trader_test", "cautious")

        self.assertTrue(result["success"])
        # Ryzyko musi być ≤ max dla cautious (0.007)
        from agents.onboarding import PERSONALITIES
        max_risk = PERSONALITIES["cautious"]["max_risk_per_trade"]
        self.assertLessEqual(result["risk_per_trade"], max_risk)


def run_tests():
    """Uruchom wszystkie testy i wyświetl podsumowanie."""
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestPersonalities))
    suite.addTests(loader.loadTestsFromTestCase(TestPromptBuilder))
    suite.addTests(loader.loadTestsFromTestCase(TestPreferredCategories))
    suite.addTests(loader.loadTestsFromTestCase(TestRunOnboarding))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    ok_count  = result.testsRun - len(result.failures) - len(result.errors)
    err_count = len(result.failures) + len(result.errors)
    print(f"\n{'='*60}")
    print(f"Tests: {result.testsRun} | OK: {ok_count} | Errors: {err_count}")
    print(f"{'='*60}")

    return len(result.failures) + len(result.errors)


if __name__ == "__main__":
    sys.exit(run_tests())
