import os
import asyncio
import logging
from pathlib import Path
import uuid
import sqlite3
import os
import aiohttp
import uvicorn

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
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
    BufferedInputFile,
)

# =========================================================
# SETTINGS
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
PLAYPAY_API_KEY = os.getenv("PLAYPAY_API_KEY")
WEBAPP_URL = os.getenv("WEBAPP_URL")

PLAYPAY_API = "https://playpay.uz/api/v1"

PORT = int(os.getenv("PORT", "10000"))
CARD_NUMBER = os.getenv("CARD_NUMBER")
ADMIN_TELEGRAM_ID = os.getenv("ADMIN_TELEGRAM_ID")

RECEIPTS_DIR = Path(__file__).resolve().parent / "boost_receipts"
RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)

if not CARD_NUMBER:
    raise RuntimeError("CARD_NUMBER is missing")

if not ADMIN_TELEGRAM_ID:
    raise RuntimeError("ADMIN_TELEGRAM_ID is missing")

ADMIN_TELEGRAM_ID = int(ADMIN_TELEGRAM_ID)
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
    
ACCOUNTS_DIR = "uploads/accounts"

os.makedirs(ACCOUNTS_DIR, exist_ok=True)

app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)
def init_accounts_db():

    conn = sqlite3.connect("accounts.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_uid TEXT UNIQUE,
            title TEXT NOT NULL,
            account_id TEXT NOT NULL,
            price INTEGER NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            seller_id TEXT NOT NULL,
            seller_username TEXT,
            account_type TEXT NOT NULL DEFAULT 'mlbb',
            image_url TEXT,
            images_json TEXT DEFAULT '[]',
            video_url TEXT
        )
    """)

    conn.commit()
    conn.close()


init_accounts_db()
@app.get("/api/accounts")
async def get_accounts(
    type: str = "all",
    category: str = "all"
):

    conn = sqlite3.connect("accounts.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    if type in ["phoenix", "mlbb"]:

        cursor.execute(
            """
            SELECT *
            FROM accounts
            WHERE account_type = ?
            ORDER BY id DESC
            """,
            (type,)
        )

    elif category in ["middle", "mega", "world"]:

        cursor.execute(
            """
            SELECT *
            FROM accounts
            WHERE category = ?
            ORDER BY id DESC
            """,
            (category,)
        )

    else:

        cursor.execute(
            """
            SELECT *
            FROM accounts
            ORDER BY id DESC
            """
        )

    accounts = [
        dict(row)
        for row in cursor.fetchall()
    ]

    conn.close()

    return accounts


@app.post("/api/accounts")
async def create_account(

    title: str = Form(...),
    account_id: str = Form(...),
    price: int = Form(...),
    category: str = Form(...),
    description: str = Form(""),

    seller_id: str = Form(...),
    seller_username: str = Form(""),

    images: list[UploadFile] = File(default=[]),
    video: UploadFile | None = File(default=None)

):

    account_type = "mlbb"

    account_uid = str(uuid.uuid4())

    account_folder = os.path.join(
        ACCOUNTS_DIR,
        account_uid
    )

    os.makedirs(
        account_folder,
        exist_ok=True
    )

    image_urls = []

if images:

    for index, image in enumerate(images):

        extension = os.path.splitext(
            image.filename or ""
        )[1]

        image_name = f"image_{index}{extension}"

        image_path = os.path.join(
            account_folder,
            image_name
        )

        with open(image_path, "wb") as f:
            f.write(
                await image.read()
            )

        image_urls.append(
            "/uploads/accounts/"
            + account_uid
            + "/"
            + image_name
        )

image_url = image_urls[0] if image_urls else ""

video_url = ""

        

    if video:

        extension = os.path.splitext(
            video.filename or ""
        )[1]

        video_name = "video" + extension

        video_path = os.path.join(
            account_folder,
            video_name
        )

        with open(video_path, "wb") as f:
            f.write(
                await video.read()
            )

        video_url = (
            "/uploads/accounts/"
            + account_uid
            + "/"
            + video_name
        )

    conn = sqlite3.connect("accounts.db")

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO accounts (
    account_uid,
    title,
    account_id,
    price,
    category,
    description,
    seller_id,
    seller_username,
    account_type,
    image_url,
    images_json,
    video_url
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""",
(
    account_uid,
    title,
    account_id,
    price,
    category,
    description,
    seller_id,
    seller_username,
    account_type,
    image_url,
    json.dumps(image_urls),
    video_url
)
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Account added",
        "account_uid": account_uid
    }
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

        if not telegram_id:

            return {
                "ok": False,
                "error": "Telegram foydalanuvchisi topilmadi",
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

        package_data = await playpay_request(
            "GET",
            f"/games/{game_id}/packages",
            params={
                "currency": "UZS",
            },
        )

        packages = package_data.get(
            "packages",
            []
        )

        selected_package = next(
            (
                package
                for package in packages
                if int(package.get("paket_id", 0))
                == package_id
            ),
            None,
        )

        if not selected_package:

            return {
                "ok": False,
                "error": "Paket topilmadi",
            }

        cost_price = float(
            selected_package["price"]["amount"]
        )

        if cost_price < 60000:
            markup = 0.05
        else:
            markup = 0.10

        customer_price = round(
            cost_price * (1 + markup)
        )

        balance = get_balance(
            telegram_id
        )

        if balance < customer_price:

            return {
                "ok": False,
                "error": (
                    f"Balans yetarli emas. "
                    f"Kerak: {customer_price:,.0f} UZS"
                ),
            }

        deducted = subtract_balance(
            telegram_id,
            customer_price
        )

        if not deducted:

            return {
                "ok": False,
                "error": "Balansdan pul yechilmadi",
            }

        try:

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

        except Exception:

            add_balance(
                telegram_id,
                customer_price
            )

            raise

        return {
            "ok": True,
            "order": result,
            "charged": customer_price,
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
# API: BOOST ORDER
# =========================================================

@app.post("/api/boost/order")
async def api_boost_order(
    service: str = Form(...),
    amount: int = Form(...),
    receipt: UploadFile = File(...),
    telegram_id: int = Form(0),
    current_rank: str = Form(""),
    current_stars: int = Form(0),
    target_rank: str = Form(""),
    target_stars: int = Form(0),
    current_mmr: int = Form(0),
    target_mmr: int = Form(0),
    region: str = Form(""),
    title_type: str = Form(""),
    player_id: str = Form(""),
    zone_id: str = Form(""),
):

    try:

        if service not in {
            "mlbb_boost",
            "mmr",
            "title",
        }:
            return {
                "ok": False,
                "error": "Noto'g'ri xizmat turi",
            }

        if amount <= 0:
            return {
                "ok": False,
                "error": "Noto'g'ri summa",
            }

        if not player_id:
            return {
                "ok": False,
                "error": "O'yin ID kiritilmagan",
            }

        if not zone_id:
            return {
                "ok": False,
                "error": "Zone ID kiritilmagan",
            }

        if not receipt.filename:
            return {
                "ok": False,
                "error": "Chek tanlanmagan",
            }

        extension = Path(
            receipt.filename
        ).suffix.lower()

        if extension not in {
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
        }:
            return {
                "ok": False,
                "error": "Faqat JPG, PNG yoki WEBP chek qabul qilinadi",
            }

        receipt_data = await receipt.read()

        if not receipt_data:
            return {
                "ok": False,
                "error": "Chek fayli bo'sh",
            }

        if len(receipt_data) > 10 * 1024 * 1024:
            return {
                "ok": False,
                "error": "Chek 10 MB dan kichik bo'lishi kerak",
            }

        order_id = (
            "BOOST-"
            + uuid.uuid4().hex[:8].upper()
        )

        receipt_filename = (
            f"{order_id}{extension}"
        )

        receipt_path = (
            RECEIPTS_DIR
            / receipt_filename
        )

        with open(
            receipt_path,
            "wb"
        ) as file:
            file.write(receipt_data)

        if service == "mlbb_boost":

            service_name = "🚀 MLBB BOOST"

            description = (
                f"Hozirgi: {current_rank} "
                f"{current_stars}⭐\n"
                f"Maqsad: {target_rank} "
                f"{target_stars}⭐"
            )

        elif service == "mmr":

            service_name = "📈 MMR"

            description = (
                f"Hozirgi MMR: {current_mmr}\n"
                f"Maqsad MMR: {target_mmr}"
            )

        else:

            service_name = "🏆 TITUL"

            description = (
                f"Region: {region}\n"
                f"Titul: {title_type}"
            )

        admin_text = (
            "🔥 <b>YANGI ZAYAVKA</b>\n\n"
            f"🆔 <b>ID:</b> {order_id}\n"
            f"🛠 <b>Xizmat:</b> {service_name}\n\n"
            f"{description}\n\n"
            f"🎮 <b>Game ID:</b> {player_id}\n"
            f"🌐 <b>Zone ID:</b> {zone_id}\n"
            f"💰 <b>Summa:</b> {amount:,} UZS\n"
            f"⏳ <b>Holat:</b> Kutilmoqda\n"
        )

        if telegram_id:
            admin_text += (
                f"\n👤 <b>Telegram ID:</b> "
                f"{telegram_id}"
            )

        await bot.send_message(
            ADMIN_TELEGRAM_ID,
            admin_text,
            parse_mode="HTML",
        )

        await bot.send_document(
            ADMIN_TELEGRAM_ID,
            BufferedInputFile(
                receipt_data,
                filename=receipt_filename,
            ),
            caption=(
                f"📸 <b>To'lov cheki</b>\n"
                f"🆔 {order_id}\n"
                f"💰 {amount:,} UZS"
            ),
            parse_mode="HTML",
        )

        logger.info(
            "BOOST ORDER CREATED: %s",
            order_id,
        )

        return {
            "ok": True,
            "order_id": order_id,
            "status": "pending",
            "amount": amount,
            "card_number": CARD_NUMBER,
        }

    except Exception as e:

        logger.exception(
            "Boost order error"
        )

        return {
            "ok": False,
            "error": str(e),
        }
# =========================================================
# API: BOOST PAYMENT INFO
# =========================================================

@app.get("/api/boost/payment-info")
async def api_boost_payment_info():

    return {
        "ok": True,
        "card_number": CARD_NUMBER,
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
