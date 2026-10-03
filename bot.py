import asyncio
import os
import aiosqlite

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


# =========================
# SETTINGS
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Render Environment Variables ga ADMIN_ID qo'yish:
# ADMIN_ID = Telegram ID raqamingiz
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

DB_NAME = "phoenix.db"

SUPPORT_USERNAME = os.getenv(
    "SUPPORT_USERNAME",
    "Shohjaxono1"
)

WEBAPP_URL = os.getenv(
    "WEBAPP_URL",
    ""
)


if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable topilmadi")


bot = Bot(BOT_TOKEN)
dp = Dispatcher()


# =========================
# STATES
# =========================

class OrderState(StatesGroup):
    waiting_game_id = State()
    waiting_server = State()
    confirming = State()


class DepositState(StatesGroup):
    waiting_amount = State()


class AdminPackageState(StatesGroup):
    waiting_name = State()
    waiting_price = State()


class AdminBalanceState(StatesGroup):
    waiting_user_id = State()
    waiting_amount = State()


class PromoState(StatesGroup):
    waiting_code = State()


# =========================
# DATABASE
# =========================

async def db():
    return await aiosqlite.connect(DB_NAME)


async def init_db():

    database = await db()

    await database.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            balance INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    await database.execute("""
        CREATE TABLE IF NOT EXISTS packages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price INTEGER NOT NULL,
            active INTEGER DEFAULT 1
        )
    """)

    await database.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            package_id INTEGER,
            package_name TEXT NOT NULL,
            price INTEGER NOT NULL,
            game_id TEXT NOT NULL,
            server TEXT NOT NULL,
            status TEXT DEFAULT 'Kutilmoqda',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    await database.execute("""
        CREATE TABLE IF NOT EXISTS promo_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            discount INTEGER DEFAULT 0,
            active INTEGER DEFAULT 1
        )
    """)

    await database.commit()

    cursor = await database.execute(
        "SELECT COUNT(*) FROM packages"
    )

    count = (await cursor.fetchone())[0]

    if count == 0:

        packages = [
            ("86 Diamonds", 12000),
            ("172 Diamonds", 23000),
            ("257 Diamonds", 34000),
            ("344 Diamonds", 45000),
            ("429 Diamonds", 56000),
            ("514 Diamonds", 67000),
        ]

        await database.executemany(
            """
            INSERT INTO packages (name, price)
            VALUES (?, ?)
            """,
            packages
        )

        await database.commit()

    await database.close()


# =========================
# USER
# =========================

async def create_user(user):

    database = await db()

    await database.execute(
        """
        INSERT INTO users
        (user_id, username, first_name)
        VALUES (?, ?, ?)

        ON CONFLICT(user_id)
        DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name
        """,
        (
            user.id,
            user.username,
            user.first_name
        )
    )

    await database.commit()
    await database.close()


async def get_balance(user_id):

    database = await db()

    cursor = await database.execute(
        """
        SELECT balance
        FROM users
        WHERE user_id = ?
        """,
        (user_id,)
    )

    row = await cursor.fetchone()

    await database.close()

    return row[0] if row else 0


# =========================
# MAIN MENU
# =========================

def main_keyboard():

    buttons = [
        [
            InlineKeyboardButton(
                text="💎 Diamond",
                callback_data="diamond"
            ),
            InlineKeyboardButton(
                text="🚀 Boost",
                callback_data="boost"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔥 Sale",
                callback_data="sale"
            ),
            InlineKeyboardButton(
                text="💰 Balans",
                callback_data="balance"
            )
        ],
        [
            InlineKeyboardButton(
                text="📦 Buyurtmalarim",
                callback_data="orders"
            ),
            InlineKeyboardButton(
                text="👤 Profil",
                callback_data="profile"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎁 Promokod",
                callback_data="promo"
            ),
            InlineKeyboardButton(
                text="🆘 Support",
                callback_data="support"
            )
        ]
    ]

    if WEBAPP_URL:

        buttons.append([
            InlineKeyboardButton(
                text="🌐 DONAT SHOP",
                web_app={"url": WEBAPP_URL}
            )
        ])

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


