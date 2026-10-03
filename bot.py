import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests
from database import init_db, get_user, add_balance
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


# =========================================================
# ENVIRONMENT
# =========================================================

TOKEN = os.environ["BOT_TOKEN"]

PORT = int(
    os.environ.get("PORT", "10000")
)

CARD_NUMBER = os.environ.get(
    "CARD_NUMBER",
    "KARTA RAQAMI KIRITILMAGAN"
)

PLAYPAY_API_KEY = os.environ.get(
    "PLAYPAY_API_KEY",
    ""
)

ADMIN_CHAT_ID = os.environ.get(
    "ADMIN_CHAT_ID",
    ""
)


# =========================================================
# SETTINGS
# =========================================================

PLAYPAY_API = "https://playpay.uz/api/v1"

SUPPORT_USERNAME = "Shohjaxono1"

MLBB_GAME_ID = 165

WEB_APP_URL = (
    "https://shura-donat-shop-bot.onrender.com"
)


# =========================================================
# WEB SERVER
# =========================================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        if self.path == "/" or self.path == "/index.html":

            try:

                with open("index.html", "rb") as f:
                    html = f.read()

                self.send_response(200)

                self.send_header(
                    "Content-Type",
                    "text/html; charset=utf-8"
                )

                self.send_header(
                    "Content-Length",
                    str(len(html))
                )

                self.end_headers()

                self.wfile.write(html)

            except FileNotFoundError:

                self.send_response(404)

                self.end_headers()

                self.wfile.write(
                    b"index.html topilmadi"
                )

            return

        self.send_response(404)
        self.end_headers()


    def log_message(
        self,
        format,
        *args
    ):

        return

def start_web_server():

    server = HTTPServer(
        ("0.0.0.0", PORT),
        HealthHandler
    )

    print(
        f"🌐 Web server port {PORT} da ishladi"
    )

    server.serve_forever()


# =========================================================
# PLAYPAY
# =========================================================

