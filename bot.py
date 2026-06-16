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

REPORT_DELAY = 8
MAX_LINES_PER_FILE = 5000

RESULT_KEEP_LATEST = 1
RESULT_DIR = BASE_DIR / "all_result"
MERGED_FILE = RESULT_DIR / "all_accounts.txt"
FINAL_ZIP = BASE_DIR / "all_result.zip"

# ==================================================
# CACHE
# ==================================================
REPORT_SESSIONS = {}

# ==================================================
# THAO TÁC FILE (CHẠY NỀN TRÁNH ĐƠ BOT)
# ==================================================
def read_text_sync(path: Path, default=""):
    try:
        if path.exists():
            return path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        print(f"[READ ERROR] {e}")
    return default

def write_text_sync(path: Path, data: str):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data, encoding="utf-8")
    except Exception as e:
        print(f"[WRITE ERROR] {e}")

def count_lines(path: Path):
    if not path.exists():
        return 0
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for line in f if line.strip())
    except:
        return 0

def get_switched_files():
    if not SWITCHED_DIR.exists():
        return []
    return sorted([x for x in SWITCHED_DIR.iterdir() if x.is_file() and x.suffix == ".txt"])

def count_accounts():
    cookie_count = count_lines(COOKIE_FILE)
    switched_count = sum(count_lines(f) for f in get_switched_files())
    return cookie_count, switched_count

def make_machine_data():
    cookie_count, switched_count = count_accounts()
    return {"machine": MY_NAME, "cookie": cookie_count, "switched": switched_count}

def split_file_sync(path: Path, lines_per_file=MAX_LINES_PER_FILE):
    parts = []
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        for i in range(0, len(lines), lines_per_file):
            chunk = lines[i:i + lines_per_file]
            chunk_path = path.parent / f"{path.stem}_part_{i // lines_per_file}.txt"
            with open(chunk_path, "w", encoding="utf-8") as out:
                out.writelines(chunk)
            parts.append(chunk_path)
    except Exception as e:
        print(f"[SPLIT ERROR] {e}")
    return parts

def zip_single_file_sync(file_path: Path):
    tmp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
    zip_path = Path(tmp.name)
    tmp.close()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(file_path, arcname=file_path.name)
    return zip_path

def extract_and_cleanup_sync(zip_path: Path, extract_dir: Path):
    try:
        extract_dir.mkdir(exist_ok=True, parents=True)
        with zipfile.ZipFile(zip_path, "r") as zipf:
            zipf.extractall(extract_dir)
        zip_path.unlink(missing_ok=True)
    except Exception as e:
        print(f"[EXTRACT ERROR] {e}")

def get_autoexec_files_sync():
    files = []
    for path in AUTOEXEC_DIRS:
        if path.exists() and path.is_dir():
            for f in path.iterdir():
                if f.is_file():
                    files.append(f.name)
    return files

def delete_autoexec_file_sync(filename: str):
    deleted = 0
    for path in AUTOEXEC_DIRS:
        target = path / filename
        if target.exists() and target.is_file():
            try:
                target.unlink()
                deleted += 1
            except Exception as e:
                print(f"[DELETE SCRIPT ERROR] {e}")
    return deleted

