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


# =========================
# ENVIRONMENT
# =========================

TOKEN = os.environ["BOT_TOKEN"]

PORT = int(
    os.environ.get(
        "PORT",
        "10000"
    )
)

CARD_NUMBER = os.environ.get(
    "CARD_NUMBER",
    "KARTA RAQAMI KIRITILMAGAN"
)

PLAYPAY_API_KEY = os.environ.get(
    "PLAYPAY_API_KEY",
    ""
)


# =========================
# SETTINGS
# =========================

PLAYPAY_API = (
    "https://playpay.uz/api/v1"
)

SUPPORT_USERNAME = (
    "Shohjaxono1"
)

MLBB_GAME_ID = 3

WEB_APP_URL = (
    "https://shura-donat-shop-bot.onrender.com"
)


# =========================
# RENDER HEALTH CHECK
# =========================

class HealthHandler(
    BaseHTTPRequestHandler
):

    def do_GET(self):

        self.send_response(200)

        self.send_header(
            "Content-Type",
            "text/plain; charset=utf-8"
        )

        self.end_headers()

        self.wfile.write(
            b"PHOENIX DONAT SHOP is running!"
        )

    def log_message(
        self,
        format,
        *args
    ):
        return


def start_web_server():

    server = HTTPServer(
        (
            "0.0.0.0",
            PORT
        ),
        HealthHandler
    )

    server.serve_forever()


# =========================
# PLAYPAY HEADERS
# =========================

def playpay_headers():

    return {
        "X-API-Key": PLAYPAY_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


# =========================
# GET DIAMOND PACKAGES
# =========================

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

    return response.json()


# =========================
# CHECK PLAYER
# =========================

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

    return response.json()


# =========================
# CREATE ORDER
# =========================

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

    return response.json()


# =========================
# START COMMAND
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    keyboard = [

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
                ),
            )
        ],

        [
            InlineKeyboardButton(
                "🆘 HELP / SUPPORT",
                callback_data="help"
            )
        ],
    ]

    await update.message.reply_text(

        "🔥 PHOENIX DONAT SHOP\n\n"

        "💎 Mobile Legends xizmatlari\n"
        "⚡ Tezkor xizmat\n\n"

        "Kerakli xizmatni tanlang:",

        reply_markup=(
            InlineKeyboardMarkup(
                keyboard
            )
        ),
    )


