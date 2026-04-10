"""
ClawPump Telegram Bot
- Auto detect cpk_ key → langsung launch
- Gambar random dengan tema & bentuk bervariasi
"""

import os
import math
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
    filters,
)

# ─── Config ───────────────────────────────────────────────────────────────────
load_dotenv()
BOT_TOKEN     = os.getenv("BOT_TOKEN")
ACCESS_CODE   = os.getenv("ACCESS_CODE", "CLAWPUMP2024")
CLAWPUMP_BASE = "https://clawpump.tech"

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

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
    "🚀 {name} launching on pump.fun. Be early, be {adj_lower}, be legendary.",
]

# ─── Color themes ─────────────────────────────────────────────────────────────
THEMES = [
    {"name": "fire",   "bg": (25, 5, 0),    "colors": [(255,80,0),(255,200,0),(220,30,0),(255,140,50),(200,60,0)]},
    {"name": "ocean",  "bg": (0, 8, 40),    "colors": [(0,150,255),(0,255,210),(40,90,200),(100,210,255),(0,180,180)]},
    {"name": "forest", "bg": (5, 25, 5),    "colors": [(0,200,60),(120,190,0),(40,160,40),(180,255,80),(0,140,70)]},
    {"name": "purple", "bg": (15, 0, 30),   "colors": [(180,0,255),(255,0,180),(120,0,220),(255,80,255),(100,0,180)]},
    {"name": "gold",   "bg": (20, 12, 0),   "colors": [(255,210,0),(255,165,0),(210,140,0),(255,235,80),(180,130,0)]},
    {"name": "cyber",  "bg": (0, 18, 18),   "colors": [(0,255,200),(0,210,255),(40,255,140),(0,255,120),(50,200,200)]},
    {"name": "sunset", "bg": (28, 5, 18),   "colors": [(255,90,40),(200,40,100),(255,160,0),(160,0,110),(255,60,80)]},
    {"name": "ice",    "bg": (5, 14, 28),   "colors": [(140,215,255),(200,240,255),(90,175,255),(225,248,255),(100,190,240)]},
    {"name": "lava",   "bg": (30, 0, 0),    "colors": [(255,50,0),(255,120,0),(200,0,0),(255,180,0),(150,0,0)]},
    {"name": "mint",   "bg": (0, 22, 18),   "colors": [(0,255,180),(80,255,200),(0,200,150),(150,255,220),(0,230,160)]},
    {"name": "rose",   "bg": (28, 5, 15),   "colors": [(255,80,120),(255,150,180),(200,40,80),(255,200,210),(180,20,80)]},
    {"name": "matrix", "bg": (0, 12, 0),    "colors": [(0,255,0),(0,200,0),(50,255,50),(0,180,0),(100,255,100)]},
]


def make_polygon(cx, cy, r, sides, rotation=0):
    points = []
    for i in range(sides):
        angle = 2 * math.pi * i / sides + rotation
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    return points


