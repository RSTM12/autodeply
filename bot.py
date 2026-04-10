"""
ClawPump Telegram Bot — dengan kode akses & input API key manual
"""

import os
import random
import asyncio
import requests
import logging
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

# ─── Load environment ─────────────────────────────────────────────────────────
load_dotenv()
BOT_TOKEN   = os.getenv("BOT_TOKEN")
ACCESS_CODE = os.getenv("ACCESS_CODE", "CLAWPUMP2024")  # ganti di Railway Variables
CLAWPUMP_BASE = "https://clawpump.tech"

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── ConversationHandler states ───────────────────────────────────────────────
(
    WAITING_ACCESS_CODE,
    WAITING_API_KEY_LAUNCH,
    WAITING_API_KEY_EARNINGS,
) = range(3)

# ─── Token generators ─────────────────────────────────────────────────────────
ADJECTIVES = [
    "Cosmic", "Lunar", "Solar", "Quantum", "Cyber", "Digital", "Neon",
    "Turbo", "Ultra", "Mega", "Alpha", "Nova", "Stellar", "Atomic",
    "Hyper", "Super", "Galactic", "Mystic", "Shadow", "Phantom",
]
NOUNS = [
    "Ape", "Cat", "Dog", "Fox", "Wolf", "Bear", "Eagle", "Shark",
    "Dragon", "Tiger", "Lion", "Panda", "Rocket", "Moon", "Star",
    "Gem", "Gold", "Diamond", "Crystal", "Phoenix",
]
SUFFIXES = ["", " DAO", " Finance", " Protocol", " Network", ""]
DESCRIPTIONS = [
    "The ultimate {adj} {noun} token on Solana. Join the revolution and ride the wave to the moon!",
    "{name} is the next-gen meme token powering the {adj_lower} economy on Solana.",
    "Ride the wave with {name} — the {noun_lower} that the crypto world has been waiting for!",
    "Built by degens, for degens. {name} is here to take over the Solana ecosystem.",
    "{name}: Where {adj_lower} meets DeFi. The future is {noun_lower}.",
    "The most {adj_lower} token on Solana. {name} combines community, memes, and real utility.",
    "🚀 {name} is launching on pump.fun. Be early, be {adj_lower}, be legendary.",
]


def generate_token_data() -> dict:
    adj    = random.choice(ADJECTIVES)
    noun   = random.choice(NOUNS)
    suffix = random.choice(SUFFIXES)
    name   = f"{adj} {noun}{suffix}"
    symbol = (adj[:3] + noun[:1]).upper() if random.random() > 0.5 else (adj[:2] + noun[:2]).upper()
    desc   = random.choice(DESCRIPTIONS).format(
        adj=adj, noun=noun, name=name,
        adj_lower=adj.lower(), noun_lower=noun.lower(),
    )
    return {"name": name, "symbol": symbol, "description": desc}


def generate_token_image(name: str, symbol: str) -> BytesIO:
    bg = (random.randint(20, 80), random.randint(20, 80), random.randint(80, 200))
    img  = Image.new("RGB", (500, 500), color=bg)
    draw = ImageDraw.Draw(img)
    for _ in range(8):
        cx, cy = random.randint(50, 450), random.randint(50, 450)
        r = random.randint(30, 120)
        draw.ellipse(
            [cx - r, cy - r, cx + r, cy + r],
            fill=(random.randint(100, 255), random.randint(100, 255), random.randint(100, 255)),
        )
    accent = (random.randint(150, 255), random.randint(100, 255), random.randint(0, 150))
    draw.ellipse([100, 100, 400, 400], fill=accent)
    try:
        f_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
        f_sm  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
    except Exception:
        f_big = f_sm = ImageFont.load_default()
    bb = draw.textbbox((0, 0), symbol, font=f_big)
    draw.text(((500 - (bb[2]-bb[0])) / 2, (500 - (bb[3]-bb[1])) / 2 - 20), symbol, fill="white", font=f_big)
    bb2 = draw.textbbox((0, 0), name, font=f_sm)
    draw.text(((500 - (bb2[2]-bb2[0])) / 2, 310), name, fill="white", font=f_sm)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


# ─── ClawPump API ─────────────────────────────────────────────────────────────

def api_upload_image(buf: BytesIO) -> str | None:
    try:
        r = requests.post(
            f"{CLAWPUMP_BASE}/api/upload",
            files={"image": ("token.png", buf, "image/png")},
            timeout=30,
        )
        d = r.json()
        return d["imageUrl"] if d.get("success") else None
    except Exception as e:
        logger.error("Upload error: %s", e)
        return None


