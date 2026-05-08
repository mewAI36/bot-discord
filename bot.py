import discord
from discord.ext import commands

import time
import shutil
import random
import zipfile
import asyncio
import tempfile

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

REPORT_DELAY = 8
MAX_LINES_PER_FILE = 5000

# ==================================================
# RUNTIME CACHE
# ==================================================

REPORT_SESSIONS = {}

# ==================================================
# READ / WRITE
# ==================================================


def read_text(path: Path, default=""):

    try:

        if path.exists():
            return path.read_text(
                encoding="utf-8"
            ).strip()

    except Exception as e:
        print(f"[READ ERROR] {e}")

    return default



def write_text(path: Path, data: str):

    try:

        path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        path.write_text(
            data,
            encoding="utf-8"
        )

    except Exception as e:
        print(f"[WRITE ERROR] {e}")


# ==================================================
# LOAD MACHINE
# ==================================================

TOKEN = read_text(TOKEN_PATH)

if not TOKEN:

    TOKEN = input("Nhập token bot: ").strip()

    write_text(TOKEN_PATH, TOKEN)

MY_NAME = read_text(NAME_PATH, "unknown-1")

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

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    heartbeat_timeout=120,
)

# ==================================================
# UTILS
# ==================================================


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
        x
        for x in SWITCHED_DIR.iterdir()
        if x.is_file() and x.suffix == ".txt"
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

    tmp = tempfile.NamedTemporaryFile(
        suffix=".zip",
        delete=False
    )

    zip_path = Path(tmp.name)

    tmp.close()

    with zipfile.ZipFile(
        zip_path,
        "w",
        zipfile.ZIP_DEFLATED
    ) as zipf:

        zipf.write(
            file_path,
            arcname=file_path.name
        )

    return zip_path


async def send_large_file(channel, file_path: Path, title: str):

    if not file_path.exists():
        return False

    total = count_lines(file_path)

    if total <= 0:
        return False

    parts = split_file(file_path)

    for index, part in enumerate(parts, start=1):

        try:

            zip_path = zip_single_file(part)

            await channel.send(
                content=(
                    f"📦 {title}"
                    f" | part `{index}/{len(parts)}`"
                    f" | `{count_lines(part)}` acc"
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


# ==================================================
# EVENTS
# ==================================================

@bot.event
async def on_ready():

    try:
        await bot.tree.sync()
    except Exception as e:
        print(e)

    print(f"✅ ONLINE: {MY_NAME}")


@bot.event
async def on_message(message: discord.Message):

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


# ==================================================
# TOTAL
# ==================================================

@bot.tree.command(
    name="total",
    description="Check máy"
)
async def total(
    interaction: discord.Interaction,
    machine: str
):

    if machine != MY_NAME:
        return

    cookie_count, switched_count = count_accounts()

    embed = discord.Embed(
        title=f"🖥️ {MY_NAME}",
        color=0x3498db
    )

    embed.add_field(
        name="🍪 Cookie",
        value=f"`{cookie_count}`",
        inline=True
    )

    embed.add_field(
        name="🔁 Switched",
        value=f"`{switched_count}`",
        inline=True
    )

    await interaction.response.send_message(embed=embed)


# ==================================================
# TOTAL ALL FIXED
# ==================================================

@bot.tree.command(
    name="total_all",
    description="Total acc all"
)
async def total_all(
    interaction: discord.Interaction,
    prefix: str
):

    if prefix != PREFIX:
        return

    await interaction.response.defer()

    session_id = str(int(time.time() * 1000))

    REPORT_SESSIONS[session_id] = {}

    # add current machine
    REPORT_SESSIONS[session_id][MY_NAME] = make_machine_data()

    # broadcast
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
            f"`{machine}` | "
            f"Cookie `{info['cookie']}` | "
            f"Switched `{info['switched']}`"
        )

    embed = discord.Embed(
        title=f"📊 TOTAL ALL [{prefix}]",
        color=0x2ecc71
    )

    embed.add_field(
        name="🍪 TOTAL COOKIE",
        value=f"`{total_cookie}`",
        inline=True
    )

    embed.add_field(
        name="🔁 TOTAL SWITCHED",
        value=f"`{total_switched}`",
        inline=True
    )

    embed.add_field(
        name="🖥️ MACHINES",
        value="\n".join(lines) if lines else "No data",
        inline=False
    )

    embed.set_footer(
        text=f"{len(data)} machines"
    )

    await interaction.followup.send(embed=embed)

    REPORT_SESSIONS.pop(session_id, None)


# ==================================================
# PUT COOKIE ALL FIXED
# ==================================================

@bot.tree.command(
    name="put_cookie_all",
    description="Chia cookie all machine"
)
async def put_cookie_all(
    interaction: discord.Interaction,
    prefix: str,
    file: discord.Attachment
):

    if prefix != PREFIX:
        return

    # mỗi máy tự xử lý riêng
    # KHÔNG dùng tong_so_may nữa

    try:

        raw = await file.read()

        content = raw.decode("utf-8")

        cookies = [
            x.strip()
            for x in content.splitlines()
            if x.strip()
        ]

        total = len(cookies)

        if total <= 0:
            return

        # ==================================================
        # MACHINE FILTER
        # ==================================================

        my_cookies = []

        for index, cookie in enumerate(cookies):

            machine_slot = (index % 100) + 1

            if machine_slot == MACHINE_ID:
                my_cookies.append(cookie)

        if not my_cookies:
            return

        write_text(
            COOKIE_FILE,
            "\n".join(my_cookies)
        )

        await interaction.response.send_message(
            f"✅ {MY_NAME} nhận `{len(my_cookies)}` acc"
        )

    except Exception as e:

        await interaction.response.send_message(
            f"❌ {e}"
        )


# ==================================================
# GET
# ==================================================

@bot.tree.command(
    name="get",
    description="Get switched machine"
)
async def get(interaction: discord.Interaction):

    await interaction.response.defer()

    switched_file = get_switched_file()

    if not switched_file:

        return await interaction.followup.send(
            "❌ Không có file"
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
            f"✅ Sent `{total}` acc"
        )


# ==================================================
# GET ALL
# ==================================================

@bot.tree.command(
    name="get_all",
    description="Get switched all"
)
async def get_all(
    interaction: discord.Interaction,
    prefix: str
):

    if prefix != PREFIX:
        return

    await interaction.response.defer()

    switched_file = get_switched_file()

    if not switched_file:
        return

    total = count_lines(switched_file)

    if total <= 0:
        return

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


# ==================================================
# PUT SCRIPT ALL
# ==================================================

@bot.tree.command(
    name="put_script_all",
    description="Put script all"
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
        f"✅ Saved `{saved}` places"
    )


# ==================================================
# RUN
# ==================================================

bot.run(
    TOKEN,
    reconnect=True
)
