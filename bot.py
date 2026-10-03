import os
import asyncio
import logging

import aiohttp
import uvicorn

from fastapi import FastAPI
from fastapi.responses import FileResponse

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

PORT = int(os.getenv("PORT", "10000"))


if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")

if not PLAYPAY_API_KEY:
    raise RuntimeError("PLAYPAY_API_KEY is missing")


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
# FASTAPI
# =========================

app = FastAPI()


# =========================
# WEBAPP
# =========================

@app.get("/")
async def home():

    return FileResponse(
        "webapp/index.html"
    )


# =========================
# PLAYPAY PACKAGES
# =========================

async def get_mlbb_packages():

    url = f"{PLAYPAY_API}/games/3/packages"

    headers = {
        "X-API-Key": PLAYPAY_API_KEY
    }

    params = {
        "currency": "UZS"
    }

    timeout = aiohttp.ClientTimeout(
        total=30
    )

    async with aiohttp.ClientSession(
        timeout=timeout
    ) as session:

        async with session.get(
            url,
            headers=headers,
            params=params,
        ) as response:

            data = await response.json()

            if response.status != 200:

                raise RuntimeError(
                    f"PlayPay HTTP {response.status}"
                )

            if not data.get("ok"):

                raise RuntimeError(
                    data.get("error", "PlayPay error")
                )

            return data


# =========================
# API
# =========================

@app.get("/api/packages")
async def packages():

    try:

        data = await get_mlbb_packages()

        return {
            "ok": True,
            "packages": data.get(
                "packages",
                []
            )
        }

    except Exception as e:

        logger.error(
            "Packages error: %s",
            e
        )

        return {
            "ok": False,
            "error": str(e)
        }


# =========================
# TELEGRAM START
# =========================

@router.message(CommandStart())
async def start_handler(
    message: Message
):

    if not WEBAPP_URL:

        await message.answer(
            "⚠️ WebApp URL hali sozlanmagan."
        )

        return


    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛒 OPEN SHOP",
                    web_app=WebAppInfo(
                        url=WEBAPP_URL
                    ),
                )
            ]
        ]
    )


    await message.answer(
        "🔥 PHOENIX DONAT SHOP\n\n"
        "Mobile Legends xizmatlari uchun "
        "rasmiy shop.\n\n"
        "👇 Shopni oching:",
        reply_markup=keyboard,
    )


# =========================
# BOT RUNNER
# =========================

async def run_bot():

    dp.include_router(router)

    logger.info(
        "🤖 Telegram bot started"
    )

    await dp.start_polling(bot)


# =========================
# SERVER RUNNER
# =========================

async def run_server():

    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level="info",
    )

    server = uvicorn.Server(config)

    logger.info(
        "🌐 WebApp server started on port %s",
        PORT
    )

    await server.serve()


# =========================
# MAIN
# =========================

async def main():

    await asyncio.gather(
        run_bot(),
        run_server(),
    )


if __name__ == "__main__":

    asyncio.run(main())
