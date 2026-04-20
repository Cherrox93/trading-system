"""
tests/test_telegram.py

Testy dla modulu telegram (reporter + commands).
Uruchomienie: python tests/test_telegram.py
"""
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from unittest import IsolatedAsyncioTestCase

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ── Test 1: reporter.send_message ─────────────────────────────────────────────

class TestReporterSendMessage(IsolatedAsyncioTestCase):
    """send_message wysyla HTTP POST i zwraca True."""

    async def test_send_message_ok(self):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__  = AsyncMock(return_value=False)
        mock_client.post       = AsyncMock(return_value=mock_response)

        with patch.dict("os.environ", {
            "TELEGRAM_BOT_TOKEN": "test_token",
            "TELEGRAM_CHAT_ID":   "123456",
        }):
            with patch("httpx.AsyncClient", return_value=mock_client):
                from telegram.reporter import send_message
                result = await send_message("Hello Test")

        self.assertTrue(result)
        mock_client.post.assert_called_once()
        call_kwargs = mock_client.post.call_args
        payload = call_kwargs[1]["json"] if call_kwargs[1] else call_kwargs[0][1]
        self.assertEqual(payload["text"], "Hello Test")
        self.assertEqual(payload["chat_id"], "123456")

    async def test_send_message_no_config(self):
        """Bez tokenu zwraca False i nie wykonuje zadnych requestow."""
        with patch.dict("os.environ", {}, clear=True):
            # wyczysc token/chat_id
            import os
            os.environ.pop("TELEGRAM_BOT_TOKEN", None)
            os.environ.pop("TELEGRAM_CHAT_ID",   None)

            from telegram.reporter import send_message
            with patch("httpx.AsyncClient") as mock_cls:
                result = await send_message("Should not send")

        self.assertFalse(result)
        mock_cls.assert_not_called()

    async def test_send_message_truncates_long_text(self):
        """Tekst dluzszy niz 4000 znakow jest obcinany."""
        captured = {}

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__  = AsyncMock(return_value=False)

        async def capture_post(url, **kwargs):
            captured["text"] = kwargs["json"]["text"]
            return mock_response

        mock_client.post = capture_post

        with patch.dict("os.environ", {
            "TELEGRAM_BOT_TOKEN": "tok",
            "TELEGRAM_CHAT_ID":   "999",
        }):
            with patch("httpx.AsyncClient", return_value=mock_client):
                from telegram.reporter import send_message
                long_text = "A" * 5000
                await send_message(long_text)

        self.assertIn("skrocono", captured["text"])
        self.assertLessEqual(len(captured["text"]), 4100)


# ── Test 2: reporter.send_daily_report ────────────────────────────────────────

class TestReporterDailyReport(IsolatedAsyncioTestCase):
    """send_daily_report formatuje i wysyla raport."""

    async def test_send_daily_report_calls_send_message(self):
        agents_data = [
            {
                "id":          "trader_01",
                "status":      "active",
                "pnl":         12.5,
                "performance": {"win_rate": 65, "trades": 20},
            },
            {
                "id":          "trader_02",
                "status":      "paused",
                "pnl":         -3.0,
                "performance": {"win_rate": 35, "trades": 8},
            },
        ]
        review = {
            "overall_assessment": "System dziala stabilnie.",
            "system_health":      "good",
            "corrections":        [],
            "best_agent":         "trader_01",
            "worst_agent":        "trader_02",
            "recommendations":    "Brak zmian.",
        }

        with patch("telegram.reporter.send_message", new_callable=AsyncMock) as mock_send:
            from telegram.reporter import send_daily_report
            await send_daily_report(agents_data, review)

        mock_send.assert_called_once()
        sent_text = mock_send.call_args[0][0]
        self.assertIn("trader_01", sent_text)
        self.assertIn("trader_02", sent_text)
        self.assertIn("RAPORT DZIENNY", sent_text)


# ── Test 3: reporter.send_emergency_alert ─────────────────────────────────────

class TestReporterEmergencyAlert(IsolatedAsyncioTestCase):
    """send_emergency_alert wysyla alert z agent_id i powodem."""

    async def test_emergency_alert_format(self):
        with patch("telegram.reporter.send_message", new_callable=AsyncMock) as mock_send:
            from telegram.reporter import send_emergency_alert
            await send_emergency_alert("trader_01", "drawdown > 10%")

        mock_send.assert_called_once()
        text = mock_send.call_args[0][0]
        self.assertIn("trader_01", text)
        self.assertIn("drawdown", text)
        self.assertIn("EMERGENCY", text)


# ── Test 4: handle_command — parser ───────────────────────────────────────────