def merge_all_accounts_sync():
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    global_merged_map = {}
    processed_files = []
    
    for machine_dir in RESULT_DIR.iterdir():
        if not machine_dir.is_dir(): continue
        
        machine_name = machine_dir.name
        machine_merged_map = {} # Chứa acc gộp TÁCH RIÊNG cho máy này
        
        request_dirs = sorted([x for x in machine_dir.iterdir() if x.is_dir()], key=lambda x: x.stat().st_mtime, reverse=True)
        for request_dir in request_dirs[:RESULT_KEEP_LATEST]:
            # CHỈ lấy file .txt chưa xử lý (bỏ qua .done)
            for txt in request_dir.rglob("*.txt"):
                try:
                    file_key = txt.stem
                    
                    if file_key not in global_merged_map:
                        global_merged_map[file_key] = set()
                    if file_key not in machine_merged_map:
                        machine_merged_map[file_key] = set()
                        
                    content = txt.read_text(encoding="utf-8", errors="ignore")
                    lines = [line.strip() for line in content.splitlines() if line.strip()]
                    
                    # Nạp data vào cả 2 map (Của riêng máy và của hệ thống)
                    global_merged_map[file_key].update(lines)
                    machine_merged_map[file_key].update(lines)
                    
                    processed_files.append(txt) # Đưa vào danh sách chờ đổi tên
                except:
                    pass

        # GHI FILE GỘP CHO TỪNG MÁY
        for file_key, accounts in machine_merged_map.items():
            machine_out_file = machine_dir / f"all_{file_key}.txt"
            
            old_accounts = set()
            if machine_out_file.exists():
                old_content = machine_out_file.read_text(encoding="utf-8", errors="ignore")
                old_accounts.update(line.strip() for line in old_content.splitlines() if line.strip())
                
            old_accounts.update(accounts)
            machine_out_file.write_text("\n".join(sorted(old_accounts)) + "\n", encoding="utf-8")

    # GHI FILE GỘP CHUNG CHO TOÀN BỘ HỆ THỐNG
    total_new = 0
    for file_key, accounts in global_merged_map.items():
        global_out_file = RESULT_DIR / f"all_{file_key}.txt"
        
        old_accounts = set()
        if global_out_file.exists():
            old_content = global_out_file.read_text(encoding="utf-8", errors="ignore")
            old_accounts.update(line.strip() for line in old_content.splitlines() if line.strip())
            
        old_accounts.update(accounts)
        global_out_file.write_text("\n".join(sorted(old_accounts)) + "\n", encoding="utf-8")
        total_new += len(accounts)

    # DỌN DẸP: Đổi tên file gốc thành .done
    for txt in processed_files:
        try:
            txt.rename(txt.with_suffix(".done"))
        except Exception as e:
            print(f"[RENAME ERROR] {e}")
            
    return total_new

def make_final_zip_sync():
    if FINAL_ZIP.exists():
        FINAL_ZIP.unlink()
        
    with zipfile.ZipFile(FINAL_ZIP, "w", zipfile.ZIP_DEFLATED) as zipf:
        
        # 1. Nén các file gộp CHUNG (nằm ở thư mục gốc)
        for file in RESULT_DIR.glob("all_*.txt"):
            zipf.write(file, arcname=file.name)
            
        # 2. Nén các file gộp RIÊNG, tạo folder cho từng máy trong zip
        for machine_dir in RESULT_DIR.iterdir():
            if not machine_dir.is_dir(): continue
            
            # Lấy các file gộp của máy đó
            for file in machine_dir.glob("all_*.txt"):
                # Tham số arcname dạng "mew-1/all_switched.txt" sẽ tự tạo folder trong file zip
                zip_path = f"{machine_dir.name}/{file.name}"
                zipf.write(file, arcname=zip_path)
                
    return FINAL_ZIP

# ==================================================
# ASYNC HELPERS
# ==================================================
async def send_large_file(channel, file_path: Path, title: str):
    if not file_path.exists():
        return False
    
    total = await asyncio.to_thread(count_lines, file_path)
    if total <= 0:
        return False

    parts = await asyncio.to_thread(split_file_sync, file_path)

    for index, part in enumerate(parts, start=1):
        try:
            zip_path = await asyncio.to_thread(zip_single_file_sync, part)
            await channel.send(
                content=f"📦 {title} | part `{index}/{len(parts)}` | `{await asyncio.to_thread(count_lines, part)}` acc",
                file=discord.File(zip_path, filename=f"{part.stem}.zip")
            )
            await asyncio.sleep(1)

            await asyncio.to_thread(zip_path.unlink, missing_ok=True)
            await asyncio.to_thread(part.unlink, missing_ok=True)
        except Exception as e:
            print(f"[SEND ERROR] {e}")
            return False
    return True

