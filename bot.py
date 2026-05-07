import discord
from discord import app_commands
from discord.ext import commands
import os, json, asyncio

# --- QUẢN LÝ TOKEN VÀ ĐỊNH DANH ---
TOKEN_PATH = "/sdcard/Download/bot_token.txt"

def get_token():
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "r") as f:
            return f.read().strip()
    else:
        token = input("🔑 Nhập Token Bot của mày: ").strip()
        with open(TOKEN_PATH, "w") as f:
            f.write(token)
        return token

TOKEN = get_token()

print("=== KHỞI ĐỘNG MÁY ===")
MY_NAME = input("Nhập tên máy này (ví dụ mew-1): ").strip()
PREFIX = MY_NAME.split('-')[0]

# --- CẤU HÌNH ĐƯỜNG DẪN ---
COOKIE_FILE = "/sdcard/Download/cookie.txt"
SWITCHED_DIR = "/sdcard/Download/Shouko/switched/"
# ==============================

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ {MY_NAME} Đã Online với Token: {TOKEN[:10]}...")

# --- LỆNH CHIA COOKIE ---
@bot.tree.command(name="put_cookie_all", description="Chia đều cookie cho dàn máy")
async def put_cookie_all(interaction: discord.Interaction, prefix: str, tong_so_may: int, file: discord.Attachment):
    if prefix != PREFIX: return
    await interaction.response.defer(ephemeral=True)
    
    if "-1" in MY_NAME:
        await interaction.followup.send(f"⏳ Đang chia acc cho {tong_so_may} máy...")

    try:
        content = (await file.read()).decode("utf-8").splitlines()
        cookies = [c.strip() for c in content if c.strip()]
        my_num = int(MY_NAME.split('-')[1])
        
        avg = len(cookies) // tong_so_may
        start = (my_num - 1) * avg
        end = start + avg if my_num < tong_so_may else len(cookies)
        
        with open(COOKIE_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(cookies[start:end]) + "\n")
        print(f"✅ Đã nhận {len(cookies[start:end])} acc.")
    except Exception as e:
        print(f"❌ Lỗi chia cookie: {e}")

# --- LỆNH GET ---
@bot.tree.command(name="get", description="Lấy acc từ máy")
async def get(interaction: discord.Interaction, target: str):
    if target != "all" and target != MY_NAME: return
    
    if not os.path.exists(SWITCHED_DIR): return
    files = os.listdir(SWITCHED_DIR)
    if not files: return

    f_path = os.path.join(SWITCHED_DIR, files[0])
    await interaction.channel.send(content=f"📦 Acc từ **{MY_NAME}**", file=discord.File(f_path, filename=f"{MY_NAME}.txt"))
    with open(f_path, "w") as f: f.truncate(0)

# --- LỆNH RESET TOKEN (Phòng khi mày nhập sai) ---
@bot.tree.command(name="reset_token", description="Xóa token cũ để nhập lại")
async def reset_token(interaction: discord.Interaction):
    if os.path.exists(TOKEN_PATH):
        os.remove(TOKEN_PATH)
        await interaction.response.send_message("✅ Đã xóa Token cũ. Hãy khởi động lại Bot để nhập mới.")
    else:
        await interaction.response.send_message("❌ Không tìm thấy file lưu Token.")

bot.run(TOKEN)
