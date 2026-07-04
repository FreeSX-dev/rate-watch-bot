"""
Точка входа Telegram-бота.

Команды:
    /watch <coin_id> <above|below> <price>   — например: /watch bitcoin above 70000
    /list                                     — показать свои активные алерты

Бот раз в POLL_INTERVAL секунд проверяет цены и присылает сообщение, когда условие срабатывает.

Нужен токен бота в переменной окружения TELEGRAM_BOT_TOKEN (получить у @BotFather).
"""

from __future__ import annotations

import logging
import os
import time

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from ratewatch.alerts import Alert, AlertStore
from ratewatch.prices import PriceFetchError, get_price

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("ratewatch")

POLL_INTERVAL_SECONDS = int(os.environ.get("POLL_INTERVAL_SECONDS", "60"))
store = AlertStore(os.environ.get("ALERTS_FILE", "alerts.json"))


async def watch_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) != 3:
        await update.message.reply_text("Использование: /watch <coin_id> <above|below> <цена>")
        return

    coin_id, direction, price_raw = args
    direction = direction.lower()
    if direction not in ("above", "below"):
        await update.message.reply_text("Направление должно быть above или below")
        return

    try:
        target_price = float(price_raw)
    except ValueError:
        await update.message.reply_text("Цена должна быть числом")
        return

    alert = Alert(
        chat_id=update.effective_chat.id,
        coin_id=coin_id.lower(),
        vs_currency="usd",
        direction=direction,
        target_price=target_price,
    )
    store.add(alert)
    await update.message.reply_text(
        f"Готово. Сообщу, когда {coin_id} будет {direction} ${target_price:,.2f}"
    )


async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pending = store.pending_for(update.effective_chat.id)
    if not pending:
        await update.message.reply_text("Активных алертов нет. Добавь через /watch")
        return

    lines = [f"{a.coin_id} {a.direction} ${a.target_price:,.2f}" for a in pending]
    await update.message.reply_text("\n".join(lines))


async def check_alerts(context: ContextTypes.DEFAULT_TYPE) -> None:
    for alert in store.all():
        if alert.triggered:
            continue
        try:
            price = get_price(alert.coin_id, alert.vs_currency)
        except PriceFetchError as exc:
            logger.warning("Пропускаю проверку: %s", exc)
            continue

        if alert.should_trigger(price):
            store.mark_triggered(alert)
            await context.bot.send_message(
                chat_id=alert.chat_id,
                text=f"{alert.coin_id} сейчас ${price:,.2f} — условие '{alert.direction} {alert.target_price}' выполнено!",
            )


def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("Установи переменную окружения TELEGRAM_BOT_TOKEN")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("watch", watch_command))
    app.add_handler(CommandHandler("list", list_command))
    app.job_queue.run_repeating(check_alerts, interval=POLL_INTERVAL_SECONDS, first=5)

    logger.info("Бот запущен, проверка цен каждые %s сек.", POLL_INTERVAL_SECONDS)
    app.run_polling()


if __name__ == "__main__":
    main()