async def save_result_file(machine_name: str, attachment: discord.Attachment):
    machine_dir = RESULT_DIR / machine_name
    machine_dir.mkdir(parents=True, exist_ok=True)

    old_dirs = sorted([x for x in machine_dir.iterdir() if x.is_dir()], key=lambda x: x.stat().st_mtime, reverse=True)
    for old in old_dirs[RESULT_KEEP_LATEST:]:
        try:
            await asyncio.to_thread(shutil.rmtree, old, ignore_errors=True)
        except:
            pass

    zip_path = machine_dir / attachment.filename
    await attachment.save(zip_path)

    extract_name = f"{int(time.time())}_{attachment.filename.replace('.zip', '')}"
    extract_dir = machine_dir / extract_name
    
    await asyncio.to_thread(extract_and_cleanup_sync, zip_path, extract_dir)

# ==================================================
# LOAD MACHINE
# ==================================================
TOKEN = read_text_sync(TOKEN_PATH).strip()
if not TOKEN:
    TOKEN = input("Nhập token bot: ").strip()
    write_text_sync(TOKEN_PATH, TOKEN)

MY_NAME = read_text_sync(NAME_PATH, "unknown-1").strip()
try:
    PREFIX, MACHINE_ID = MY_NAME.split("-")
    MACHINE_ID = int(MACHINE_ID)
except:
    PREFIX = "unknown"
    MACHINE_ID = 1

# ==================================================
# DISCORD
# ==================================================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, heartbeat_timeout=120)

@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
    except Exception as e:
        print(f"[SYNC ERROR] {e}")
    print(f"✅ ONLINE: {MY_NAME}")

