const tg = window.Telegram?.WebApp;

if (tg) {
    tg.ready();
    tg.expand();
}


/* =====================================================
   HELPERS
===================================================== */

function $(id) {
    return document.getElementById(id);
}


function formatPrice(value) {

    const number = Number(value || 0);

    return new Intl.NumberFormat(
        "uz-UZ"
    ).format(number) + " UZS";
}


function openModal(html) {

    $("modalContent").innerHTML = html;

    $("modal").classList.add("show");

}


function closeModal() {

    $("modal").classList.remove("show");

}


function alertUser(message) {

    if (tg && tg.showAlert) {
        tg.showAlert(message);
    } else {
        alert(message);
    }

}


/* =====================================================
   TELEGRAM USER
===================================================== */
async function loadBalance() {

    const user = tg?.initDataUnsafe?.user;

    if (!user?.id) {
        return;
    }

    try {

        const response = await fetch(
            `/api/balance?telegram_id=${encodeURIComponent(user.id)}&v=${Date.now()}`
        );

        const data = await response.json();

        if (!data.ok) {
            console.error("Balance error:", data.error);
            return;
        }

        const balance = Number(data.balance || 0);

        const balanceValue =
            document.getElementById("balanceValue");

        if (balanceValue) {
            balanceValue.textContent =
                `${balance.toLocaleString("uz-UZ")} UZS`;
        }

    } catch (error) {

        console.error(
            "Balance loading error:",
            error
        );

    }
}
async function loadPlayPayBalance() {

    try {

        const response = await fetch(
            `/api/playpay-balance?v=${Date.now()}`
        );

        const data = await response.json();

        if (!data.ok) {
            console.error(
                "PlayPay balance error:",
                data.error
            );
            return;
        }

        const balance =
            Number(data.balance?.amount || 0);

        const element =
            document.getElementById(
                "playpayBalanceValue"
            );

        if (element) {

            element.textContent =
                `$${balance.toLocaleString("en-US", {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                })}`;

        }

    } catch (error) {

        console.error(
            "PlayPay balance loading error:",
            error
        );

    }

}
function loadTelegramUser() {

    const user = tg?.initDataUnsafe?.user;

    if (!user) {
        return;
    }

    const name =
        [
            user.first_name,
            user.last_name
        ]
        .filter(Boolean)
        .join(" ");

    $("userName").textContent =
        name || "PHOENIX USER";

    $("userUsername").textContent =
        user.username
            ? "@" + user.username
            : "Telegram user";

    if (user.photo_url) {

        $("userAvatar").style.backgroundImage =
            `url("${user.photo_url}")`;

        $("userAvatar").style.backgroundSize =
            "cover";

        $("userAvatar").textContent =
            "";

    }

}


/* =====================================================
   HOME
===================================================== */

function goHome() {

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });

}


/* =====================================================
   DIAMONDS
===================================================== */

async function openDiamonds() {

    openModal(`
        <div class="modal-title">
            💎 Mobile Legends
        </div>

        <div class="modal-subtitle">
            Regionni tanlang
        </div>

        <div class="loading">
            <div class="spinner"></div>
            Regionlar yuklanmoqda...
        </div>
    `);


    try {

        const response =
            await fetch(
                "/api/regions?v=" +
                Date.now()
            );

        const data =
            await response.json();


        if (!data.ok) {

            throw new Error(
                data.error ||
                "Regionlarni olishda xatolik"
            );

        }


        const regions =
            data.regions || [];


        if (!regions.length) {

            $("modalContent").innerHTML = `
                <div class="empty">
                    😕 Mobile Legends regionlari topilmadi.
                </div>
            `;

            return;
        }


        let html = `
            <div class="modal-title">
                💎 Mobile Legends
            </div>

            <div class="modal-subtitle">
                Server / regionni tanlang
            </div>

            <div class="region-list">
        `;


        regions.forEach(
            (region) => {

                html += `
                    <button
                        class="region-card"
                        onclick="loadPackages(
                            ${region.game_id},
                            '${escapeHtml(
                                region.name
                            )}'
                        )"
                    >

                        <div class="region-icon">
                            🌐
                        </div>

                        <div class="region-name">
                            ${escapeHtml(
                                region.name
                            )}
                        </div>

                        <div class="region-info">
                            ${region.packages_count || 0}
                            ta paket
                        </div>

                    </button>
                `;

            }
        );


        html += `
            </div>
        `;


        $("modalContent").innerHTML =
            html;


    } catch (error) {

        console.error(error);

        $("modalContent").innerHTML = `
            <div class="empty">

                ❌ Xatolik

                <br><br>

                ${escapeHtml(
                    error.message
                )}

                <br><br>

                <button
                    class="primary-button"
                    onclick="openDiamonds()"
                >
                    Qayta urinish
                </button>

            </div>
        `;

    }

}


