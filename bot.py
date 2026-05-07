import discord
from discord import app_commands
from discord.ext import commands
import os, json, asyncio, datetime

# --- LẤY DATA TỪ FILE ---
TOKEN_PATH = "/sdcard/Download/bot_token.txt"
NAME_PATH = "/sdcard/Download/name.txt"

def get_token():
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "r") as f: return f.read().strip()
    tk = input("🔑 Nhập Token Bot lần đầu: ").strip()
    with open(TOKEN_PATH, "w") as f: f.write(tk)
    return tk

def get_my_name():
    if os.path.exists(NAME_PATH):
        with open(NAME_PATH, "r") as f: return f.read().strip()
    return "unknown-0"

TOKEN = get_token()
MY_NAME = get_my_name()
PREFIX = MY_NAME.split('-')[0]

# --- ĐƯỜNG DẪN ---
COOKIE_FILE = "/sdcard/Download/cookie.txt"
SWITCHED_DIR = "/sdcard/Download/Shouko/switched/"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def count_accs():
    c, s = 0, 0
    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, "r") as f: c = len([l for l in f if l.strip()])
    if os.path.exists(SWITCHED_DIR):
        files = [f for f in os.listdir(SWITCHED_DIR) if f.endswith('.txt')]
        if files:
            with open(os.path.join(SWITCHED_DIR, files[0]), "r") as f: s = len([l for l in f if l.strip()])
    return c, s

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ {MY_NAME} ONLINE!")

# --- [1] TOTAL LẺ ---
@bot.tree.command(name="total", description="Check lẻ 1 máy")
async def total(interaction: discord.Interaction, id_may: str):
    if id_may != MY_NAME: return
    c, s = count_accs()
    await interaction.response.send_message(f"📊 **{MY_NAME}**\n- 🍪 Cookie: `{c}`\n- 📦 Switched: `{s}`")

# --- [2] TOTAL ALL (FIX LỖI CỘNG DỒN ẢO) ---
@bot.tree.command(name="total_all", description="Tổng kết toàn dàn máy")
async def total_all(interaction: discord.Interaction, prefix: str):
    if prefix != PREFIX: return
    
    # Lấy mốc thời gian khi vừa gõ lệnh
    now = datetime.datetime.now(datetime.timezone.utc)
    c, s = count_accs()
    
    # Báo cáo lẻ từng máy
    await interaction.channel.send(f"🖥️ **{MY_NAME}** | 🍪:`{c}` | 📦:`{s}`")
    
    if "-1" in MY_NAME:
        await interaction.response.defer(ephemeral=True)
        await asyncio.sleep(8) # Đợi các máy khác nhắn xong
        
        tc, ts = 0, 0
        # Quét lịch sử tin nhắn
        async for msg in interaction.channel.history(limit=100):
            # CHỈ CỘNG: Tin nhắn của Bot + Chứa icon 🖥️ + Chứa Prefix + Gửi SAU mốc 'now'
            if msg.author == bot.user and "🖥️" in msg.content and prefix in msg.content:
                if msg.created_at >= (now - datetime.timedelta(seconds=5)):
                    try:
                        p = msg.content.split('`')
                        tc += int(p[1])
                        ts += int(p[3])
                    except: continue
        
        embed = discord.Embed(title=f"🏆 TỔNG KẾT DÀN {prefix.upper()}", color=0x2ecc71)
        embed.add_field(name="🍪 TỔNG COOKIE", value=f"`{tc}`", inline=True)
        embed.add_field(name="📦 TỔNG SWITCHED", value=f"`{ts}`", inline=True)
        embed.set_footer(text=f"Cập nhật: {datetime.datetime.now().strftime('%H:%M:%S')}")
        await interaction.channel.send(embed=embed)

# --- [3] CHIA ACC (PUT COOKIE ALL) ---
@bot.tree.command(name="put_cookie_all", description="Chia đều cookie")
async def put_cookie_all(interaction: discord.Interaction, prefix: str, tong_so_may: int, file: discord.Attachment):
    if prefix != PREFIX: return
    await interaction.response.defer(ephemeral=True)
    content = (await file.read()).decode("utf-8").splitlines()
    cookies = [c.strip() for c in content if c.strip()]
    try:
        my_num = int(MY_NAME.split('-')[1])
        avg = len(cookies) // tong_so_may
        start = (my_num - 1) * avg
        end = start + avg if my_num < tong_so_may else len(cookies)
        with open(COOKIE_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(cookies[start:end]))
        print(f"✅ Đã nhận {len(cookies[start:end])} acc.")
    except: pass

# --- [4] THU HOẠCH (GET ALL) ---
@bot.tree.command(name="get_all", description="Lấy file acc đã cày xong")
async def get_all(interaction: discord.Interaction, prefix: str):
    if prefix != PREFIX: return
    if not os.path.exists(SWITCHED_DIR): return
    files = [f for f in os.listdir(SWITCHED_DIR) if f.endswith('.txt')]
    if not files: return
    f_p = os.path.join(SWITCHED_DIR, files[0])
    await interaction.channel.send(content=f"📦 Acc {MY_NAME}", file=discord.File(f_p))
    with open(f_p, "w") as f: f.truncate(0)

# --- [5] NẠP SCRIPT (PUT SCRIPT ALL) ---
@bot.tree.command(name="put_script_all", description="Nạp script toàn dàn")
async def put_script_all(interaction: discord.Interaction, prefix: str, file: discord.Attachment):
    if prefix != PREFIX: return
    for root, dirs, _ in os.walk("/sdcard/"):
        for d in dirs:
            if d.lower() in ["autoexec", "autoexecute"]:
                await file.save(os.path.join(root, d, file.filename))

bot.run(TOKEN)