@bot.event
async def on_message(message: discord.Message):
    if not message.author.bot:
        return
    content = message.content

    if message.attachments and content.startswith("📦"):
        try:
            machine_name = content.split("|")[0].replace("📦", "").strip()
            await save_result_file(machine_name, message.attachments[0])
        except Exception as e:
            print(f"[ATTACHMENT ERROR] {e}")

    elif content.startswith("TOTAL_REQUEST|"):
        try:
            _, session_id, prefix = content.split("|")
            if prefix == PREFIX:
                data = await asyncio.to_thread(make_machine_data)
                await message.channel.send(f"TOTAL_RESPONSE|{session_id}|{data['machine']}|{data['cookie']}|{data['switched']}")
        except Exception as e:
            print(f"[TOTAL_REQ ERROR] {e}")

    elif content.startswith("PUT_COOKIE|"):
        try:
            _, prefix, machine_name = content.split("|")
            if prefix == PREFIX and machine_name == MY_NAME and message.attachments:
                temp_path = BASE_DIR / f"temp_cookie_{MY_NAME}.txt"
                await message.attachments[0].save(temp_path)
                
                content_str = await asyncio.to_thread(read_text_sync, temp_path)
                cookies = [x.strip() for x in content_str.splitlines() if x.strip()]
                
                all_cookie = set()
                if COOKIE_FILE.exists():
                    old_str = await asyncio.to_thread(read_text_sync, COOKIE_FILE)
                    all_cookie.update(x.strip() for x in old_str.splitlines() if x.strip())
                all_cookie.update(cookies)
                
                await asyncio.to_thread(write_text_sync, COOKIE_FILE, "\n".join(sorted(all_cookie)) + "\n")
                print(f"✅ RECEIVED COOKIE: {MY_NAME}")
                await asyncio.to_thread(temp_path.unlink, missing_ok=True)
        except Exception as e:
            print(f"[PUT_COOKIE ERROR] {e}")

    elif content.startswith("BROADCAST_COOKIE|"):
        try:
            _, prefix = content.split("|")
            if prefix == PREFIX and message.attachments:
                temp_path = BASE_DIR / f"temp_broadcast_{MY_NAME}.txt"
                await message.attachments[0].save(temp_path)
                
                content_str = await asyncio.to_thread(read_text_sync, temp_path)
                my_cookies = []
                
                # Quét file tổng, chỉ lấy những dòng có tiền tố là tên máy của mình
                for line in content_str.splitlines():
                    if line.startswith(f"{MY_NAME}|"):
                        my_cookies.append(line.split("|", 1)[1].strip())
                        
                # Nếu có cookie thuộc về máy này thì tiến hành ghi vào file
                if my_cookies:
                    all_cookie = set()
                    if COOKIE_FILE.exists():
                        old_str = await asyncio.to_thread(read_text_sync, COOKIE_FILE)
                        all_cookie.update(x.strip() for x in old_str.splitlines() if x.strip())
                    
                    all_cookie.update(my_cookies)
                    await asyncio.to_thread(write_text_sync, COOKIE_FILE, "\n".join(sorted(all_cookie)) + "\n")
                    print(f"✅ FILTERED & ADDED {len(my_cookies)} COOKIES TỪ BROADCAST")
                
                await asyncio.to_thread(temp_path.unlink, missing_ok=True)
        except Exception as e:
            print(f"[BROADCAST ERROR] {e}")

    elif content.startswith("PUT_SCRIPT|"):
        try:
            _, prefix = content.split("|")
            if prefix == PREFIX and message.attachments:
                saved = 0
                for path in AUTOEXEC_DIRS:
                    try:
                        await asyncio.to_thread(path.mkdir, parents=True, exist_ok=True)
                        save_path = path / message.attachments[0].filename
                        await message.attachments[0].save(save_path)
                        saved += 1
                    except Exception as e:
                        print(f"[SCRIPT SAVE ERROR] {e}")
                print(f"✅ SCRIPT SAVED {saved}")
        except Exception as e:
            print(f"[PUT_SCRIPT ERROR] {e}")

    elif content.startswith("GET_ALL_REQUEST|"):
        try:
            _, prefix = content.split("|")
            if prefix == PREFIX:
                switched_files = await asyncio.to_thread(get_switched_files)
                if not switched_files:
                    return

                delay = (MACHINE_ID * 4) + random.randint(1, 3)
                await asyncio.sleep(delay)

                for switched_file in switched_files:
                    total = await asyncio.to_thread(count_lines, switched_file)
                    if total > 0:
                        success = await send_large_file(message.channel, switched_file, MY_NAME)
                        if success:
                            backup = switched_file.with_suffix(".sent")
                            try:
                                await asyncio.to_thread(shutil.move, switched_file, backup)
                            except Exception as e:
                                print(f"[MOVE ERROR] {e}")
        except Exception as e:
            print(f"[GET_ALL_REQ ERROR] {e}")

    elif content.startswith("TOTAL_RESPONSE|"):
        try:
            _, session_id, machine, cookie, switched = content.split("|")
            if session_id in REPORT_SESSIONS:
                REPORT_SESSIONS[session_id][machine] = {"machine": machine, "cookie": int(cookie), "switched": int(switched)}
        except Exception as e:
            print(f"[TOTAL_RES ERROR] {e}")

    await bot.process_commands(message)

# ==================================================
# COMMANDS
# ==================================================
@bot.tree.command(name="total", description="Check machine")
async def total(interaction: discord.Interaction, machine: str):
    if machine != MY_NAME:
        return
    cookie_count, switched_count = await asyncio.to_thread(count_accounts)
    embed = discord.Embed(title=f"🖥️ {MY_NAME}", color=0x3498db)
    embed.add_field(name="🍪 Cookie", value=f"`{cookie_count}`", inline=True)
    embed.add_field(name="🔁 Switched", value=f"`{switched_count}`", inline=True)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="total_all", description="Total acc all machine")