/* =====================================================
   PACKAGES
===================================================== */

async function loadPackages(
    gameId,
    regionName
) {

    openModal(`
        <div class="modal-title">
            💎 ${escapeHtml(regionName)}
        </div>

        <div class="loading">
            <div class="spinner"></div>
            Paketlar yuklanmoqda...
        </div>
    `);


    try {

        const response =
            await fetch(
                `/api/packages/${gameId}?v=${Date.now()}`
            );


        const data =
            await response.json();


        if (!data.ok) {

            throw new Error(
                data.error ||
                "Paketlarni olishda xatolik"
            );

        }


        let packages =
            data.packages || [];


        /*
            MUHIM:

            Bir xil nomdagi paketlardan
            faqat ENG ARZONINI qoldiramiz.
        */

        packages =
            getCheapestPackages(
                packages
            );


        if (!packages.length) {

            $("modalContent").innerHTML = `
                <div class="empty">
                    😕 Bu regionda paket topilmadi.
                </div>
            `;

            return;
        }


        let html = `

            <div class="modal-title">
                💎 ${escapeHtml(regionName)}
            </div>

            <div class="modal-subtitle">
                Eng arzon narxlar ko‘rsatilmoqda
            </div>

            <div class="package-list">
        `;


        packages.forEach(
            (pkg) => {

                const packageId =
                    pkg.paket_id ??
                    pkg.package_id ??
                    pkg.id;

                const name =
                    pkg.name ??
                    pkg.title ??
                    pkg.package_name ??
                    "Donat paketi";

                const price =
    typeof pkg.price === "object"
        ? (
            pkg.price.amount ??
            0
        )
        : (
            pkg.price ??
            pkg.amount ??
            pkg.price_uzs ??
            0
        );

                const image =
                    pkg.image ??
                    pkg.image_url ??
                    pkg.photo ??
                    pkg.photo_url ??
                    "";


                html += `

                    <div class="package-card">

                        <div class="package-image">

                            ${
                                image
                                ?
                                `
                                <img
                                    src="${escapeAttribute(image)}"
                                    alt="${escapeAttribute(name)}"
                                    onerror="this.style.display='none'"
                                >
                                `
                                :
                                getPackageEmoji(name)
                            }

                        </div>


                        <div class="package-name">
                            ${escapeHtml(name)}
                        </div>


                        <div class="package-price">
                            ${formatPrice(price)}
                        </div>


                        <button
                            class="buy-button"
                            onclick='buyPackage(
                                ${JSON.stringify({
                                    game_id: gameId,
                                    paket_id: packageId,
                                    name: name,
                                    price: price,
                                    image: image,
                                    region: regionName
                                })}
                            )'
                        >
                            🛒 Sotib olish
                        </button>

                    </div>
                `;

            }
        );


        html += `
            </div>
        `;


        $("modalContent").innerHTML =
            html;


    } catch (error) {

        console.error(error);

        $("modalContent").innerHTML = `

            <div class="empty">

                ❌ Paketlarni yuklab bo‘lmadi.

                <br><br>

                ${escapeHtml(
                    error.message
                )}

                <br><br>

                <button
                    class="primary-button"
                    onclick="openDiamonds()"
                >
                    Orqaga
                </button>

            </div>

        `;

    }

}


/* =====================================================
   CHEAPEST PACKAGE
===================================================== */

