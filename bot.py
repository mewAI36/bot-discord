import discord
from discord import app_commands
from discord.ext import commands
import os

# ================= CẤU HÌNH =================
TOKEN = 'MTQ5MTI3OTU5OTM3NDU2NTQwNg.GDFPVa.2O19JOwvSt5GguMLVeOnPJc-3rof0f4JMbHD9k'
MY_ID = 1  # <--- SỬA SỐ NÀY CHO TỪNG MÁY (1-10)

# Đường dẫn mặc định
COOKIE_FILE = "cookie.txt"
AUTOEXEC_PATH = "/sdcard/codex/autoexec/" 
# ============================================

# Cấp quyền và tạo folder nếu chưa có
if not os.path.exists(AUTOEXEC_PATH):
    try:
        os.makedirs(AUTOEXEC_PATH)
    except:
        pass

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print(f"✅ Đã đồng bộ Slash Commands cho Máy {MY_ID}")

bot = MyBot()

@bot.event
async def on_ready():
    print(f'🚀 Bot Máy {MY_ID} đã sẵn sàng!')

# 1. Lệnh /putcookie: Nối thêm nội dung vào cookie.txt
@bot.tree.command(name="putcookie", description="Nối nội dung file gửi lên vào cookie.txt")
@app_commands.describe(id_may="Số máy (1-10)", file="File chứa cookie mới")
async def putcookie(interaction: discord.Interaction, id_may: int, file: discord.Attachment):
    if id_may == MY_ID:
        try:
            content = await file.read()
            text = content.decode('utf-8').strip()
            
            # Mở file cookie.txt ở chế độ Append
            with open(COOKIE_FILE, "a", encoding="utf-8") as f:
                f.write(f"\n{text}")
                
            await interaction.response.send_message(f"✅ [MÁY {MY_ID}] Đã nối thêm nội dung vào `{COOKIE_FILE}`")
        except Exception as e:
            await interaction.response.send_message(f"❌ [MÁY {MY_ID}] Lỗi: {e}")
    else:
        await interaction.response.send_message(f"⏳ Đang đợi Máy {id_may} phản hồi...", ephemeral=True)

# 2. Lệnh /putscript: Lưu file vào autoexec với TÊN FILE GỐC
@bot.tree.command(name="putscript", description="Lưu file vào /delta/autoexec theo tên file gửi")
@app_commands.describe(id_may="Số máy (1-10)", file="File script muốn gửi")
async def putscript(interaction: discord.Interaction, id_may: int, file: discord.Attachment):
    if id_may == MY_ID:
        try:
            # Lấy đúng tên file mày đính kèm trên Discord
            file_name = file.filename 
            full_path = os.path.join(AUTOEXEC_PATH, file_name)
            
            # Lưu file
            await file.save(full_path)
            await interaction.response.send_message(f"🔥 [MÁY {MY_ID}] Đã nạp file `{file_name}` vào `/delta/autoexec/` thành công!")
        except Exception as e:
            await interaction.response.send_message(f"❌ [MÁY {MY_ID}] Lỗi khi lưu script: {e}")
    else:
        await interaction.response.send_message(f"⏳ Đang đợi Máy {id_may} phản hồi...", ephemeral=True)

# 3. Lệnh /get: Lấy file cookie về
@bot.tree.command(name="get", description="Lấy file cookie.txt từ máy cụ thể")
@app_commands.describe(id_may="Số máy (1-10)")
async def get(interaction: discord.Interaction, id_may: int):
    if id_may == MY_ID:
        if os.path.exists(COOKIE_FILE):
            await interaction.response.send_message(content=f"📤 [MÁY {MY_ID}] Gửi lại file `{COOKIE_FILE}`:", file=discord.File(COOKIE_FILE))
        else:
            await interaction.response.send_message(f"❌ [MÁY {MY_ID}] Không tìm thấy file `{COOKIE_FILE}`")
    else:
        await interaction.response.send_message(f"🔍 Đang kiểm tra Máy {id_may}...", ephemeral=True)

bot.run(TOKEN)