async def total_all(interaction: discord.Interaction, prefix: str):
    if prefix != PREFIX:
        return
    await interaction.response.defer()
    session_id = str(int(time.time() * 1000))
    REPORT_SESSIONS[session_id] = {MY_NAME: await asyncio.to_thread(make_machine_data)}
    await interaction.channel.send(f"TOTAL_REQUEST|{session_id}|{prefix}")
    
    await asyncio.sleep(REPORT_DELAY)
    data = REPORT_SESSIONS.pop(session_id, {})
    
    total_cookie = sum(info["cookie"] for info in data.values())
    total_switched = sum(info["switched"] for info in data.values())
    lines = [f"🖥️ `{m}`\n🍪 Cookie `{d['cookie']}`\n🔁 Switched `{d['switched']}`" for m, d in sorted(data.items())]

    embed = discord.Embed(title=f"📊 TOTAL ALL [{prefix}]", color=0x2ecc71)
    embed.add_field(name="🍪 TOTAL COOKIE", value=f"`{total_cookie}`", inline=True)
    embed.add_field(name="🔁 TOTAL SWITCHED", value=f"`{total_switched}`", inline=True)
    embed.add_field(name=f"🖥️ MACHINES ({len(data)})", value="\n\n".join(lines) if lines else "No data", inline=False)
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="put_cookie", description="Put cookie specific machine")
async def put_cookie(interaction: discord.Interaction, machine: str, file: discord.Attachment):
    if machine != MY_NAME:
        return
    await interaction.response.defer()
    try:
        content = (await file.read()).decode("utf-8", errors="ignore")
        cookies = [line.strip() for line in content.splitlines() if line.strip()]
        if not cookies:
            return await interaction.followup.send("❌ File rỗng")

        all_cookie = set()
        if COOKIE_FILE.exists():
            old = await asyncio.to_thread(read_text_sync, COOKIE_FILE)
            all_cookie.update(x.strip() for x in old.splitlines() if x.strip())
        all_cookie.update(cookies)

        await asyncio.to_thread(write_text_sync, COOKIE_FILE, "\n".join(sorted(all_cookie)) + "\n")
        await interaction.followup.send(f"✅ Added `{len(cookies)}` cookie\n🖥️ `{MY_NAME}`\n🍪 Total `{len(all_cookie)}`")
    except Exception as e:
        await interaction.followup.send(f"❌ ERROR: {e}")

@bot.tree.command(name="put_cookie_all", description="Broadcast cookie cho tất cả máy (Chống Rate Limit)")
async def put_cookie_all(interaction: discord.Interaction, prefix: str, total_machines: int, file: discord.Attachment):
    if prefix != PREFIX:
        return
    await interaction.response.defer()
    try:
        content = (await file.read()).decode("utf-8", errors="ignore")
        cookies = [line.strip() for line in content.splitlines() if line.strip()]
        if not cookies:
            return await interaction.followup.send("❌ File rỗng")

        broadcast_lines = []
        for index, cookie in enumerate(cookies):
            # Tính toán chính xác xem cookie này thuộc về máy nào
            machine_name = f"{prefix}-{ (index % total_machines) + 1 }"
            broadcast_lines.append(f"{machine_name}|{cookie}")

        # Ghi toàn bộ ra 1 file temp duy nhất
        temp_path = BASE_DIR / f"broadcast_cookie_{prefix}.txt"
        await asyncio.to_thread(write_text_sync, temp_path, "\n".join(broadcast_lines) + "\n")
        
        # CHỈ GỬI ĐÚNG 1 TIN NHẮN CHỨA FILE TỔNG
        await interaction.channel.send(
            content=f"BROADCAST_COOKIE|{prefix}",
            file=discord.File(temp_path, filename=f"broadcast_{prefix}.txt")
        )
        
        await asyncio.to_thread(temp_path.unlink, missing_ok=True)
        await interaction.followup.send(f"✅ Đã gửi `1` file tổng chứa `{len(cookies)}` cookie cho `{total_machines}` máy.\n🤖 Các máy sẽ tự động tải về và nhặt data riêng của nó.")
    except Exception as e:
        await interaction.followup.send(f"❌ ERROR: {e}")

@bot.tree.command(name="put_autoexec", description="Put autoexec specific machine")
async def put_autoexec(interaction: discord.Interaction, machine: str, file: discord.Attachment):
    if machine != MY_NAME:
        return
    await interaction.response.defer()
    saved = 0
    for path in AUTOEXEC_DIRS:
        try:
            await asyncio.to_thread(path.mkdir, parents=True, exist_ok=True)
            await file.save(path / file.filename)
            saved += 1
        except Exception as e:
            print(f"[PUT_AUTOEXEC ERROR] {e}")
    await interaction.followup.send(f"✅ Saved `{file.filename}`\n🖥️ `{MY_NAME}`\n📂 `{saved}` places")

