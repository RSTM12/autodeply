"""
ClawPump Telegram Bot
- Auto detect cpk_ → launch
- Earnings: auto-detect agentId via /api/agent/portfolio (tanpa input apapun)
- 20 tema x 5 bg x 13 dekorasi x 5 badge
"""

import os
import math
import random
import asyncio
import requests
import logging
import time
import numpy as np
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
import stem
import stem.control

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ─── Config ────────────────────────────────────────────────────────────────────
load_dotenv()
BOT_TOKEN     = os.getenv("BOT_TOKEN")
ACCESS_CODE   = os.getenv("ACCESS_CODE", "CLAWPUMP2024")
CLAWPUMP_BASE = "https://clawpump.tech"

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── Token data ────────────────────────────────────────────────────────────────
ADJECTIVES = [
    "Cosmic","Lunar","Solar","Quantum","Cyber","Digital","Neon","Turbo",
    "Ultra","Mega","Alpha","Nova","Stellar","Atomic","Hyper","Super",
    "Galactic","Mystic","Shadow","Phantom","Blazing","Frozen","Ancient",
    "Electric","Thunder","Silent","Golden","Crystal","Crimson","Emerald",
]
NOUNS = [
    "Ape","Cat","Dog","Fox","Wolf","Bear","Eagle","Shark","Dragon","Tiger",
    "Lion","Panda","Rocket","Moon","Star","Gem","Gold","Diamond","Crystal",
    "Phoenix","Cobra","Hawk","Rhino","Whale","Panther","Viper","Jaguar",
    "Titan","Oracle","Spectre",
]
SUFFIXES = ["", " DAO", " Finance", " Protocol", " Network", "", " Labs", " X"]
DESCRIPTIONS = [
    "The ultimate {adj} {noun} token on Solana. Join the revolution and ride the wave to the moon!",
    "{name} is the next-gen meme token powering the {adj_lower} economy on Solana.",
    "Ride the wave with {name} — the {noun_lower} that the crypto world has been waiting for!",
    "Built by degens, for degens. {name} is here to take over the Solana ecosystem.",
    "{name}: Where {adj_lower} meets DeFi. The future is {noun_lower}.",
    "The most {adj_lower} token on Solana. {name} combines community, memes, and real utility.",
    "🚀 {name} launching on pump.fun. Be early, be {adj_lower}, be legendary.",
    "From the depths of the {adj_lower} universe comes {name}. The {noun_lower} revolution starts now.",
    "{name} is not just a token — it's a movement. Join the {noun_lower} believers on Solana.",
    "Why settle for ordinary? {name} brings {adj_lower} energy to every trade on pump.fun.",
]

