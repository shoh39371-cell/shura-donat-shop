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

// ======================================================
// PHOENIX BOOST SERVICE
// ======================================================

const BOOST_RANKS = [
    "Epic",
    "Legend",
    "Mythic",
    "Mythical Honor",
    "Mythical Glory"
];

// 1 STAR NARXLARI
const BOOST_PRICES = {
    "Epic": 4000,
    "Legend": 5000,
    "Mythic": 6000,
    "Mythical Honor": 7000,
    "Mythical Glory": 9000
};

// MMR
const MMR_STEP = 500;
const MMR_PRICE = 30000;

// TITUL
const TITLE_PRICES = {
    "Silver": 30000,
    "Gold": 70000,
    "Davlat": 200000
};

let boostCurrentRank = 0;
let boostCurrentStars = 0;

let boostTargetRank = 1;
let boostTargetStars = 1;


// ======================================================
// BOOST MENU
// ======================================================

function openBoost() {

    openModal(`
        <div class="modal-title">
            🚀 Boost xizmati
        </div>

        <div class="modal-subtitle">
            MLBB uchun professional xizmatlar
        </div>

        <button
            class="boost-menu-btn boost-menu-mlbb"
            onclick="openMLBBBoost()">

            🚀 &nbsp;
            <b>MLBB Boost</b>

        </button>

        <button
            class="boost-menu-btn boost-menu-title"
            onclick="openTitleServices()">

            🏆 &nbsp;
            <b>Titul olib berish</b>

        </button>
    `);
}


// ======================================================
// MLBB BOOST
// ======================================================

function openMLBBBoost() {

    renderMLBBBoost();

}


function renderMLBBBoost() {

    const totalStars =
        calculateBoostStars();

    const totalPrice =
        calculateBoostPrice();


    openModal(`

        <div class="modal-title">
            🚀 MLBB Boost
        </div>

        <div class="modal-subtitle">
            Rankingizni professional boosterlar ko‘taradi
        </div>


        <!-- CURRENT -->

        <div class="boost-card">

            <div class="boost-section-title">
                Hozirgi rank
            </div>

            <div class="boost-rank-box">

                <button
                    class="boost-counter"
                    onclick="changeCurrentRank(-1)">
                    −
                </button>

                <div class="boost-rank-name">
                    ${BOOST_RANKS[boostCurrentRank]}
                </div>

                <button
                    class="boost-counter"
                    onclick="changeCurrentRank(1)">
                    +
                </button>

            </div>


            <div class="boost-stars">

                <button
                    class="boost-star-btn"
                    onclick="changeCurrentStars(-1)">
                    −
                </button>

                <div class="boost-star-value">
                    ⭐ ${boostCurrentStars}
                </div>

                <button
                    class="boost-star-btn"
                    onclick="changeCurrentStars(1)">
                    +
                </button>

            </div>

        </div>


        <!-- TARGET -->

        <div class="boost-card">

            <div class="boost-section-title">
                Maqsad rank
            </div>

            <div class="boost-rank-box">

                <button
                    class="boost-counter"
                    onclick="changeTargetRank(-1)">
                    −
                </button>

                <div class="boost-rank-name">
                    ${BOOST_RANKS[boostTargetRank]}
                </div>

                <button
                    class="boost-counter"
                    onclick="changeTargetRank(1)">
                    +
                </button>

            </div>


            <div class="boost-stars">

                <button
                    class="boost-star-btn"
                    onclick="changeTargetStars(-1)">
                    −
                </button>

                <div class="boost-star-value">
                    ⭐ ${boostTargetStars}
                </div>

                <button
                    class="boost-star-btn"
                    onclick="changeTargetStars(1)">
                    +
                </button>

            </div>

        </div>


        <!-- PRICE -->

        <div class="boost-total">

            <div class="boost-total-label">
                Jami
            </div>

            <div class="boost-total-stars">
                ⭐ ${totalStars} yulduz
            </div>

            <div class="boost-price">
                💰 ${formatPrice(totalPrice)}
            </div>

        </div>


        <!-- ACCOUNT -->

        <div class="boost-card">

            <div class="boost-section-title">
                Akkaunt ma’lumotlari
            </div>

            <input
                id="boostPlayerId"
                class="boost-input"
                type="text"
                inputmode="numeric"
                placeholder="🎮 O‘yin ID"
            >

            <input
                id="boostZoneId"
                class="boost-input"
                type="text"
                inputmode="numeric"
                placeholder="🌐 Zone ID"
            >

        </div>


        <button
            class="boost-action boost-check"
            onclick="checkBoostAccount()">

            🔍 Akkauntni tekshirish

        </button>


        <button
            class="boost-action boost-pay"
            onclick="openBoostPayment()">

            💳 To‘lovga o‘tish ·
            ${formatPrice(totalPrice)}

        </button>

    `);
}


