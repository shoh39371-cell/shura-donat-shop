import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
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

CARD_NUMBER = os.environ.get(
    "CARD_NUMBER",
    "KARTA RAQAMI KIRITILMAGAN"
)

PLAYPAY_API_KEY = os.environ.get(
    "PLAYPAY_API_KEY",
    ""
)

PLAYPAY_API = "https://playpay.uz/api/v1"
SUPPORT_USERNAME = "Shohjaxono1"
MLBB_GAME_ID = 3

WEB_APP_URL = "https://shura-donat-shop-bot.onrender.com"


# =========================
# RENDER HEALTH CHECK
# =========================

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"PHOENIX DONAT SHOP is running!")

    def log_message(self, format, *args):
        return


def start_web_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    server.serve_forever()


# =========================
# PLAYPAY API
# =========================

def playpay_headers():
    return {
        "X-API-Key": PLAYPAY_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def get_diamond_packages():
    response = requests.get(
        f"{PLAYPAY_API}/games/{MLBB_GAME_ID}/packages",
        headers=playpay_headers(),
        params={"currency": "UZS"},
        timeout=30,
    )
    return response.json()


def check_player(player_id, server_id):
    response = requests.post(
        f"{PLAYPAY_API}/check_id",
        headers=playpay_headers(),
        json={
            "game_id": MLBB_GAME_ID,
            "player_id": player_id,
            "server_id": server_id,
        },
        timeout=30,
    )
    return response.json()


def create_order(package_id, player_id, server_id):
    response = requests.post(
        f"{PLAYPAY_API}/order",
        headers=playpay_headers(),
        json={
            "game_id": MLBB_GAME_ID,
            "paket_id": package_id,
            "player_id": player_id,
            "server_id": server_id,
        },
        timeout=30,
    )
    return response.json()


# =========================
# START
# =========================

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
            InlineKeyboardButton(
                "🌐 PHOENIX DONAT SHOP",
                web_app=WebAppInfo(url=WEB_APP_URL),
            )
        ],
        [
            InlineKeyboardButton("🆘 HELP / SUPPORT", callback_data="help")
        ],
    ]

    await update.message.reply_text(
        "🔥 PHOENIX DONAT SHOP\n\n"
        "💎 Mobile Legends xizmatlari\n"
        "⚡ Tezkor xizmat\n\n"
        "Kerakli xizmatni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================
# BUTTON HANDLER
# =========================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    try:
        await query.answer()
    except Exception:
        # Eski callback query bo'lsa, bot ishlashda davom etadi.
        pass

    # =====================
    # DIAMOND
    # =====================

    if query.data == "diamond":
        if not PLAYPAY_API_KEY:
            await query.message.reply_text(
                "❌ PlayPay API kaliti sozlanmagan.\n\n"
                "Render → Environment → PLAYPAY_API_KEY"
            )
            return

        try:
            data = get_diamond_packages()

            if not data.get("ok"):
                await query.message.reply_text(
                    "❌ Diamond paketlarini olishda xatolik.\n\n"
                    f"Xato: {data.get('error', 'unknown')}"
                )
                return

            packages = data.get("packages", [])

            if not packages:
                await query.message.reply_text(
                    "❌ Hozircha diamond paketlari mavjud emas."
                )
                return

            keyboard = []

            for package in packages:
                package_id = package.get("paket_id")
                name = package.get("name", "Diamond")
                price = package.get("price", {}).get("amount", 0)

                keyboard.append([
                    InlineKeyboardButton(
                        f"💎 {name} — {price:,} so‘m",
                        callback_data=f"diamond_{package_id}",
                    )
                ])

            await query.message.reply_text(
                "💎 DIAMOND\n\n"
                "Kerakli diamond paketini tanlang:",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        except Exception:
            await query.message.reply_text(
                "❌ PlayPay API bilan bog‘lanishda xatolik.\n\n"
                "API key va PlayPay sozlamalarini tekshiring."
            )
        return

    # =====================
    # DIAMOND PACKAGE
    # =====================

    if query.data.startswith("diamond_"):
        package_id = query.data.replace("diamond_", "", 1)

        context.user_data["diamond_package_id"] = package_id
        context.user_data["diamond_step"] = "player_id"

        await query.message.reply_text(
            "💎 DIAMOND BUYURTMA\n\n"
            "1️⃣ Mobile Legends Player ID / User ID ni yozing.\n\n"
            "Masalan:\n"
            "123456789"
        )
        return

    # =====================
    # CONFIRM DIAMOND
    # =====================

    if query.data == "confirm_diamond":
        package_id = context.user_data.get("diamond_package_id")
        player_id = context.user_data.get("diamond_player_id")
        server_id = context.user_data.get("diamond_server_id")

        if not package_id or not player_id or not server_id:
            await query.message.reply_text(
                "❌ Buyurtma ma'lumotlari topilmadi.\n"
                "Qaytadan DIAMOND bo‘limiga kiring."
            )
            return

        if not PLAYPAY_API_KEY:
            await query.message.reply_text(
                "❌ PlayPay API key sozlanmagan."
            )
            return

        try:
            result = create_order(package_id, player_id, server_id)

            if result.get("ok"):
                order_id = result.get("order_id", "Noma'lum")

                await query.message.reply_text(
                    "✅ BUYURTMA QABUL QILINDI!\n\n"
                    f"💎 Paket: {context.user_data.get('diamond_package_name', 'Diamond')}\n"
                    f"👤 Player ID: {player_id}\n"
                    f"🌐 Server ID: {server_id}\n\n"
                    f"🧾 Order ID: {order_id}\n\n"
                    "⏳ Diamond yetkazilishi kutilmoqda."
                )
            else:
                await query.message.reply_text(
                    "❌ Buyurtma yaratilmadi.\n\n"
                    f"Xato: {result.get('error', 'unknown')}"
                )

        except Exception:
            await query.message.reply_text(
                "❌ PlayPay API bilan bog‘lanishda xatolik."
            )

        context.user_data["diamond_step"] = None
        return

    # =====================
    # CANCEL DIAMOND
    # =====================

    if query.data == "cancel_diamond":
        for key in (
            "diamond_package_id",
            "diamond_player_id",
            "diamond_server_id",
            "diamond_package_name",
            "diamond_customer_price",
        ):
            context.user_data.pop(key, None)

        context.user_data["diamond_step"] = None

        await query.message.reply_text(
            "❌ Diamond buyurtmasi bekor qilindi."
        )
        return

    # =====================
    # PAID
    # =====================

    if query.data == "paid":
        amount = context.user_data.get("topup_amount")

        if not amount:
            await query.message.reply_text(
                "❌ Top Up summasi topilmadi.\n"
                "Qaytadan TOP UP ni tanlang."
            )
            return

        context.user_data["waiting_receipt"] = True

        await query.message.reply_text(
            "📸 TO‘LOVNI TASDIQLASH\n\n"
            f"💰 Summa: {amount:,} so‘m\n\n"
            "To‘lov chek yoki skrinshotini shu yerga yuboring.\n\n"
            "⚠️ Chek tekshirilmaguncha balans avtomatik oshirilmaydi."
        )
        return

    # =====================
    # SUPPORT
    # =====================

    if query.data == "help":
        keyboard = [[
            InlineKeyboardButton(
                "💬 Operatorga yozish",
                url=f"https://t.me/{SUPPORT_USERNAME}",
            )
        ]]

        await query.message.reply_text(
            "🆘 SUPPORT\n\n"
            "Savolingiz yoki muammoingiz bo‘lsa,\n"
            "operatorga yozing:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    # =====================
    # TOP UP
    # =====================

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

    # =====================
    # CUSTOM AMOUNT
    # =====================

    if query.data == "custom_amount":
        context.user_data["waiting_amount"] = True

        await query.message.reply_text(
            "✏️ BOSHQA SUMMA\n\n"
            "Kerakli summani faqat raqam bilan yozing.\n\n"
            "Masalan:\n"
            "37000"
        )
        return

    # =====================
    # FIXED TOP UP
    # =====================

    if query.data.startswith("topup_"):
        try:
            amount = int(query.data.replace("topup_", "", 1))
        except ValueError:
            await query.message.reply_text("❌ Summa noto‘g‘ri.")
            return

        await show_payment_info(query.message, context, amount)
        return

    # =====================
    # BOOST MENU
    # =====================

    if query.data == "boost":
        keyboard = [
            [InlineKeyboardButton("🟣 EPIC", callback_data="boost_epic")],
            [InlineKeyboardButton("🔵 LEGEND", callback_data="boost_legend")],
            [InlineKeyboardButton("🔴 MYTHIC", callback_data="boost_mythic")],
            [InlineKeyboardButton("🟠 MYTHICAL HONOR", callback_data="boost_honor")],
            [InlineKeyboardButton("🟡 MYTHICAL GLORY", callback_data="boost_glory")],
        ]

        await query.message.reply_text(
            "🚀 BOOST\n\n"
            "🟣 Epic — 4 000 so‘m / star\n"
            "🔵 Legend — 5 000 so‘m / star\n"
            "🔴 Mythic — 6 000 so‘m / point\n"
            "🟠 Mythical Honor — 7 000 so‘m / point\n"
            "🟡 Mythical Glory — 8 000 so‘m / point\n\n"
            "Qaysi target rank kerak?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    # =====================
    # BOOST TARGET
    # =====================

    if query.data.startswith("boost_"):
        rank_prices = {
            "boost_epic": ("Epic", 4000),
            "boost_legend": ("Legend", 5000),
            "boost_mythic": ("Mythic", 6000),
            "boost_honor": ("Mythical Honor", 7000),
            "boost_glory": ("Mythical Glory", 8000),
        }

        rank_name, price = rank_prices.get(query.data, ("", 0))

        if not rank_name:
            return

        context.user_data["boost_target_rank"] = rank_name
        context.user_data["boost_price"] = price
        context.user_data["boost_step"] = "current_rank"

        await query.message.reply_text(
            f"🚀 {rank_name.upper()} BOOST\n\n"
            "1️⃣ Hozirgi rankingizni yozing.\n\n"
            "Masalan:\n"
            "Epic V\n"
            "Epic III\n"
            "Legend V\n"
            "Legend I\n"
            "Mythic"
        )
        return

    # =====================
    # SALE
    # =====================

    if query.data == "sale":
        await query.message.reply_text(
            "🔥 SALE\n\n"
            "Aksiyalar tez orada shu yerda."
        )
        return


# =========================
# PAYMENT
# =========================

async def show_payment_info(message, context, amount):
    context.user_data["topup_amount"] = amount

    keyboard = [
        [InlineKeyboardButton("✅ Men to‘ladim", callback_data="paid")],
        [
            InlineKeyboardButton(
                "🆘 Support",
                url=f"https://t.me/{SUPPORT_USERNAME}",
            )
        ],
    ]

    await message.reply_text(
        "💳 TOP UP\n\n"
        f"💰 Summa: {amount:,} so‘m\n\n"
        f"💳 KARTA:\n{CARD_NUMBER}\n\n"
        "Yuqoridagi kartaga aynan shu summani o‘tkazing.\n\n"
        "To‘lovdan keyin «✅ Men to‘ladim» tugmasini bosing.\n\n"
        "⚠️ To‘lov tekshirilmaguncha balans avtomatik oshirilmaydi.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================
# TEXT HANDLER
# =========================

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # =====================
    # DIAMOND PLAYER ID
    # =====================

    if context.user_data.get("diamond_step") == "player_id":
        if not text.isdigit():
            await update.message.reply_text(
                "❌ Player ID faqat raqamlardan iborat bo‘lishi kerak."
            )
            return

        context.user_data["diamond_player_id"] = text
        context.user_data["diamond_step"] = "server_id"

        await update.message.reply_text(
            "2️⃣ Server ID / Zone ID ni yozing.\n\n"
            "Masalan:\n"
            "1234"
        )
        return

    # =====================
    # DIAMOND SERVER ID
    # =====================

    if context.user_data.get("diamond_step") == "server_id":
        if not text.isdigit():
            await update.message.reply_text(
                "❌ Server ID faqat raqamlardan iborat bo‘lishi kerak."
            )
            return

        player_id = context.user_data.get("diamond_player_id")
        server_id = text
        package_id = context.user_data.get("diamond_package_id")

        try:
            check = check_player(player_id, server_id)

            if not check.get("ok"):
                await update.message.reply_text(
                    "❌ ID tekshirishda xatolik.\n\n"
                    f"{check.get('error', 'unknown')}"
                )
                context.user_data["diamond_step"] = None
                return

            if not check.get("valid"):
                await update.message.reply_text(
                    "❌ Player ID yoki Server ID noto‘g‘ri.\n\n"
                    "Ma’lumotlarni tekshirib qaytadan urinib ko‘ring."
                )
                context.user_data["diamond_step"] = None
                return

            player_name = check.get("player_name", "")
            context.user_data["diamond_server_id"] = server_id

            packages_data = get_diamond_packages()
            packages = packages_data.get("packages", [])

            selected_package = None

            for package in packages:
                if str(package.get("paket_id")) == str(package_id):
                    selected_package = package
                    break

            if not selected_package:
                await update.message.reply_text("❌ Paket topilmadi.")
                context.user_data["diamond_step"] = None
                return

            package_name = selected_package.get("name", "Diamond")
            customer_price = selected_package.get("price", {}).get("amount", 0)

            context.user_data["diamond_package_name"] = package_name
            context.user_data["diamond_customer_price"] = customer_price
            context.user_data["diamond_step"] = None

            keyboard = [
                [
                    InlineKeyboardButton(
                        "✅ TASDIQLASH VA DONAT",
                        callback_data="confirm_diamond",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "❌ Bekor qilish",
                        callback_data="cancel_diamond",
                    )
                ],
            ]

            await update.message.reply_text(
                "💎 BUYURTMA TASDIQLASH\n\n"
                f"💎 Paket: {package_name}\n"
                f"💰 Narx: {customer_price:,} so‘m\n\n"
                f"👤 Player: {player_name}\n"
                f"🆔 User ID: {player_id}\n"
                f"🌐 Server ID: {server_id}\n\n"
                "Ma’lumotlar to‘g‘rimi?",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        except Exception:
            await update.message.reply_text(
                "❌ PlayPay API bilan bog‘lanishda xatolik."
            )
            context.user_data["diamond_step"] = None

        return

    # =====================
    # BOOST CURRENT RANK
    # =====================

    if context.user_data.get("boost_step") == "current_rank":
        context.user_data["boost_current_rank"] = text
        context.user_data["boost_step"] = "current_points"

        await update.message.reply_text(
            "2️⃣ Hozirgi star/point soningizni yozing.\n\n"
            "Masalan:\n"
            "25\n"
            "43\n"
            "58"
        )
        return

    # =====================
    # BOOST CURRENT POINTS
    # =====================

    if context.user_data.get("boost_step") == "current_points":
        if not text.isdigit():
            await update.message.reply_text(
                "❌ Star/point sonini faqat raqam bilan yozing."
            )
            return

        points = int(text)
        target_rank = context.user_data.get("boost_target_rank", "")
        price = int(context.user_data.get("boost_price", 0))
        current_rank = context.user_data.get("boost_current_rank", "")

        context.user_data["boost_current_points"] = points
        context.user_data["boost_step"] = None

        await update.message.reply_text(
            "🚀 BOOST BUYURTMA\n\n"
            f"📍 Hozirgi rank: {current_rank}\n"
            f"⭐ Hozirgi star/point: {points}\n"
            f"🎯 Target rank: {target_rank}\n"
            f"💰 Tarif: {price:,} so‘m / star yoki point\n\n"
            "⚠️ Aniq narx rank oralig‘i va kerakli point/star "
            "soni operator tomonidan tasdiqlanadi.\n\n"
            "Buyurtmani davom ettirish uchun operatorga yozing:",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "💬 Operatorga yozish",
                        url=f"https://t.me/{SUPPORT_USERNAME}",
                    )
                ]
            ]),
        )
        return

    # =====================
    # CUSTOM TOP UP AMOUNT
    # =====================

    if context.user_data.get("waiting_amount"):
     
