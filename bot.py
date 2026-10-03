import os
import asyncio
import logging
from pathlib import Path

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

BOT_TOKEN = os.getenv("BOT_TOKEN")
PLAYPAY_API_KEY = os.getenv("PLAYPAY_API_KEY")
WEBAPP_URL = os.getenv("WEBAPP_URL")

PLAYPAY_API = "https://playpay.uz/api/v1"
PORT = int(os.getenv("PORT", "10000"))

BASE_DIR = Path(__file__).resolve().parent
WEBAPP_FILE = BASE_DIR / "webapp" / "index.html"

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")

if not PLAYPAY_API_KEY:
    raise RuntimeError("PLAYPAY_API_KEY is missing")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

app = FastAPI()


# =========================
# WEBAPP
# =========================

@app.get("/")
async def home():
    return FileResponse(WEBAPP_FILE)


# =========================
# PLAYPAY REQUEST
# =========================

async def playpay_get(path, params=None):
    url = f"{PLAYPAY_API}{path}"

    headers = {
        "X-API-Key": PLAYPAY_API_KEY
    }

    timeout = aiohttp.ClientTimeout(total=30)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(
            url,
            headers=headers,
            params=params or {},
        ) as response:

            data = await response.json()

            if response.status != 200:
                raise RuntimeError(
                    f"PlayPay HTTP {response.status}: {data}"
                )

            if not data.get("ok"):
                raise RuntimeError(
                    data.get("error", "PlayPay error")
                )

            return data


# =========================
# GET ALL MLBB REGIONS
# =========================

async def get_mlbb_games():

    data = await playpay_get("/games")

    games = data.get("games", [])

    mlbb_games = []

    for game in games:

        name = str(game.get("name", "")).lower()

        if "mobile legends" in name:

            mlbb_games.append({
                "game_id": game.get("game_id"),
                "name": game.get("name"),
                "id_label": game.get("id_label"),
                "requires_server": game.get("requires_server"),
                "requires_charname": game.get("requires_charname"),
                "packages_count": game.get("packages_count"),
            })

    return mlbb_games


# =========================
# REGIONS API
# =========================

@app.get("/api/regions")
async def regions():

    try:

        games = await get_mlbb_games()

        return {
            "ok": True,
            "regions": games,
        }

    except Exception as e:

        logger.error("Regions error: %s", e)

        return {
            "ok": False,
            "error": str(e),
        }


# =========================
# PACKAGES BY GAME ID
# =========================

@app.get("/api/packages/{game_id}")
async def packages(game_id: int):

    try:

        # Security: only positive game IDs
        if game_id <= 0:
            return {
                "ok": False,
                "error": "Invalid game_id",
            }

        # Make sure this game is actually MLBB
        games = await get_mlbb_games()

        allowed_ids = {
            int(game["game_id"])
            for game in games
            if game.get("game_id") is not None
        }

        if game_id not in allowed_ids:
            return {
                "ok": False,
                "error": "This is not a Mobile Legends game ID",
            }

        data = await playpay_get(
            f"/games/{game_id}/packages",
            {
                "currency": "UZS"
            },
        )

        return {
            "ok": True,
            "game_id": game_id,
            "packages": data.get("packages", []),
        }

    except Exception as e:

        logger.error(
            "Packages error for game %s: %s",
            game_id,
            e,
        )

        return {
            "ok": False,
            "error": str(e),
        }


# =========================
# TELEGRAM /START
# =========================

@router.message(CommandStart())
async def start_handler(message: Message):

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
# BOT
# =========================

async def run_bot():

    dp.include_router(router)

    logger.info(
        "🤖 Telegram bot started"
    )

    await dp.start_polling(bot)


# =========================
# WEB SERVER
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
        PORT,
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
