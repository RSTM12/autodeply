"""
ClawPump Telegram Bot
Launch Solana tokens & check earnings via ClawPump API
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

# ─── Load environment ────────────────────────────────────────────────────────
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CLAWPUMP_BASE = "https://clawpump.tech"

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ─── In-memory storage (per user) ────────────────────────────────────────────
user_data_store: dict = {}

# ─── ConversationHandler states ──────────────────────────────────────────────
WAITING_API_KEY = 1

# ─── Token data generators ───────────────────────────────────────────────────
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
    adj = random.choice(ADJECTIVES)
    noun = random.choice(NOUNS)
    suffix = random.choice(SUFFIXES)
    name = f"{adj} {noun}{suffix}"
    symbol = (adj[:2] + noun[:2]).upper()
    if random.random() > 0.5:
        symbol = (adj[:3] + noun[:1]).upper()
    desc_template = random.choice(DESCRIPTIONS)
    description = desc_template.format(
        adj=adj, noun=noun, name=name,
        adj_lower=adj.lower(), noun_lower=noun.lower(),
    )
    return {"name": name, "symbol": symbol, "description": description}


def generate_token_image(name: str, symbol: str) -> BytesIO:
    bg_color = (
        random.randint(20, 80),
        random.randint(20, 80),
        random.randint(80, 200),
    )
    img = Image.new("RGB", (500, 500), color=bg_color)
    draw = ImageDraw.Draw(img)

    for _ in range(8):
        cx = random.randint(50, 450)
        cy = random.randint(50, 450)
        r = random.randint(30, 120)
        color = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)

    accent = (random.randint(150, 255), random.randint(100, 255), random.randint(0, 150))
    draw.ellipse([100, 100, 400, 400], fill=accent)

    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
    except Exception:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), symbol, font=font_large)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((500 - tw) / 2, (500 - th) / 2 - 20), symbol, fill="white", font=font_large)

    bbox2 = draw.textbbox((0, 0), name, font=font_small)
    tw2 = bbox2[2] - bbox2[0]
    draw.text(((500 - tw2) / 2, 310), name, fill="white", font=font_small)

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


# ─── ClawPump API helpers ─────────────────────────────────────────────────────

def api_upload_image(image_buf: BytesIO) -> str | None:
    try:
        resp = requests.post(
            f"{CLAWPUMP_BASE}/api/upload",
            files={"image": ("token.png", image_buf, "image/png")},
            timeout=30,
        )
        data = resp.json()
        if data.get("success"):
            return data["imageUrl"]
        logger.error("Upload failed: %s", data)
        return None
    except Exception as e:
        logger.error("Upload exception: %s", e)
        return None


def api_launch_token(api_key: str, token: dict, image_url: str) -> dict:
    payload = {
        "name": token["name"],
        "symbol": token["symbol"],
        "description": token["description"],
        "imageUrl": image_url,
    }
    try:
        resp = requests.post(
            f"{CLAWPUMP_BASE}/api/launch",
            json=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=60,
        )
        data = resp.json()
        data["_status_code"] = resp.status_code
        return data
    except Exception as e:
        return {"success": False, "error": str(e), "_status_code": 0}


def api_check_earnings(agent_id: str) -> dict:
    try:
        resp = requests.get(
            f"{CLAWPUMP_BASE}/api/fees/earnings",
            params={"agentId": agent_id},
            timeout=20,
        )
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def api_get_stats() -> dict:
    try:
        resp = requests.get(f"{CLAWPUMP_BASE}/api/stats", timeout=15)
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


# ─── Bot command handlers ─────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    has_key = uid in user_data_store and user_data_store[uid].get("api_key")

    text = (
        "👋 *Selamat datang di ClawPump Bot!*\n\n"
        "Bot ini membantu kamu launch token Solana di pump.fun "
        "dan earn *65% dari setiap trading fee* — otomatis!\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📋 *Daftar Perintah:*\n"
        "  `/setkey` — Set API key kamu\n"
        "  `/launch` — Launch token baru (detail & gambar random)\n"
        "  `/earnings` — Cek earnings kamu\n"
        "  `/stats` — Statistik platform ClawPump\n"
        "  `/mykey` — Cek status API key kamu\n"
        "  `/help` — Bantuan\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    if has_key:
        text += "✅ API key sudah tersimpan. Kamu siap launch!\nKetik /launch untuk mulai."
    else:
        text += "⚠️ Belum ada API key. Ketik /setkey untuk memulai."

    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🆘 *Panduan ClawPump Bot*\n\n"
        "*1. Dapatkan API Key*\n"
        "Login ke [clawpump.tech](https://clawpump.tech) dengan Google → copy API key (`cpk_...`)\n\n"
        "*2. Set API Key di Bot*\n"
        "Ketik `/setkey` lalu masukkan API key kamu\n\n"
        "*3. Launch Token*\n"
        "Ketik `/launch` — bot akan:\n"
        "  • Generate nama, simbol & deskripsi random\n"
        "  • Generate gambar token random\n"
        "  • Upload & launch otomatis ke pump.fun\n"
        "  • Kirim hasil launch (link, mint address, dll)\n\n"
        "*4. Cek Earnings*\n"
        "Ketik `/earnings` untuk lihat berapa SOL yang sudah kamu earned\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💡 *Tips:*\n"
        "• Gasless launch: max 1x per 24 jam\n"
        "• Kamu earn 65% dari setiap trading fee\n"
        "• Fee dikumpulkan tiap jam, langsung ke wallet kamu\n"
    )
    await update.message.reply_text(text, parse_mode="Markdown", disable_web_page_preview=True)


# ── /setkey flow ──────────────────────────────────────────────────────────────

async def cmd_setkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔑 *Masukkan API Key kamu* (format: `cpk_...`)\n\n"
        "Dapatkan API key di [clawpump.tech](https://clawpump.tech) → login Google → dashboard\n\n"
        "_Ketik /cancel untuk membatalkan_",
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )
    return WAITING_API_KEY


async def receive_api_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    api_key = update.message.text.strip()

    if not api_key.startswith("cpk_"):
        await update.message.reply_text(
            "❌ API key tidak valid. Harus diawali dengan `cpk_`\n"
            "Coba lagi atau ketik /cancel",
            parse_mode="Markdown",
        )
        return WAITING_API_KEY

    if uid not in user_data_store:
        user_data_store[uid] = {}
    user_data_store[uid]["api_key"] = api_key

    await update.message.reply_text(
        "✅ *API key berhasil disimpan!*\n\n"
        "Sekarang kamu bisa:\n"
        "• `/launch` — Launch token baru\n"
        "• `/earnings` — Cek earnings",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Dibatalkan.")
    return ConversationHandler.END


# ── /mykey ────────────────────────────────────────────────────────────────────

async def cmd_mykey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    api_key = user_data_store.get(uid, {}).get("api_key")
    if api_key:
        masked = api_key[:8] + "..." + api_key[-4:]
        await update.message.reply_text(
            f"🔑 API key tersimpan: `{masked}`\n\nGunakan /setkey untuk menggantinya.",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text("⚠️ Belum ada API key. Gunakan /setkey untuk menyimpan.")


# ── /launch ───────────────────────────────────────────────────────────────────

async def cmd_launch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    api_key = user_data_store.get(uid, {}).get("api_key")

    if not api_key:
        await update.message.reply_text(
            "⚠️ Kamu belum set API key.\nGunakan /setkey terlebih dahulu."
        )
        return

    msg = await update.message.reply_text(
        "🚀 *Memulai proses launch...*\n\n⏳ Generating token data & gambar...",
        parse_mode="Markdown",
    )

    token = generate_token_data()
    image_buf = generate_token_image(token["name"], token["symbol"])

    await msg.edit_text(
        f"🚀 *Token Generated!*\n\n"
        f"📛 Name: `{token['name']}`\n"
        f"🔤 Symbol: `{token['symbol']}`\n"
        f"📝 Desc: _{token['description']}_\n\n"
        f"⏳ Uploading gambar ke ClawPump...",
        parse_mode="Markdown",
    )

    image_buf.seek(0)
    await update.message.reply_photo(
        photo=image_buf,
        caption=f"🖼️ Token image: *{token['name']}* (${token['symbol']})",
        parse_mode="Markdown",
    )

    image_buf.seek(0)
    image_url = await asyncio.get_event_loop().run_in_executor(
        None, api_upload_image, image_buf
    )

    if not image_url:
        await msg.edit_text(
            "❌ *Gagal upload gambar!*\n\nServer ClawPump mungkin sedang down. Coba lagi nanti.",
            parse_mode="Markdown",
        )
        return

    await msg.edit_text(
        f"✅ Gambar uploaded!\n\n"
        f"⏳ Launching token *{token['name']}* ke pump.fun...\n"
        f"_(Proses ini bisa memakan 10–30 detik)_",
        parse_mode="Markdown",
    )

    result = await asyncio.get_event_loop().run_in_executor(
        None, api_launch_token, api_key, token, image_url
    )

    status_code = result.get("_status_code", 0)

    if result.get("success"):
        mint = result.get("mintAddress", "N/A")
        tx = result.get("txHash", "N/A")
        pump_url = result.get("pumpUrl", "#")
        explorer_url = result.get("explorerUrl", "#")

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🟢 Lihat di Pump.fun", url=pump_url)],
            [InlineKeyboardButton("🔍 Explorer (Solscan)", url=explorer_url)],
        ])

        await msg.edit_text(
            f"🎉 *Token Berhasil Launch!*\n\n"
            f"📛 Name: `{token['name']}`\n"
            f"🔤 Symbol: `${token['symbol']}`\n"
            f"📝 Desc: _{token['description']}_\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 Mint Address:\n`{mint}`\n\n"
            f"🔗 TX Hash:\n`{tx}`\n\n"
            f"💰 Kamu akan earn *65% dari setiap trading fee* secara otomatis!\n"
            f"Gunakan /earnings untuk cek pendapatanmu.",
            parse_mode="Markdown",
            reply_markup=keyboard,
        )

    elif status_code == 429:
        retry = result.get("retryAfterHours", "?")
        await msg.edit_text(
            f"⏳ *Rate Limit!*\n\n"
            f"Kamu sudah launch hari ini. Coba lagi dalam *{retry} jam*.\n\n"
            f"ℹ️ Gasless launch dibatasi 1x per 24 jam per API key.",
            parse_mode="Markdown",
        )

    elif status_code == 401:
        await msg.edit_text(
            "❌ *API Key tidak valid atau expired!*\n\n"
            "Gunakan /setkey untuk memperbarui API key kamu.\n"
            "Pastikan kamu login di [clawpump.tech](https://clawpump.tech)",
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )

    elif status_code == 503:
        fallback = result.get("suggestions", {}).get("paymentFallback", {}).get("selfFunded", {})
        sol_amount = fallback.get("amountSol", 0.03)
        await msg.edit_text(
            f"⚠️ *Gasless Launch Tidak Tersedia*\n\n"
            f"Treasury ClawPump sedang rendah.\n"
            f"Coba lagi nanti atau gunakan Self-Funded ({sol_amount} SOL).\n\n"
            f"Info: [clawpump.tech/launch.md](https://clawpump.tech/launch.md)",
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )

    elif status_code == 400:
        details = result.get("details", result.get("error", "Unknown validation error"))
        await msg.edit_text(
            f"❌ *Validasi Gagal!*\n\nDetail: `{details}`",
            parse_mode="Markdown",
        )

    else:
        error_msg = result.get("message") or result.get("error") or "Unknown error"
        await msg.edit_text(
            f"❌ *Launch Gagal!*\n\n"
            f"Status: `{status_code}`\n"
            f"Error: `{error_msg}`\n\n"
            f"Coba lagi dalam beberapa menit.",
            parse_mode="Markdown",
        )


# ── /earnings ─────────────────────────────────────────────────────────────────

async def cmd_earnings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_info = user_data_store.get(uid, {})
    api_key = user_info.get("api_key")

    if not api_key:
        await update.message.reply_text("⚠️ Belum ada API key. Gunakan /setkey terlebih dahulu.")
        return

    agent_id = user_info.get("agent_id")

    if not agent_id:
        await update.message.reply_text(
            "🔍 *Cek Earnings*\n\n"
            "Masukkan Agent ID kamu:\n"
            "_(Bisa dilihat di dashboard clawpump.tech)_",
            parse_mode="Markdown",
        )
        context.user_data["awaiting_agent_id"] = True
        return

    await _fetch_and_show_earnings(update, agent_id)


async def receive_agent_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_agent_id"):
        return

    uid = update.effective_user.id
    agent_id = update.message.text.strip()

    if uid not in user_data_store:
        user_data_store[uid] = {}
    user_data_store[uid]["agent_id"] = agent_id
    context.user_data["awaiting_agent_id"] = False

    await _fetch_and_show_earnings(update, agent_id)


async def _fetch_and_show_earnings(update: Update, agent_id: str):
    msg = await update.message.reply_text("⏳ Mengambil data earnings...")

    result = await asyncio.get_event_loop().run_in_executor(
        None, api_check_earnings, agent_id
    )

    if "error" in result and not result.get("agentId"):
        await msg.edit_text(
            f"❌ *Gagal mengambil earnings!*\n\nError: `{result['error']}`",
            parse_mode="Markdown",
        )
        return

    total_earned  = result.get("totalEarned", 0)
    total_sent    = result.get("totalSent", 0)
    total_pending = result.get("totalPending", 0)
    total_held    = result.get("totalHeld", 0)
    tokens        = result.get("tokenBreakdown", [])

    token_lines = ""
    for t in tokens[:5]:
        mint = t.get("mintAddress", "N/A")
        short_mint = mint[:8] + "..." + mint[-4:] if len(mint) > 12 else mint
        agent_share = t.get("totalAgentShare", 0)
        token_lines += f"  • `{short_mint}` → {agent_share:.4f} SOL\n"

    text = (
        f"💰 *Earnings — Agent: `{agent_id}`*\n\n"
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


# ── /stats ────────────────────────────────────────────────────────────────────

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("⏳ Mengambil statistik platform...")

    result = await asyncio.get_event_loop().run_in_executor(None, api_get_stats)

    if "error" in result:
        await msg.edit_text(f"❌ Gagal ambil stats: `{result['error']}`", parse_mode="Markdown")
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


# ── Unknown command ───────────────────────────────────────────────────────────

async def cmd_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❓ Perintah tidak dikenal. Ketik /help untuk bantuan.")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN tidak ditemukan! Set di file .env atau Railway Variables.")

    app = Application.builder().token(BOT_TOKEN).build()

    setkey_conv = ConversationHandler(
        entry_points=[CommandHandler("setkey", cmd_setkey)],
        states={
            WAITING_API_KEY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_api_key)
            ],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("launch", cmd_launch))
    app.add_handler(CommandHandler("earnings", cmd_earnings))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("mykey", cmd_mykey))
    app.add_handler(setkey_conv)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_agent_id))
    app.add_handler(MessageHandler(filters.COMMAND, cmd_unknown))

    logger.info("🤖 Bot started! Polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
