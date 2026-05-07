import discord
from discord import app_commands
from discord.ext import commands
import os, json, asyncio

# --- TOKEN & ĐỊNH DANH ---
TOKEN_PATH = "/sdcard/Download/bot_token.txt"

def get_token():
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "r") as f: return f.read().strip()
    tk = input("🔑 Nhập Token Bot: ").strip()
    with open(TOKEN_PATH, "w") as f: f.write(tk)
    return tk

TOKEN = get_token()
MY_NAME = input("Nhập tên máy (mew-1): ").strip()
PREFIX = MY_NAME.split('-')[0]

# --- ĐƯỜNG DẪN ---
COOKIE_FILE = "/sdcard/Download/cookie.txt"
SWITCHED_DIR = "/sdcard/Download/Shouko/switched/"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- HÀM ĐẾM ACC ---
def count_accs():
    c_num = 0
    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, "r") as f:
            c_num = len([l for l in f if l.strip()])
    s_num = 0
    if os.path.exists(SWITCHED_DIR):
        files = [f for f in os.listdir(SWITCHED_DIR) if f.endswith('.txt')]
        if files:
            with open(os.path.join(SWITCHED_DIR, files[0]), "r") as f:
                s_num = len([l for l in f if l.strip()])
    return c_num, s_num

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

# --- [2] TOTAL ALL (BÁO CÁO & TỔNG KẾT KÉP) ---
@bot.tree.command(name="total_all", description="Tổng kết toàn bộ dàn máy")
async def total_all(interaction: discord.Interaction, prefix: str):
    if prefix != PREFIX: return
    c, s = count_accs()
    # Các máy báo cáo lẻ vào kênh
    await interaction.channel.send(f"🖥️ **{MY_NAME}** | 🍪:`{c}` | 📦:`{s}`")

    # Máy Đội trưởng (-1) sẽ tính tổng Grand Total
    if "-1" in MY_NAME:
        await interaction.response.defer(ephemeral=True)
        await asyncio.sleep(7) # Đợi 7 giây để thu thập tin nhắn
        
        t_cookie = 0
        t_switched = 0
        async for msg in interaction.channel.history(limit=100):
            if msg.author == bot.user and "🖥️" in msg.content and prefix in msg.content:
                try:
                    parts = msg.content.split('`')
                    t_cookie += int(parts[1])
                    t_switched += int(parts[3])
                except: continue
        
        embed = discord.Embed(title=f"🏆 TỔNG KẾT DÀN {prefix.upper()}", color=0x00ff00)
        embed.add_field(name="🍪 TỔNG COOKIE", value=f"`{t_cookie}` acc", inline=True)
        embed.add_field(name="📦 TỔNG SWITCHED", value=f"`{t_switched}` acc", inline=True)
        await interaction.channel.send(embed=embed)

# --- [3] PUT COOKIE ALL (CHIA BÀI) ---
@bot.tree.command(name="put_cookie_all", description="Chia đều cookie cho dàn")
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
        with open(COOKIE_FILE, "w") as f:
            f.write("\n".join(cookies[start:end]) + "\n")
        print(f"✅ Nhận {len(cookies[start:end])} acc.")
    except: pass

# --- [4] GET ALL (THU HOẠCH) ---
@bot.tree.command(name="get_all", description="Lấy acc từ tất cả máy")
async def get_all(interaction: discord.Interaction, prefix: str):
    if prefix != PREFIX: return
    if not os.path.exists(SWITCHED_DIR): return
    files = [f for f in os.listdir(SWITCHED_DIR) if f.endswith('.txt')]
    if not files: return
    f_path = os.path.join(SWITCHED_DIR, files[0])
    await interaction.channel.send(content=f"📦 Acc từ **{MY_NAME}**", file=discord.File(f_path, filename=f"{MY_NAME}.txt"))
    with open(f_path, "w") as f: f.truncate(0)

# --- [5] PUT SCRIPT ALL (NẠP SCRIPT) ---
@bot.tree.command(name="put_script_all", description="Nạp script vào Autoexec toàn dàn")
async def put_script_all(interaction: discord.Interaction, prefix: str, file: discord.Attachment):
    if prefix != PREFIX: return
    for root, dirs, _ in os.walk("/sdcard/"):
        for d in dirs:
            if d.lower() in ["autoexec", "autoexecute"]:
                await file.save(os.path.join(root, d, file.filename))

bot.run(TOKEN)