def make_star(cx, cy, r_out, r_in, points_count=5, rotation=0):
    points = []
    for i in range(points_count * 2):
        r = r_out if i % 2 == 0 else r_in
        angle = math.pi * i / points_count + rotation - math.pi / 2
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    return points


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
    theme  = random.choice(THEMES)
    style  = random.choice(["circles", "polygons", "stars", "burst", "mosaic", "rings", "mixed"])
    colors = theme["colors"]
    bg     = theme["bg"]

    img  = Image.new("RGB", (500, 500), color=bg)
    draw = ImageDraw.Draw(img)

    # ── Draw decorative background shapes ────────────────────────────────────
    if style == "circles":
        for _ in range(12):
            cx, cy = random.randint(-50, 550), random.randint(-50, 550)
            r = random.randint(25, 160)
            draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=random.choice(colors))

    elif style == "polygons":
        for _ in range(10):
            cx, cy = random.randint(20, 480), random.randint(20, 480)
            r      = random.randint(40, 130)
            sides  = random.choice([3, 4, 5, 6, 8])
            rot    = random.uniform(0, math.pi)
            pts    = make_polygon(cx, cy, r, sides, rot)
            draw.polygon(pts, fill=random.choice(colors))

    elif style == "stars":
        for _ in range(7):
            cx, cy  = random.randint(50, 450), random.randint(50, 450)
            r_out   = random.randint(50, 130)
            r_in    = r_out // random.randint(2, 3)
            n_pts   = random.choice([4, 5, 6, 8])
            rot     = random.uniform(0, math.pi)
            pts     = make_star(cx, cy, r_out, r_in, n_pts, rot)
            draw.polygon(pts, fill=random.choice(colors))

    elif style == "burst":
        cx, cy = 250, 250
        for i in range(24):
            angle  = 2 * math.pi * i / 24
            length = random.randint(100, 240)
            width  = random.randint(4, 22)
            x2 = cx + length * math.cos(angle)
            y2 = cy + length * math.sin(angle)
            draw.line([(cx, cy), (x2, y2)], fill=random.choice(colors), width=width)
        # Center circle
        draw.ellipse([170, 170, 330, 330], fill=bg)

    elif style == "mosaic":
        cell = 80
        for row in range(7):
            for col in range(7):
                if random.random() > 0.35:
                    x = col * cell - 20 + random.randint(-10, 10)
                    y = row * cell - 20 + random.randint(-10, 10)
                    shape = random.choice(["rect", "circle"])
                    c = random.choice(colors)
                    if shape == "rect":
                        w = h = random.randint(30, 70)
                        draw.rectangle([x, y, x+w, y+h], fill=c)
                    else:
                        r = random.randint(20, 45)
                        draw.ellipse([x-r, y-r, x+r, y+r], fill=c)

    elif style == "rings":
        for r in range(220, 0, -40):
            c = random.choice(colors)
            draw.ellipse([250-r, 250-r, 250+r, 250+r], outline=c, width=random.randint(8, 25))

    elif style == "mixed":
        # Campuran semua bentuk
        for _ in range(5):
            cx, cy = random.randint(20, 480), random.randint(20, 480)
            shape = random.choice(["circle", "polygon", "star"])
            c = random.choice(colors)
            if shape == "circle":
                r = random.randint(30, 120)
                draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=c)
            elif shape == "polygon":
                r = random.randint(40, 110)
                sides = random.choice([3, 4, 5, 6])
                pts = make_polygon(cx, cy, r, sides, random.uniform(0, math.pi))
                draw.polygon(pts, fill=c)
            elif shape == "star":
                r_o = random.randint(50, 110)
                pts = make_star(cx, cy, r_o, r_o//2, random.choice([4,5,6]), random.uniform(0, math.pi))
                draw.polygon(pts, fill=c)

    # ── Central badge (lingkaran gelap di tengah untuk teks) ──────────────────
    badge_color = tuple(max(c - 30, 0) for c in bg)
    # Ring dekoratif
    ring_color = random.choice(colors)
    draw.ellipse([85, 85, 415, 415], fill=ring_color)
    draw.ellipse([100, 100, 400, 400], fill=badge_color)

    # ── Teks symbol & name ────────────────────────────────────────────────────
    try:
        f_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
        f_sm  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 26)
    except Exception:
        f_big = ImageFont.load_default()
        f_sm  = ImageFont.load_default()

    text_color = random.choice(colors)

    bb = draw.textbbox((0, 0), symbol, font=f_big)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    draw.text(((500 - tw) / 2, (500 - th) / 2 - 25), symbol, fill=text_color, font=f_big)

    # Truncate long name
    display_name = name if len(name) <= 20 else name[:18] + "…"
    bb2 = draw.textbbox((0, 0), display_name, font=f_sm)
    tw2 = bb2[2] - bb2[0]
    draw.text(((500 - tw2) / 2, 305), display_name, fill="white", font=f_sm)

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
        return d.get("imageUrl") if d.get("success") else None
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
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type":  "application/json",
            },
            timeout=60,
        )
        d = r.json()
        d["_status_code"] = r.status_code
        return d
    except Exception as e:
        return {"success": False, "error": str(e), "_status_code": 0}


def api_check_earnings(api_key: str) -> dict:
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


# ─── Helpers ──────────────────────────────────────────────────────────────────

def is_authorized(context: ContextTypes.DEFAULT_TYPE) -> bool:
    return context.user_data.get("authorized", False)