// ======================================================
// RANK
// ======================================================

function changeCurrentRank(value) {

    boostCurrentRank += value;

    if (boostCurrentRank < 0)
        boostCurrentRank = 0;

    if (boostCurrentRank >= BOOST_RANKS.length)
        boostCurrentRank = BOOST_RANKS.length - 1;

    boostCurrentStars = 0;

    renderMLBBBoost();
}


function changeTargetRank(value) {

    boostTargetRank += value;

    if (boostTargetRank < 0)
        boostTargetRank = 0;

    if (boostTargetRank >= BOOST_RANKS.length)
        boostTargetRank = BOOST_RANKS.length - 1;

    boostTargetStars = 0;

    renderMLBBBoost();
}


// ======================================================
// STARS
// ======================================================

function changeCurrentStars(value) {

    boostCurrentStars += value;

    if (boostCurrentStars < 0)
        boostCurrentStars = 0;

    if (boostCurrentStars > 99)
        boostCurrentStars = 99;

    renderMLBBBoost();
}


function changeTargetStars(value) {

    boostTargetStars += value;

    if (boostTargetStars < 0)
        boostTargetStars = 0;

    if (boostTargetStars > 99)
        boostTargetStars = 99;

    renderMLBBBoost();
}


// ======================================================
// STAR CALCULATION
// ======================================================

function calculateBoostStars() {

    if (boostTargetRank < boostCurrentRank)
        return 0;


    if (boostTargetRank === boostCurrentRank) {

        return Math.max(
            0,
            boostTargetStars - boostCurrentStars
        );

    }


    let stars = 0;


    // Current rankdan chiqish
    stars += Math.max(
        0,
        5 - boostCurrentStars
    );


    // Oradagi ranklar
    for (
        let i = boostCurrentRank + 1;
        i < boostTargetRank;
        i++
    ) {

        stars += 5;

    }


    // Target rank
    stars += boostTargetStars;


    return stars;
}


// ======================================================
// PRICE CALCULATION
// ======================================================

function calculateBoostPrice() {

    if (boostTargetRank < boostCurrentRank)
        return 0;


    // Bir xil rank
    if (boostTargetRank === boostCurrentRank) {

        const stars = Math.max(
            0,
            boostTargetStars - boostCurrentStars
        );

        return stars *
            BOOST_PRICES[
                BOOST_RANKS[boostCurrentRank]
            ];
    }


    let price = 0;


    // Current rankdagi qolgan yulduzlar
    const currentStars =
        Math.max(
            0,
            5 - boostCurrentStars
        );


    price +=
        currentStars *
        BOOST_PRICES[
            BOOST_RANKS[boostCurrentRank]
        ];


    // Oraliq ranklar
    for (
        let i = boostCurrentRank + 1;
        i < boostTargetRank;
        i++
    ) {

        price +=
            5 *
            BOOST_PRICES[
                BOOST_RANKS[i]
            ];

    }


    // Target rankdagi yulduzlar
    price +=
        boostTargetStars *
        BOOST_PRICES[
            BOOST_RANKS[boostTargetRank]
        ];


    return price;
}


// ======================================================
// ACCOUNT CHECK
// ======================================================