function getCheapestPackages(
    packages
) {

    const groups = {};

    packages.forEach(
        (pkg) => {

            const name =
                String(
                    pkg.name ??
                    pkg.title ??
                    pkg.package_name ??
                    ""
                )
                .trim()
                .toLowerCase();


            const price =
                Number(
                    pkg.price ??
                    pkg.amount ??
                    pkg.price_uzs ??
                    0
                );


            if (!name) {
                return;
            }


            if (
                !groups[name] ||
                price <
                Number(
                    groups[name].price ??
                    groups[name].amount ??
                    groups[name].price_uzs ??
                    Infinity
                )
            ) {

                groups[name] = pkg;

            }

        }
    );


    return Object.values(groups);

}


/* =====================================================
   BUY PACKAGE
===================================================== */

function buyPackage(pkg) {

    openModal(`

        <div class="modal-title">
            🛒 Buyurtma
        </div>

        <div class="modal-subtitle">
            ${escapeHtml(pkg.name)}
            •
            ${formatPrice(pkg.price)}
        </div>


        <div class="form-group">

            <label class="form-label">
                User ID
            </label>

            <input
                class="form-input"
                id="playerIdInput"
                type="text"
                inputmode="numeric"
                placeholder="Masalan: 123456789"
            >

        </div>


        <div class="form-group">

            <label class="form-label">
                Server ID
            </label>

            <input
                class="form-input"
                id="serverIdInput"
                type="text"
                inputmode="numeric"
                placeholder="Masalan: 1234"
            >

        </div>


        <div class="form-group">

            <label class="form-label">
                Promo kod
            </label>

            <input
                class="form-input"
                id="promoInput"
                type="text"
                placeholder="Agar mavjud bo‘lsa"
            >

        </div>


        <button
            class="primary-button"
            onclick='checkPlayer(
                ${JSON.stringify(pkg)}
            )'
        >
            Davom etish
        </button>

    `);

}


/* =====================================================
   CHECK PLAYER
===================================================== */

async function checkPlayer(pkg) {

    const playerId =
        $("playerIdInput")
        ?.value
        .trim();


    const serverId =
        $("serverIdInput")
        ?.value
        .trim();


    if (!playerId) {

        alertUser(
            "User ID kiriting."
        );

        return;
    }


    if (!serverId) {

        alertUser(
            "Server ID kiriting."
        );

        return;
    }


    $("modalContent").innerHTML = `

        <div class="loading">

            <div class="spinner"></div>

            Player tekshirilmoqda...

        </div>

    `;


    try {

        const response =
            await fetch(
                "/api/check-player",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            game_id:
                                pkg.game_id,

                            player_id:
                                playerId,

                            server_id:
                                serverId
                        })
                }
            );


        const data =
            await response.json();


        if (!data.ok) {

            throw new Error(
                data.error ||
                "ID tekshirishda xatolik"
            );

        }


        showConfirmation(
            pkg,
            data.player_name,
            playerId,
            serverId
        );


    } catch (error) {

        $("modalContent").innerHTML = `

            <div class="empty">

                ❌ ${escapeHtml(
                    error.message
                )}

                <br><br>

                <button
                    class="primary-button"
                    onclick='buyPackage(
                        ${JSON.stringify(pkg)}
                    )'
                >
                    Qayta kiritish
                </button>

            </div>

        `;

    }

}


/* =====================================================
   CONFIRM
===================================================== */

function showConfirmation(
    pkg,
    playerName,
    playerId,
    serverId
) {

    openModal(`

        <div class="modal-title">
            ✅ Tasdiqlash
        </div>

        <div class="modal-subtitle">
            Ma’lumotlarni tekshiring
        </div>

        <div class="confirmation-card">

            <b>
                ${escapeHtml(pkg.name)}
            </b>

            <br><br>

            👤
            ${escapeHtml(
                playerName || "Player"
            )}

            <br>

            🆔
            ${escapeHtml(playerId)}

            <br>

            🌐
            ${escapeHtml(serverId)}

            <br><br>

            💰
            <b>
                ${formatPrice(pkg.price)}
            </b>

        </div>

        <button
            class="primary-button"
            onclick='createOrder(
                ${JSON.stringify(pkg)},
                "${escapeAttribute(playerId)}",
                "${escapeAttribute(serverId)}"
            )'
        >
            Tasdiqlash
        </button>

    `);

}

