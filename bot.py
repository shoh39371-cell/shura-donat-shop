import os
import asyncio
import logging
from pathlib import Path

import aiohttp
import uvicorn

from fastapi import FastAPI
from database import (
    init_db,
    create_or_update_user,
    get_user,
    get_balance,
    subtract_balance,
    add_balance,
)
from fastapi.responses import FileResponse, JSONResponse

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
)

# =========================================================
# SETTINGS
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
PLAYPAY_API_KEY = os.getenv("PLAYPAY_API_KEY")
WEBAPP_URL = os.getenv("WEBAPP_URL")

PLAYPAY_API = "https://playpay.uz/api/v1"

PORT = int(os.getenv("PORT", "10000"))

BASE_DIR = Path(__file__).resolve().parent
WEBAPP_DIR = BASE_DIR / "webapp"
WEBAPP_FILE = WEBAPP_DIR / "index.html"

# =========================================================
# CHECK ENVIRONMENT
# =========================================================

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")

if not PLAYPAY_API_KEY:
    raise RuntimeError("PLAYPAY_API_KEY is missing")

if not WEBAPP_URL:
    raise RuntimeError("WEBAPP_URL is missing")

# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("phoenix")

# =========================================================
# TELEGRAM
# =========================================================

bot = Bot(token=BOT_TOKEN)

dp = Dispatcher()

router = Router()

# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(
    title="PHOENIX DONAT SHOP",
    version="1.0.0",
)
@app.get("/style.css")
async def style_css():
    return FileResponse(
        WEBAPP_DIR / "style.css",
        media_type="text/css"
    )


@app.get("/app.js")
async def app_js():
    return FileResponse(
        WEBAPP_DIR / "app.js",
        media_type="application/javascript"
)
# =========================================================
# WEBAPP HOME
# =========================================================

@app.get("/")
async def home():

    if not WEBAPP_FILE.exists():
        return JSONResponse(
            {
                "ok": False,
                "error": "webapp/index.html topilmadi",
            },
            status_code=500,
        )

    return FileResponse(
        WEBAPP_FILE,
        media_type="text/html",
    )

# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
async def health():

    return {
        "ok": True,
        "service": "PHOENIX DONAT SHOP",
    }

# =========================================================
# PLAYPAY REQUEST
# =========================================================

async def playpay_request(
    method: str,
    path: str,
    payload: dict | None = None,
    params: dict | None = None,
):

    url = f"{PLAYPAY_API}{path}"

    headers = {
        "X-API-Key": PLAYPAY_API_KEY,
        "Content-Type": "application/json",
    }

    timeout = aiohttp.ClientTimeout(
        total=30
    )

    async with aiohttp.ClientSession(
        timeout=timeout
    ) as session:

        if method.upper() == "GET":

            async with session.get(
                url,
                headers=headers,
                params=params or {},
            ) as response:

                data = await response.json()

        else:

            async with session.post(
                url,
                headers=headers,
                json=payload or {},
            ) as response:

                data = await response.json()

        if response.status != 200:

            raise RuntimeError(
                f"PlayPay HTTP {response.status}: {data}"
            )

        if not data.get("ok"):

            raise RuntimeError(
                data.get(
                    "error",
                    "PlayPay API xatosi",
                )
            )

        return data
# =========================================================
# API: PLAYPAY BALANCE
# =========================================================

@app.get("/api/playpay-balance")
async def api_playpay_balance():

    try:

        data = await playpay_request(
            "GET",
            "/balance",
        )

        return {
            "ok": True,
            "balance": data.get("balance"),
            "discount_pct": data.get(
                "discount_pct",
                0,
            ),
            "markup_pct": data.get(
                "markup_pct",
                0,
            ),
        }

    except Exception as e:

        logger.exception(
            "PlayPay balance error"
        )

        return {
            "ok": False,
            "error": str(e),
        }
# =========================================================
# GET ALL PLAYPAY GAMES
# =========================================================

async def get_games():

    return await playpay_request(
        "GET",
        "/games",
    )

# =========================================================
# GET ALL MOBILE LEGENDS REGIONS
# =========================================================

async def get_mlbb_regions():

    data = await get_games()

    games = data.get(
        "games",
        [],
    )

    regions = []

    for game in games:

        name = str(
            game.get(
                "name",
                "",
            )
        ).strip()

        if "mobile legends" not in name.lower():
            continue

        game_id = game.get(
            "game_id"
        )

        if game_id is None:
            continue

        regions.append(
            {
                "game_id": int(game_id),

                "name": name,

                "id_label": game.get(
                    "id_label",
                    "User ID",
                ),

                "requires_server": bool(
                    game.get(
                        "requires_server",
                        False,
                    )
                ),

                "requires_charname": bool(
                    game.get(
                        "requires_charname",
                        False,
                    )
                ),

                "packages_count": game.get(
                    "packages_count",
                    0,
                ),
            }
        )

    return regions

# =========================================================
# API: REGIONS
# =========================================================

@app.get("/api/regions")
async def api_regions():

    try:

        regions = await get_mlbb_regions()

        return {
            "ok": True,
            "regions": regions,
        }

    except Exception as e:

        logger.exception(
            "Regions error"
        )

        return {
            "ok": False,
            "error": str(e),
        }

