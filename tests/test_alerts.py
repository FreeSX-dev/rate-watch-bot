import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ratewatch.alerts import Alert, AlertStore  # noqa: E402


def test_should_trigger_above():
    alert = Alert(chat_id=1, coin_id="bitcoin", vs_currency="usd", direction="above", target_price=100)
    assert alert.should_trigger(150) is True
    assert alert.should_trigger(50) is False


def test_should_trigger_below():
    alert = Alert(chat_id=1, coin_id="bitcoin", vs_currency="usd", direction="below", target_price=100)
    assert alert.should_trigger(50) is True
    assert alert.should_trigger(150) is False


def test_already_triggered_never_fires_again():
    alert = Alert(chat_id=1, coin_id="bitcoin", vs_currency="usd", direction="above", target_price=100, triggered=True)
    assert alert.should_trigger(999) is False


def test_store_persists_and_reloads(tmp_path):
    file_path = tmp_path / "alerts.json"
    store = AlertStore(file_path)
    store.add(Alert(chat_id=42, coin_id="ethereum", vs_currency="usd", direction="above", target_price=5000))

    reloaded = AlertStore(file_path)
    pending = reloaded.pending_for(42)

    assert len(pending) == 1
    assert pending[0].coin_id == "ethereum"


def test_mark_triggered_removes_from_pending(tmp_path):
    store = AlertStore(tmp_path / "alerts.json")
    alert = Alert(chat_id=7, coin_id="bitcoin", vs_currency="usd", direction="above", target_price=100)
    store.add(alert)

    store.mark_triggered(store.all()[0])

    assert store.pending_for(7) == []


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-v"]))