/* =====================================================
   ORDER PLACEHOLDER
===================================================== */

async function createOrder(
    pkg,
    playerId,
    serverId
) {

    if (!pkg) {
        alertUser("Paket topilmadi.");
        return;
    }

    if (!playerId) {
        alertUser("User ID topilmadi.");
        return;
    }

    if (!serverId) {
        alertUser("Server ID topilmadi.");
        return;
    }

    openModal(`

        <div class="modal-title">
            ⏳ Buyurtma
        </div>

        <div class="loading">

            <div class="spinner"></div>

            Buyurtma yaratilmoqda...

        </div>

    `);

    try {

        const response =
            await fetch(
                "/api/create-order",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
    JSON.stringify({
        game_id:
            pkg.game_id,

        package_id:
            pkg.paket_id,

        player_id:
            playerId,

        server_id:
            serverId,

        telegram_id:
            tg?.initDataUnsafe?.user?.id
    })
                }
            );


        const data =
            await response.json();


        if (!data.ok) {

            throw new Error(
                data.error ||
                "Buyurtma yaratishda xatolik"
            );

        }


        $("modalContent").innerHTML = `

            <div class="modal-title">
                ✅ Buyurtma yaratildi
            </div>

            <div class="confirmation-card">

                💎
                ${escapeHtml(pkg.name)}

                <br><br>

                👤
                ${escapeHtml(playerId)}

                <br>

                🌐
                ${escapeHtml(serverId)}

                <br><br>

                💰
                <b>
                    ${formatPrice(pkg.price)}
                </b>

            </div>

            <div class="modal-subtitle">
                Buyurtma muvaffaqiyatli yaratildi.
            </div>

            <button
                class="primary-button"
                onclick="closeModal()"
            >
                Yopish
            </button>

        `;


    } catch (error) {

        $("modalContent").innerHTML = `

            <div class="empty">

                ❌
                ${escapeHtml(
                    error.message
                )}

                <br><br>

                <button
                    class="primary-button"
                    onclick='showConfirmation(
                        ${JSON.stringify(pkg)},
                        "",
                        "${escapeAttribute(playerId)}",
                        "${escapeAttribute(serverId)}"
                    )'
                >
                    Qayta urinish
                </button>

            </div>

        `;

    }

}


/* =====================================================
   OTHER SECTIONS
===================================================== */

async function openBalance() {

    const user = tg?.initDataUnsafe?.user;

    if (!user?.id) {

        openModal(`
            <div class="modal-title">
                💳 Balans
            </div>

            <div class="empty">
                Telegram foydalanuvchisi aniqlanmadi.
            </div>
        `);

        return;
    }

    try {

        const response = await fetch(
            `/api/balance?telegram_id=${encodeURIComponent(user.id)}&v=${Date.now()}`
        );

        const data = await response.json();

        if (!data.ok) {
            throw new Error(
                data.error || "Balansni olishda xatolik"
            );
        }

        const balance = Number(data.balance || 0);

        const balanceText =
            `${balance.toLocaleString("uz-UZ")} UZS`;

        openModal(`
            <div class="modal-title">
                💳 Balansni to‘ldirish
            </div>

            <div class="modal-subtitle">
                Joriy balans: ${escapeHtml(balanceText)}
            </div>

            <div style="margin-top: 20px;">

                <input
                    id="topupAmount"
                    type="number"
                    inputmode="numeric"
                    min="1000"
                    step="1000"
                    placeholder="Summani kiriting"
                    style="
                        width: 100%;
                        box-sizing: border-box;
                        padding: 14px;
                        border-radius: 12px;
                        border: 1px solid rgba(255,255,255,0.15);
                        background: rgba(255,255,255,0.06);
                        color: white;
                        font-size: 16px;
                        outline: none;
                    "
                >

                <button
                    class="hero-button"
                    onclick="startTopUp()"
                    style="margin-top: 12px; width: 100%;"
                >
                    💳 Davom etish
                </button>

            </div>
        `);

    } catch (error) {

        console.error("Balance error:", error);

        openModal(`
            <div class="modal-title">
                💳 Balans
            </div>

            <div class="empty">
                Balansni yuklashda xatolik yuz berdi.
            </div>
        `);
    }
}
function startTopUp() {

    const input = document.getElementById("topupAmount");

    if (!input) {
        return;
    }

    const amount = Number(input.value);

    if (!amount || amount < 1000) {

        alertUser(
            "Kamida 1 000 UZS kiriting."
        );

        return;
    }

    openModal(`
        <div class="modal-title">
            💳 To‘lov
        </div>

        <div class="modal-subtitle">
            To‘ldirish summasi
        </div>

        <div class="balance-value">
            ${amount.toLocaleString("uz-UZ")} UZS
        </div>

        <div class="empty">
            To‘lov tizimi keyingi bosqichda ulanadi.
        </div>
    `);
}

