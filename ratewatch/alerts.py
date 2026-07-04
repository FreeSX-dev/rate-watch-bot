"""Логика алертов: храним подписки в JSON-файле, проверяем условия срабатывания."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Alert:
    chat_id: int
    coin_id: str
    vs_currency: str
    direction: str  # "above" or "below"
    target_price: float
    triggered: bool = False

    def should_trigger(self, current_price: float) -> bool:
        if self.triggered:
            return False
        if self.direction == "above":
            return current_price >= self.target_price
        if self.direction == "below":
            return current_price <= self.target_price
        raise ValueError(f"Неизвестное направление: {self.direction}")


class AlertStore:
    """Простое файловое хранилище алертов — без БД, для личного/малого использования достаточно."""

    def __init__(self, path: Path | str = "alerts.json"):
        self.path = Path(path)
        self._alerts: list[Alert] = self._load()

    def _load(self) -> list[Alert]:
        if not self.path.exists():
            return []
        raw = json.loads(self.path.read_text())
        return [Alert(**item) for item in raw]

    def _save(self) -> None:
        self.path.write_text(json.dumps([asdict(a) for a in self._alerts], indent=2))

    def add(self, alert: Alert) -> None:
        self._alerts.append(alert)
        self._save()

    def all(self) -> list[Alert]:
        return list(self._alerts)

    def pending_for(self, chat_id: int) -> list[Alert]:
        return [a for a in self._alerts if a.chat_id == chat_id and not a.triggered]

    def mark_triggered(self, alert: Alert) -> None:
        alert.triggered = True
        self._save()