def back_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Orqaga",
                    callback_data="home"
                )
            ]
        ]
    )


async def home_text(user_id):

    balance = await get_balance(user_id)

    return f"""
🔥 <b>PHOENIX DONAT</b>

🎮 Mobile Legends xizmatlari

💰 Balans:
<b>{balance:,} so'm</b>

Kerakli bo'limni tanlang:
"""


# =========================
# START
# =========================

@dp.message(CommandStart())
async def start(message: Message):

    await create_user(message.from_user)

    text = await home_text(
        message.from_user.id
    )

    await message.answer(
        text,
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )


# =========================
# HOME
# =========================

@dp.callback_query(F.data == "home")
async def home(callback: CallbackQuery):

    text = await home_text(
        callback.from_user.id
    )

    await callback.message.edit_text(
        text,
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# DIAMOND
# =========================

@dp.callback_query(F.data == "diamond")
async def diamond(callback: CallbackQuery):

    database = await db()

    cursor = await database.execute(
        """
        SELECT id, name, price
        FROM packages
        WHERE active = 1
        ORDER BY id
        """
    )

    packages = await cursor.fetchall()

    await database.close()

    buttons = []

    for package_id, name, price in packages:

        buttons.append([
            InlineKeyboardButton(
                text=f"💎 {name} — {price:,} so'm",
                callback_data=f"package_{package_id}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Orqaga",
            callback_data="home"
        )
    ])

    await callback.message.edit_text(
        """
💎 <b>MOBILE LEGENDS</b>

Kerakli Diamond paketini tanlang:
""",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        ),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# PACKAGE
# =========================

@dp.callback_query(F.data.startswith("package_"))
async def package_select(
    callback: CallbackQuery,
    state: FSMContext
):

    package_id = int(
        callback.data.split("_")[1]
    )

    database = await db()

    cursor = await database.execute(
        """
        SELECT name, price
        FROM packages
        WHERE id = ?
        AND active = 1
        """,
        (package_id,)
    )

    package = await cursor.fetchone()

    await database.close()

    if not package:

        await callback.answer(
            "Paket topilmadi",
            show_alert=True
        )

        return

    name, price = package

    await state.update_data(
        package_id=package_id,
        package_name=name,
        price=price
    )

    await state.set_state(
        OrderState.waiting_game_id
    )

    await callback.message.edit_text(
        f"""
💎 <b>{name}</b>

💰 Narxi:
<b>{price:,} so'm</b>

🎮 MLBB ID raqamingizni yuboring:
""",
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# GAME ID
# =========================

@dp.message(OrderState.waiting_game_id)
async def game_id(
    message: Message,
    state: FSMContext
):

    if not message.text:
        return

    await state.update_data(
        game_id=message.text.strip()
    )

    await state.set_state(
        OrderState.waiting_server
    )

    await message.answer(
        """
🌐 <b>Server ID</b>ni yuboring.

Masalan:
<code>1234</code>
""",
        parse_mode="HTML"
    )


# =========================
# SERVER
# =========================

@dp.message(OrderState.waiting_server)
async def server_id(
    message: Message,
    state: FSMContext
):

    if not message.text:
        return

    data = await state.get_data()

    server = message.text.strip()

    balance = await get_balance(
        message.from_user.id
    )

    price = data["price"]

    if balance < price:

        await state.clear()

        await message.answer(
            f"""
❌ <b>Balans yetarli emas.</b>

💰 Balansingiz:
<b>{balance:,} so'm</b>

💵 Kerak:
<b>{price:,} so'm</b>

Avval balansni to'ldiring.
""",
            reply_markup=main_keyboard(),
            parse_mode="HTML"
        )

        return

    await state.update_data(
        server=server
    )

    await state.set_state(
        OrderState.confirming
    )

    await message.answer(
        f"""
📦 <b>BUYURTMA TASDIQLASH</b>

💎 Paket:
<b>{data["package_name"]}</b>

💰 Narx:
<b>{price:,} so'm</b>

🎮 MLBB ID:
<code>{data["game_id"]}</code>

🌐 Server:
<code>{server}</code>
""",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Tasdiqlash",
                        callback_data="confirm_order"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Bekor qilish",
                        callback_data="cancel_order"
                    )
                ]
            ]
        ),
        parse_mode="HTML"
    )