THEMES = [
    {"name":"fire",     "bg1":(40,5,0),   "bg2":(80,10,0),  "colors":[(255,80,0),(255,200,0),(220,30,0),(255,140,50),(200,60,0)]},
    {"name":"ocean",    "bg1":(0,8,40),   "bg2":(0,20,80),  "colors":[(0,150,255),(0,255,210),(40,90,200),(100,210,255),(0,180,180)]},
    {"name":"forest",   "bg1":(5,25,5),   "bg2":(10,50,10), "colors":[(0,200,60),(120,190,0),(40,160,40),(180,255,80),(0,140,70)]},
    {"name":"purple",   "bg1":(15,0,30),  "bg2":(30,0,60),  "colors":[(180,0,255),(255,0,180),(120,0,220),(255,80,255),(100,0,180)]},
    {"name":"gold",     "bg1":(20,12,0),  "bg2":(45,28,0),  "colors":[(255,210,0),(255,165,0),(210,140,0),(255,235,80),(180,130,0)]},
    {"name":"cyber",    "bg1":(0,18,18),  "bg2":(0,35,35),  "colors":[(0,255,200),(0,210,255),(40,255,140),(0,255,120),(50,200,200)]},
    {"name":"sunset",   "bg1":(28,5,18),  "bg2":(60,10,35), "colors":[(255,90,40),(200,40,100),(255,160,0),(160,0,110),(255,60,80)]},
    {"name":"ice",      "bg1":(5,14,28),  "bg2":(10,28,55), "colors":[(140,215,255),(200,240,255),(90,175,255),(225,248,255),(100,190,240)]},
    {"name":"lava",     "bg1":(30,0,0),   "bg2":(65,5,0),   "colors":[(255,50,0),(255,120,0),(200,0,0),(255,180,0),(150,0,0)]},
    {"name":"mint",     "bg1":(0,22,18),  "bg2":(0,45,32),  "colors":[(0,255,180),(80,255,200),(0,200,150),(150,255,220),(0,230,160)]},
    {"name":"rose",     "bg1":(28,5,15),  "bg2":(55,10,28), "colors":[(255,80,120),(255,150,180),(200,40,80),(255,200,210),(180,20,80)]},
    {"name":"matrix",   "bg1":(0,12,0),   "bg2":(0,25,0),   "colors":[(0,255,0),(0,200,0),(50,255,50),(0,180,0),(100,255,100)]},
    {"name":"toxic",    "bg1":(5,20,0),   "bg2":(15,40,5),  "colors":[(100,255,0),(180,255,0),(50,200,0),(220,255,50),(0,180,0)]},
    {"name":"blood",    "bg1":(20,0,0),   "bg2":(45,0,0),   "colors":[(200,0,0),(255,0,50),(150,0,0),(255,50,50),(180,20,0)]},
    {"name":"space",    "bg1":(0,0,15),   "bg2":(5,0,35),   "colors":[(100,0,255),(0,100,255),(50,0,200),(200,100,255),(0,150,255)]},
    {"name":"arctic",   "bg1":(8,15,25),  "bg2":(15,28,50), "colors":[(200,230,255),(150,200,255),(255,255,255),(180,210,240),(120,180,255)]},
    {"name":"desert",   "bg1":(35,22,5),  "bg2":(65,42,10), "colors":[(255,180,80),(220,140,50),(255,220,100),(200,120,30),(255,200,120)]},
    {"name":"neon",     "bg1":(5,0,12),   "bg2":(12,0,22),  "colors":[(255,0,255),(0,255,255),(255,255,0),(0,255,0),(255,0,128)]},
    {"name":"volcano",  "bg1":(25,5,0),   "bg2":(55,10,0),  "colors":[(255,100,0),(255,60,0),(200,40,0),(255,180,50),(150,20,0)]},
    {"name":"electric", "bg1":(0,5,20),   "bg2":(5,10,40),  "colors":[(0,200,255),(100,220,255),(0,150,255),(50,255,200),(0,180,200)]},
]

# ─── Image helpers ─────────────────────────────────────────────────────────────

