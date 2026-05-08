import discord
from discord.ext import commands

import os
import io
import time
import shutil
import random
import zipfile
import asyncio
import tempfile

from pathlib import Path

==================================================

CONFIG

==================================================

BASE_DIR = Path("/sdcard/Download")

TOKEN_PATH = BASE_DIR / "bot_token.txt" NAME_PATH = BASE_DIR / "name.txt"

COOKIE_FILE = BASE_DIR / "cookie.txt"

SWITCHED_DIR = BASE_DIR / "Shouko" / "switched"

AUTOEXEC_DIRS = [ Path("/sdcard/Codex/Autoexec"), Path("/sdcard/Delta/Autoexecute"), ]

REPORT_DELAY = 5 MAX_LINES_PER_FILE = 5000 MAX_ZIP_SIZE_MB = 20

==================================================

RUNTIME CACHE

==================================================

REPORT_SESSIONS = {}

==================================================

READ / WRITE

==================================================

def read_text(path: Path, default=""): try: if path.exists(): return path.read_text(encoding="utf-8").strip() except Exception as e: print(f"[READ ERROR] {path}: {e}")

return default

def write_text(path: Path, data: str): try: path.parent.mkdir(parents=True, exist_ok=True) path.write_text(data, encoding="utf-8") except Exception as e: print(f"[WRITE ERROR] {path}: {e}")

==================================================

LOAD DATA

==================================================

TOKEN = read_text(TOKEN_PATH)

if not TOKEN: TOKEN = input("Nhập Token Bot: ").strip() write_text(TOKEN_PATH, TOKEN)

MY_NAME = read_text(NAME_PATH, "unknown-0")

try: PREFIX, MACHINE_ID = MY_NAME.split("-") MACHINE_ID = int(MACHINE_ID) except: PREFIX = "unknown" MACHINE_ID = 0

==================================================

DISCORD

==================================================

intents = discord.Intents.default() intents.message_content = True

bot = commands.Bot( command_prefix="!", intents=intents, heartbeat_timeout=120, )

==================================================

UTILS

==================================================

def count_lines(path: Path):

if not path.exists():
    return 0

try:
    with path.open("rb") as f:
        return sum(1 for line in f if line.strip())
except:
    return 0

def get_switched_file():

if not SWITCHED_DIR.exists():
    return None

files = sorted([
    f
    for f in SWITCHED_DIR.iterdir()
    if f.is_file() and f.suffix == ".txt"
])

return files[0] if files else None

def count_accounts():

cookie_count = count_lines(COOKIE_FILE)

switched_count = 0

switched_file = get_switched_file()

if switched_file:
    switched_count = count_lines(switched_file)

return cookie_count, switched_count

def make_machine_data():

cookie_count, switched_count = count_accounts()

return {
    "machine": MY_NAME,
    "cookie": cookie_count,
    "switched": switched_count,
}

def split_file(path: Path, lines_per_file=MAX_LINES_PER_FILE):

parts = []

with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

for i in range(0, len(lines), lines_per_file):

    chunk = lines[i:i + lines_per_file]

    chunk_path = (
        path.parent /
        f"{path.stem}_part_{i // lines_per_file}.txt"
    )

    with open(chunk_path, "w", encoding="utf-8") as out:
        out.writelines(chunk)

    parts.append(chunk_path)

return parts

def zip_single_file(file_path: Path):

temp_zip = tempfile.NamedTemporaryFile(
    suffix=".zip",
    delete=False
)

zip_path = Path(temp_zip.name)

temp_zip.close()

with zipfile.ZipFile(
    zip_path,
    "w",
    zipfile.ZIP_DEFLATED
) as zipf:

    zipf.write(file_path, arcname=file_path.name)

return zip_path

async def send_large_file(channel, file_path: Path, title: str):

if not file_path.exists():
    return False

total = count_lines(file_path)

if total <= 0:
    return False

# split trước
parts = split_file(file_path)

for index, part in enumerate(parts, start=1):

    try:
        zip_path = zip_single_file(part)

        await channel.send(
            content=(
                f"📦 {title}"
                f" | part `{index}/{len(parts)}`"
                f" | `{count_lines(part)}` accounts"
            ),
            file=discord.File(
                zip_path,
                filename=f"{part.stem}.zip"
            )
        )

        await asyncio.sleep(1)

        try:
            zip_path.unlink(missing_ok=True)
        except:
            pass

    except Exception as e:
        print(f"[SEND ERROR] {e}")
        return False

return True

==================================================

EVENTS

==================================================

@bot.event async def on_ready():

try:
    await bot.tree.sync()
except Exception as e:
    print(e)

print(f"✅ {MY_NAME} ONLINE")

@bot.event async def on_message(message: discord.Message):

if message.author.bot:
    return

content = message.content

# ==================================================
# TOTAL REQUEST
# ==================================================

if content.startswith("TOTAL_REQUEST|"):

    try:
        _, session_id, prefix = content.split("|")

        if prefix != PREFIX:
            return

        data = make_machine_data()

        await message.channel.send(
            (
                f"TOTAL_RESPONSE|"
                f"{session_id}|"
                f"{data['machine']}|"
                f"{data['cookie']}|"
                f"{data['switched']}"
            )
        )

    except Exception as e:
        print(e)

# ==================================================
# TOTAL RESPONSE
# ==================================================

elif content.startswith("TOTAL_RESPONSE|"):

    try:
        _, session_id, machine, cookie, switched = content.split("|")

        if session_id not in REPORT_SESSIONS:
            return

        REPORT_SESSIONS[session_id][machine] = {
            "machine": machine,
            "cookie": int(cookie),
            "switched": int(switched),
        }

    except Exception as e:
        print(e)

