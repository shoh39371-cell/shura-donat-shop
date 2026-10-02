import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = os.environ["BOT_TOKEN"]
PORT = int(os.environ.get("PORT", "10000"))


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"SHURA DONAT SHOP is running!")

    def log_message(self, format, *args):
        return


def start_web_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    server.serve_forever()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("💎 DIAMOND", callback_data="diamond"),
            InlineKeyboardButton("💳 TOP UP", callback_data="topup"),
        ],
        [
            InlineKeyboardButton("🚀 BOOST", callback_data="boost"),
            InlineKeyboardButton("🔥 SALE", callback_data="sale"),
        ],
        [
            InlineKeyboardButton("🆘 HELP", callback_data="help"),
        ],
    ]

    await update.message.reply_text(
        "💎 SHURA DONAT SHOP\n\n"
        "🔥 Mobile Legends xizmatlari\n"
        "⚡ Tezkor xizmat\n\n"
        "Kerakli xizmatni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    messages = {
        "diamond": "💎 DIAMOND\n\nDiamond buyurtma qilish uchun operator bilan bog‘laning.",
        "topup": "💳 TOP UP\n\nTop Up xizmati uchun operator bilan bog‘laning.",
        "boost": "🚀 BOOST\n\nBoost xizmati uchun operator bilan bog‘laning.",
        "sale": "🔥 SALE\n\nAksiyalar tez orada shu yerda chiqadi.",
        "help": "🆘 HELP\n\nYordam uchun operator bilan bog‘laning.",
    }

    await query.message.reply_text(messages.get(query.data, "Noma'lum buyruq."))


def main():
    threading.Thread(target=start_web_server, daemon=True).start()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("SHURA DONAT SHOP bot ishga tushdi!")
    app.run_polling()


if __name__ == "__main__":
    main()
