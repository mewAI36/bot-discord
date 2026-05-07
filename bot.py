import discord
from discord.ext import commands
import os
import asyncio
import datetime
import time
from pathlib import Path

# ==================================================
# CONFIG
# ==================================================

BASE_DIR = Path("/sdcard/Download")

TOKEN_PATH = BASE_DIR / "bot_token.txt"
NAME_PATH = BASE_DIR / "name.txt"

COOKIE_FILE = BASE_DIR / "cookie.txt"
SWITCHED_DIR = BASE_DIR / "Shouko" / "switched"

AUTOEXEC_DIRS = [
    Path("/sdcard/AutoExec"),
    Path("/sdcard/AutoExecute"),
]

REPORT_DELAY = 5

# ==================================================
# READ / WRITE
# ==================================================

def read_text(path: Path, default=""):
    try:
        if path.exists():
            return path.read_text(encoding="utf-8").strip()
    except Exception as e:
        print(f"[READ ERROR] {path}: {e}")

    return default


def write_text(path: Path, data: str):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data, encoding="utf-8")
    except Exception as e:
        print(f"[WRITE ERROR] {path}: {e}")

# ==================================================
# LOAD DATA
# ==================================================

TOKEN = read_text(TOKEN_PATH)

if not TOKEN:
    TOKEN = input("🔑 Nhập Token Bot: ").strip()
    write_text(TOKEN_PATH, TOKEN)

MY_NAME = read_text(NAME_PATH, "unknown-0")

try:
    PREFIX, MACHINE_ID = MY_NAME.split("-")
    MACHINE_ID = int(MACHINE_ID)
except:
    PREFIX = "unknown"
    MACHINE_ID = 0

# ==================================================
# DISCORD
# ==================================================

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# ==================================================
# UTILS
# ==================================================

def count_lines(path: Path):
    if not path.exists():
        return 0

    try:
        with open(path, "r", encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())
    except:
        return 0


def get_switched_file():
    if not SWITCHED_DIR.exists():
        return None

    files = sorted([
        f for f in SWITCHED_DIR.iterdir()
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


def parse_report(content: str):

    try:
        parts = content.split("|")

        return {
            "session": parts[1],
            "machine": parts[2],
            "cookie": int(parts[3]),
            "switched": int(parts[4]),
        }

    except:
        return None

# ==================================================
# EVENTS
# ==================================================

@bot.event
async def on_ready():

    try:
        await bot.tree.sync()
    except Exception as e:
        print(e)

    print(f"✅ {MY_NAME} ONLINE")


# ==================================================
# TOTAL SINGLE
# ==================================================

@bot.tree.command(
    name="total",
    description="Check máy hiện tại"
)
async def total(
    interaction: discord.Interaction,
    id_may: str
):

    if id_may != MY_NAME:
        return

    c, s = count_accounts()

    embed = discord.Embed(
        title=f"📊 {MY_NAME}",
        color=0x3498db
    )

    embed.add_field(
        name="🍪 Cookie",
        value=f"`{c}`",
        inline=True
    )

    embed.add_field(
        name="📦 Switched",
        value=f"`{s}`",
        inline=True
    )

    await interaction.response.send_message(
        embed=embed
    )

# ==================================================
# TOTAL ALL
# ==================================================

@bot.tree.command(
    name="total_all",
    description="Tổng kết toàn dàn"
)
async def total_all(
    interaction: discord.Interaction,
    prefix: str
):

    if prefix != PREFIX:
        return

    await interaction.response.defer(
        ephemeral=True
    )

    # session unique
    session_id = str(int(time.time() * 1000))

    c, s = count_accounts()

    # report format:
    # REPORT|session|machine|cookie|switched
    report = (
        f"REPORT|"
        f"{session_id}|"
        f"{MY_NAME}|"
        f"{c}|"
        f"{s}"
    )

    await interaction.channel.send(report)

    # chỉ máy số 1 tổng hợp
    if MACHINE_ID != 1:
        return

    # đợi máy khác gửi
    await asyncio.sleep(REPORT_DELAY)

    total_cookie = 0
    total_switched = 0

    scanned = set()

    async for msg in interaction.channel.history(limit=100):

        if msg.author != bot.user:
            continue

        if not msg.content.startswith("REPORT|"):
            continue

        data = parse_report(msg.content)

        if not data:
            continue

        # chỉ lấy đúng session
        if data["session"] != session_id:
            continue

        machine = data["machine"]

        # chống cộng trùng
        if machine in scanned:
            continue

        scanned.add(machine)

        total_cookie += data["cookie"]
        total_switched += data["switched"]

    embed = discord.Embed(
        title=f"🏆 TỔNG KẾT DÀN {prefix.upper()}",
        color=0x2ecc71
    )

    embed.add_field(
        name="🍪 TỔNG COOKIE",
        value=f"`{total_cookie}`",
        inline=True
    )

    embed.add_field(
        name="📦 TỔNG SWITCHED",
        value=f"`{total_switched}`",
        inline=True
    )

    embed.set_footer(
        text=f"{len(scanned)} máy phản hồi"
    )

    await interaction.channel.send(
        embed=embed
    )

# ==================================================
# PUT COOKIE ALL
# ==================================================

@bot.tree.command(
    name="put_cookie_all",
    description="Chia cookie toàn dàn"
)
async def put_cookie_all(
    interaction: discord.Interaction,
    prefix: str,
    tong_so_may: int,
    file: discord.Attachment
):

    if prefix != PREFIX:
        return

    await interaction.response.defer(
        ephemeral=True
    )

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
            await interaction.followup.send(
                "❌ File rỗng",
                ephemeral=True
            )
            return

        chunk_size = total // tong_so_may
        remain = total % tong_so_may

        start = (
            (MACHINE_ID - 1)
            * chunk_size
        )

        end = start + chunk_size

        # máy cuối ăn dư
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

# ==================================================
# GET ALL
# ==================================================

@bot.tree.command(
    name="get_all",
    description="Lấy file switched"
)
async def get_all(
    interaction: discord.Interaction,
    prefix: str
):

    if prefix != PREFIX:
        return

    switched_file = get_switched_file()

    if not switched_file:
        return

    if count_lines(switched_file) == 0:
        return

    await interaction.channel.send(
        content=f"📦 {MY_NAME}",
        file=discord.File(switched_file)
    )

    # clear file
    write_text(switched_file, "")

# ==================================================
# PUT SCRIPT ALL
# ==================================================

@bot.tree.command(
    name="put_script_all",
    description="Nạp script toàn dàn"
)
async def put_script_all(
    interaction: discord.Interaction,
    prefix: str,
    file: discord.Attachment
):

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

# ==================================================
# RUN
# ==================================================

bot.run(TOKEN)