def playpay_headers():

    return {
        "X-API-Key": PLAYPAY_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def get_diamond_packages():

    response = requests.get(

        f"{PLAYPAY_API}/games/"
        f"{MLBB_GAME_ID}/packages",

        headers=playpay_headers(),

        params={
            "currency": "UZS"
        },

        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def check_player(
    player_id,
    server_id
):

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

    response.raise_for_status()

    return response.json()


def create_order(
    package_id,
    player_id,
    server_id
):

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

    response.raise_for_status()

    return response.json()


# =========================================================
# MAIN MENU
# =========================================================

def main_menu_keyboard():

    return InlineKeyboardMarkup([

        [

            InlineKeyboardButton(
                "💎 DIAMOND",
                callback_data="diamond"
            ),

            InlineKeyboardButton(
                "💳 TOP UP",
                callback_data="topup"
            ),

        ],

        [

            InlineKeyboardButton(
                "🚀 BOOST",
                callback_data="boost"
            ),

            InlineKeyboardButton(
                "🔥 SALE",
                callback_data="sale"
            ),

        ],

        [

            InlineKeyboardButton(
                "🌐 PHOENIX DONAT SHOP",
                web_app=WebAppInfo(
                    url=WEB_APP_URL
                )
            )

        ],

        [

            InlineKeyboardButton(
                "🆘 HELP / SUPPORT",
                callback_data="help"
            )

        ],

    ])


async def send_main_menu(message):

    await message.reply_text(

        "🔥 PHOENIX DONAT SHOP\n\n"

        "💎 Mobile Legends xizmatlari\n"
        "⚡ Tezkor xizmat\n"
        "🔐 Ishonchli xizmat\n\n"

        "Kerakli xizmatni tanlang:",

        reply_markup=main_menu_keyboard()
    )


# =========================================================
# START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data.clear()

    await send_main_menu(
        update.message
    )
    # =========================================================
# DIAMOND PACKAGES
# =========================================================

async def show_diamond_packages(
    query,
    context
):

    if not PLAYPAY_API_KEY:

        await query.message.reply_text(
            "❌ PlayPay API key sozlanmagan.\n\n"
            "Render → Environment → "
            "PLAYPAY_API_KEY ni tekshiring."
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

        packages = data.get(
            "packages",
            []
        )

        if not packages:

            await query.message.reply_text(
                "❌ Hozircha diamond paketlari mavjud emas."
            )

            return

        keyboard = []

        for package in packages:

            package_id = package.get(
                "paket_id"
            )

            if package_id is None:
                continue

            name = package.get(
                "name",
                "Diamond"
            )

            price_data = package.get(
                "price",
                0
            )

            if isinstance(
                price_data,
                dict
            ):

                price = price_data.get(
                    "amount",
                    0
                )

            else:

                price = price_data or 0

            try:

                price_text = (
                    f"{int(price):,}"
                )

            except (
                TypeError,
                ValueError
            ):

                price_text = str(price)

            context.user_data[
                f"package_{package_id}_name"
            ] = name

            context.user_data[
                f"package_{package_id}_price"
            ] = price

            keyboard.append([

                InlineKeyboardButton(

                    f"💎 {name} — "
                    f"{price_text} so‘m",

                    callback_data=(
                        f"diamond_{package_id}"
                    )

                )

            ])

        if not keyboard:

            await query.message.reply_text(
                "❌ Paketlar topilmadi."
            )

            return

        await query.message.reply_text(

            "💎 DIAMOND\n\n"
            "Kerakli diamond paketini tanlang:",

            reply_markup=InlineKeyboardMarkup(
                keyboard
            )

        )

    except Exception as e:

        print(
            "DIAMOND PACKAGES ERROR:",
            repr(e)
        )

        await query.message.reply_text(

            "❌ PlayPay API bilan "
            "bog‘lanishda xatolik yuz berdi."

        )


# =========================================================
# PAYMENT INFO
# =========================================================

async def show_payment_info(
    message,
    context,
    amount
):

    context.user_data[
        "topup_amount"
    ] = amount

    keyboard = InlineKeyboardMarkup([

        [

            InlineKeyboardButton(
                "✅ TO‘LOV QILDIM",
                callback_data="paid"
            )

        ],

        [

            InlineKeyboardButton(
                "🔙 Bosh menyu",
                callback_data="back_menu"
            )

        ]

    ])

    await message.reply_text(

        "💳 TO‘LOV MA'LUMOTLARI\n\n"

        f"💰 Summa: {amount:,} so‘m\n\n"

        f"💳 Karta: {CARD_NUMBER}\n\n"

        "To‘lovni amalga oshirgach, "
        "«TO‘LOV QILDIM» tugmasini bosing.",

        reply_markup=keyboard

    )


# =========================================================
# BUTTON HANDLER
# =========================================================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    try:

        await query.answer()

    except Exception:

        pass

    data = query.data or ""


    # =====================================================
    # DIAMOND
    # =====================================================

    if data == "diamond":

        await show_diamond_packages(
            query,
            context
        )

        return


    # =====================================================
    # SELECT DIAMOND
    # =====================================================

    if data.startswith(
        "diamond_"
    ):

        package_id = data.replace(
            "diamond_",
            "",
            1
        )

        package_name = context.user_data.get(

            f"package_{package_id}_name",

            "Diamond"

        )

        package_price = context.user_data.get(

            f"package_{package_id}_price",

            0

        )

        context.user_data[
            "diamond_package_id"
        ] = package_id

        context.user_data[
            "diamond_package_name"
        ] = package_name

        context.user_data[
            "diamond_customer_price"
        ] = package_price

        context.user_data[
            "diamond_step"
        ] = "player_id"

        await query.message.reply_text(

            "💎 DIAMOND BUYURTMA\n\n"

            f"📦 Paket: {package_name}\n"

            f"💰 Narx: "
            f"{package_price:,} so‘m\n\n"

            "1️⃣ Mobile Legends "
            "Player ID / User ID ni yozing.\n\n"

            "Masalan:\n"
            "123456789"

        )

        return


    # =====================================================
    # CONFIRM DIAMOND
    # =====================================================

    if data == "confirm_diamond":

        package_id = context.user_data.get(
            "diamond_package_id"
        )

        player_id = context.user_data.get(
            "diamond_player_id"
        )

        server_id = context.user_data.get(
            "diamond_server_id"
        )

        if not package_id or not player_id or not server_id:

            await query.message.reply_text(

                "❌ Buyurtma ma'lumotlari "
                "topilmadi.\n\n"

                "Qaytadan DIAMOND "
                "bo‘limiga kiring."

            )

            return

        if not PLAYPAY_API_KEY:

            await query.message.reply_text(
                "❌ PlayPay API key sozlanmagan."
            )

            return

        await query.message.reply_text(
            "⏳ Buyurtma yaratilmoqda..."
        )

        try:

            result = create_order(

                package_id,
                player_id,
                server_id

            )

            if result.get("ok"):

                order_id = result.get(
                    "order_id",
                    "Noma'lum"
                )

                package_name = (
                    context.user_data.get(
                        "diamond_package_name",
                        "Diamond"
                    )
                )

                await query.message.reply_text(

                    "✅ BUYURTMA QABUL QILINDI!\n\n"

                    f"💎 Paket: {package_name}\n"

                    f"👤 Player ID: {player_id}\n"

                    f"🌐 Server ID: {server_id}\n"

                    f"🧾 Order ID: {order_id}\n\n"

                    "⏳ Diamond yetkazilishi "
                    "kutilmoqda."

                )

            else:

                await query.message.reply_text(

                    "❌ Buyurtma yaratilmadi.\n\n"

                    f"Xato: "
                    f"{result.get('error', 'unknown')}"

                )

        except Exception as e:

            print(
                "ORDER ERROR:",
                repr(e)
            )

            await query.message.reply_text(

                "❌ Buyurtma yaratishda "
                "xatolik."

            )

        return


    # =====================================================
    # CANCEL DIAMOND
    # =====================================================

    if data == "cancel_diamond":

        for key in [

            "diamond_package_id",
            "diamond_package_name",
            "diamond_customer_price",
            "diamond_player_id",
            "diamond_server_id",
            "diamond_step",

        ]:

            context.user_data.pop(
                key,
                None
            )

        await query.message.reply_text(

            "❌ Diamond buyurtmasi "
            "bekor qilindi."

        )

        return


    # =====================================================
    # TOP UP
    # =====================================================

    if data == "topup":

        keyboard = InlineKeyboardMarkup([

            [

                InlineKeyboardButton(
                    "💰 10 000 so‘m",
                    callback_data="topup_10000"
                )

            ],

            [

                InlineKeyboardButton(
                    "💰 20 000 so‘m",
                    callback_data="topup_20000"
                )

            ],

            [

                InlineKeyboardButton(
                    "💰 50 000 so‘m",
                    callback_data="topup_50000"
                )

            ],

            [

                InlineKeyboardButton(
                    "💰 100 000 so‘m",
                    callback_data="topup_100000"
                )

            ],

            [

                InlineKeyboardButton(
                    "✏️ Boshqa summa",
                    callback_data="custom_amount"
                )

            ],

            [

                InlineKeyboardButton(
                    "🔙 Bosh menyu",
                    callback_data="back_menu"
                )

            ]

        ])

        await query.message.reply_text(

            "💳 TOP UP\n\n"

            "Balansni qancha "
            "to‘ldirmoqchisiz?",

            reply_markup=keyboard

        )

        return


    # =====================================================
    # CUSTOM AMOUNT
    # =====================================================

    if data == "custom_amount":

        context.user_data[
            "waiting_amount"
        ] = True

        await query.message.reply_text(

            "✏️ BOSHQA SUMMA\n\n"

            "Kerakli summani faqat "
            "raqam bilan yozing.\n\n"

            "Masalan:\n"
            "37000"

        )

        return


    # =====================================================
    # TOP UP AMOUNT
    # =====================================================

    if data.startswith(
        "topup_"
    ):

        try:

            amount = int(
                data.replace(
                    "topup_",
                    "",
                    1
                )
            )

        except ValueError:

            await query.message.reply_text(
                "❌ Summa noto‘g‘ri."
            )

            return

        await show_payment_info(
            query.message,
            context,
            amount
        )

        return
        # =========================================================
# PAYMENT CONFIRMATION
# =========================================================

    if data == "paid":

        amount = context.user_data.get(
            "topup_amount"
        )

        if not amount:

            await query.message.reply_text(
                "❌ Top Up summasi topilmadi."
            )

            return

        context.user_data[
            "waiting_receipt"
        ] = True

        await query.message.reply_text(

            "📸 TO‘LOVNI TASDIQLASH\n\n"

            f"💰 Summa: {amount:,} so‘m\n\n"

            "To‘lov chek yoki skrinshotini "
            "shu yerga yuboring."

        )

        return


# =========================================================
# BOOST
# =========================================================

    if data == "boost":

        keyboard = InlineKeyboardMarkup([

            [
                InlineKeyboardButton(
                    "🟣 EPIC",
                    callback_data="boost_epic"
                )
            ],

            [
                InlineKeyboardButton(
                    "🔵 LEGEND",
                    callback_data="boost_legend"
                )
            ],

            [
                InlineKeyboardButton(
                    "🔴 MYTHIC",
                    callback_data="boost_mythic"
                )
            ],

            [
                InlineKeyboardButton(
                    "🟠 MYTHICAL HONOR",
                    callback_data="boost_honor"
                )
            ],

            [
                InlineKeyboardButton(
                    "🟡 MYTHICAL GLORY",
                    callback_data="boost_glory"
                )
            ],

            [
                InlineKeyboardButton(
                    "🔙 Bosh menyu",
                    callback_data="back_menu"
                )
            ]

        ])

        await query.message.reply_text(

            "🚀 BOOST\n\n"

            "🟣 Epic — 4 000 so‘m / star\n"
            "🔵 Legend — 5 000 so‘m / star\n"
            "🔴 Mythic — 6 000 so‘m / point\n"
            "🟠 Mythical Honor — 7 000 so‘m / point\n"
            "🟡 Mythical Glory — 8 000 so‘m / point\n\n"

            "Qaysi target rank kerak?",

            reply_markup=keyboard

        )

        return


# =========================================================
# BOOST RANK
# =========================================================

    if data.startswith(
        "boost_"
    ):

        rank_prices = {

            "boost_epic": (
                "Epic",
                4000
            ),

            "boost_legend": (
                "Legend",
                5000
            ),

            "boost_mythic": (
                "Mythic",
                6000
            ),

            "boost_honor": (
                "Mythical Honor",
                7000
            ),

            "boost_glory": (
                "Mythical Glory",
                8000
            ),

        }

        rank_name, price = rank_prices.get(

            data,

            ("", 0)

        )

        if not rank_name:

            return

        context.user_data[
            "boost_target_rank"
        ] = rank_name

        context.user_data[
            "boost_price"
        ] = price

        context.user_data[
            "boost_step"
        ] = "current_rank"

        await query.message.reply_text(

            f"🚀 {rank_name.upper()} BOOST\n\n"

            "1️⃣ Hozirgi rankingizni yozing.\n\n"

            "Masalan:\n"
            "Epic V\n"
            "Legend V\n"
            "Mythic"

        )

        return


# =========================================================
# SALE
# =========================================================

    if data == "sale":

        await query.message.reply_text(

            "🔥 SALE\n\n"

            "Aksiyalar tez orada shu yerda."

        )

        return


# =========================================================
# HELP
# =========================================================

    if data == "help":

        await query.message.reply_text(

            "🆘 SUPPORT\n\n"

            f"Operator: @{SUPPORT_USERNAME}\n\n"

            "Savollar yoki muammolar bo‘lsa "
            "operatorga yozing."

        )

        return


# =========================================================
# BACK TO MENU
# =========================================================

    if data == "back_menu":

        context.user_data.clear()

        await send_main_menu(
            query.message
        )

        return


# =========================================================
# CONFIRM BOOST
# =========================================================

    if data == "confirm_boost":

        await handle_boost_confirmation(
            query,
            context
        )

        return


# =========================================================
# CANCEL BOOST
# =========================================================

    if data == "cancel_boost":

        context.user_data.clear()

        await query.message.reply_text(

            "❌ Boost buyurtmasi "
            "bekor qilindi."

        )

        return


# =========================================================
# TEXT HANDLER
# =========================================================

async def text_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = (
        update.message.text or ""
    ).strip()


    # =====================================================
    # CUSTOM TOP UP AMOUNT
    # =====================================================

    if context.user_data.get(
        "waiting_amount"
    ):

        try:

            amount = int(
                text
                .replace(" ", "")
                .replace(",", "")
            )

            if amount <= 0:

                raise ValueError

        except ValueError:

            await update.message.reply_text(

                "❌ Noto‘g‘ri summa.\n\n"
                "Masalan: 37000"

            )

            return

        context.user_data[
            "waiting_amount"
        ] = False

        await show_payment_info(

            update.message,
            context,
            amount

        )

        return


    # =====================================================
    # DIAMOND PLAYER ID
    # =====================================================

    if context.user_data.get(
        "diamond_step"
    ) == "player_id":

        if not text.isdigit():

            await update.message.reply_text(

                "❌ Player ID faqat "
                "raqamlardan iborat "
                "bo‘lishi kerak."

            )

            return

        context.user_data[
            "diamond_player_id"
        ] = text

        context.user_data[
            "diamond_step"
        ] = "server_id"

        await update.message.reply_text(

            "🌐 Endi Server ID ni yozing.\n\n"

            "Masalan:\n"
            "1234"

        )

        return


    # =====================================================
    # DIAMOND SERVER ID
    # =====================================================

    if context.user_data.get(
        "diamond_step"
    ) == "server_id":

        if not text.isdigit():

            await update.message.reply_text(

                "❌ Server ID faqat "
                "raqamlardan iborat "
                "bo‘lishi kerak."

            )

            return

        player_id = context.user_data.get(
            "diamond_player_id"
        )

        server_id = text

        context.user_data[
            "diamond_server_id"
        ] = server_id

        await update.message.reply_text(
            "⏳ Player ID tekshirilmoqda..."
        )

        try:

            result = check_player(

                player_id,
                server_id

            )

            if result.get("ok"):

                name = result.get(

                    "nickname",

                    result.get(
                        "name",
                        "Noma'lum"
                    )

                )

                package_name = (
                    context.user_data.get(
                        "diamond_package_name",
                        "Diamond"
                    )
                )

                price = (
                    context.user_data.get(
                        "diamond_customer_price",
                        0
                    )
                )

                keyboard = InlineKeyboardMarkup([

                    [

                        InlineKeyboardButton(

                            "✅ TASDIQLASH",

                            callback_data=(
                                "confirm_diamond"
                            )

                        ),

                        InlineKeyboardButton(

                            "❌ BEKOR",

                            callback_data=(
                                "cancel_diamond"
                            )

                        ),

                    ]

                ])

                await update.message.reply_text(

                    "✅ PLAYER TOPILDI!\n\n"

                    f"👤 Nickname: {name}\n"
                    f"🆔 Player ID: {player_id}\n"
                    f"🌐 Server ID: {server_id}\n\n"

                    f"💎 Paket: {package_name}\n"

                    f"💰 Narx: "
                    f"{price:,} so‘m\n\n"

                    "Ma'lumotlar to‘g‘ri bo‘lsa "
                    "tasdiqlang.",

                    reply_markup=keyboard

                )

                context.user_data[
                    "diamond_step"
                ] = "confirm"

            else:

                await update.message.reply_text(

                    "❌ Player topilmadi.\n\n"

                    "Player ID va Server ID ni "
                    "tekshirib qaytadan kiriting."

                )

        except Exception as e:

            print(
                "CHECK PLAYER ERROR:",
                repr(e)
            )

            await update.message.reply_text(

                "❌ Player ID tekshirishda "
                "xatolik yuz berdi."

            )

        return


    # =====================================================
    # BOOST STEPS
    # =====================================================

    boost_step = context.user_data.get(
        "boost_step"
    )


    if boost_step == "current_rank":

        context.user_data[
            "boost_current_rank"
        ] = text

        context.user_data[
            "boost_step"
        ] = "player_id"

        await update.message.reply_text(

            "👤 Mobile Legends "
            "Player ID ni yozing."

        )

        return


    if boost_step == "player_id":

        if not text.isdigit():

            await update.message.reply_text(

                "❌ Player ID faqat "
                "raqamlardan iborat "
                "bo‘lishi kerak."

            )

            return

        context.user_data[
            "boost_player_id"
        ] = text

        context.user_data[
            "boost_step"
        ] = "server_id"

        await update.message.reply_text(

            "🌐 Server ID ni yozing."

        )

        return


    if boost_step == "server_id":

        if not text.isdigit():

            await update.message.reply_text(

                "❌ Server ID faqat "
                "raqamlardan iborat "
                "bo‘lishi kerak."

            )

            return

        context.user_data[
            "boost_server_id"
        ] = text

        context.user_data[
            "boost_step"
        ] = "confirm"

        target = (
            context.user_data.get(
                "boost_target_rank",
                "Noma'lum"
            )
        )

        current = (
            context.user_data.get(
                "boost_current_rank",
                "Noma'lum"
            )
        )

        price = (
            context.user_data.get(
                "boost_price",
                0
            )
        )

        keyboard = InlineKeyboardMarkup([

            [

                InlineKeyboardButton(

                    "✅ TASDIQLASH",

                    callback_data=(
                        "confirm_boost"
                    )

                ),

                InlineKeyboardButton(

                    "❌ BEKOR",

                    callback_data=(
                        "cancel_boost"
                    )

                ),

            ]

        ])

        await update.message.reply_text(

            "🚀 BOOST BUYURTMASI\n\n"

            f"📌 Hozirgi rank: {current}\n"

            f"🎯 Target rank: {target}\n"

            f"👤 Player ID: "
            f"{context.user_data.get('boost_player_id')}\n"

            f"🌐 Server ID: {text}\n"

            f"💰 Narx: {price:,} so‘m\n\n"

            "Ma'lumotlar to‘g‘ri bo‘lsa "
            "tasdiqlang.",

            reply_markup=keyboard

        )

        return


    # =====================================================
    # UNKNOWN TEXT
    # =====================================================

    await update.message.reply_text(

        "❓ Tushunmadim.\n\n"

        "Bosh menyuni ochish uchun "
        "/start ni bosing."

    )


# =========================================================
# BOOST CONFIRMATION
# =========================================================

async def handle_boost_confirmation(
    query,
    context
):

    target = context.user_data.get(
        "boost_target_rank"
    )

    current = context.user_data.get(
        "boost_current_rank"
    )

    player_id = context.user_data.get(
        "boost_player_id"
    )

    server_id = context.user_data.get(
        "boost_server_id"
    )

    price = context.user_data.get(
        "boost_price",
        0
    )

    if not all([
        target,
        current,
        player_id,
        server_id
    ]):

        await query.message.reply_text(

            "❌ Boost ma'lumotlari "
            "to‘liq emas."

        )

        return

    await query.message.reply_text(

        "✅ BOOST BUYURTMASI "
        "QABUL QILINDI!\n\n"

        f"📌 Hozirgi rank: {current}\n"

        f"🎯 Target: {target}\n"

        f"👤 Player ID: {player_id}\n"

        f"🌐 Server ID: {server_id}\n"

        f"💰 Narx: {price:,} so‘m\n\n"

        "⏳ Operator buyurtmani "
        "ko‘rib chiqadi."

    )

    if ADMIN_CHAT_ID:

        try:

            await context.bot.send_message(

                chat_id=int(
                    ADMIN_CHAT_ID
                ),

                text=(

                    "🚀 YANGI BOOST BUYURTMASI\n\n"

                    f"👤 User ID: "
                    f"{query.from_user.id}\n"

                    f"📌 Hozirgi rank: "
                    f"{current}\n"

                    f"🎯 Target: {target}\n"

                    f"🆔 Player ID: "
                    f"{player_id}\n"

                    f"🌐 Server ID: "
                    f"{server_id}\n"

                    f"💰 Narx: "
                    f"{price:,} so‘m"

                )

            )

        except Exception as e:

            print(
                "ADMIN BOOST MESSAGE ERROR:",
                repr(e)
            )


# =========================================================
# RECEIPT PHOTO
# =========================================================

async def receipt_photo_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not context.user_data.get(
        "waiting_receipt"
    ):

        await update.message.reply_text(

            "📸 Agar to‘lov qilgan bo‘lsangiz, "
            "avval «TO‘LOV QILDIM» tugmasini bosing."

        )

        return

    amount = context.user_data.get(
        "topup_amount",
        0
    )

    await update.message.reply_text(

        "✅ Chek qabul qilindi!\n\n"

        "⏳ Operator tekshiradi. "

        "Tekshiruvdan keyin siz bilan "
        "bog‘laniladi."

    )

    if ADMIN_CHAT_ID:

        try:

            photo = update.message.photo[-1]

            caption = (

                "💳 YANGI TOP UP CHEKI\n\n"

                f"👤 User ID: "
                f"{update.effective_user.id}\n"

                f"👤 Username: "
                f"@{update.effective_user.username or 'yo‘q'}\n"

                f"💰 Summa: "
                f"{amount:,} so‘m"

            )

            await context.bot.send_photo(

                chat_id=int(
                    ADMIN_CHAT_ID
                ),

                photo=photo.file_id,

                caption=caption

            )

        except Exception as e:

            print(
                "ADMIN PHOTO ERROR:",
                repr(e)
            )

    context.user_data[
        "waiting_receipt"
    ] = False


# =========================================================
# ERROR HANDLER
# =========================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    print(
        "BOT ERROR:",
        repr(context.error)
    )


# =========================================================
# MAIN
# =========================================================

def main():
    init_db()
    threading.Thread(

        target=start_web_server,

        daemon=True

    ).start()


    application = (

        ApplicationBuilder()

        .token(TOKEN)

        .build()

    )


    application.add_handler(

        CommandHandler(
            "start",
            start
        )

    )


    application.add_handler(

        CallbackQueryHandler(
            button_handler
        )

    )


    application.add_handler(

        MessageHandler(
            filters.PHOTO,
            receipt_photo_handler
        )

    )


    application.add_handler(

        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            text_handler
        )

    )


    application.add_error_handler(
        error_handler
    )


    print(
        "🤖 PHOENIX DONAT SHOP BOT ISHLADI!"
    )


    application.run_polling()


# =========================================================
# START BOT
# =========================================================

if __name__ == "__main__":

    main()
