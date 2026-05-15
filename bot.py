import discord
from discord.ext import commands

import asyncio
import random
import shutil
import tempfile
import time
import zipfile
from pathlib import Path

# ==================================================
# CONFIG
# ==================================================

BASE_DIR = Path("/sdcard/Download")

TOKEN_PATH = BASE_DIR / "bot_token.txt"
NAME_PATH = BASE_DIR / "name.txt"
COOKIE_FILE = BASE_DIR / "cookie.txt"

SWITCHED_DIR = BASE_DIR / "Shouko" / "switched"
AUTOEXEC_DIRS = [Path("/sdcard/Delta/Autoexecute")]

# Cấu hình mới cho hệ thống Output
RESULT_DIR = BASE_DIR / "all_result"
MERGED_FILE = RESULT_DIR / "all_accounts.txt"
FINAL_ZIP = BASE_DIR / "all_result.zip"

REPORT_DELAY = 8
MAX_LINES_PER_FILE = 5000

# ==================================================
# CACHE & UTILS
# ==================================================

REPORT_SESSIONS = {}

def read_text(path: Path, default=""):
    try:
        if path.exists():
            return path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        print(f"[READ ERROR] {e}")
    return default

def write_text(path: Path, data: str):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data, encoding="utf-8")
    except Exception as e:
        print(f"[WRITE ERROR] {e}")

# ==================================================
# LOAD MACHINE INFO
# ==================================================

TOKEN = read_text(TOKEN_PATH).strip()
if not TOKEN:
    TOKEN = input("Nhập token bot: ").strip()
    write_text(TOKEN_PATH, TOKEN)

MY_NAME = read_text(NAME_PATH, "unknown-1").strip()

try:
    PREFIX, MACHINE_ID = MY_NAME.split("-")
    MACHINE_ID = int(MACHINE_ID)
except:
    PREFIX = "unknown"
    MACHINE_ID = 1

# ==================================================
# CORE FUNCTIONS (NEW)
# ==================================================

async def save_result_file(machine_name: str, attachment: discord.Attachment):
    """Lưu attachment từ máy con, giải nén vào folder riêng"""
    machine_dir = RESULT_DIR / machine_name
    machine_dir.mkdir(parents=True, exist_ok=True)

    zip_path = machine_dir / attachment.filename
    await attachment.save(zip_path)

    try:
        # Giải nén vào thư mục của máy đó
        with zipfile.ZipFile(zip_path, "r") as zipf:
            zipf.extractall(machine_dir)
        
        # Xóa file zip sau khi giải nén để tránh rác
        zip_path.unlink(missing_ok=True)
    except Exception as e:
        print(f"[EXTRACT ERROR] {e}")

def merge_all_accounts():
    """Gộp toàn bộ .txt trong các folder machine thành 1 file duy nhất (không trùng)"""
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    all_acc = set()

    # Quét tất cả file .txt trong các thư mục con (loại trừ file tổng)
    for txt in RESULT_DIR.rglob("*.txt"):
        if txt.name == MERGED_FILE.name:
            continue
        try:
            content = txt.read_text(encoding="utf-8", errors="ignore")
            for line in content.splitlines():
                clean_line = line.strip()
                if clean_line:
                    all_acc.add(clean_line)
        except:
            continue

    sorted_acc = sorted(list(all_acc))
    MERGED_FILE.write_text("\n".join(sorted_acc) + "\n", encoding="utf-8")
    return len(sorted_acc)

def make_final_zip():
    """Đóng gói toàn bộ folder all_result thành file zip tổng"""
    if FINAL_ZIP.exists():
        FINAL_ZIP.unlink()

    with zipfile.ZipFile(FINAL_ZIP, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file in RESULT_DIR.rglob("*"):
            if file.is_file() and file.name != FINAL_ZIP.name:
                zipf.write(file, file.relative_to(RESULT_DIR))
    return FINAL_ZIP

# ==================================================
# DISCORD SETUP
# ==================================================

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# (Giữ các hàm count_lines, get_switched_file, count_accounts, split_file, send_large_file từ file cũ...)
def count_lines(path: Path):
    if not path.exists(): return 0
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for line in f if line.strip())
    except: return 0

def get_switched_file():
    if not SWITCHED_DIR.exists(): return None
    files = sorted([x for x in SWITCHED_DIR.iterdir() if x.is_file() and x.suffix == ".txt"])
    return files[0] if files else None

def count_accounts():
    cookie_count = count_lines(COOKIE_FILE)
    switched_file = get_switched_file()
    switched_count = count_lines(switched_file) if switched_file else 0
    return cookie_count, switched_count

def make_machine_data():
    c, s = count_accounts()
    return {"machine": MY_NAME, "cookie": c, "switched": s}

def split_file(path: Path, lines_per_file=MAX_LINES_PER_FILE):
    parts = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    for i in range(0, len(lines), lines_per_file):
        chunk = lines[i:i + lines_per_file]
        chunk_path = path.parent / f"{path.stem}_part_{i // lines_per_file}.txt"
        with open(chunk_path, "w", encoding="utf-8") as out:
            out.writelines(chunk)
        parts.append(chunk_path)
    return parts

def zip_single_file(file_path: Path):
    tmp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
    zip_path = Path(tmp.name)
    tmp.close()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(file_path, arcname=file_path.name)
    return zip_path

