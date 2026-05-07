import discord
from discord import app_commands
from discord.ext import commands
import os, json, asyncio, zipfile

# --- HỆ THỐNG TOKEN & ĐỊNH DANH ---
TOKEN_PATH = "/sdcard/Download/bot_token.txt"

def get_token():
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "r") as f: return f.read().strip()
    tk = input("🔑 Nhập Token Bot: ").strip()
    with open(TOKEN_PATH, "w") as f: f.write(tk)
    return tk

TOKEN = get_token()
MY_NAME = input("Nhập tên máy (ví dụ mew-1): ").strip()
PREFIX = MY_NAME.split('-')[0]

# --- ĐƯỜNG DẪN FILE ---
COOKIE_FILE = "/sdcard/Download/cookie.txt"
SWITCHED_DIR = "/sdcard/Download/Shouko/switched/"
JSON_CONFIG = "/sdcard/Download/config-change.json"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def count_accs():
    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, "r") as f:
            return len([l for l in f if l.strip()])
    return 0

def find_auto_folders():
    paths = []
    for root, dirs, _ in os.walk("/sdcard/"):
        for d in dirs:
            if d.lower() in ["autoexec", "autoexecute"]:
                paths.append(os.path.join(root, d))
    return list(set(paths))

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ {MY_NAME} ĐÃ ONLINE!")

# --- [1] TOTAL & TOTAL ALL ---
@bot.tree.command(name="total", description="Check lẻ 1 máy")
async def total(interaction: discord.Interaction, id_may: str):
    if id_may != MY_NAME: return
    await interaction.response.send_message(f"📊 **{MY_NAME}**: `{count_accs()}` acc.")

@bot.tree.command(name="total_all", description="Check toàn bộ dàn máy")
async def total_all(interaction: discord.Interaction, prefix: str):
    if prefix != PREFIX: return
    await interaction.channel.send(f"🖥️ **{MY_NAME}**: `{count_accs()}` acc.")

# --- [2] PUT COOKIE ALL (Chia đều, dư dồn máy cuối) ---
@bot.tree.command(name="put_cookie_all", description="Chia đều cookie cho dàn máy")
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
            f.write("\n".join(cookies[start:end]) + "\n")
        print(f"✅ Nhận {len(cookies[start:end])} acc.")
    except: pass

# --- [3] GET ALL (Lấy acc & Xóa file) ---
@bot.tree.command(name="get_all", description="Thu hoạch acc từ tất cả máy")
async def get_all(interaction: discord.Interaction, prefix: str):
    if prefix != PREFIX: return
    if not os.path.exists(SWITCHED_DIR): return
    files = os.listdir(SWITCHED_DIR)
    if not files: return

    f_path = os.path.join(SWITCHED_DIR, files[0])
    await interaction.channel.send(content=f"📦 Acc từ **{MY_NAME}**", file=discord.File(f_path, filename=f"{MY_NAME}.txt"))
    with open(f_path, "w") as f: f.truncate(0)

# --- [4] PUT SCRIPT ALL (Nạp script toàn dàn) ---
@bot.tree.command(name="put_script_all", description="Gửi script vào Autoexec toàn máy")
async def put_script_all(interaction: discord.Interaction, prefix: str, file: discord.Attachment):
    if prefix != PREFIX: return
    folders = find_auto_folders()
    for fld in folders:
        await file.save(os.path.join(fld, file.filename))
    print(f"✅ Đã dán script vào {len(folders)} folder.")

# --- [5] CONFIG CHANGE ALL ---
@bot.tree.command(name="config_all", description="Chỉnh sửa JSON toàn dàn")
async def config_all(interaction: discord.Interaction, prefix: str, god_human: bool = None, level: int = None):
    if prefix != PREFIX: return
    data = {}
    if os.path.exists(JSON_CONFIG):
        with open(JSON_CONFIG, "r") as f: data = json.load(f)
    if god_human is not None: data["god_human"] = god_human
    if level is not None: data["level"] = level
    with open(JSON_CONFIG, "w") as f: json.dump(data, f, indent=4)
    print(f"⚙️ Config Updated!")

bot.run(TOKEN)