class TestHandleCommandParser(IsolatedAsyncioTestCase):
    """handle_command parsuje tekst i wywoluje odpowiedni handler."""

    async def test_status_command(self):
        with patch("telegram.commands.cmd_status", new_callable=AsyncMock) as mock_s:
            mock_s.return_value = "STATUS OK"
            from telegram.commands import handle_command
            result = await handle_command("/status")

        mock_s.assert_called_once()
        self.assertEqual(result, "STATUS OK")

    async def test_pause_command_with_id(self):
        with patch("telegram.commands.cmd_pause", new_callable=AsyncMock) as mock_p:
            mock_p.return_value = "Zatrzymano"
            from telegram.commands import handle_command
            result = await handle_command("/pause trader_01")

        mock_p.assert_called_once_with("trader_01")
        self.assertEqual(result, "Zatrzymano")

    async def test_pause_command_no_id(self):
        from telegram.commands import handle_command
        result = await handle_command("/pause")
        self.assertIn("Uzycie", result)
        self.assertIn("AGENT_ID", result)

    async def test_fund_command(self):
        with patch("telegram.commands.cmd_fund", new_callable=AsyncMock) as mock_f:
            mock_f.return_value = "Budzet zaktualizowany"
            from telegram.commands import handle_command
            result = await handle_command("/fund trader_01 50.0")

        mock_f.assert_called_once_with("trader_01", 50.0)

    async def test_fund_bad_amount(self):
        from telegram.commands import handle_command
        result = await handle_command("/fund trader_01 abc")
        self.assertIn("liczba", result)

    async def test_unknown_command(self):
        from telegram.commands import handle_command
        result = await handle_command("/unknown_xyz")
        self.assertIn("Nieznana komenda", result)
        self.assertIn("/help", result.lower())

    async def test_botname_suffix_stripped(self):
        """Komenda z @botname jest poprawnie parsowana."""
        with patch("telegram.commands.cmd_help", new_callable=AsyncMock) as mock_h:
            mock_h.return_value = "HELP"
            from telegram.commands import handle_command
            result = await handle_command("/help@MyTradingBot")

        mock_h.assert_called_once()


# ── Test 5: cmd_pause / cmd_resume ────────────────────────────────────────────

class TestCmdPauseResume(IsolatedAsyncioTestCase):
    """cmd_pause i cmd_resume zmieniaja status agenta."""

    def _make_agent(self, status="active"):
        return {
            "id":           "test_agent_tg",
            "status":       status,
            "personality":  "neutral",
            "budget_usdt":  100.0,
            "used_usdt":    0.0,
            "pnl_usdt":     0.0,
            "risk_per_trade": 0.005,
            "strategies":   "[]",
        }

    async def test_pause_active_agent(self):
        with patch("database.db.get_agent",    return_value=self._make_agent("active")), \
             patch("database.db.update_agent") as mock_update, \
             patch("database.db.log_activity"):
            from telegram.commands import cmd_pause
            result = await cmd_pause("test_agent_tg")

        mock_update.assert_called_once_with("test_agent_tg", status="paused")
        self.assertIn("zatrzymany", result)

    async def test_pause_already_paused(self):
        with patch("database.db.get_agent", return_value=self._make_agent("paused")):
            from telegram.commands import cmd_pause
            result = await cmd_pause("test_agent_tg")

        self.assertIn("juz zatrzymany", result)

    async def test_resume_paused_agent(self):
        with patch("database.db.get_agent",    return_value=self._make_agent("paused")), \
             patch("database.db.update_agent") as mock_update, \
             patch("database.db.log_activity"):
            from telegram.commands import cmd_resume
            result = await cmd_resume("test_agent_tg")

        mock_update.assert_called_once_with("test_agent_tg", status="active")
        self.assertIn("wznowiony", result)

    async def test_pause_nonexistent_agent(self):
        with patch("database.db.get_agent", return_value=None):
            from telegram.commands import cmd_pause
            result = await cmd_pause("ghost_agent")

        self.assertIn("nie istnieje", result)


# ── Test 6: cmd_new — walidacja osobowosci ────────────────────────────────────

class TestCmdNew(IsolatedAsyncioTestCase):
    """cmd_new waliduje osobowosc i wywoluje spawn_agent."""

    async def test_invalid_personality(self):
        with patch("database.db.get_agent", return_value=None):
            from telegram.commands import cmd_new
            result = await cmd_new("new_trader", "yolo", 50.0)

        self.assertIn("Nieznana osobowosc", result)
        self.assertIn("yolo", result)

    async def test_agent_already_exists(self):
        existing = {
            "id": "existing_trader", "status": "active",
            "personality": "neutral", "budget_usdt": 100.0,
            "used_usdt": 0.0, "pnl_usdt": 0.0,
            "risk_per_trade": 0.005, "strategies": "[]",
        }
        with patch("database.db.get_agent", return_value=existing):
            from telegram.commands import cmd_new
            result = await cmd_new("existing_trader", "neutral", 50.0)

        self.assertIn("juz istnieje", result)

    async def test_valid_spawn(self):
        spawn_result = {
            "success":    True,
            "agent_id":   "new_trader",
            "onboarding": {
                "strategies":    ["trend_following"],
                "risk_per_trade": 0.005,
                "model_used":     "groq",
            },
        }
        with patch("database.db.get_agent", return_value=None), \
             patch("telegram.reporter.send_message", new_callable=AsyncMock), \
             patch("factory.spawn_agent.spawn_agent", new_callable=AsyncMock,
                   return_value=spawn_result) as mock_spawn:
            from telegram.commands import cmd_new
            result = await cmd_new("new_trader", "neutral", 50.0)

        mock_spawn.assert_called_once_with("new_trader", "neutral", 50.0)
        self.assertIn("gotowy", result)
        self.assertIn("new_trader", result)


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestReporterSendMessage))
    suite.addTests(loader.loadTestsFromTestCase(TestReporterDailyReport))
    suite.addTests(loader.loadTestsFromTestCase(TestReporterEmergencyAlert))
    suite.addTests(loader.loadTestsFromTestCase(TestHandleCommandParser))
    suite.addTests(loader.loadTestsFromTestCase(TestCmdPauseResume))
    suite.addTests(loader.loadTestsFromTestCase(TestCmdNew))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
