import os
import asyncio
import logging
from pathlib import Path

import aiohttp
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
)

# =========================
# SETTINGS
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
PLAYPAY_API_KEY = os.getenv("PLAYPAY_API_KEY")
WEBAPP_URL = os.getenv("WEBAPP_URL")

PLAYPAY_API = "https://playpay.uz/api/v1"

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is missing")

if not PLAYPAY_API_KEY:
    raise RuntimeError("PLAYPAY_API_KEY environment variable is missing")

if not WEBAPP_URL:
    raise RuntimeError("WEBAPP_URL environment variable is missing")


# =========================
# LOGGING
# =========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# =========================
# BOT
# =========================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()


# =========================
# START
# =========================

@router.message(CommandStart())
async def start_handler(message: Message):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛒 OPEN SHOP",
                    web_app=WebAppInfo(url=WEBAPP_URL),
                )
            ]
        ]
    )

    await message.answer(
        "🔥 PHOENIX DONAT SHOP\n\n"
        "Mobile Legends xizmatlari uchun do‘kon.\n\n"
        "👇 Do‘konni ochish uchun tugmani bosing:",
        reply_markup=keyboard,
    )


# =========================
# PLAYPAY - MLBB PACKAGES
# =========================

async def get_mlbb_packages():

    url = f"{PLAYPAY_API}/games/3/packages"

    headers = {
        "X-API-Key": PLAYPAY_API_KEY
    }

    params = {
        "currency": "UZS"
    }

    timeout = aiohttp.ClientTimeout(total=30)

    async with aiohttp.ClientSession(timeout=timeout) as session:

        async with session.get(
            url,
            headers=headers,
            params=params,
        ) as response:

            data = await response.json()

            if response.status != 200:
                raise RuntimeError(
                    f"PlayPay HTTP {response.status}: {data}"
                )

            if not data.get("ok"):
                raise RuntimeError(
                    f"PlayPay error: {data}"
                )

            return data


# =========================
# TEST PLAYPAY
# =========================

async def test_playpay():

    try:

        data = await get_mlbb_packages()

        packages = data.get("packages", [])

        logger.info(
            "PlayPay MLBB packages: %s",
            len(packages)
        )

        for package in packages:

            logger.info(
                "MLBB | %s | %s UZS",
                package.get("name"),
                package.get("charged", {}).get("amount"),
            )

    except Exception as e:

        logger.error(
            "PlayPay test error: %s",
            e
        )


# =========================
# MAIN
# =========================

async def main():

    dp.include_router(router)

    logger.info("🔥 PHOENIX DONAT SHOP IS STARTING...")

    # PlayPay ulanishini tekshiramiz
    await test_playpay()

    logger.info("🤖 BOT STARTED")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