async def send_large_file(channel, file_path: Path, title: str):
    if not file_path.exists(): return False
    total = count_lines(file_path)
    if total <= 0: return False
    parts = split_file(file_path)
    for index, part in enumerate(parts, start=1):
        try:
            zip_path = zip_single_file(part)
            await channel.send(
                content=f"📦 {title} | part `{index}/{len(parts)}` | `{count_lines(part)}` acc",
                file=discord.File(zip_path, filename=f"{part.stem}.zip")
            )
            await asyncio.sleep(1)
            zip_path.unlink(missing_ok=True)
            part.unlink(missing_ok=True)
        except Exception as e:
            print(f"[SEND ERROR] {e}")
            return False
    return True

# ==================================================
# EVENTS & COMMANDS
# ==================================================

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ ONLINE: {MY_NAME}")

@bot.event
async def on_message(message: discord.Message):
    if not message.author.bot: return
    content = message.content

    # TỰ ĐỘNG THU THẬP FILE KHI CÁC MÁY CON GỬI LÊN
    if message.attachments and content.startswith("📦"):
        try:
            # Parse tên máy từ format: "📦 farm-1 | part 1..."
            machine_name = content.split("|")[0].replace("📦", "").strip()
            await save_result_file(machine_name, message.attachments[0])
            print(f"📥 Đã lưu và giải nén dữ liệu từ: {machine_name}")
        except Exception as e:
            print(f"Error processing result: {e}")

    # Xử lý các lệnh text-based (TOTAL_REQUEST, PUT_COOKIE, vv.)
    if content.startswith("TOTAL_REQUEST|"):
        _, session_id, prefix = content.split("|")
        if prefix == PREFIX:
            data = make_machine_data()
            await message.channel.send(f"TOTAL_RESPONSE|{session_id}|{data['machine']}|{data['cookie']}|{data['switched']}")

    elif content.startswith("GET_ALL_REQUEST|"):
        _, prefix = content.split("|")
        if prefix == PREFIX:
            sw_file = get_switched_file()
            if sw_file and count_lines(sw_file) > 0:
                await asyncio.sleep(random.randint(1, 10))
                if await send_large_file(message.channel, sw_file, MY_NAME):
                    shutil.move(sw_file, sw_file.with_suffix(".sent"))

    elif content.startswith("TOTAL_RESPONSE|"):
        try:
            _, sid, mac, coo, swi = content.split("|")
            if sid in REPORT_SESSIONS:
                REPORT_SESSIONS[sid][mac] = {"machine": mac, "cookie": int(coo), "switched": int(swi)}
        except: pass

    await bot.process_commands(message)

# LỆNH EXPORT TỔNG HỢP (MỚI)
@bot.tree.command(name="export_all", description="Gộp và xuất toàn bộ kết quả thu thập được")
async def export_all(interaction: discord.Interaction):
    await interaction.response.defer()
    
    try:
        total_acc = merge_all_accounts()
        zip_path = make_final_zip()
        
        await interaction.followup.send(
            content=f"✅ **Tổng hợp hoàn tất!**\n- Tổng số acc (đã lọc trùng): `{total_acc}`\n- Đã đóng gói thư mục `all_result/` vào file zip.",
            file=discord.File(zip_path, filename="all_result_final.zip")
        )
    except Exception as e:
        await interaction.followup.send(f"❌ Lỗi export: {e}")

# (Giữ lại các lệnh /total, /total_all, /put_cookie_all, /get_all từ code cũ của bạn...)
@bot.tree.command(name="total_all", description="Xem tổng quan tất cả máy")
async def total_all(interaction: discord.Interaction, prefix: str):
    if prefix != PREFIX: return
    await interaction.response.defer()
    sid = str(int(time.time() * 1000))
    REPORT_SESSIONS[sid] = {MY_NAME: make_machine_data()}
    await interaction.channel.send(f"TOTAL_REQUEST|{sid}|{prefix}")
    await asyncio.sleep(REPORT_DELAY)
    data = REPORT_SESSIONS.pop(sid, {})
    
    tc, ts, lines = 0, 0, []
    for name in sorted(data.keys()):
        i = data[name]
        tc += i['cookie']; ts += i['switched']
        lines.append(f"🖥️ `{name}`: 🍪 `{i['cookie']}` | 🔁 `{i['switched']}`")

    emb = discord.Embed(title=f"📊 TOTAL ALL [{prefix}]", color=0x2ecc71)
    emb.add_field(name="🍪 COOKIE", value=f"`{tc}`", inline=True)
    emb.add_field(name="🔁 SWITCHED", value=f"`{ts}`", inline=True)
    emb.add_field(name="MACHINES", value="\n".join(lines) if lines else "No data", inline=False)
    await interaction.followup.send(embed=emb)

@bot.tree.command(name="get_all", description="Yêu cầu tất cả máy gửi file về")
async def get_all(interaction: discord.Interaction, prefix: str):
    if prefix != PREFIX: return
    await interaction.response.defer()
    await interaction.channel.send(f"GET_ALL_REQUEST|{prefix}")
    await interaction.followup.send("📦 Đã phát lệnh thu thập đến tất cả máy. Chờ bot tự động tải về...")

bot.run(TOKEN, reconnect=True)