def api_launch_token(api_key: str, token: dict, image_url: str) -> dict:
    try:
        r = requests.post(
            f"{CLAWPUMP_BASE}/api/launch",
            json={
                "name":        token["name"],
                "symbol":      token["symbol"],
                "description": token["description"],
                "imageUrl":    image_url,
            },
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            timeout=60,
        )
        d = r.json()
        d["_status_code"] = r.status_code
        return d
    except Exception as e:
        return {"success": False, "error": str(e), "_status_code": 0}


def api_check_earnings(api_key: str) -> dict:
    """Fetch earnings using API key as Bearer auth (no agent ID needed)."""
    try:
        r = requests.get(
            f"{CLAWPUMP_BASE}/api/fees/earnings",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=20,
        )
        d = r.json()
        d["_status_code"] = r.status_code
        return d
    except Exception as e:
        return {"error": str(e), "_status_code": 0}


def api_get_stats() -> dict:
    try:
        return requests.get(f"{CLAWPUMP_BASE}/api/stats", timeout=15).json()
    except Exception as e:
        return {"error": str(e)}


# ─── Helper: cek apakah user sudah terautentikasi ────────────────────────────

def is_authorized(context: ContextTypes.DEFAULT_TYPE) -> bool:
    return context.user_data.get("authorized", False)


async def reject_unauthorized(update: Update):
    await update.message.reply_text(
        "🚫 *LU MAU NGAPAIN KESINI? MAKSA AMAT*",
        parse_mode="Markdown",
    )


# ─── /start — minta kode akses ───────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_authorized(context):
        await show_menu(update)
        return ConversationHandler.END

    await update.message.reply_text(
        "🔐 *Masukkan kode akses untuk melanjutkan:*",
        parse_mode="Markdown",
    )
    return WAITING_ACCESS_CODE


async def receive_access_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()

    if code != ACCESS_CODE:
        await update.message.reply_text(
            "🚫 *LU MAU NGAPAIN KESINI? MAKSA AMAT*",
            parse_mode="Markdown",
        )
        return WAITING_ACCESS_CODE  # minta lagi

    context.user_data["authorized"] = True
    await update.message.reply_text("✅ *Akses diberikan!*", parse_mode="Markdown")
    await show_menu(update)
    return ConversationHandler.END


async def show_menu(update: Update):
    await update.message.reply_text(
        "👋 *Selamat datang di ClawPump Bot!*\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📋 *Perintah:*\n"
        "  `/launch`   — Launch token baru\n"
        "  `/earnings` — Cek earnings SOL\n"
        "  `/stats`    — Statistik platform\n"
        "  `/help`     — Bantuan\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Setiap perintah akan meminta API key kamu secara langsung.",
        parse_mode="Markdown",
    )


# ─── /launch ─────────────────────────────────────────────────────────────────

async def cmd_launch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(context):
        await reject_unauthorized(update)
        return ConversationHandler.END

    await update.message.reply_text(
        "🔑 *Masukkan API key ClawPump kamu:*\n\n"
        "_(Format: `cpk_...` — tidak akan disimpan)_\n\n"
        "Ketik /cancel untuk batal.",
        parse_mode="Markdown",
    )
    return WAITING_API_KEY_LAUNCH


