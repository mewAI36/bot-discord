import discord
from discord import app_commands
from discord.ext import commands
import os, json, asyncio

# ================= CẤU HÌNH =================
TOKEN = "MTQ5MTI3OTU5OTM3NDU2NTQwNg.GDFPVa.2O19JOwvSt5GguMLVeOnPJc-3rof0f4JMbHD9k026"
COOKIE_FILE = "/sdcard/Download/cookie.txt"
SWITCHED_DIR = "/sdcard/Download/Shouko/switched/"
# ============================================

# Nhập tên máy khi khởi động (Ví dụ: mew-1, mew-2...)
print("=== KHỞI ĐỘNG MÁY ===")
MY_NAME = input("Nhập tên máy này (ví dụ mew-1): ").strip()
PREFIX = MY_NAME.split('-')[0] # Lấy "mew"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ {MY_NAME} Đã Online!")

# --- LỆNH CHIA COOKIE (Mỗi máy tự cắt phần của mình) ---
@bot.tree.command(name="put_cookie_all", description="Chia đều cookie cho dàn máy")
async def put_cookie_all(interaction: discord.Interaction, prefix: str, tong_so_may: int, file: discord.Attachment):
    if prefix != PREFIX: return
    await interaction.response.defer(ephemeral=True)
    
    # Chỉ máy số 1 thông báo đang xử lý để tránh spam
    if "-1" in MY_NAME:
        await interaction.followup.send(f"⏳ Đang chia acc cho {tong_so_may} máy...")

    content = (await file.read()).decode("utf-8").splitlines()
    cookies = [c.strip() for c in content if c.strip()]
    
    # Lấy số thứ tự máy từ tên (ví dụ mew-5 -> lấy số 5)
    try:
        my_num = int(MY_NAME.split('-')[1])
    except: return

    avg = len(cookies) // tong_so_may
    start = (my_num - 1) * avg
    end = start + avg if my_num < tong_so_may else len(cookies)
    
    with open(COOKIE_FILE, "w") as f:
        f.write("\n".join(cookies[start:end]) + "\n")
    
    print(f"✅ Đã nhận {len(cookies[start:end])} acc.")

# --- LỆNH LẤY FILE (Gõ 'all' để lấy hết, hoặc gõ đúng tên máy) ---
@bot.tree.command(name="get", description="Lấy acc từ máy")
async def get(interaction: discord.Interaction, target: str):
    # Nếu target là 'all' hoặc đúng tên máy thì mới chạy
    if target != "all" and target != MY_NAME: return
    
    files = os.listdir(SWITCHED_DIR) if os.path.exists(SWITCHED_DIR) else []
    if not files: return # Im lặng nếu không có file

    f_path = os.path.join(SWITCHED_DIR, files[0])
    # Gửi file kèm tên máy để phân biệt
    await interaction.channel.send(content=f"📦 Acc từ **{MY_NAME}**", file=discord.File(f_path, filename=f"{MY_NAME}.txt"))
    
    with open(f_path, "w") as f: f.truncate(0)

# --- LỆNH NẠP SCRIPT CHO CẢ DÀN ---
@bot.tree.command(name="put_script_all", description="Nạp script cho cả dàn")
async def put_script_all(interaction: discord.Interaction, prefix: str, file: discord.Attachment):
    if prefix != PREFIX: return
    
    found = False
    for root, dirs, _ in os.walk("/sdcard/"):
        for d in dirs:
            if d.lower() in ["autoexec", "autoexecute"]:
                await file.save(os.path.join(root, d, file.filename))
                found = True
    if found: print(f"✅ Đã nạp script {file.filename}")

bot.run(TOKEN)