# =========================
# BUTTON HANDLER
# =========================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    try:

        await query.answer()

    except Exception:

        pass


    # =====================
    # DIAMOND
    # =====================

    if query.data == "diamond":

        if not PLAYPAY_API_KEY:

            await query.message.reply_text(

                "❌ PlayPay API kaliti "
                "sozlanmagan.\n\n"

                "Render → Environment → "
                "PLAYPAY_API_KEY"
            )

            return


        try:

            data = (
                get_diamond_packages()
            )


            if not data.get("ok"):

                await query.message.reply_text(

                    "❌ Diamond paketlarini "
                    "olishda xatolik.\n\n"

                    f"Xato: "
                    f"{data.get('error', 'unknown')}"
                )

                return


            packages = data.get(
                "packages",
                []
            )


            if not packages:

                await query.message.reply_text(

                    "❌ Hozircha diamond "
                    "paketlari mavjud emas."
                )

                return


            keyboard = []


            for package in packages:

                package_id = package.get(
                    "paket_id"
                )

                name = package.get(
                    "name",
                    "Diamond"
                )

                price = package.get(
                    "price",
                    {}
                ).get(
                    "amount",
                    0
                )


                keyboard.append(

                    [
                        InlineKeyboardButton(

                            f"💎 {name} — "
                            f"{price:,} so‘m",

                            callback_data=(
                                f"diamond_"
                                f"{package_id}"
                            ),
                        )
                    ]
                )


            await query.message.reply_text(

                "💎 DIAMOND\n\n"

                "Kerakli diamond "
                "paketini tanlang:",

                reply_markup=(
                    InlineKeyboardMarkup(
                        keyboard
                    )
                ),
            )


        except Exception:

            await query.message.reply_text(

                "❌ PlayPay API bilan "
                "bog‘lanishda xatolik.\n\n"

                "API key va PlayPay "
                "sozlamalarini tekshiring."
            )


        return


    # =====================
    # DIAMOND PACKAGE
    # =====================

    if query.data.startswith(
        "diamond_"
    ):

        package_id = (
            query.data.replace(
                "diamond_",
                "",
                1
            )
        )


        context.user_data[
            "diamond_package_id"
        ] = package_id


        context.user_data[
            "diamond_step"
        ] = "player_id"


        await query.message.reply_text(

            "💎 DIAMOND BUYURTMA\n\n"

            "1️⃣ Mobile Legends "
            "Player ID / User ID ni yozing.\n\n"

            "Masalan:\n"
            "123456789"
        )

        return


    # =====================
    # CONFIRM DIAMOND
    # =====================

    if query.data == (
        "confirm_diamond"
    ):

        package_id = (
            context.user_data.get(
                "diamond_package_id"
            )
        )

        player_id = (
            context.user_data.get(
                "diamond_player_id"
            )
        )

        server_id = (
            context.user_data.get(
                "diamond_server_id"
            )
        )


        if (
            not package_id
            or not player_id
            or not server_id
        ):

            await query.message.reply_text(

                "❌ Buyurtma ma'lumotlari "
                "topilmadi.\n"

                "Qaytadan DIAMOND "
                "bo‘limiga kiring."
            )

            return


        if not PLAYPAY_API_KEY:

            await query.message.reply_text(

                "❌ PlayPay API key "
                "sozlanmagan."
            )

            return


        try:

            result = create_order(
                package_id,
                player_id,
                server_id
            )


            if result.get("ok"):

                order_id = (
                    result.get(
                        "order_id",
                        "Noma'lum"
                    )
                )


                await query.message.reply_text(

                    "✅ BUYURTMA "
                    "QABUL QILINDI!\n\n"

                    f"💎 Paket: "
                    f"{context.user_data.get('diamond_package_name', 'Diamond')}\n"

                    f"👤 Player ID: "
                    f"{player_id}\n"

                    f"🌐 Server ID: "
                    f"{server_id}\n\n"

                    f"🧾 Order ID: "
                    f"{order_id}\n\n"

                    "⏳ Diamond yetkazilishi "
                    "kutilmoqda."
                )


            else:

                await query.message.reply_text(

                    "❌ Buyurtma yaratilmadi.\n\n"

                    f"Xato: "
                    f"{result.get('error', 'unknown')}"
                )


        except Exception:

            await query.message.reply_text(

                "❌ PlayPay API bilan "
                "bog‘lanishda xatolik."
            )


        context.user_data[
            "diamond_step"
        ] = None

        return


    # =====================
    # CANCEL DIAMOND
    # =====================

    if query.data == (
        "cancel_diamond"
    ):

        keys = (

            "diamond_package_id",

            "diamond_player_id",

            "diamond_server_id",

            "diamond_package_name",

            "diamond_customer_price",
        )


        for key in keys:

            context.user_data.pop(
                key,
                None
            )


        context.user_data[
            "diamond_step"
        ] = None


        await query.message.reply_text(

            "❌ Diamond buyurtmasi "
            "bekor qilindi."
        )

        return


    # =====================
    # PAID
    # =====================

    if query.data == "paid":

        amount = (
            context.user_data.get(
                "topup_amount"
            )
        )


        if not amount:

            await query.message.reply_text(

                "❌ Top Up summasi "
                "topilmadi.\n"

                "Qaytadan TOP UP "
                "ni tanlang."
            )

            return


        context.user_data[
            "waiting_receipt"
        ] = True


        await query.message.reply_text(

            "📸 TO‘LOVNI "
            "TASDIQLASH\n\n"

            f"💰 Summa: "
            f"{amount:,} so‘m\n\n"

            "To‘lov chek yoki "
            "skrinshotini shu yerga "
            "yuboring.\n\n"

            "⚠️ Chek tekshirilmaguncha "
            "balans avtomatik "
            "oshirilmaydi."
        )

        return


    # =====================
    # SUPPORT
    # =====================

    if query.data == "help":

        keyboard = [

            [
                InlineKeyboardButton(

                    "💬 Operatorga yozish",

                    url=(
                        "https://t.me/"
                        f"{SUPPORT_USERNAME}"
                    ),
                )
            ]
        ]


        await query.message.reply_text(

            "🆘 SUPPORT\n\n"

            "Savolingiz yoki "
            "muammoingiz bo‘lsa,\n"

            "operatorga yozing:",

            reply_markup=(
                InlineKeyboardMarkup(
                    keyboard
                )
            ),
        )

        return


    # =====================
    # TOP UP
    # =====================

    if query.data == "topup":

        keyboard = [

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
        ]


        await query.message.reply_text(

            "💳 TOP UP\n\n"

            "Balansni qancha "
            "to‘ldirmoqchisiz?",

            reply_markup=(
                InlineKeyboardMarkup(
                    keyboard
                )
            ),
        )

        return


    # =====================
    # CUSTOM AMOUNT
    # =====================

    if query.data == (
        "custom_amount"
    ):

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


    # =====================
    # FIXED TOP UP
    # =====================

    if query.data.startswith(
        "topup_"
    ):

        try:

            amount = int(
                query.data.replace(
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


    # =====================
    # BOOST MENU
    # =====================

    if query.data == "boost":

        keyboard = [

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
        ]


        await query.message.reply_text(

            "🚀 BOOST\n\n"

            "🟣 Epic — "
            "4 000 so‘m / star\n"

            "🔵 Legend — "
            "5 000 so‘m / star\n"

            "🔴 Mythic — "
            "6 000 so‘m / point\n"

            "🟠 Mythical Honor — "
            "7 000 so‘m / point\n"

            "🟡 Mythical Glory — "
            "8 000 so‘m / point\n\n"

            "Qaysi target rank kerak?",

            reply_markup=(
                InlineKeyboardMarkup(
                    keyboard
                )
            ),
        )

        return


    # =====================
    # BOOST TARGET
    # =====================

    if query.data.startswith(
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


        rank_name, price = (
            rank_prices.get(
                query.data,
                ("", 0)
            )
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

            f"🚀 "
            f"{rank_name.upper()} "
            f"BOOST\n\n"

            "1️⃣ Hozirgi rankingizni "
            "yozing.\n\n"

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

            "Aksiyalar tez orada "
            "shu yerda."
        )

        return


# =========================
# PAYMENT INFO
# =========================

async def show_payment_info(
    message,
    context,
    amount
):

    context.user_data[
        "topup_amount"
    ] = amount


    context.user_data[
        "waiting_receipt"
    ] = False


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

                url=(
                    "https://t.me/"
                    f"{SUPPORT_USERNAME}"
                ),
            )
        ],
    ]


    await message.reply_text(

        "💳 TOP UP\n\n"

        f"💰 Summa: "
        f"{amount:,} so‘m\n\n"

        f"💳 KARTA:\n"
        f"{CARD_NUMBER}\n\n"

        "Yuqoridagi kartaga aynan "
        "shu summani o‘tkazing.\n\n"

        "To‘lovdan keyin "
        "«✅ Men to‘ladim» "
        "tugmasini bosing.\n\n"

        "⚠️ To‘lov tekshirilmaguncha "
        "balans avtomatik "
        "oshirilmaydi.",

        reply_markup=(
            InlineKeyboardMarkup(
                keyboard
            )
        ),
    )


# =========================
# TEXT HANDLER
# =========================

async def text_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return


    if not update.message.text:
        return


    text = (
        update.message.text.strip()
    )


    # =====================
    # DIAMOND PLAYER ID
    # =====================

    if context.user_data.get(
        "diamond_step"
    ) == "player_id":

        if not text.isdigit():

            await update.message.reply_text(

                "❌ Player ID faqat "
             