def set_expecting(context: ContextTypes.DEFAULT_TYPE, state):
    context.user_data["expecting"] = state


def get_expecting(context: ContextTypes.DEFAULT_TYPE):
    return context.user_data.get("expecting")


async def reject_unauthorized(update: Update):
    await update.message.reply_text("🚫 *LU MAU NGAPAIN KESINI? MAKSA AMAT*", parse_mode="Markdown")


async def show_menu(update: Update):
    await update.message.reply_text(
        "✅ *Akses diberikan! Selamat datang.*\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📋 *Perintah:*\n"
        "  /launch   — Launch token (minta API key)\n"
        "  /earnings — Cek earnings SOL\n"
        "  /stats    — Statistik platform\n"
        "  /help     — Bantuan\n"
        "  /cancel   — Batalkan operasi\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "💡 *Shortcut:* Langsung kirim API key (`cpk_...`) → bot auto launch!",
        parse_mode="Markdown",
    )


# ─── Commands ─────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_authorized(context):
        await show_menu(update)
        return
    set_expecting(context, "access_code")
    await update.message.reply_text(
        "🔐 *Masukkan kode akses untuk melanjutkan:*",
        parse_mode="Markdown",
    )


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    set_expecting(context, None)
    await update.message.reply_text("❌ Dibatalkan.")


async def cmd_launch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(context):
        await reject_unauthorized(update)
        return
    set_expecting(context, "api_key_earnings")  # reset earnings state kalau ada
    set_expecting(context, None)
    await update.message.reply_text(
        "🔑 *Kirim API key kamu* (format: `cpk_...`)\n\n"
        "Bot langsung launch setelah menerima key.\n"
        "Atau /cancel untuk batal.",
        parse_mode="Markdown",
    )


async def cmd_earnings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(context):
        await reject_unauthorized(update)
        return
    set_expecting(context, "api_key_earnings")
    await update.message.reply_text(
        "🔑 *Kirim API key kamu* untuk cek earnings:\n\n"
        "_(Format: `cpk_...` — tidak disimpan)_\n\n"
        "Atau /cancel untuk batal.",
        parse_mode="Markdown",
    )


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(context):
        await reject_unauthorized(update)
        return
    set_expecting(context, None)
    msg    = await update.message.reply_text("⏳ Mengambil statistik...")
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


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(context):
        await reject_unauthorized(update)
        return
    set_expecting(context, None)
    await update.message.reply_text(
        "🆘 *Panduan ClawPump Bot*\n\n"
        "🚀 *Cara Launch (2 cara):*\n"
        "  1. Ketik `/launch` → kirim API key\n"
        "  2. Langsung kirim `cpk_...` → auto launch!\n\n"
        "💰 *Cek Earnings:*\n"
        "  Ketik `/earnings` → kirim API key\n\n"
        "📊 `/stats` → Statistik platform\n"
        "❌ `/cancel` → Batalkan operasi\n\n"
        "💡 API key: [clawpump.tech](https://clawpump.tech) → login Google",
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )


# ─── Message handler utama ────────────────────────────────────────────────────

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text      = update.message.text.strip()
    expecting = get_expecting(context)

    # ── Belum authorized ─────────────────────────────────────────────────────
    if not is_authorized(context):
        if expecting == "access_code":
            if text == ACCESS_CODE:
                context.user_data["authorized"] = True
                set_expecting(context, None)
                await show_menu(update)
            else:
                await update.message.reply_text(
                    "🚫 *LU MAU NGAPAIN KESINI? MAKSA AMAT*",
                    parse_mode="Markdown",
                )
        else:
            await reject_unauthorized(update)
        return

    # ── AUTO LAUNCH: user kirim cpk_ langsung tanpa perintah apapun ──────────
    if text.startswith("cpk_"):
        api_key = text
        set_expecting(context, None)
        try:
            await update.message.delete()
        except Exception:
            pass
        # Cek apakah sedang mode earnings
        if expecting == "api_key_earnings":
            await do_earnings(update, context, api_key)
        else:
            # Default: launch
            await do_launch(update, context, api_key)
        return

    # ── Tidak ada state & bukan cpk_ ─────────────────────────────────────────
    if not expecting:
        await update.message.reply_text(
            "Gunakan perintah atau kirim langsung API key (`cpk_...`) untuk launch.\n"
            "Ketik /help untuk bantuan.",
            parse_mode="Markdown",
        )
        return

    # ── Input tidak valid saat menunggu API key ───────────────────────────────
    if expecting in ("api_key_earnings",):
        await update.message.reply_text(
            "❌ Format salah. API key harus diawali `cpk_`\nCoba lagi atau /cancel",
            parse_mode="Markdown",
        )