# =========================================================
# API: PACKAGES
# =========================================================
@app.get("/api/packages/{game_id}")
async def api_packages(
    game_id: int,
):

    try:

        regions = await get_mlbb_regions()

        allowed_ids = {
            region["game_id"]
            for region in regions
        }

        if game_id not in allowed_ids:

            return {
                "ok": False,
                "error": "Noto'g'ri Mobile Legends region",
            }

        data = await playpay_request(
            "GET",
            f"/games/{game_id}/packages",
            params={
                "currency": "UZS",
            },
        )

        packages = data.get(
            "packages",
            [],
        )

        for package in packages:

            price = float(
                package.get("price", {}).get(
                    "amount",
                    0,
                )
            )

            if price < 60000:
                markup = 0.05
            else:
                markup = 0.10

            final_price = round(
                price * (1 + markup)
            )

            package["price"]["amount"] = final_price

            package["markup_pct"] = int(
                markup * 100
            )

        return {
            "ok": True,
            "game_id": game_id,
            "packages": packages,
        }

    except Exception as e:

        logger.exception(
            "Packages error"
        )

        return {
            "ok": False,
            "error": str(e),
        }

# =========================================================
# API: BALANCE
# =========================================================

@app.get("/api/balance")
async def api_balance(telegram_id: int):

    try:

        balance = get_balance(
            telegram_id
        )

        return {
            "ok": True,
            "balance": balance,
        }

    except Exception as e:

        logger.exception(
            "Balance error"
        )

        return {
            "ok": False,
            "error": str(e),
        }
# =========================================================
# API: CHECK PLAYER ID
# =========================================================

@app.post("/api/check-player")
async def api_check_player(
    data: dict,
):

    try:

        game_id = int(
            data.get(
                "game_id"
            )
        )

        player_id = str(
            data.get(
                "player_id",
                "",
            )
        ).strip()

        server_id = str(
            data.get(
                "server_id",
                "",
            )
        ).strip()
        telegram_id = int(
    data.get(
        "telegram_id",
        0,
    )
)
        if not player_id:

            return {
                "ok": False,
                "error": "User ID kiritilmagan",
            }

        if not server_id:

            return {
                "ok": False,
                "error": "Server ID kiritilmagan",
            }

        regions = await get_mlbb_regions()

        allowed_ids = {
            region["game_id"]
            for region in regions
        }

        if game_id not in allowed_ids:

            return {
                "ok": False,
                "error": "Noto'g'ri Mobile Legends region",
            }

        result = await playpay_request(
            "POST",
            "/check_id",
            payload={
                "game_id": game_id,
                "player_id": player_id,
                "server_id": server_id,
            },
        )

        if not result.get("valid"):

            return {
                "ok": False,
                "error": "User ID yoki Server ID noto'g'ri",
            }

        return {
            "ok": True,
            "valid": True,
            "player_name": result.get(
                "player_name"
            ),
            "player_id": player_id,
            "server_id": server_id,
        }

    except Exception as e:

        logger.exception(
            "Player check error"
        )

        return {
            "ok": False,
            "error": str(e),
        }
# =========================================================
# API: CREATE PLAYPAY ORDER
# =========================================================

@app.post("/api/create-order")
async def api_create_order(data: dict):

    try:

        game_id = int(
            data.get("game_id")
        )

        package_id = int(
            data.get("package_id")
        )

        player_id = str(
            data.get(
                "player_id",
                "",
            )
        ).strip()

        server_id = str(
            data.get(
                "server_id",
                "",
            )
        ).strip()

        if not player_id:

            return {
                "ok": False,
                "error": "User ID kiritilmagan",
            }

        if not server_id:

            return {
                "ok": False,
                "error": "Server ID kiritilmagan",
            }

        regions = await get_mlbb_regions()

        allowed_ids = {
            region["game_id"]
            for region in regions
        }

        if game_id not in allowed_ids:

            return {
                "ok": False,
                "error": "Noto'g'ri Mobile Legends region",
            }

        result = await playpay_request(
            "POST",
            "/order",
            payload={
                "game_id": game_id,
                "paket_id": package_id,
                "player_id": player_id,
                "server_id": server_id,
            },
        )

        return {
            "ok": True,
            "order": result,
        }

    except Exception as e:

        logger.exception(
            "Create order error"
        )

        return {
            "ok": False,
            "error": str(e),
        }
# =========================================================
# TELEGRAM /START
# =========================================================

@router.message(
    CommandStart()
)
async def start_handler(
    message: Message,
):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔥 OPEN SHOP",
                    web_app=WebAppInfo(
                        url=WEBAPP_URL
                    ),
                )
            ]
        ]
    )

    await message.answer(
        "🔥 <b>PHOENIX DONAT SHOP</b>\n\n"
        "Mobile Legends va boshqa "
        "gaming xizmatlari uchun premium shop.\n\n"
        "👇 Shopni ochish uchun tugmani bosing.",
        reply_markup=keyboard,
        parse_mode="HTML",
    )

# =========================================================
# BOT
# =========================================================

async def run_bot():

    dp.include_router(
        router
    )

    logger.info(
        "🤖 PHOENIX BOT STARTED"
    )

    await dp.start_polling(
        bot
    )

# =========================================================
# WEB SERVER
# =========================================================

async def run_server():

    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level="info",
    )

    server = uvicorn.Server(
        config
    )

    logger.info(
        "🌐 WEBAPP STARTED ON PORT %s",
        PORT,
    )

    await server.serve()

# =========================================================
# MAIN
# =========================================================

async def main():
    init_db()

    await asyncio.gather(
        run_bot(),
        run_server(),
    )

# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    asyncio.run(
        main()
        )