// =========================
// MLBB BOOST
// =========================

const MLBB_RANKS = [
    "Warrior",
    "Elite",
    "Master",
    "Grandmaster",
    "Epic",
    "Legend",
    "Mythic",
    "Mythical Honor",
    "Mythical Glory"
];

let boostCurrentRank = 0;
let boostCurrentStars = 0;
let boostTargetRank = 0;
let boostTargetStars = 0;

const BOOST_PRICE_PER_STAR = 7500;


// =========================
// BOOST MAIN MENU
// =========================

function openBoost() {
    openModal(`
        <div class="modal-title">🚀 Boost xizmati</div>

        <div class="modal-subtitle">
            MLBB Boost va titul xizmatlari
        </div>

        <button class="hero-button"
            onclick="openMLBBBoost()"
            style="width:100%; margin-top:20px;">
            🚀 MLBB Boost
        </button>

        <button class="hero-button"
            onclick="openTitleBoost()"
            style="width:100%; margin-top:12px;">
            🏆 Titul olib berish
        </button>
    `);
}


// =========================
// MLBB BOOST
// =========================

function openMLBBBoost() {
    boostCurrentRank = 0;
    boostCurrentStars = 0;
    boostTargetRank = 0;
    boostTargetStars = 0;

    renderMLBBBoost();
}


function renderMLBBBoost() {

    const totalStars = calculateBoostStars();
    const totalPrice = totalStars * BOOST_PRICE_PER_STAR;

    openModal(`
        <div class="modal-title">🚀 MLBB Boost</div>

        <div class="modal-subtitle">
            Rankingizni professional boosterlar ko‘taradi
        </div>

        <div style="margin-top:20px;">
            <b>Hozirgi rank</b>

            <div style="
                display:flex;
                align-items:center;
                justify-content:space-between;
                margin-top:10px;
            ">

                <button onclick="changeCurrentRank(-1)">−</button>

                <div style="text-align:center;">
                    <div class="balance-value">
                        ${MLBB_RANKS[boostCurrentRank]}
                    </div>

                    <div>
                        Yulduz:
                        <button onclick="changeCurrentStars(-1)">−</button>
                        <b>${boostCurrentStars}</b>
                        <button onclick="changeCurrentStars(1)">+</button>
                    </div>
                </div>

                <button onclick="changeCurrentRank(1)">+</button>
            </div>
        </div>


        <div style="margin-top:25px;">
            <b>Maqsad rank</b>

            <div style="
                display:flex;
                align-items:center;
                justify-content:space-between;
                margin-top:10px;
            ">

                <button onclick="changeTargetRank(-1)">−</button>

                <div style="text-align:center;">
                    <div class="balance-value">
                        ${MLBB_RANKS[boostTargetRank]}
                    </div>

                    <div>
                        Yulduz:
                        <button onclick="changeTargetStars(-1)">−</button>
                        <b>${boostTargetStars}</b>
                        <button onclick="changeTargetStars(1)">+</button>
                    </div>
                </div>

                <button onclick="changeTargetRank(1)">+</button>
            </div>
        </div>


        <div style="
            margin-top:25px;
            padding:15px;
            border-radius:12px;
            background:rgba(255,255,255,.06);
        ">
            <div>⭐ Jami yulduz</div>

            <div class="balance-value">
                ${totalStars}
            </div>

            <div style="margin-top:8px;">
                💰 ${formatPrice(totalPrice)}
            </div>
        </div>


        <div style="margin-top:20px;">

            <input
                id="boostPlayerId"
                type="text"
                inputmode="numeric"
                placeholder="O‘yin ID"
                style="width:100%;"
            >

            <input
                id="boostZoneId"
                type="text"
                inputmode="numeric"
                placeholder="Zone ID"
                style="width:100%; margin-top:10px;"
            >

        </div>


        <button class="hero-button"
            onclick="checkBoostAccount()"
            style="width:100%; margin-top:15px;">
            🔍 Akkauntni tekshirish
        </button>

        <button class="hero-button"
            onclick="openBoostPayment()"
            style="width:100%; margin-top:10px;">
            💳 To‘lovga o‘tish · ${formatPrice(totalPrice)}
        </button>

    `);
}