async function checkBoostAccount() {

    const playerId =
        document
            .getElementById("boostPlayerId")
            ?.value
            .trim();

    const zoneId =
        document
            .getElementById("boostZoneId")
            ?.value
            .trim();


    if (!playerId) {

        alertUser("🎮 O‘yin ID kiriting.");

        return;
    }


    if (!zoneId) {

        alertUser("🌐 Zone ID kiriting.");

        return;
    }


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

                    body: JSON.stringify({

                        game_id: 1,

                        player_id:
                            playerId,

                        server_id:
                            zoneId

                    })
                }
            );


        const data =
            await response.json();


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

            <div class="boost-total">

                <div class="boost-total-label">
                    Player
                </div>

                <div class="boost-total-stars">
                    ${escapeHtml(
                        data.player_name ||
                        "Noma’lum"
                    )}
                </div>

            </div>

            <div class="boost-card">

                🎮 O‘yin ID:
                <b>${escapeHtml(playerId)}</b>

                <br><br>

                🌐 Zone ID:
                <b>${escapeHtml(zoneId)}</b>

            </div>

            <button
                class="boost-action boost-pay"
                onclick="openMLBBBoost()">

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


// ======================================================
// BOOST PAYMENT
// ======================================================

function openBoostPayment() {

    const playerId =
        document
            .getElementById("boostPlayerId")
            ?.value
            .trim();

    const zoneId =
        document
            .getElementById("boostZoneId")
            ?.value
            .trim();

    const stars =
        calculateBoostStars();

    const price =
        calculateBoostPrice();


    if (!playerId) {

        alertUser("🎮 O‘yin ID kiriting.");

        return;
    }


    if (!zoneId) {

        alertUser("🌐 Zone ID kiriting.");

        return;
    }


    if (stars <= 0) {

        alertUser(
            "Maqsad rankni to‘g‘ri tanlang."
        );

        return;
    }


    openModal(`

        <div class="modal-title">
            💳 Boost to‘lovi
        </div>

        <div class="boost-card">

            <div>
                📍 Hozirgi:
                <b>
                    ${BOOST_RANKS[boostCurrentRank]}
                    · ${boostCurrentStars} ⭐
                </b>
            </div>

            <div style="margin-top:12px">
                🎯 Maqsad:
                <b>
                    ${BOOST_RANKS[boostTargetRank]}
                    · ${boostTargetStars} ⭐
                </b>
            </div>

            <div style="margin-top:12px">
                🎮 ID:
                <b>${escapeHtml(playerId)}</b>
            </div>

            <div style="margin-top:12px">
                🌐 Zone:
                <b>${escapeHtml(zoneId)}</b>
            </div>

        </div>


        <div class="boost-total">

            <div class="boost-total-label">
                To‘lov
            </div>

            <div class="boost-price">
                💰 ${formatPrice(price)}
            </div>

        </div>


        <div class="boost-card">

            <div class="boost-section-title">
                To‘lovdan keyin chek
            </div>

            <div class="boost-title-sub">
                Kartaga to‘lov qilgach,
                chek yoki skrinshotni shu yerga yuklaysiz.
            </div>

        </div>


        <button
            class="boost-action boost-pay"
            onclick="showBoostReceiptForm()">

            💳 To‘ladim — chek yuborish

        </button>

    `);
}


// ======================================================
// RECEIPT
// ======================================================

function showBoostReceiptForm() {

    const price =
        calculateBoostPrice();


    openModal(`

        <div class="modal-title">
            📸 To‘lov cheki
        </div>

        <div class="modal-subtitle">
            ${formatPrice(price)}
        </div>


        <div class="boost-card">

            <div class="boost-section-title">
                To‘lov cheki / skrinshot
            </div>

            <input
                id="boostReceipt"
                class="boost-input"
                type="file"
                accept="image/*"
            >

            <div class="boost-title-sub">
                To‘lov qilganingizdan keyin
                chek rasmini tanlang.
            </div>

        </div>


        <button
            class="boost-action boost-pay"
            onclick="sendBoostOrder()">

            📤 Zayavkani yuborish

        </button>

    `);
}


// ======================================================
// SEND BOOST ORDER
// ======================================================