async def receive_api_key_launch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api_key = update.message.text.strip()

    if not api_key.startswith("cpk_"):
        await update.message.reply_text(
            "❌ Format salah. Harus diawali `cpk_`\nCoba lagi atau /cancel",
            parse_mode="Markdown",
        )
        return WAITING_API_KEY_LAUNCH

    # Hapus pesan API key user (keamanan)
    try:
        await update.message.delete()
    except Exception:
        pass

    msg = await update.message.reply_text(
        "⏳ *Generating token data & gambar...*",
        parse_mode="Markdown",
    )

    # Generate data & gambar
    token     = generate_token_data()
    image_buf = generate_token_image(token["name"], token["symbol"])

    await msg.edit_text(
        f"🎲 *Token Generated!*\n\n"
        f"📛 Name:   `{token['name']}`\n"
        f"🔤 Symbol: `{token['symbol']}`\n"
        f"📝 Desc:   _{token['description']}_\n\n"
        f"⏳ Uploading gambar...",
        parse_mode="Markdown",
    )

    # Kirim preview gambar
    image_buf.seek(0)
    await update.message.reply_photo(
        photo=image_buf,
        caption=f"🖼️ *{token['name']}* (${token['symbol']})",
        parse_mode="Markdown",
    )

    # Upload gambar
    image_buf.seek(0)
    image_url = await asyncio.get_event_loop().run_in_executor(None, api_upload_image, image_buf)

    if not image_url:
        await msg.edit_text(
            "❌ *Gagal upload gambar!*\nServer ClawPump mungkin sedang down. Coba lagi nanti.",
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    await msg.edit_text(
        f"✅ Gambar uploaded!\n\n"
        f"⏳ Launching *{token['name']}* ke pump.fun...\n"
        f"_(10–30 detik)_",
        parse_mode="Markdown",
    )

    # Launch token
    result      = await asyncio.get_event_loop().run_in_executor(None, api_launch_token, api_key, token, image_url)
    status_code = result.get("_status_code", 0)

    if result.get("success"):
        mint         = result.get("mintAddress", "N/A")
        tx           = result.get("txHash", "N/A")
        pump_url     = result.get("pumpUrl", "#")
        explorer_url = result.get("explorerUrl", "#")

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🟢 Lihat di Pump.fun", url=pump_url)],
            [InlineKeyboardButton("🔍 Solscan Explorer", url=explorer_url)],
        ])
        await msg.edit_text(
            f"🎉 *Token Berhasil Launch!*\n\n"
            f"📛 Name:   `{token['name']}`\n"
            f"🔤 Symbol: `${token['symbol']}`\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 Mint Address:\n`{mint}`\n\n"
            f"🔗 TX Hash:\n`{tx}`\n\n"
            f"💰 Kamu akan earn *65% dari setiap trading fee* otomatis!",
            parse_mode="Markdown",
            reply_markup=keyboard,
        )

    elif status_code == 429:
        retry = result.get("retryAfterHours", "?")
        await msg.edit_text(
            f"⏳ *Rate Limit!*\n\nCoba lagi dalam *{retry} jam*.\n"
            f"_(Gasless launch max 1x per 24 jam)_",
            parse_mode="Markdown",
        )
    elif status_code == 401:
        await msg.edit_text(
            "❌ *API Key tidak valid atau expired!*\n\n"
            "Pastikan kamu copy API key yang benar dari clawpump.tech",
            parse_mode="Markdown",
        )
    elif status_code == 503:
        sol = result.get("suggestions", {}).get("paymentFallback", {}).get("selfFunded", {}).get("amountSol", 0.03)
        await msg.edit_text(
            f"⚠️ *Gasless Tidak Tersedia Saat Ini*\n\n"
            f"Treasury rendah. Coba lagi nanti atau pakai Self-Funded ({sol} SOL).",
            parse_mode="Markdown",
        )
    elif status_code == 400:
        details = result.get("details", result.get("error", "Validation error"))
        await msg.edit_text(f"❌ *Validasi Gagal!*\n\n`{details}`", parse_mode="Markdown")
    else:
        err = result.get("message") or result.get("error") or "Unknown error"
        await msg.edit_text(
            f"❌ *Launch Gagal!*\n\nStatus: `{status_code}`\nError: `{err}`",
            parse_mode="Markdown",
        )

    return ConversationHandler.END


# ─── /earnings ────────────────────────────────────────────────────────────────

async def cmd_earnings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(context):
        await reject_unauthorized(update)
        return ConversationHandler.END

    await update.message.reply_text(
        "🔑 *Masukkan API key ClawPump kamu:*\n\n"
        "_(Earnings akan ditarik berdasarkan API key — tidak disimpan)_\n\n"
        "Ketik /cancel untuk batal.",
        parse_mode="Markdown",
    )
    return WAITING_API_KEY_EARNINGS


