import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.environ["BOT_TOKEN"]
PORT = int(os.environ.get("PORT", "10000"))

# Karta raqamini GitHub kodiga yozmaymiz.
CARD_NUMBER = os.environ.get("CARD_NUMBER", "KARTA RAQAMI KIRITILMAGAN")

SUPPORT_USERNAME = "Shohjaxono1"


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
            InlineKeyboardButton("🆘 HELP / SUPPORT", callback_data="help"),
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

    # SUPPORT
    if query.data == "help":
        keyboard = [[
            InlineKeyboardButton(
                "💬 Operatorga yozish",
                url=f"https://t.me/{SUPPORT_USERNAME}"
            )
        ]]

        await query.message.reply_text(
            "🆘 SUPPORT\n\n"
            "Savolingiz yoki muammoingiz bo‘lsa, operatorga yozing:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    # TOP UP MENU
    if query.data == "topup":
        keyboard = [
            [InlineKeyboardButton("💰 10 000 so‘m", callback_data="topup_10000")],
            [InlineKeyboardButton("💰 20 000 so‘m", callback_data="topup_20000")],
            [InlineKeyboardButton("💰 50 000 so‘m", callback_data="topup_50000")],
            [InlineKeyboardButton("💰 100 000 so‘m", callback_data="topup_100000")],
            [InlineKeyboardButton("✏️ Boshqa summa", callback_data="custom_amount")],
        ]

        await query.message.reply_text(
            "💳 TOP UP\n\n"
            "Balansni qancha to‘ldirmoqchisiz?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    # CUSTOM AMOUNT
    if query.data == "custom_amount":
        context.user_data["waiting_amount"] = True

        await query.message.reply_text(
            "✏️ Boshqa summa\n\n"
            "Kerakli summani faqat raqam bilan yozing.\n"
            "Masalan: 37000"
        )
        return

    # FIXED AMOUNT
    if query.data.startswith("topup_"):
        amount = int(query.data.replace("topup_", ""))
        await show_payment_info(query.message, context, amount)
        return

    messages = {
        "diamond":
            "💎 DIAMOND\n\n"
            "Diamond buyurtma qilish uchun operator bilan bog‘laning.",

        "boost":
            "🚀 BOOST\n\n"
            "Boost xizmati uchun operator bilan bog‘laning.",

        "sale":
            "🔥 SALE\n\n"
            "Aksiyalar tez orada shu yerda chiqadi.",
    }

    await query.message.reply_text(
        messages.get(query.data, "Noma'lum buyruq.")
    )


async def show_payment_info(message, context, amount):
    context.user_data["topup_amount"] = amount

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Men to‘ladim",
                callback_data="paid"
            )
        ],
        [
            InlineKeyboardButton(
                "🆘 Support",
                url=f"https://t.me/{SUPPORT_USERNAME}"
            )
        ],
    ]

    await message.reply_text(
        "💳 TOP UP\n\n"
        f"💰 Summa: {amount:,} so‘m\n\n"
        f"💳 Karta:\n{CARD_NUMBER}\n\n"
        "Yuqoridagi kartaga aynan shu summani o‘tkazing.\n"
        "To‘lovdan keyin «✅ Men to‘ladim» tugmasini bosing.\n\n"
        "⚠️ To‘lov tasdiqlanmaguncha balans avtomatik oshirilmaydi.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("waiting_amount"):
        return

    text = update.message.text.strip().replace(" ", "").replace(",", "")

    if not text.isdigit():
        await update.message.reply_text(
            "❌ Faqat summa yozing.\nMasalan: 37000"
        )
        return

    amount = int(text)

    if amount < 1000:
        await update.message.reply_text(
            "❌ Minimal summa 1 000 so‘m."
        )
        return

    if amount > 10000000:
        await update.message.reply_text(
            "❌ Juda katta summa kiritildi."
        )
        return

    context.user_data["waiting_amount"] = False

    await show_payment_info(update.message, context, amount)


async def paid_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    amount = context.user_data.get("topup_amount")

    if not amount:
        await query.message.reply_text(
            "❌ Top Up summasi topilmadi. Qaytadan TOP UP ni tanlang."
        )
        return

    context.user_data["waiting_receipt"] = True

    await query.message.reply_text(
        "📸 To‘lovni tasdiqlash\n\n"
        f"💰 Summa: {amount:,} so‘m\n\n"
        "Endi to‘lov chek/skrinshotini shu yerga yuboring.\n\n"
        "⚠️ Chek tekshirilgandan keyin balans masalasi hal qilinadi."
    )


async def receipt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("waiting_receipt"):
        return

    context.user_data["waiting_receipt"] = False

    await update.message.reply_text(
        "📨 Chek qabul qilindi.\n\n"
        "To‘lovni tekshirish uchun operator bilan bog‘laning:",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "💬 @Shohjaxono1",
                    url=f"https://t.me/{SUPPORT_USERNAME}"
                )
            ]
        ])
    )


def main():
    threading.Thread(
        target=start_web_server,
        daemon=True
    ).start()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CallbackQueryHandler(paid_handler, pattern="^paid$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.add_handler(MessageHandler(filters.PHOTO, receipt_handler))

    print("SHURA DONAT SHOP bot ishga tushdi!")
    app.run_polling()


if __name__ == "__main__":
    main()