async function sendBoostOrder() {

    const receipt =
        document
            .getElementById("boostReceipt")
            ?.files?.[0];


    const playerId =
        document
            .getElementById("boostPlayerId")
            ?.value
            .trim();


    const zoneId =
        document
            .getElementById("boostZoneId")
            ?.value
            .trim();


    const price =
        calculateBoostPrice();


    if (!receipt) {

        alertUser(
            "📸 Avval to‘lov chekini yuklang."
        );

        return;
    }


    if (!playerId || !zoneId) {

        alertUser(
            "🎮 Game ID va Zone ID kerak."
        );

        return;
    }


    const formData =
        new FormData();


    formData.append(
        "service",
        "mlbb_boost"
    );


    formData.append(
        "current_rank",
        BOOST_RANKS[boostCurrentRank]
    );


    formData.append(
        "current_stars",
        boostCurrentStars
    );


    formData.append(
        "target_rank",
        BOOST_RANKS[boostTargetRank]
    );


    formData.append(
        "target_stars",
        boostTargetStars
    );


    formData.append(
        "player_id",
        playerId
    );


    formData.append(
        "zone_id",
        zoneId
    );


    formData.append(
        "amount",
        price
    );


    formData.append(
        "receipt",
        receipt
    );


    try {

        const response =
            await fetch(
                "/api/boost/order",
                {
                    method: "POST",
                    body: formData
                }
            );


        const data =
            await response.json();


        if (!data.ok) {

            alertUser(
                data.error ||
                "Zayavka yuborilmadi."
            );

            return;
        }


        openModal(`

            <div class="modal-title">
                ✅ Zayavka yuborildi
            </div>

            <div class="boost-total">

                <div class="boost-total-label">
                    Zayavka
                </div>

                <div class="boost-total-stars">
                    #${escapeHtml(
                        data.order_id ||
                        "NEW"
                    )}
                </div>

            </div>

            <div class="boost-card">

                💰 Summa:
                <b>${formatPrice(price)}</b>

                <br><br>

                ⏳ Holat:
                <b>Kutilmoqda</b>

                <br><br>

                👤 Booster/admin siz bilan
                Telegram orqali bog‘lanadi.

            </div>

        `);

    } catch (error) {

        console.error(error);

        alertUser(
            "Server bilan aloqa qilishda xatolik."
        );
    }
}


// ======================================================
// TITUL MENU
// ======================================================

function openTitleService() {

    openModal(`

        <div class="modal-title">
            🏆 Titul olish
        </div>

        <div class="modal-subtitle">
            Kerakli titulni tanlang
        </div>


        <div class="boost-card">

            <div class="boost-section-title">
                Titul turi
            </div>


            <button
                class="boost-action boost-check"
                onclick="selectTitleType('Silver')">

                🥈 Silver Titul

                <span style="margin-left:auto;">
                    30 000 UZS
                </span>

            </button>


            <button
                class="boost-action boost-check"
                onclick="selectTitleType('Gold')">

                🥇 Gold Titul

                <span style="margin-left:auto;">
                    70 000 UZS
                </span>

            </button>


            <button
                class="boost-action boost-check"
                onclick="selectTitleType('State/Country')">

                🌍 State / Country

                <span style="margin-left:auto;">
                    200 000 UZS
                </span>

            </button>

        </div>

    `);
}

// ======================================================
// MMR SERVICE
// ======================================================