await bot.process_commands(message)

==================================================

TOTAL SINGLE

==================================================

@bot.tree.command( name="total", description="Check máy hiện tại" ) async def total( interaction: discord.Interaction, id_may: str ):

if id_may != MY_NAME:
    return

c, s = count_accounts()

embed = discord.Embed(
    title=f"🖥️ {MY_NAME}",
    color=0x3498db
)

embed.add_field(
    name="🍪 Cookie",
    value=f"`{c}`",
    inline=True
)

embed.add_field(
    name="🔁 Switched",
    value=f"`{s}`",
    inline=True
)

await interaction.response.send_message(embed=embed)

==================================================

TOTAL ALL V2

==================================================

@bot.tree.command( name="total_all", description="Tổng acc toàn dàn" ) async def total_all( interaction: discord.Interaction, prefix: str ):

if prefix != PREFIX:
    return

await interaction.response.defer()

session_id = str(int(time.time() * 1000))

REPORT_SESSIONS[session_id] = {}

REPORT_SESSIONS[session_id][MY_NAME] = make_machine_data()

await interaction.channel.send(
    f"TOTAL_REQUEST|{session_id}|{prefix}"
)

await asyncio.sleep(REPORT_DELAY)

data = REPORT_SESSIONS.get(session_id, {})

total_cookie = 0
total_switched = 0

lines = []

for machine, info in sorted(data.items()):

    total_cookie += info["cookie"]
    total_switched += info["switched"]

    lines.append(
        f"`{machine}` → "
        f"Cookie `{info['cookie']}` | "
        f"Switched `{info['switched']}`"
    )

embed = discord.Embed(
    title=f"📊 TOTAL ALL [{prefix.upper()}]",
    color=0x2ecc71
)

embed.add_field(
    name="🍪 Total Cookie",
    value=f"`{total_cookie}`",
    inline=True
)

embed.add_field(
    name="🔁 Total Switched",
    value=f"`{total_switched}`",
    inline=True
)

embed.add_field(
    name="🖥️ Machines",
    value="\n".join(lines[:25]) if lines else "Không có data",
    inline=False
)

embed.set_footer(
    text=f"{len(data)} machines responded"
)

await interaction.followup.send(embed=embed)

REPORT_SESSIONS.pop(session_id, None)

==================================================

PUT COOKIE ALL

==================================================

@bot.tree.command( name="put_cookie_all", description="Chia cookie toàn dàn" ) async def put_cookie_all( interaction: discord.Interaction, prefix: str, tong_so_may: int, file: discord.Attachment ):

if prefix != PREFIX:
    return

await interaction.response.defer(ephemeral=True)

try:

    content = (
        await file.read()
    ).decode("utf-8")

    cookies = [
        line.strip()
        for line in content.splitlines()
        if line.strip()
    ]

    total = len(cookies)

    if total == 0:
        return await interaction.followup.send(
            "❌ File rỗng",
            ephemeral=True
        )

    chunk_size = total // tong_so_may
    remain = total % tong_so_may

    start = ((MACHINE_ID - 1) * chunk_size)
    end = start + chunk_size

    if MACHINE_ID == tong_so_may:
        end += remain

    my_cookies = cookies[start:end]

    write_text(
        COOKIE_FILE,
        "\n".join(my_cookies)
    )

    await interaction.followup.send(
        f"✅ Nhận `{len(my_cookies)}` acc",
        ephemeral=True
    )

except Exception as e:

    await interaction.followup.send(
        f"❌ {e}",
        ephemeral=True
    )

==================================================

GET (ONE MACHINE)

==================================================

@bot.tree.command( name="get", description="Lấy switched máy hiện tại" ) async def get(interaction: discord.Interaction):

await interaction.response.defer()

switched_file = get_switched_file()

if not switched_file:
    return await interaction.followup.send(
        "❌ Không có file switched"
    )

total = count_lines(switched_file)

if total <= 0:
    return await interaction.followup.send(
        "❌ File rỗng"
    )

success = await send_large_file(
    interaction.channel,
    switched_file,
    MY_NAME
)

if success:

    backup = switched_file.with_suffix(".sent")

    try:
        shutil.move(switched_file, backup)
    except Exception as e:
        print(e)

    await interaction.followup.send(
        f"✅ Đã gửi `{total}` accounts"
    )

==================================================

GET ALL

==================================================

@bot.tree.command( name="get_all", description="Lấy switched toàn dàn" ) async def get_all( interaction: discord.Interaction, prefix: str ):

if prefix != PREFIX:
    return

await interaction.response.defer()

switched_file = get_switched_file()

if not switched_file:
    return

total = count_lines(switched_file)

if total <= 0:
    return

# anti spam
delay = random.randint(1, 10)

await asyncio.sleep(delay)

success = await send_large_file(
    interaction.channel,
    switched_file,
    MY_NAME
)

if success:

    backup = switched_file.with_suffix(".sent")

    try:
        shutil.move(switched_file, backup)
    except Exception as e:
        print(e)

==================================================

PUT SCRIPT ALL

==================================================

@bot.tree.command( name="put_script_all", description="Nạp script toàn dàn" ) async def put_script_all( interaction: discord.Interaction, prefix: str, file: discord.Attachment ):

if prefix != PREFIX:
    return

saved = 0

for path in AUTOEXEC_DIRS:

    try:

        path.mkdir(
            parents=True,
            exist_ok=True
        )

        save_path = path / file.filename

        await file.save(save_path)

        saved += 1

    except Exception as e:
        print(e)

await interaction.response.send_message(
    f"✅ Đã nạp script vào `{saved}` folder"
)

==================================================

RUN

==================================================

bot.run( TOKEN, reconnect=True )