import discord
from discord import app_commands
from discord.ext import commands
import os, json, asyncio, zipfile

# --- HỆ THỐNG QUẢN LÝ TOKEN & ĐỊNH DANH ---
TOKEN_PATH = "/sdcard/Download/bot_token.txt"

def get_token():
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "r") as f:
            return f.read().strip()
    else:
        print("🔑 Lần đầu thiết lập, hãy nhập Token Bot.")
        token = input("Nhập Token: ").strip()
        with open(TOKEN_PATH, "w") as f:
            f.write(token)
        return token

TOKEN = get_token()

print("=== HỆ THỐNG DÀN MÁY MEW-BOT ===")
MY_NAME = input("Nhập định danh máy (ví dụ mew-1): ").strip()
PREFIX = MY_NAME.split('-')[0]

# --- CẤU HÌNH ĐƯỜNG DẪN ---
COOKIE_FILE = "/sdcard/Download/cookie.txt"
SWITCHED_DIR = "/sdcard/Download/Shouko/switched/"
JSON_CONFIG = "/sdcard/Download/config-change.json"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Hàm tìm folder Autoexec/Autoexecute toàn máy
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

# --- [1] PUT COOKIE ALL: CHIA ĐỀU ACC ---
@bot.tree.command(name="put_cookie_all", description="Chia đều cookie cho dàn máy")
async def put_cookie_all(interaction: discord.Interaction, prefix: str, tong_so_may: int, file: discord.Attachment):
    if prefix != PREFIX: return
    await interaction.response.defer(ephemeral=True)
    
    if "-1" in MY_NAME: await interaction.followup.send(f"⏳ Đang chia acc cho {tong_so_may} máy...")

    content = (await file.read()).decode("utf-8").splitlines()
    cookies = [c.strip() for c in content if c.strip()]
    
    try:
        my_num = int(MY_NAME.split('-')[1])
        avg = len(cookies) // tong_so_may
        start = (my_num - 1) * avg
        end = start + avg if my_num < tong_so_may else len(cookies)
        
        with open(COOKIE_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(cookies[start:end]) + "\n")
        print(f"✅ Đã nhận {len(cookies[start:end])} acc.")
    except: pass

# --- [2] PUT SCRIPT ALL: DÒ VÀ DÁN TẤT CẢ ---
@bot.tree.command(name="put_script_all", description="Dò tìm và dán script vào toàn bộ folder Autoexec")
async def put_script_all(interaction: discord.Interaction, prefix: str, file: discord.Attachment):
    if prefix != PREFIX: return
    await interaction.response.defer(ephemeral=True)
    
    folders = find_auto_folders()
    for folder in folders:
        await file.save(os.path.join(folder, file.filename))
    
    print(f"✅ Đã nạp script vào {len(folders)} folder.")
    if "-1" in MY_NAME: await interaction.followup.send(f"✅ Đã nạp xong script cho hệ thống {PREFIX}")

# --- [3] GET ALL: NHẢ ACC VÀ XÓA TRẮNG ---
@bot.tree.command(name="get_all", description="Lấy acc từ tất cả các máy")
async def get_all(interaction: discord.Interaction, prefix: str):
    if prefix != PREFIX: return
    
    if not os.path.exists(SWITCHED_DIR): return
    files = os.listdir(SWITCHED_DIR)
    if not files: return

    f_path = os.path.join(SWITCHED_DIR, files[0])
    await interaction.channel.send(content=f"📦 Acc từ **{MY_NAME}**", file=discord.File(f_path, filename=f"{MY_NAME}.txt"))
    
    with open(f_path, "w") as f: f.truncate(0)

# --- [4] LIST & DELETE SCRIPT ---
@bot.tree.command(name="listscript", description="Xem danh sách script")
async def listscript(interaction: discord.Interaction, id_may: str):
    if id_may != MY_NAME: return
    folders = find_auto_folders()
    msg = f"📂 **Script tại {MY_NAME}:**\n"
    for fld in folders:
        files = os.listdir(fld)
        msg += f"\n`{fld}`:\n" + "\n".join([f"- {f}" for f in files])
    await interaction.response.send_message(msg[:2000])

@bot.tree.command(name="scriptdelete", description="Xóa script cụ thể")
async def scriptdelete(interaction: discord.Interaction, id_may: str, ten_file: str):
    if id_may != MY_NAME: return
    folders = find_auto_folders()
    for fld in folders:
        p = os.path.join(fld, ten_file)
        if os.path.exists(p): os.remove(p)
    await interaction.response.send_message(f"🗑️ Đã xóa `{ten_file}` trên {MY_NAME}")

# --- [5] CONFIG CHANGE ---
@bot.tree.command(name="config_change", description="Chỉnh file JSON")
async def config_change(interaction: discord.Interaction, id_may: str, god_human: bool = None, level: int = None):
    if id_may != MY_NAME: return
    data = {}
    if os.path.exists(JSON_CONFIG):
        with open(JSON_CONFIG, "r") as f: data = json.load(f)
    if god_human is not None: data["god_human"] = god_human
    if level is not None: data["level"] = level
    with open(JSON_CONFIG, "w") as f: json.dump(data, f, indent=4)
    await interaction.response.send_message(f"✅ Đã update JSON cho {MY_NAME}")

# --- [6] RESET TOKEN ---
@bot.tree.command(name="reset_token", description="Xóa token cũ")
async def reset_token(interaction: discord.Interaction):
    if os.path.exists(TOKEN_PATH):
        os.remove(TOKEN_PATH)
        await interaction.response.send_message("🗑️ Đã xóa token. Hãy khởi động lại Termux.")

bot.run(TOKEN)
