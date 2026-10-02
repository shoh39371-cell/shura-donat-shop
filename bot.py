import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("💎 DIAMOND", callback_data="diamond"),
            InlineKeyboardButton("💳 TOP UP", callback_data="topup")
        ],
        [
            InlineKeyboardButton("🚀 BOOST", callback_data="boost"),
            InlineKeyboardButton("🔥 SALE", callback_data="sale")
        ],
        [
            InlineKeyboardButton("🆘 HELP", callback_data="help")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "💎 SHURA DONAT SHOP\n\n"
        "🔥 Mobile Legends xizmatlari\n"
        "⚡ Tezkor va ishonchli xizmat\n\n"
        "Kerakli xizmatni tanlang:",
        reply_markup=reply_markup
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    messages = {
        "diamond": "💎 DIAMOND\n\nDiamond buyurtma qilish uchun operator bilan bog‘laning.",
        "topup": "💳 TOP UP\n\nTop Up xizmati uchun operator bilan bog‘laning.",
        "boost": "🚀 BOOST\n\nBoost xizmati uchun operator bilan bog‘laning.",
        "sale": "🔥 SALE\n\nAksiyalar tez orada shu yerda chiqadi.",
        "help": "🆘 HELP\n\nYordam kerak bo‘lsa, operator bilan bog‘laning."
    }

    await query.message.reply_text(messages.get(query.data, "Noma'lum buyruq."))


def main():
    token = os.environ.get("BOT_TOKEN")

    if not token:
        raise ValueError("BOT_TOKEN topilmadi!")

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("SHURA DONAT SHOP bot ishga tushdi!")
    app.run_polling()


if __name__ == "__main__":
    main()