// =========================
// RANK
// =========================

function changeCurrentRank(value) {

    boostCurrentRank += value;

    if (boostCurrentRank < 0)
        boostCurrentRank = 0;

    if (boostCurrentRank >= MLBB_RANKS.length)
        boostCurrentRank = MLBB_RANKS.length - 1;

    boostCurrentStars = 0;

    renderMLBBBoost();
}


function changeTargetRank(value) {

    boostTargetRank += value;

    if (boostTargetRank < 0)
        boostTargetRank = 0;

    if (boostTargetRank >= MLBB_RANKS.length)
        boostTargetRank = MLBB_RANKS.length - 1;

    boostTargetStars = 0;

    renderMLBBBoost();
}


// =========================
// STARS
// =========================

function changeCurrentStars(value) {

    boostCurrentStars += value;

    if (boostCurrentStars < 0)
        boostCurrentStars = 0;

    if (boostCurrentStars > 100)
        boostCurrentStars = 100;

    renderMLBBBoost();
}


function changeTargetStars(value) {

    boostTargetStars += value;

    if (boostTargetStars < 0)
        boostTargetStars = 0;

    if (boostTargetStars > 100)
        boostTargetStars = 100;

    renderMLBBBoost();
}


// =========================
// TOTAL STARS
// =========================

function calculateBoostStars() {

    const rankDifference =
        boostTargetRank - boostCurrentRank;

    if (rankDifference < 0)
        return 0;

    const starsBetweenRanks =
        rankDifference * 5;

    const finalStars =
        starsBetweenRanks +
        boostTargetStars -
        boostCurrentStars;

    return Math.max(0, finalStars);
}


// =========================
// CHECK ACCOUNT
// =========================

async function checkBoostAccount() {

    const playerId =
        document.getElementById("boostPlayerId")?.value.trim();

    const zoneId =
        document.getElementById("boostZoneId")?.value.trim();

    if (!playerId) {
        alertUser("O‘yin ID kiriting.");
        return;
    }

    if (!zoneId) {
        alertUser("Zone ID kiriting.");
        return;
    }

    alertUser("Akkaunt tekshirilmoqda...");

    try {

        const response = await fetch("/api/check-player", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                game_id: 1,

                player_id: playerId,

                server_id: zoneId

            })

        });

        const data = await response.json();

        if (!data.ok) {

            alertUser(
                data.error ||
                "Akkauntni tekshirib bo‘lmadi."
            );

            return;
        }

        openModal(`

            <div class="modal-title">
                ✅ Akkaunt tasdiqlandi
            </div>

            <div class="modal-subtitle">
                Player: ${escapeHtml(
                    data.player_name || "Noma’lum"
                )}
            </div>

            <div style="margin-top:20px;">

                <div>
                    🎮 ID: ${escapeHtml(playerId)}
                </div>

                <div style="margin-top:8px;">
                    🌐 Zone: ${escapeHtml(zoneId)}
                </div>

            </div>

            <button
                class="hero-button"
                onclick="openMLBBBoost()"
                style="width:100%; margin-top:20px;"
            >
                ← Orqaga
            </button>

        `);

    } catch (error) {

        console.error(error);

        alertUser(
            "Server bilan aloqa qilishda xatolik."
        );
    }
}


// =========================
// BOOST PAYMENT
// =========================