async def receive_api_key_earnings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api_key = update.message.text.strip()

    if not api_key.startswith("cpk_"):
        await update.message.reply_text(
            "❌ Format salah. Harus diawali `cpk_`\nCoba lagi atau /cancel",
            parse_mode="Markdown",
        )
        return WAITING_API_KEY_EARNINGS

    # Hapus pesan API key user (keamanan)
    try:
        await update.message.delete()
    except Exception:
        pass

    msg = await update.message.reply_text("⏳ Mengambil data earnings...")

    result      = await asyncio.get_event_loop().run_in_executor(None, api_check_earnings, api_key)
    status_code = result.get("_status_code", 0)

    if status_code == 401 or "error" in result:
        err = result.get("error", "Unauthorized")
        await msg.edit_text(
            f"❌ *Gagal mengambil earnings!*\n\n`{err}`\n\nPastikan API key kamu valid.",
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    agent_id      = result.get("agentId", "N/A")
    total_earned  = result.get("totalEarned", 0)
    total_sent    = result.get("totalSent", 0)
    total_pending = result.get("totalPending", 0)
    total_held    = result.get("totalHeld", 0)
    tokens        = result.get("tokenBreakdown", [])

    token_lines = ""
    for t in tokens[:5]:
        mint        = t.get("mintAddress", "N/A")
        short_mint  = mint[:8] + "..." + mint[-4:] if len(mint) > 12 else mint
        agent_share = t.get("totalAgentShare", 0)
        token_lines += f"  • `{short_mint}` → {agent_share:.4f} SOL\n"

    text = (
        f"💰 *Earnings Report*\n"
        f"Agent: `{agent_id}`\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Total Earned:  `{total_earned:.4f} SOL`\n"
        f"📤 Total Sent:    `{total_sent:.4f} SOL`\n"
        f"⏳ Pending:       `{total_pending:.4f} SOL`\n"
        f"🔒 Held:          `{total_held:.4f} SOL`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
    )
    if token_lines:
        text += f"\n📊 *Token Breakdown:*\n{token_lines}"
    text += "\n_Fee dikumpulkan tiap jam & dikirim otomatis ke wallet kamu._"

    await msg.edit_text(text, parse_mode="Markdown")
    return ConversationHandler.END


# ─── /stats ───────────────────────────────────────────────────────────────────

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(context):
        await reject_unauthorized(update)
        return

    msg    = await update.message.reply_text("⏳ Mengambil statistik platform...")
    result = await asyncio.get_event_loop().run_in_executor(None, api_get_stats)

    if "error" in result:
        await msg.edit_text(f"❌ Gagal: `{result['error']}`", parse_mode="Markdown")
        return

    await msg.edit_text(
        f"📊 *ClawPump Platform Stats*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🪙 Total Tokens:   `{result.get('totalTokens', 0)}`\n"
        f"🚀 Total Launches: `{result.get('totalLaunches', 0)}`\n"
        f"💹 Market Cap:     `${result.get('totalMarketCap', 0):,.0f}`\n"
        f"📈 Volume 24h:     `${result.get('totalVolume24h', 0):,.0f}`\n"
        f"━━━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown",
    )


# ─── /help ────────────────────────────────────────────────────────────────────

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(context):
        await reject_unauthorized(update)
        return

    await update.message.reply_text(
        "🆘 *Panduan ClawPump Bot*\n\n"
        "*Semua perintah minta API key secara manual — tidak disimpan.*\n\n"
        "`/launch`   → Generate token random & launch ke pump.fun\n"
        "`/earnings` → Cek earnings SOL via API key\n"
        "`/stats`    → Statistik platform ClawPump\n"
        "`/cancel`   → Batalkan operasi saat ini\n\n"
        "💡 API key bisa didapat di [clawpump.tech](https://clawpump.tech) → login Google",
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )


# ─── /cancel ─────────────────────────────────────────────────────────────────

async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Dibatalkan.")
    return ConversationHandler.END


# ─── Unknown ──────────────────────────────────────────────────────────────────

async def cmd_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(context):
        await reject_unauthorized(update)
        return
    await update.message.reply_text("❓ Perintah tidak dikenal. Ketik /help untuk bantuan.")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN tidak ditemukan!")

    app = Application.builder().token(BOT_TOKEN).build()

    # ConversationHandler: /start → kode akses
    start_conv = ConversationHandler(
        entry_points=[CommandHandler("start", cmd_start)],
        states={
            WAITING_ACCESS_CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_access_code)
            ],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
    )

    # ConversationHandler: /launch → API key
    launch_conv = ConversationHandler(
        entry_points=[CommandHandler("launch", cmd_launch)],
        states={
            WAITING_API_KEY_LAUNCH: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_api_key_launch)
            ],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
    )

    # ConversationHandler: /earnings → API key
    earnings_conv = ConversationHandler(
        entry_points=[CommandHandler("earnings", cmd_earnings)],
        states={
            WAITING_API_KEY_EARNINGS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_api_key_earnings)
            ],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
    )

    app.add_handler(start_conv)
    app.add_handler(launch_conv)
    app.add_handler(earnings_conv)
    app.add_handler(CommandHandler("stats",   cmd_stats))
    app.add_handler(CommandHandler("help",    cmd_help))
    app.add_handler(CommandHandler("cancel",  cmd_cancel))
    app.add_handler(MessageHandler(filters.COMMAND, cmd_unknown))

    logger.info("🤖 Bot started! Polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