function openMMRService() {

    openModal(`

        <div class="modal-title">
            📈 MMR oshirish
        </div>

        <div class="modal-subtitle">
            Har +500 MMR = 30 000 so‘m
        </div>


        <div class="boost-card">

            <input
                id="mmrCurrent"
                class="boost-input"
                type="number"
                placeholder="📊 Hozirgi MMR"
            >

            <input
                id="mmrTarget"
                class="boost-input"
                type="number"
                placeholder="🎯 Kerakli MMR"
            >

            <input
                id="mmrPlayerId"
                class="boost-input"
                type="text"
                placeholder="🎮 O‘yin ID"
            >

            <input
                id="mmrZoneId"
                class="boost-input"
                type="text"
                placeholder="🌐 Zone ID"
            >

        </div>


        <div
            id="mmrResult"
            class="boost-total">

            <div class="boost-total-label">
                Jami
            </div>

            <div class="boost-price">
                💰 0 so‘m
            </div>

        </div>


        <button
            class="boost-action boost-check"
            onclick="calculateMMR()">

            🧮 Narxni hisoblash

        </button>

    `);
}
function openTitleServices() {

    openModal(`

        <div class="modal-title">
            🏆 Titul olib berish
        </div>

        <div class="modal-subtitle">
            Xizmat turini tanlang
        </div>

        <button
            class="boost-action boost-check"
            onclick="openMMRService()">

            📈 MMR oshirish

        </button>

        <button
            class="boost-action boost-pay"
            onclick="openTitleService()">

            🏆 Titul olish

        </button>

    `);
}
function selectTitleType(titleType) {

    const prices = {
        "Silver": 30000,
        "Gold": 70000,
        "State/Country": 200000
    };

    const price = prices[titleType];

    openModal(`

        <div class="modal-title">
            ${titleType === "Silver" ? "🥈" :
              titleType === "Gold" ? "🥇" : "🌍"}
            ${escapeHtml(titleType)}
        </div>

        <div class="modal-subtitle">
            Akkaunt ma'lumotlari
        </div>


        <div class="boost-card">

            <div class="boost-section-title">
                Titul ma'lumotlari
            </div>


            <input
                id="titleRegion"
                class="boost-input"
                type="text"
                placeholder="📍 Region / Viloyat / Shahar"
            >


            <input
                id="titlePlayerId"
                class="boost-input"
                type="text"
                inputmode="numeric"
                placeholder="🎮 O‘yin ID"
            >


            <input
                id="titleZoneId"
                class="boost-input"
                type="text"
                inputmode="numeric"
                placeholder="🌐 Zone ID"
            >

        </div>


        <div class="boost-total">

            <div class="boost-total-label">
                Jami
            </div>

            <div class="boost-price">
                💰 ${formatPrice(price)}
            </div>

        </div>


        <button
            class="boost-action boost-pay"
            onclick="createTitleOrderWithType(
                '${escapeAttribute(titleType)}'
            )"
            style="margin-top:15px; width:100%;">

            💳 To‘lovga o‘tish ·
            ${formatPrice(price)}

        </button>

    `);
}
function createTitleOrderWithType(titleType) {

    const region =
        document.getElementById("titleRegion")?.value.trim();

    const playerId =
        document.getElementById("titlePlayerId")?.value.trim();

    const zoneId =
        document.getElementById("titleZoneId")?.value.trim();

    if (!region) {
        alertUser("Region / viloyat / shaharni kiriting.");
        return;
    }

    if (!playerId) {
        alertUser("Game IDni kiriting.");
        return;
    }

    if (!zoneId) {
        alertUser("Zone IDni kiriting.");
        return;
    }

    const prices = {
        "Silver": 30000,
        "Gold": 70000,
        "State/Country": 200000
    };

    const price = prices[titleType];

    openTitlePayment(
        region,
        playerId,
        zoneId,
        titleType,
        price
    );
}
function calculateMMR() {

    const current =
        Number(
            document
                .getElementById("mmrCurrent")
                ?.value || 0
        );

    const target =
        Number(
            document
                .getElementById("mmrTarget")
                ?.value || 0
        );

    if (!current || !target) {
        alertUser(
            "Hozirgi va kerakli MMRni kiriting."
        );
        return;
    }

    if (target <= current) {
        alertUser(
            "Kerakli MMR hozirgi MMRdan katta bo‘lishi kerak."
        );
        return;
    }

    const difference =
        target - current;

    const steps =
        Math.ceil(
            difference / MMR_STEP
        );

    const price =
        steps * MMR_PRICE;

    const result =
        document.getElementById(
            "mmrResult"
        );

    if (result) {

        result.innerHTML = `

            <div class="boost-total-label">
                Jami
            </div>

            <div class="boost-total-stars">
                📈 +${difference} MMR
            </div>

            <div class="boost-price">
                💰 ${formatPrice(price)}
            </div>

            <button
                class="boost-action boost-pay"
                onclick="openMMRPayment()"
                style="margin-top:15px; width:100%;"
            >
                💳 To‘lovga o‘tish
            </button>

        `;

    }

}
   