function openBoostPayment() {

    const playerId =
        document.getElementById("boostPlayerId")?.value.trim();

    const zoneId =
        document.getElementById("boostZoneId")?.value.trim();

    if (!playerId) {

        alertUser("Avval O‘yin ID kiriting.");

        return;
    }

    if (!zoneId) {

        alertUser("Avval Zone ID kiriting.");

        return;
    }

    const totalStars =
        calculateBoostStars();

    if (totalStars <= 0) {

        alertUser(
            "Maqsad rank hozirgi rankdan yuqori bo‘lishi kerak."
        );

        return;
    }

    const totalPrice =
        totalStars * BOOST_PRICE_PER_STAR;


    openModal(`

        <div class="modal-title">
            💳 Boost to‘lovi
        </div>

        <div class="modal-subtitle">
            MLBB Boost
        </div>

        <div style="margin-top:20px;">

            <div>
                Hozirgi:
                <b>
                    ${MLBB_RANKS[boostCurrentRank]}
                    · ${boostCurrentStars} ⭐
                </b>
            </div>

            <div style="margin-top:8px;">
                Maqsad:
                <b>
                    ${MLBB_RANKS[boostTargetRank]}
                    · ${boostTargetStars} ⭐
                </b>
            </div>

            <div style="margin-top:8px;">
                Jami:
                <b>${totalStars} ⭐</b>
            </div>

        </div>


        <div class="balance-value"
            style="margin-top:20px;">
            ${formatPrice(totalPrice)}
        </div>


        <button
            class="hero-button"
            onclick="createBoostOrder()"
            style="width:100%; margin-top:20px;"
        >
            💳 To‘lovni tasdiqlash
        </button>

    `);
}


function createBoostOrder() {

    alertUser(
        "Boost buyurtmasini qabul qilish tizimi keyingi bosqichda ulanadi."
    );
}


// =========================
// TITUL XIZMATI
// =========================

function openTitleBoost() {

    openModal(`

        <div class="modal-title">
            🏆 Titul olib berish
        </div>

        <div class="modal-subtitle">
            Kerakli titul ma’lumotlarini kiriting
        </div>


        <input
            id="titleRegion"
            type="text"
            placeholder="Region / Davlat / Shahar"
            style="width:100%; margin-top:20px;"
        >


        <input
            id="titleType"
            type="text"
            placeholder="Qanday titul kerak?"
            style="width:100%; margin-top:10px;"
        >


        <input
            id="titleMMR"
            type="number"
            inputmode="numeric"
            placeholder="Kerakli MMR"
            style="width:100%; margin-top:10px;"
        >


        <input
            id="titlePlayerId"
            type="text"
            inputmode="numeric"
            placeholder="O‘yin ID"
            style="width:100%; margin-top:10px;"
        >


        <input
            id="titleZoneId"
            type="text"
            inputmode="numeric"
            placeholder="Zone ID"
            style="width:100%; margin-top:10px;"
        >


        <button
            class="hero-button"
            onclick="checkTitleOrder()"
            style="width:100%; margin-top:18px;"
        >
            🔍 Akkauntni tekshirish
        </button>

    `);
}


// =========================
// TITLE CHECK
// =========================