# =========================
# CONFIRM ORDER
# =========================

@dp.callback_query(F.data == "confirm_order")
async def confirm_order(
    callback: CallbackQuery,
    state: FSMContext
):

    data = await state.get_data()

    user_id = callback.from_user.id
    price = data["price"]

    database = await db()

    cursor = await database.execute(
        """
        SELECT balance
        FROM users
        WHERE user_id = ?
        """,
        (user_id,)
    )

    row = await cursor.fetchone()

    if not row or row[0] < price:

        await database.close()
        await state.clear()

        await callback.message.edit_text(
            "❌ Balans yetarli emas.",
            reply_markup=main_keyboard()
        )

        return

    new_balance = row[0] - price

    await database.execute(
        """
        UPDATE users
        SET balance = ?
        WHERE user_id = ?
        """,
        (new_balance, user_id)
    )

    cursor = await database.execute(
        """
        INSERT INTO orders
        (
            user_id,
            package_id,
            package_name,
            price,
            game_id,
            server,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            data["package_id"],
            data["package_name"],
            price,
            data["game_id"],
            data["server"],
            "Kutilmoqda"
        )
    )

    order_id = cursor.lastrowid

    await database.commit()
    await database.close()

    await state.clear()

    await callback.message.edit_text(
        f"""
✅ <b>BUYURTMA QABUL QILINDI</b>

🆔 Buyurtma:
<b>#{order_id}</b>

💎 {data["package_name"]}

🎮 ID:
<code>{data["game_id"]}</code>

🌐 Server:
<code>{data["server"]}</code>

💰 Summa:
<b>{price:,} so'm</b>

⏳ Holat:
<b>Kutilmoqda</b>
""",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )

    # ADMIN NOTIFICATION

    if ADMIN_ID:

        try:

            await bot.send_message(
                ADMIN_ID,
                f"""
📦 <b>YANGI BUYURTMA</b>

🆔 #{order_id}

👤 User:
<code>{user_id}</code>

💎 {data["package_name"]}

💰 {price:,} so'm

🎮 ID:
<code>{data["game_id"]}</code>

🌐 Server:
<code>{data["server"]}</code>

⏳ Kutilmoqda
""",
                parse_mode="HTML"
            )

        except Exception:
            pass

    await callback.answer()


# =========================
# CANCEL
# =========================

@dp.callback_query(F.data == "cancel_order")
async def cancel_order(
    callback: CallbackQuery,
    state: FSMContext
):

    await state.clear()

    await callback.message.edit_text(
        "❌ Buyurtma bekor qilindi.",
        reply_markup=main_keyboard()
    )

    await callback.answer()


# =========================
# BALANCE
# =========================

@dp.callback_query(F.data == "balance")
async def balance(callback: CallbackQuery):

    balance = await get_balance(
        callback.from_user.id
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="10 000 so'm",
                    callback_data="deposit_10000"
                )
            ],
            [
                InlineKeyboardButton(
                    text="20 000 so'm",
                    callback_data="deposit_20000"
                )
            ],
            [
                InlineKeyboardButton(
                    text="50 000 so'm",
                    callback_data="deposit_50000"
                )
            ],
            [
                InlineKeyboardButton(
                    text="100 000 so'm",
                    callback_data="deposit_100000"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Orqaga",
                    callback_data="home"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        f"""
💰 <b>BALANS</b>

Hozirgi balans:
<b>{balance:,} so'm</b>

Balansni to'ldirish summasini tanlang:
""",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# DEPOSIT
# =========================

@dp.callback_query(F.data.startswith("deposit_"))
async def deposit(callback: CallbackQuery):

    amount = int(
        callback.data.split("_")[1]
    )

    await callback.message.edit_text(
        f"""
💳 <b>BALANS TO'LDIRISH</b>

💰 Summa:
<b>{amount:,} so'm</b>

To'lovni amalga oshirish uchun operator bilan bog'laning.

⚠️ To'lov tizimi API orqali alohida ulanadi.
""",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="👨‍💻 Operator",
                        url=f"https://t.me/{SUPPORT_USERNAME.lstrip('@')}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⬅️ Orqaga",
                        callback_data="balance"
                    )
                ]
            ]
        ),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# ORDERS
# =========================

@dp.callback_query(F.data == "orders")
async def orders(callback: CallbackQuery):

    database = await db()

    cursor = await database.execute(
        """
        SELECT id, package_name, price, status
        FROM orders
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 20
        """,
        (callback.from_user.id,)
    )

    rows = await cursor.fetchall()

    await database.close()

    if not rows:

        text = """
📦 <b>BUYURTMALARIM</b>

Hali buyurtmalaringiz yo'q.
"""

    else:

        text = "📦 <b>BUYURTMALARIM</b>\n\n"

        for order_id, name, price, status in rows:

            text += (
                f"🆔 #{order_id}\n"
                f"💎 {name}\n"
                f"💰 {price:,} so'm\n"
                f"📌 {status}\n\n"
            )

    await callback.message.edit_text(
        text,
        reply_markup=back_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# PROFILE
# =========================

@dp.callback_query(F.data == "profile")
async def profile(callback: CallbackQuery):

    user = callback.from_user

    balance = await get_balance(
        user.id
    )

    username = (
        f"@{user.username}"
        if user.username
        else "yo'q"
    )

    await callback.message.edit_text(
        f"""
👤 <b>PROFIL</b>

🆔 Telegram ID:
<code>{user.id}</code>

👤 Username:
{username}

💰 Balans:
<b>{balance:,} so'm</b>
""",
        reply_markup=back_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# PROMO
# =========================

@dp.callback_query(F.data == "promo")
async def promo(callback: CallbackQuery, state: FSMContext):

    await state.set_state(
        PromoState.waiting_code
    )

    await callback.message.edit_text(
        """
🎁 <b>PROMOKOD</b>

Promokodingizni yuboring:
""",
        parse_mode="HTML"
    )

    await callback.answer()


@dp.message(PromoState.waiting_code)
async def promo_code(
    message: Message,
    state: FSMContext
):

    code = message.text.strip().upper()

    database = await db()

    cursor = await database.execute(
        """
        SELECT discount
        FROM promo_codes
        WHERE code = ?
        AND active = 1
        """,
        (code,)
    )

    row = await cursor.fetchone()

    await database.close()

    await state.clear()

    if not row:

        await message.answer(
            "❌ Promokod topilmadi.",
            reply_markup=main_keyboard()
        )

        return

    await message.answer(
        f"""
✅ <b>PROMOKOD QABUL QILINDI</b>

🎁 Chegirma:
<b>{row[0]}%</b>
""",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )


# =========================
# BOOST / SALE
# =========================

@dp.callback_query(F.data == "boost")
async def boost(callback: CallbackQuery):

    await callback.message.edit_text(
        """
🚀 <b>BOOST</b>

Boost xizmatlari tez orada qo'shiladi.
""",
        reply_markup=back_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


@dp.callback_query(F.data == "sale")
async def sale(callback: CallbackQuery):

    await callback.message.edit_text(
        """
🔥 <b>SALE</b>

Chegirmali xizmatlar tez orada qo'shiladi.
""",
        reply_markup=back_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# SUPPORT
# =========================

@dp.callback_query(F.data == "support")
async def support(callback: Ca