function createTitleOrder() {

    const region =
        document.getElementById("titleRegion")?.value.trim();

    const playerId =
        document.getElementById("titlePlayerId")?.value.trim();

    const zoneId =
        document.getElementById("titleZoneId")?.value.trim();

    const titleType =
        document.getElementById("titleType")?.value;

    if (!region) {
        alertUser("Region / viloyat / shaharni kiriting.");
        return;
    }

    if (!playerId) {
        alertUser("Game IDni kiriting.");
        return;
    }

    if (!zoneId) {
        alertUser("Zone IDni kiriting.");
        return;
    }

    if (!titleType) {
        alertUser("Titulni tanlang.");
        return;
    }

    let price = 0;

    if (titleType === "Silver") {
        price = 30000;
    } else if (titleType === "Gold") {
        price = 70000;
    } else if (titleType === "State/Country") {
        price = 200000;
    }

    openModal(`

        <div class="modal-title">
            💳 Titul uchun to‘lov
        </div>

        <div class="modal-subtitle">
            🏆 ${escapeHtml(titleType)} titul
        </div>

        <div style="margin-top:15px;">
            📍 Region: ${escapeHtml(region)}
        </div>

        <div style="margin-top:8px;">
            🎮 Game ID: ${escapeHtml(playerId)}
        </div>

        <div style="margin-top:8px;">
            🌐 Zone ID: ${escapeHtml(zoneId)}
        </div>

        <div class="boost-price" style="margin-top:15px;">
            💰 ${formatPrice(price)} UZS
        </div>

        <button
            class="boost-action boost-pay"
            onclick="openTitlePayment(
                '${escapeAttribute(region)}',
                '${escapeAttribute(playerId)}',
                '${escapeAttribute(zoneId)}',
                '${escapeAttribute(titleType)}',
                ${price}
            )"
            style="margin-top:15px; width:100%;"
        >
            💳 To‘lovga o‘tish
        </button>

    `);
}
function openTitlePayment(
    region,
    playerId,
    zoneId,
    titleType,
    price
) {

    openModal(`

        <div class="modal-title">
            💳 To‘lov
        </div>

        <div class="modal-subtitle">
            🏆 ${escapeHtml(titleType)} titul
        </div>

        <div class="boost-price" style="margin-top:15px;">
            💰 ${formatPrice(price)} UZS
        </div>

        <div style="
            margin-top:20px;
            padding:15px;
            border-radius:12px;
            background:rgba(255,255,255,0.08);
        ">

            <div>
                💳 Karta raqami
            </div>

            <div
                id="titleCardNumber"
                style="
                    margin-top:8px;
                    font-size:18px;
                    font-weight:bold;
            ">
                Yuklanmoqda...
            </div>

        </div>

        <div style="margin-top:15px;">
            To‘lovni amalga oshirgach, chekni yuboring.
        </div>

        <button
            class="boost-action boost-pay"
            onclick="showTitleReceiptForm(
                '${escapeAttribute(region)}',
                '${escapeAttribute(playerId)}',
                '${escapeAttribute(zoneId)}',
                '${escapeAttribute(titleType)}',
                ${price}
            )"
            style="margin-top:15px; width:100%;"
        >
            📸 Chek yuborish
        </button>

    `);

    fetch("/api/boost/payment-info")
        .then(response => response.json())
        .then(data => {

            const card =
                document.getElementById(
                    "titleCardNumber"
                );

            if (card) {

                if (data.ok) {
                    card.textContent =
                        data.card_number;
                } else {
                    card.textContent =
                        "Karta raqami topilmadi";
                }

            }

        })
        .catch(() => {

            const card =
                document.getElementById(
                    "titleCardNumber"
                );

            if (card) {
                card.textContent =
                    "Karta ma'lumotini olishda xatolik";
            }

        });
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