@bot.tree.command(name="put_script_all", description="Put script all machine")
async def put_script_all(interaction: discord.Interaction, prefix: str, file: discord.Attachment):
    if prefix != PREFIX:
        return
    await interaction.response.defer()
    await interaction.channel.send(content=f"PUT_SCRIPT|{prefix}", file=await file.to_file())
    await interaction.followup.send(f"✅ Broadcasted `{file.filename}`")

@bot.tree.command(name="get", description="Get switched specific machine")
async def get(interaction: discord.Interaction, machine: str):
    if machine != MY_NAME:
        return
    await interaction.response.defer()
    
    switched_files = await asyncio.to_thread(get_switched_files)
    if not switched_files:
        return await interaction.followup.send("❌ Không có file")

    total_all = 0
    sent_files = 0
    for switched_file in switched_files:
        total = await asyncio.to_thread(count_lines, switched_file)
        if total > 0:
            success = await send_large_file(interaction.channel, switched_file, MY_NAME)
            if success:
                total_all += total
                sent_files += 1
                try:
                    await asyncio.to_thread(shutil.move, switched_file, switched_file.with_suffix(".sent"))
                except Exception as e:
                    print(f"[MOVE ERROR] {e}")

    await interaction.followup.send(f"✅ Sent `{total_all}` acc\n📂 Files `{sent_files}`\n🖥️ `{MY_NAME}`")

@bot.tree.command(name="get_all", description="Get switched all & auto export")
async def get_all(interaction: discord.Interaction, prefix: str, wait_time: int = 90):
    if prefix != PREFIX:
        return
    await interaction.response.defer()
    
    await interaction.channel.send(f"GET_ALL_REQUEST|{prefix}")
    await interaction.followup.send(f"📦 Đã yêu cầu gửi file. Đang chờ `{wait_time}` giây để tổng hợp...")
    
    await asyncio.sleep(wait_time)
    
    total = await asyncio.to_thread(merge_all_accounts_sync)
    zip_path = await asyncio.to_thread(make_final_zip_sync)
    
    files = list(RESULT_DIR.glob("all_*.txt"))
    if not files or total == 0:
        await interaction.channel.send("❌ Không có dữ liệu được gộp thành công.")
        return

    await interaction.channel.send(
        content=f"✅ Hoàn tất Export `{len(files)}` files\n📦 Tổng cộng gộp được `{total}` acc MỚI",
        file=discord.File(zip_path, filename="all_result.zip")
    )

@bot.tree.command(name="list_script", description="Xem danh sách script trong Autoexecute của máy cụ thể")
async def list_script(interaction: discord.Interaction, machine: str):
    if machine != MY_NAME:
        return
    await interaction.response.defer()

    found_files = await asyncio.to_thread(get_autoexec_files_sync)

    if not found_files:
        return await interaction.followup.send(f"📂 Không có file script nào trong thư mục Autoexecute của `{MY_NAME}`.")

    embed = discord.Embed(title=f"📜 Scripts đang có trên {MY_NAME}", color=0xf1c40f)
    embed.description = "\n".join([f"• `{name}`" for name in found_files])
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="del_script", description="Xóa 1 script khỏi Autoexecute của máy cụ thể")
async def del_script(interaction: discord.Interaction, machine: str, filename: str):
    if machine != MY_NAME:
        return
    await interaction.response.defer()

    deleted_count = await asyncio.to_thread(delete_autoexec_file_sync, filename)

    if deleted_count > 0:
        await interaction.followup.send(f"✅ Đã xóa thành công script `{filename}` khỏi máy `{MY_NAME}`.")
    else:
        await interaction.followup.send(f"❌ Không tìm thấy script `{filename}` trên máy `{MY_NAME}`.")

if __name__ == "__main__":
    bot.run(TOKEN, reconnect=True)