def make_gradient(w,h,c1,c2,direction="vertical"):
    c1=np.array(c1,dtype=np.float32); c2=np.array(c2,dtype=np.float32)
    if direction=="vertical":
        t=np.linspace(0,1,h)[:,None,None]; arr=np.broadcast_to(c1*(1-t)+c2*t,(h,w,3)).copy()
    elif direction=="horizontal":
        t=np.linspace(0,1,w)[None,:,None]; arr=np.broadcast_to(c1*(1-t)+c2*t,(h,w,3)).copy()
    elif direction=="diagonal":
        ty=np.linspace(0,1,h)[:,None]; tx=np.linspace(0,1,w)[None,:]
        t=((ty+tx)/2)[:,:,None]; arr=c1*(1-t)+c2*t
    else:
        yy,xx=np.mgrid[0:h,0:w]; r=np.sqrt((xx-w//2)**2+(yy-h//2)**2)
        t=np.clip(r/math.sqrt((w//2)**2+(h//2)**2),0,1)[:,:,None]; arr=c1*(1-t)+c2*t
    return Image.fromarray(arr.astype(np.uint8))

def make_polygon(cx,cy,r,sides,rotation=0):
    return [(cx+r*math.cos(2*math.pi*i/sides+rotation),cy+r*math.sin(2*math.pi*i/sides+rotation)) for i in range(sides)]

def make_star(cx,cy,r_out,r_in,n=5,rotation=-math.pi/2):
    pts=[]
    for i in range(n*2):
        r=r_out if i%2==0 else r_in; a=math.pi*i/n+rotation
        pts.append((cx+r*math.cos(a),cy+r*math.sin(a)))
    return pts

def draw_badge(draw,shape,cx,cy,r,fill):
    if shape=="circle": draw.ellipse([cx-r,cy-r,cx+r,cy+r],fill=fill)
    elif shape=="hexagon": draw.polygon(make_polygon(cx,cy,r,6,math.pi/6),fill=fill)
    elif shape=="diamond": draw.polygon(make_polygon(cx,cy,r,4,0),fill=fill)
    elif shape=="shield": draw.polygon(make_polygon(cx,cy-8,r,5,-math.pi/2),fill=fill)
    elif shape=="rounded_rect": draw.rounded_rectangle([cx-r,cy-r,cx+r,cy+r],radius=35,fill=fill)

def draw_outlined_text(draw,xy,text,font,fill,outline):
    x,y=xy
    for dx in [-2,-1,0,1,2]:
        for dy in [-2,-1,0,1,2]:
            if dx!=0 or dy!=0: draw.text((x+dx,y+dy),text,font=font,fill=outline)
    draw.text((x,y),text,font=font,fill=fill)

def generate_token_data():
    adj=random.choice(ADJECTIVES); noun=random.choice(NOUNS); suffix=random.choice(SUFFIXES)
    name=f"{adj} {noun}{suffix}"
    symbol=(adj[:3]+noun[:1]).upper() if random.random()>0.5 else (adj[:2]+noun[:2]).upper()
    desc=random.choice(DESCRIPTIONS).format(adj=adj,noun=noun,name=name,adj_lower=adj.lower(),noun_lower=noun.lower())
    return {"name":name,"symbol":symbol,"description":desc}

def generate_token_image(name,symbol):
    SIZE=500; theme=random.choice(THEMES); colors=theme["colors"]
    bg_style=random.choice(["solid","vertical","horizontal","diagonal","radial"])
    img=Image.new("RGB",(SIZE,SIZE),theme["bg1"]) if bg_style=="solid" else make_gradient(SIZE,SIZE,theme["bg1"],theme["bg2"],direction=bg_style)
    draw=ImageDraw.Draw(img)
    style=random.choice(["circles","polygons","stars","burst","mosaic","rings","hex_grid","stripes","confetti","waves","lightning","triangles","mixed"])
    if style=="circles":
        for _ in range(random.randint(8,15)):
            cx=random.randint(-40,SIZE+40);cy=random.randint(-40,SIZE+40);r=random.randint(20,160)
            draw.ellipse([cx-r,cy-r,cx+r,cy+r],fill=random.choice(colors))
    elif style=="polygons":
        for _ in range(random.randint(7,12)):
            cx,cy=random.randint(10,SIZE-10),random.randint(10,SIZE-10)
            draw.polygon(make_polygon(cx,cy,random.randint(35,130),random.choice([3,4,5,6,8]),random.uniform(0,math.pi)),fill=random.choice(colors))
    elif style=="stars":
        for _ in range(random.randint(5,9)):
            cx,cy=random.randint(30,SIZE-30),random.randint(30,SIZE-30)
            r_o=random.randint(45,130);r_i=r_o//random.randint(2,4)
            draw.polygon(make_star(cx,cy,r_o,r_i,random.choice([4,5,6,8]),random.uniform(0,math.pi)),fill=random.choice(colors))
    elif style=="burst":
        cx,cy=SIZE//2,SIZE//2;n=random.randint(16,36)
        for i in range(n):
            a=2*math.pi*i/n;l=random.randint(100,245)
            draw.line([(cx,cy),(cx+l*math.cos(a),cy+l*math.sin(a))],fill=random.choice(colors),width=random.randint(3,20))
    elif style=="mosaic":
        cell=random.choice([50,65,80,100])
        for row in range(SIZE//cell+2):
            for col in range(SIZE//cell+2):
                if random.random()>0.3:
                    x=col*cell-cell//2;y=row*cell-cell//2;sz=random.randint(cell//3,cell*2//3);c=random.choice(colors)
                    sh=random.choice(["rect","circle","tri"])
                    if sh=="rect": draw.rectangle([x,y,x+sz,y+sz],fill=c)
                    elif sh=="circle": draw.ellipse([x,y,x+sz,y+sz],fill=c)
                    else: draw.polygon([(x,y+sz),(x+sz//2,y),(x+sz,y+sz)],fill=c)
    elif style=="rings":
        cx,cy=SIZE//2,SIZE//2;step=random.randint(25,50)
        for r in range(230,0,-step): draw.ellipse([cx-r,cy-r,cx+r,cy+r],outline=random.choice(colors),width=random.randint(6,22))
    elif style=="hex_grid":
        r=random.randint(28,55);h_dist=r*math.sqrt(3);v_dist=r*1.5;row_i=0;y=float(-r)
        while y<SIZE+r:
            x=-r+(h_dist/2 if row_i%2 else 0)
            while x<SIZE+r:
                if random.random()>0.2: draw.polygon(make_polygon(x,y,r-2,6,math.pi/6),fill=random.choice(colors))
                x+=h_dist
            y+=v_dist;row_i+=1
    elif style=="stripes":
        angle=random.choice([0,45,90,135]);width=random.randint(18,60);gap=random.randint(5,30);step=width+gap
        if angle==0:
            y=-width
            while y<SIZE+width: draw.rectangle([0,y,SIZE,y+width],fill=random.choice(colors));y+=step
        elif angle==90:
            x=-width
            while x<SIZE+width: draw.rectangle([x,0,x+width,SIZE],fill=random.choice(colors));x+=step
        elif angle==45:
            for i in range(-SIZE,SIZE*2,step): draw.polygon([(i,0),(i+width,0),(i+width+SIZE,SIZE),(i+SIZE,SIZE)],fill=random.choice(colors))
        else:
            for i in range(-SIZE,SIZE*2,step): draw.polygon([(i,SIZE),(i+width,SIZE),(i+width-SIZE,0),(i-SIZE,0)],fill=random.choice(colors))
    elif style=="confetti":
        for _ in range(random.randint(60,110)):
            cx=random.randint(0,SIZE);cy=random.randint(0,SIZE);c=random.choice(colors);sz=random.randint(5,28)
            sh=random.choice(["circle","rect","line"])
            if sh=="circle": draw.ellipse([cx,cy,cx+sz,cy+sz],fill=c)
            elif sh=="rect": draw.polygon(make_polygon(cx,cy,sz,4,random.uniform(0,math.pi)),fill=c)
            else:
                a=random.uniform(0,math.pi);l=random.randint(10,38)
                draw.line([(cx,cy),(cx+l*math.cos(a),cy+l*math.sin(a))],fill=c,width=random.randint(2,6))
    elif style=="waves":
        for _ in range(random.randint(5,12)):
            c=random.choice(colors);y_base=random.randint(40,SIZE-40);amp=random.randint(12,65)
            freq=random.uniform(0.008,0.045);phase=random.uniform(0,math.pi*2)
            pts=[(x,int(y_base+amp*math.sin(freq*x+phase))) for x in range(0,SIZE+1,3)]
            draw.line(pts,fill=c,width=random.randint(4,20))
    elif style=="lightning":
        for _ in range(random.randint(3,7)):
            c=random.choice(colors);x=random.randint(60,SIZE-60);y=0;pts=[(x,y)]
            while y<SIZE:
                x=max(10,min(SIZE-10,x+random.randint(-45,45)));y+=random.randint(30,85);pts.append((x,y))
            draw.line(pts,fill=c,width=random.randint(3,12))
    elif style=="triangles":
        sz=random.randint(55,100)
        for row in range(SIZE//sz+2):
            for col in range(SIZE*2//sz+2):
                x=col*sz//2-sz//2;y=row*sz-sz//2
                if random.random()>0.3:
                    c=random.choice(colors)
                    pts=[(x,y+sz),(x+sz//2,y),(x+sz,y+sz)] if (col+row)%2==0 else [(x,y),(x+sz,y),(x+sz//2,y+sz)]
                    draw.polygon(pts,fill=c)
    elif style=="mixed":
        for _ in range(random.randint(8,14)):
            cx,cy=random.randint(20,SIZE-20),random.randint(20,SIZE-20);c=random.choice(colors)
            sh=random.choice(["circle","polygon","star","line"])
            if sh=="circle":
                r=random.randint(20,110);draw.ellipse([cx-r,cy-r,cx+r,cy+r],fill=c)
            elif sh=="polygon":
                draw.polygon(make_polygon(cx,cy,random.randint(30,100),random.choice([3,4,5,6]),random.uniform(0,math.pi)),fill=c)
            elif sh=="star":
                r=random.randint(35,100);draw.polygon(make_star(cx,cy,r,r//2,random.choice([4,5,6])),fill=c)
            else:
                a=random.uniform(0,math.pi);l=random.randint(50,160)
                draw.line([(cx,cy),(cx+l*math.cos(a),cy+l*math.sin(a))],fill=c,width=random.randint(5,22))

    badge_shape=random.choice(["circle","hexagon","diamond","shield","rounded_rect"])
    ring_color=random.choice(colors);badge_r=158
    draw_badge(draw,badge_shape,SIZE//2,SIZE//2,badge_r+14,ring_color)
    badge_bg=tuple(max(c-15,0) for c in theme["bg1"])
    draw_badge(draw,badge_shape,SIZE//2,SIZE//2,badge_r,badge_bg)
    font_size=72 if len(symbol)<=4 else 56 if len(symbol)<=6 else 44
    try:
        f_big=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",font_size)
        f_sm=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",24)
    except Exception:
        f_big=f_sm=ImageFont.load_default()
    text_fill=random.choice(colors)
    bb=draw.textbbox((0,0),symbol,font=f_big);tw,th=bb[2]-bb[0],bb[3]-bb[1]
    draw_outlined_text(draw,((SIZE-tw)//2,(SIZE-th)//2-22),symbol,f_big,fill=text_fill,outline=badge_bg)
    display_name=name if len(name)<=22 else name[:20]+"…"
    bb2=draw.textbbox((0,0),display_name,font=f_sm);tw2=bb2[2]-bb2[0]
    draw.text(((SIZE-tw2)//2,308),display_name,fill="white",font=f_sm)
    buf=BytesIO();img.save(buf,format="PNG");buf.seek(0)
    return buf


# ─── ClawPump API ──────────────────────────────────────────────────────────────

def api_upload_image(buf):
    try:
        r=requests.post(f"{CLAWPUMP_BASE}/api/upload",files={"image":("token.png",buf,"image/png")},timeout=30)
        d=r.json();return d.get("imageUrl") if d.get("success") else None
    except Exception as e:
        logger.error("Upload: %s",e);return None

# ─── HANYA FUNGSI INI YANG DIUBAH ─────────────────────────────────────────────

def _rotate_tor_ip():
    try:
        with stem.control.Controller.from_port(port=9051) as ctrl:
            ctrl.authenticate()
            ctrl.signal(stem.Signal.NEWNYM)
            time.sleep(5)
        logger.info("TOR: circuit rotated")
        return True
    except Exception as e:
        logger.warning("TOR rotate gagal: %s", e)
        return False

def _tor_ready():
    """Cek apakah TOR SOCKS proxy bisa dipakai"""
    try:
        r = requests.get(
            "https://check.torproject.org/api/ip",
            proxies={"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"},
            timeout=10,
        )
        return r.status_code == 200
    except Exception:
        return False

def api_launch_token(api_key, token, image_url):
    try:
        # Coba pakai TOR dulu
        tor_ok = _rotate_tor_ip()

        if tor_ok and _tor_ready():
            logger.info("Launch via TOR")
            proxy = {
                "http":  "socks5h://127.0.0.1:9050",
                "https": "socks5h://127.0.0.1:9050",
            }
        else:
            # Fallback: langsung tanpa proxy
            logger.warning("TOR tidak ready, fallback ke direct connection")
            proxy = None

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
            proxies=proxy,
            timeout=60,
        )
        d = r.json(); d["_sc"] = r.status_code; return d

    except Exception as e:
        logger.error("api_launch_token: %s", e)
        return {"success": False, "error": str(e), "_sc": 0}

# ─── END FUNGSI YANG DIUBAH ────────────────────────────────────────────────────

def api_get_portfolio(api_key):
    try:
        r=requests.get(
            f"{CLAWPUMP_BASE}/api/agent/portfolio",
            headers={"Authorization":f"Bearer {api_key}"},
            timeout=15,
        )
        d=r.json();d["_sc"]=r.status_code;return d
    except Exception as e:
        return {"error":str(e),"_sc":0}

def api_get_earnings(api_key,agent_id):
    try:
        r=requests.get(
            f"{CLAWPUMP_BASE}/api/fees/earnings",
            params={"agentId":agent_id},
            headers={"Authorization":f"Bearer {api_key}"},
            timeout=20,
        )
        d=r.json();d["_sc"]=r.status_code;return d
    except Exception as e:
        return {"error":str(e),"_sc":0}

def api_get_stats():
    try:
        return requests.get(f"{CLAWPUMP_BASE}/api/stats",timeout=15).json()
    except Exception as e:
        return {"error":str(e)}


# ─── Helpers ───────────────────────────────────────────────────────────────────

def is_authorized(ctx): return ctx.user_data.get("authorized",False)
def set_expecting(ctx,state): ctx.user_data["expecting"]=state
def get_expecting(ctx): return ctx.user_data.get("expecting")

async def reject_unauthorized(update):
    await update.message.reply_text("🚫 *LU MAU NGAPAIN KESINI? MAKSA AMAT*",parse_mode="Markdown")

async def show_menu(update):
    await update.message.reply_text(
        "✅ *Akses diberikan! Selamat datang.*\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📋 *Perintah:*\n"
        "  /launch   — Launch token baru\n"
        "  /earnings — Cek earnings & detail agent\n"
        "  /stats    — Statistik platform\n"
        "  /help     — Bantuan\n"
        "  /cancel   — Batalkan operasi\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "💡 Kirim `cpk_...` langsung → auto launch!\n"
        "💡 /earnings lalu kirim `cpk_...` → auto cek tanpa input ID",
        parse_mode="Markdown",
    )


# ─── Commands ──────────────────────────────────────────────────────────────────

async def cmd_start(update,ctx):
    if is_authorized(ctx): await show_menu(update); return
    set_expecting(ctx,"access_code")
    await update.message.reply_text("🔐 *Masukkan kode akses:*",parse_mode="Markdown")

async def cmd_cancel(update,ctx):
    set_expecting(ctx,None)
    await update.message.reply_text("❌ Dibatalkan.")

async def cmd_launch(update,ctx):
    if not is_authorized(ctx): await reject_unauthorized(update); return
    set_expecting(ctx,None)
    await update.message.reply_text(
        "🔑 *Kirim API key kamu* (`cpk_...`)\n\nBot langsung launch. /cancel untuk batal.",
        parse_mode="Markdown")

async def cmd_earnings(update,ctx):
    if not is_authorized(ctx): await reject_unauthorized(update); return
    set_expecting(ctx,"api_key_earnings")
    await update.message.reply_text(
        "🔑 *Kirim API key kamu* (`cpk_...`)\n\nBot auto-detect agent & tampilkan semua info. /cancel untuk batal.",
        parse_mode="Markdown")

async def cmd_stats(update,ctx):
    if not is_authorized(ctx): await reject_unauthorized(update); return
    set_expecting(ctx,None)
    msg=await update.message.reply_text("⏳ Mengambil statistik...")
    result=await asyncio.get_event_loop().run_in_executor(None,api_get_stats)
    if "error" in result:
        await msg.edit_text(f"❌ Gagal: `{result['error']}`",parse_mode="Markdown");return
    await msg.edit_text(
        f"📊 *ClawPump Platform Stats*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🪙 Total Tokens:   `{result.get('totalTokens',0)}`\n"
        f"🚀 Total Launches: `{result.get('totalLaunches',0)}`\n"
        f"💹 Market Cap:     `${result.get('totalMarketCap',0):,.0f}`\n"
        f"📈 Volume 24h:     `${result.get('totalVolume24h',0):,.0f}`\n"
        f"━━━━━━━━━━━━━━━━━━━━",parse_mode="Markdown")

async def cmd_help(update,ctx):
    if not is_authorized(ctx): await reject_unauthorized(update); return
    set_expecting(ctx,None)
    await update.message.reply_text(
        "🆘 *Panduan ClawPump Bot*\n\n"
        "🚀 *Launch:*\n"
        "  • Ketik /launch → kirim `cpk_...`\n"
        "  • Atau langsung kirim `cpk_...` → auto launch!\n\n"
        "💰 *Cek Earnings:*\n"
        "  • Ketik /earnings → kirim `cpk_...`\n"
        "  • Bot otomatis detect agent & tampilkan detail\n\n"
        "📊 /stats — Statistik platform\n"
        "❌ /cancel — Batalkan\n\n"
        "💡 API key: [clawpump.tech](https://clawpump.tech) → login Google",
        parse_mode="Markdown",disable_web_page_preview=True)


# ─── Message handler ───────────────────────────────────────────────────────────

async def handle_text(update,ctx):
    text=update.message.text.strip()
    expecting=get_expecting(ctx)

    if not is_authorized(ctx):
        if expecting=="access_code":
            if text==ACCESS_CODE:
                ctx.user_data["authorized"]=True
                set_expecting(ctx,None)
                await show_menu(update)
            else:
                await update.message.reply_text("🚫 *LU MAU NGAPAIN KESINI? MAKSA AMAT*",parse_mode="Markdown")
        else:
            await reject_unauthorized(update)
        return

    if text.startswith("cpk_"):
        try: await update.message.delete()
        except Exception: pass
        mode=expecting if expecting=="api_key_earnings" else "launch"
        set_expecting(ctx,None)
        if mode=="api_key_earnings":
            await do_earnings(update,ctx,text)
        else:
            await do_launch(update,ctx,text)
        return

    if not expecting:
        await update.message.reply_text("Kirim `cpk_...` untuk launch, atau /earnings untuk cek earnings.",parse_mode="Markdown")
        return

    if expecting=="api_key_earnings":
        await update.message.reply_text("❌ Format salah. Harus diawali `cpk_`\nCoba lagi atau /cancel",parse_mode="Markdown")


# ─── Launch ────────────────────────────────────────────────────────────────────

async def do_launch(update,ctx,api_key):
    msg=await update.message.reply_text("⏳ *Generating token...*",parse_mode="Markdown")
    token=generate_token_data()
    image_buf=generate_token_image(token["name"],token["symbol"])

    await msg.edit_text(
        f"🎲 *Token Generated!*\n\n"
        f"📋 Name:   `{token['name']}`\n"
        f"🔤 Symbol: `{token['symbol']}`\n"
        f"📝 Desc:   _{token['description']}_\n\n"
        f"⏳ Uploading gambar...",parse_mode="Markdown")

    image_buf.seek(0)
    await update.message.reply_photo(photo=image_buf,caption=f"🖼️ *{token['name']}* (${token['symbol']})",parse_mode="Markdown")

    image_buf.seek(0)
    image_url=await asyncio.get_event_loop().run_in_executor(None,api_upload_image,image_buf)
    if not image_url:
        await msg.edit_text("❌ *Gagal upload gambar!*\nCoba lagi nanti.",parse_mode="Markdown");return

    await msg.edit_text(
        f"✅ Gambar uploaded!\n\n"
        f"⏳ Launching *{token['name']}* ke pump.fun via TOR...\n"
        f"_(10–30 detik)_",parse_mode="Markdown")

    result=await asyncio.get_event_loop().run_in_executor(None,api_launch_token,api_key,token,image_url)
    sc=result.get("_sc",0)

    if result.get("success"):
        mint=result.get("mintAddress","N/A");tx=result.get("txHash","N/A")
        pump_url=result.get("pumpUrl","#");explorer_url=result.get("explorerUrl","#")
        keyboard=InlineKeyboardMarkup([
            [InlineKeyboardButton("🟢 Lihat di Pump.fun",url=pump_url)],
            [InlineKeyboardButton("🔍 Solscan Explorer",url=explorer_url)],
        ])
        await msg.edit_text(
            f"🎉 *Token Berhasil Launch!*\n\n"
            f"📋 Name:   `{token['name']}`\n"
            f"🔤 Symbol: `${token['symbol']}`\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 Mint Address:\n`{mint}`\n\n"
            f"🔗 TX Hash:\n`{tx}`\n\n"
            f"💰 Earn *65% dari setiap trading fee* otomatis!",
            parse_mode="Markdown",reply_markup=keyboard)
    elif sc==429:
        retry=result.get("retryAfterHours","?")
        await msg.edit_text(f"⏳ *Rate Limit!*\n\nCoba lagi dalam *{retry} jam*.",parse_mode="Markdown")
    elif sc==401:
        await msg.edit_text("❌ *API Key tidak valid!*\n\nPastikan API key benar dari clawpump.tech",parse_mode="Markdown")
    elif sc==503:
        sol=result.get("suggestions",{}).get("paymentFallback",{}).get("selfFunded",{}).get("amountSol",0.03)
        await msg.edit_text(f"⚠️ *Gasless Tidak Tersedia*\n\nCoba lagi nanti atau pakai Self-Funded ({sol} SOL).",parse_mode="Markdown")
    elif sc==400:
        await msg.edit_text(f"❌ *Validasi Gagal!*\n\n`{result.get('details',result.get('error',''))}`",parse_mode="Markdown")
    else:
        err=result.get("message") or result.get("error") or "Unknown error"
        await msg.edit_text(f"❌ *Launch Gagal!*\n\nStatus: `{sc}`\nError: `{err}`",parse_mode="Markdown")


# ─── Earnings ──────────────────────────────────────────────────────────────────

async def do_earnings(update,ctx,api_key):
    msg=await update.message.reply_text("🔍 *Auto-detecting agent dari API key...*",parse_mode="Markdown")

    portfolio=await asyncio.get_event_loop().run_in_executor(None,api_get_portfolio,api_key)
    sc=portfolio.get("_sc",0)

    if sc==401:
        await msg.edit_text("❌ *API Key tidak valid!*\n\nPastikan API key benar dari clawpump.tech",parse_mode="Markdown");return
    if sc==0 or "error" in portfolio:
        await msg.edit_text(f"❌ *Gagal connect ke ClawPump!*\n\n`{portfolio.get('error','Connection error')}`",parse_mode="Markdown");return

    agent_id = portfolio.get("agentId") or portfolio.get("agent_id")
    username = portfolio.get("username") or portfolio.get("name") or agent_id
    wallet   = portfolio.get("walletAddress") or portfolio.get("wallet") or "N/A"

    if not agent_id:
        await msg.edit_text(
            f"⚠️ *Agent terdeteksi tapi agentId tidak ditemukan.*\n\n"
            f"Response:\n`{str(portfolio)[:300]}`\n\n"
            f"Hubungi support di [clawpump.tech](https://clawpump.tech)",
            parse_mode="Markdown",disable_web_page_preview=True);return

    await msg.edit_text(f"✅ Agent: `{agent_id}`\n\n⏳ Mengambil earnings...",parse_mode="Markdown")

    earnings=await asyncio.get_event_loop().run_in_executor(None,api_get_earnings,api_key,agent_id)
    esc=earnings.get("_sc",0)

    if esc==401 or (esc!=200 and "error" in earnings):
        await msg.edit_text(f"❌ *Gagal ambil earnings!*\n\n`{earnings.get('error','Error')}`",parse_mode="Markdown");return

    total_earned  = earnings.get("totalEarned",0)
    total_sent    = earnings.get("totalSent",0)
    total_pending = earnings.get("totalPending",0)
    total_held    = earnings.get("totalHeld",0)
    tokens        = earnings.get("tokenBreakdown",[])

    token_lines=""
    for t in tokens[:5]:
        mint=t.get("mintAddress","N/A")
        short=mint[:8]+"..."+mint[-4:] if len(mint)>12 else mint
        share=t.get("totalAgentShare",0)
        collected=t.get("totalCollected",0)
        token_lines+=f"  • `{short}`\n    Collected: `{collected:.4f}` | Kamu: `{share:.4f}` SOL\n"

    wallet_display=f"`{wallet[:16]}...{wallet[-6:]}`" if len(wallet)>22 else f"`{wallet}`"

    text=(
        f"👤 *Detail Agent*\n\n"
        f"🆔 Agent ID: `{agent_id}`\n"
        f"📋 Username: `{username}`\n"
        f"💳 Wallet:   {wallet_display}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 *Earnings*\n\n"
        f"✅ Total Earned:  `{total_earned:.4f} SOL`\n"
        f"📤 Total Sent:    `{total_sent:.4f} SOL`\n"
        f"⏳ Pending:       `{total_pending:.4f} SOL`\n"
        f"🔒 Held:          `{total_held:.4f} SOL`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
    )
    if token_lines:
        text+=f"\n📊 *Token Breakdown ({len(tokens)} token):*\n{token_lines}"
    text+="\n_Fee dikumpulkan tiap jam & otomatis ke wallet kamu._"

    keyboard=InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Dashboard Agent",url=f"https://clawpump.tech/agent/{agent_id}")],
    ])
    await msg.edit_text(text,parse_mode="Markdown",reply_markup=keyboard)


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    if not BOT_TOKEN: raise ValueError("BOT_TOKEN tidak ditemukan!")
    app=Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",    cmd_start))
    app.add_handler(CommandHandler("launch",   cmd_launch))
    app.add_handler(CommandHandler("earnings", cmd_earnings))
    app.add_handler(CommandHandler("stats",    cmd_stats))
    app.add_handler(CommandHandler("help",     cmd_help))
    app.add_handler(CommandHandler("cancel",   cmd_cancel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,handle_text))
    logger.info("🤖 Bot started! Polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__=="__main__":
    main()