function checkTitleOrder() {

    const region =
        document.getElementById("titleRegion")?.value.trim();

    const titleType =
        document.getElementById("titleType")?.value.trim();

    const mmr =
        document.getElementById("titleMMR")?.value.trim();

    const playerId =
        document.getElementById("titlePlayerId")?.value.trim();

    const zoneId =
        document.getElementById("titleZoneId")?.value.trim();


    if (!region) {

        alertUser("Region / davlat / shaharni yozing.");

        return;
    }

    if (!titleType) {

        alertUser("Qanday titul kerakligini yozing.");

        return;
    }

    if (!mmr || Number(mmr) <= 0) {

        alertUser("Kerakli MMRni kiriting.");

        return;
    }

    if (!playerId) {

        alertUser("O‘yin ID kiriting.");

        return;
    }

    if (!zoneId) {

        alertUser("Zone ID kiriting.");

        return;
    }


    openModal(`

        <div class="modal-title">
            🏆 Titul buyurtmasi
        </div>

        <div style="margin-top:20px;">

            <div>
                🌍 Region:
                <b>${escapeHtml(region)}</b>
            </div>

            <div style="margin-top:8px;">
                🏆 Titul:
                <b>${escapeHtml(titleType)}</b>
            </div>

            <div style="margin-top:8px;">
                📈 MMR:
                <b>${escapeHtml(mmr)}</b>
            </div>

            <div style="margin-top:8px;">
                🎮 ID:
                <b>${escapeHtml(playerId)}</b>
            </div>

            <div style="margin-top:8px;">
                🌐 Zone:
                <b>${escapeHtml(zoneId)}</b>
            </div>

        </div>


        <div class="empty"
            style="margin-top:20px;">
            Buyurtma ma’lumotlari tayyor.
        </div>


        <button
            class="hero-button"
            onclick="createTitleOrder()"
            style="width:100%; margin-top:15px;"
        >
            💳 To‘lovga o‘tish
        </button>

    `);
}


function createTitleOrder() {

    alertUser(
        "Titul buyurtmasini qabul qilish tizimi keyingi bosqichda ulanadi."
    );
}


function openAccounts() {

    openModal(`

        <div class="modal-title">
            🎮 Account Marketplace
        </div>

        <div class="empty">
            MLBB account marketplace
            keyingi bosqichda qo‘shiladi.
        </div>

    `);

}


function openOrders() {

    openModal(`

        <div class="modal-title">
            📦 Buyurtmalar
        </div>

        <div class="empty">
            Hozircha buyurtmalar yo‘q.
        </div>

    `);

}


function openPromo() {

    openModal(`

        <div class="modal-title">
            🎁 Promo kod
        </div>

        <div class="form-group">

            <input
                class="form-input"
                placeholder="Promo kodni kiriting"
            >

        </div>

        <button
            class="primary-button"
        >
            Qo‘llash
        </button>

    `);

}


function openSupport() {

    openModal(`

        <div class="modal-title">
            🆘 Yordam
        </div>

        <div class="empty">
            Support tizimi keyingi bosqichda ulanadi.
        </div>

    `);

}


function openProfile() {

    const user =
        tg?.initDataUnsafe?.user;


    openModal(`

        <div class="modal-title">
            👤 Profil
        </div>

        <div class="empty">

            ${
                user
                ?
                `
                    ${escapeHtml(
                        user.first_name ||
                        ""
                    )}

                    <br><br>

                    ${
                        user.username
                        ?
                        "@" +
                        escapeHtml(
                            user.username
                        )
                        :
                        ""
                    }
                `
                :
                "Telegram profil"
            }

        </div>

    `);

}


function openNotifications() {

    openModal(`

        <div class="modal-title">
            🔔 Xabarlar
        </div>

        <div class="empty">
            Hozircha yangi xabar yo‘q.
        </div>

    `);

}


/* =====================================================
   PACKAGE ICON
===================================================== */

function getPackageEmoji(
    name
) {

    const text =
        String(name)
        .toLowerCase();


    if (
        text.includes("weekly") ||
        text.includes("haftalik") ||
        text.includes("pass")
    ) {
        return "🎫";
    }


    if (
        text.includes("twilight")
    ) {
        return "🌙";
    }


    if (
        text.includes("diamond") ||
        text.includes("diamonds")
    ) {
        return "💎";
    }


    if (
        text.includes("bundle") ||
        text.includes("pack")
    ) {
        return "🎁";
    }


    return "💎";

}


/* =====================================================
   SECURITY / HTML ESCAPE
===================================================== */

function escapeHtml(
    value
) {

    return String(
        value ?? ""
    )
    .replace(
        /&/g,
        "&amp;"
    )
    .replace(
        /</g,
        "&lt;"
    )
    .replace(
        />/g,
        "&gt;"
    )
    .replace(
        /"/g,
        "&quot;"
    )
    .replace(
        /'/g,
        "&#039;"
    );

}


function escapeAttribute(
    value
) {

 return escapeHtml(
        value
    );

}

/* =====================================================
   START
===================================================== */

loadTelegramUser();
loadPlayPayBalance();