# ─── Proses launch ────────────────────────────────────────────────────────────

async def do_launch(update: Update, context: ContextTypes.DEFAULT_TYPE, api_key: str):
    msg = await update.message.reply_text(
        "⏳ *Generating token...*",
        parse_mode="Markdown",
    )

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

    image_buf.seek(0)
    await update.message.reply_photo(
        photo=image_buf,
        caption=f"🖼️ *{token['name']}* (${token['symbol']})",
        parse_mode="Markdown",
    )

    image_buf.seek(0)
    image_url = await asyncio.get_event_loop().run_in_executor(None, api_upload_image, image_buf)

    if not image_url:
        await msg.edit_text(
            "❌ *Gagal upload gambar!*\nServer ClawPump mungkin down. Coba lagi nanti.",
            parse_mode="Markdown",
        )
        return

    await msg.edit_text(
        f"✅ Gambar uploaded!\n\n⏳ Launching *{token['name']}* ke pump.fun...\n_(10–30 detik)_",
        parse_mode="Markdown",
    )

    result      = await asyncio.get_event_loop().run_in_executor(
        None, api_launch_token, api_key, token, image_url
    )
    status_code = result.get("_status_code", 0)

    if result.get("success"):
        mint         = result.get("mintAddress", "N/A")
        tx           = result.get("txHash", "N/A")
        pump_url     = result.get("pumpUrl", "#")
        explorer_url = result.get("explorerUrl", "#")
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🟢 Lihat di Pump.fun", url=pump_url)],
            [InlineKeyboardButton("🔍 Solscan Explorer",  url=explorer_url)],
        ])
        await msg.edit_text(
            f"🎉 *Token Berhasil Launch!*\n\n"
            f"📛 Name:   `{token['name']}`\n"
            f"🔤 Symbol: `${token['symbol']}`\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 Mint Address:\n`{mint}`\n\n"
            f"🔗 TX Hash:\n`{tx}`\n\n"
            f"💰 Earn *65% dari setiap trading fee* otomatis!",
            parse_mode="Markdown",
            reply_markup=keyboard,
        )
    elif status_code == 429:
        retry = result.get("retryAfterHours", "?")
        await msg.edit_text(
            f"⏳ *Rate Limit!*\n\nCoba lagi dalam *{retry} jam*.\n_(Max 1 launch per 24 jam)_",
            parse_mode="Markdown",
        )
    elif status_code == 401:
        await msg.edit_text(
            "❌ *API Key tidak valid atau expired!*\n\n"
            "Pastikan API key benar dari clawpump.tech",
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


# ─── Proses earnings ──────────────────────────────────────────────────────────

async def do_earnings(update: Update, context: ContextTypes.DEFAULT_TYPE, api_key: str):
    msg    = await update.message.reply_text("⏳ Mengambil data earnings...")
    result = await asyncio.get_event_loop().run_in_executor(None, api_check_earnings, api_key)
    status = result.get("_status_code", 0)

    if status == 401 or (status != 200 and "error" in result):
        err = result.get("error", "Unauthorized / API key tidak valid")
        await msg.edit_text(
            f"❌ *Gagal mengambil earnings!*\n\n`{err}`",
            parse_mode="Markdown",
        )
        return

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
    text += "\n_Fee dikumpulkan tiap jam & otomatis ke wallet kamu._"

    await msg.edit_text(text, parse_mode="Markdown")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN tidak ditemukan!")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",    cmd_start))
    app.add_handler(CommandHandler("launch",   cmd_launch))
    app.add_handler(CommandHandler("earnings", cmd_earnings))
    app.add_handler(CommandHandler("stats",    cmd_stats))
    app.add_handler(CommandHandler("help",     cmd_help))
    app.add_handler(CommandHandler("cancel",   cmd_cancel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("🤖 Bot started! Polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
