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

SWITCHED_DIR = (
    BASE_DIR /
    "Shouko" /
    "switched"
)

AUTOEXEC_DIRS = [
    Path("/sdcard/AutoExec"),
    Path("/sdcard/AutoExecute"),
]

REPORT_DELAY = 8
MAX_LINES_PER_FILE = 5000

# ==================================================
# CACHE
# ==================================================

REPORT_SESSIONS = {}

# ==================================================
# READ / WRITE
# ==================================================

def read_text(
    path: Path,
    default=""
):

    try:

        if path.exists():

            return path.read_text(
                encoding="utf-8",
                errors="ignore"
            )

    except Exception as e:

        print(f"[READ ERROR] {e}")

    return default


def write_text(
    path: Path,
    data: str
):

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

TOKEN = read_text(TOKEN_PATH).strip()

if not TOKEN:

    TOKEN = input(
        "Nhập token bot: "
    ).strip()

    write_text(
        TOKEN_PATH,
        TOKEN
    )

MY_NAME = read_text(
    NAME_PATH,
    "unknown-1"
).strip()

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

        with path.open(
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as f:

            return sum(
                1
                for line in f
                if line.strip()
            )

    except:
        return 0


def get_switched_file():

    if not SWITCHED_DIR.exists():
        return None

    files = sorted([
        x
        for x in SWITCHED_DIR.iterdir()
        if (
            x.is_file()
            and
            x.suffix == ".txt"
        )
    ])

    return files[0] if files else None


def count_accounts():

    cookie_count = count_lines(
        COOKIE_FILE
    )

    switched_count = 0

    switched_file = get_switched_file()

    if switched_file:

        switched_count = count_lines(
            switched_file
        )

    return (
        cookie_count,
        switched_count
    )


def make_machine_data():

    cookie_count, switched_count = (
        count_accounts()
    )

    return {
        "machine": MY_NAME,
        "cookie": cookie_count,
        "switched": switched_count,
    }


def split_file(
    path: Path,
    lines_per_file=MAX_LINES_PER_FILE
):

    parts = []

    with open(
        path,
        "r",
        encoding="utf-8",
        errors="ignore"
    ) as f:

        lines = f.readlines()

    for i in range(
        0,
        len(lines),
        lines_per_file
    ):

        chunk = lines[
            i:i + lines_per_file
        ]

        chunk_path = (
            path.parent /
            f"{path.stem}_part_{i // lines_per_file}.txt"
        )

        with open(
            chunk_path,
            "w",
            encoding="utf-8"
        ) as out:

            out.writelines(chunk)

        parts.append(chunk_path)

    return parts


def zip_single_file(
    file_path: Path
):

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


async def send_large_file(
    channel,
    file_path: Path,
    title: str
):

    if not file_path.exists():
        return False

    total = count_lines(
        file_path
    )

    if total <= 0:
        return False

    parts = split_file(file_path)

    for index, part in enumerate(
        parts,
        start=1
    ):

        try:

            zip_path = zip_single_file(
                part
            )

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
                zip_path.unlink(
                    missing_ok=True
                )
            except:
                pass

            try:
                part.unlink(
                    missing_ok=True
                )
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
async def on_message(
    message: discord.Message
):

    content = message.content

    # ==================================================
    # TOTAL REQUEST
    # ==================================================

    if content.startswith(
        "TOTAL_REQUEST|"
    ):

        try:

            _, session_id, prefix = (
                content.split("|")
            )

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
    # PUT COOKIE
    # ==================================================

    elif content.startswith(
        "PUT_COOKIE|"
    ):

        try:

            _, prefix, machine_id = (
                content.split("|")
            )

            if prefix != PREFIX:
                return

            if int(machine_id) != MACHINE_ID:
                return

            if not message.attachments:
                return

            attachment = (
                message.attachments[0]
            )

            temp_path = (
                BASE_DIR /
                f"temp_cookie_{MACHINE_ID}.txt"
            )

            await attachment.save(
                temp_path
            )

            cookie_data = temp_path.read_text(
                encoding="utf-8",
                errors="ignore"
            )

            if not cookie_data.strip():
                return

            COOKIE_FILE.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            COOKIE_FILE.write_text(
                cookie_data,
                encoding="utf-8"
            )

            print(
                f"✅ RECEIVED COOKIE: {MY_NAME}"
            )

            try:
                temp_path.unlink(
                    missing_ok=True
                )
            except:
                pass

        except Exception as e:
            print(e)

    # ==================================================
    # TOTAL RESPONSE
    # ==================================================

    elif content.startswith(
        "TOTAL_RESPONSE|"
    ):

        try:

            (
                _,
                session_id,
                machine,
                cookie,
                switched
            ) = content.split("|")

            if (
                session_id
                not in REPORT_SESSIONS
            ):
                return

            REPORT_SESSIONS[
                session_id
            ][machine] = {

                "machine": machine,
                "cookie": int(cookie),
                "switched": int(switched),
            }

        except Exception as e:
            print(e)

    await bot.process_commands(
        message
    )

# ==================================================
# TOTAL
# ==================================================

@bot.tree.command(
    name="total",
    description="Check machine"
)
async def total(
    interaction: discord.Interaction,
    machine: str
):

    if machine != MY_NAME:
        return

    cookie_count, switched_count = (
        count_accounts()
    )

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

    await interaction.response.send_message(
        embed=embed
    )

# ==================================================
# TOTAL ALL
# ==================================================

@bot.tree.command(
    name="total_all",
    description="Total acc all machine"
)
async def total_all(
    interaction: discord.Interaction,
    prefix: str
):

    if prefix != PREFIX:
        return

    await interaction.response.defer()

    session_id = str(
        int(time.time() * 1000)
    )

    REPORT_SESSIONS[
        session_id
    ] = {}

    # self
    REPORT_SESSIONS[
        session_id
    ][MY_NAME] = make_machine_data()

    # broadcast
    await interaction.channel.send(
        f"TOTAL_REQUEST|{session_id}|{prefix}"
    )

    await asyncio.sleep(
        REPORT_DELAY
    )

    data = REPORT_SESSIONS.get(
        session_id,
        {}
    )

    total_cookie = 0
    total_switched = 0

    lines = []

    for machine_name in sorted(
        data.keys()
    ):

        info = data[machine_name]

        cookie = info["cookie"]
        switched = info["switched"]

        total_cookie += cookie
        total_switched += switched

        lines.append(
            f"🖥️ `{machine_name}`"
            f"\n🍪 Cookie `{cookie}`"
            f"\n🔁 Switched `{switched}`"
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
        name=f"🖥️ MACHINES ({len(data)})",
        value=(
            "\n\n".join(lines)
            if lines else "No data"
        ),
        inline=False
    )

    await interaction.followup.send(
        embed=embed
    )

    REPORT_SESSIONS.pop(
        session_id,
        None
    )

# ==================================================
# PUT COOKIE ALL
# ==================================================

@bot.tree.command(
    name="put_cookie_all",
    description="Split cookie all machine"
)
async def put_cookie_all(
    interaction: discord.Interaction,
    prefix: str,
    total_machines: int,
    file: discord.Attachment
):

    if prefix != PREFIX:
        return

    await interaction.response.defer()

    try:

        if total_machines <= 0:

            return await interaction.followup.send(
                "❌ total_machines invalid"
            )

        raw = await file.read()

        content = raw.decode(
            "utf-8",
            errors="ignore"
        )

        cookies = [
            line.strip()
            for line in content.splitlines()
            if line.strip()
        ]

        total_cookie = len(cookies)

        if total_cookie <= 0:

            return await interaction.followup.send(
                "❌ File rỗng"
            )

        chunks = [
            []
            for _ in range(
                total_machines
            )
        ]

        # chia đều
        for index, cookie in enumerate(
            cookies
        ):

            machine_index = (
                index % total_machines
            )

            chunks[
                machine_index
            ].append(cookie)

        sent = 0

        for machine_id, machine_cookies in enumerate(
            chunks,
            start=1
        ):

            if not machine_cookies:
                continue

            temp_path = (
                BASE_DIR /
                f"temp_cookie_{machine_id}.txt"
            )

            temp_path.write_text(
                "\n".join(machine_cookies),
                encoding="utf-8"
            )

            await interaction.channel.send(
                content=(
                    f"PUT_COOKIE|"
                    f"{prefix}|"
                    f"{machine_id}"
                ),
                file=discord.File(
                    temp_path,
                    filename=f"cookie_{machine_id}.txt"
                )
            )

            sent += len(
                machine_cookies
            )

            await asyncio.sleep(1)

            try:
                temp_path.unlink(
                    missing_ok=True
                )
            except:
                pass

        await interaction.followup.send(
            (
                f"✅ Split `{sent}` cookie"
                f" -> `{total_machines}` machines"
            )
        )

    except Exception as e:

        await interaction.followup.send(
            f"❌ ERROR: {e}"
        )

# ==================================================
# GET
# ==================================================

@bot.tree.command(
    name="get",
    description="Get switched machine"
)
async def get(
    interaction: discord.Interaction
):

    await interaction.response.defer()

    switched_file = get_switched_file()

    if not switched_file:

        return await interaction.followup.send(
            "❌ Không có file"
        )

    total = count_lines(
        switched_file
    )

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

        backup = switched_file.with_suffix(
            ".sent"
        )

        try:
            shutil.move(
                switched_file,
                backup
            )
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

    total = count_lines(
        switched_file
    )

    if total <= 0:
        return

    delay = random.randint(
        1,
        10
    )

    await asyncio.sleep(delay)

    success = await send_large_file(
        interaction.channel,
        switched_file,
        MY_NAME
    )

    if success:

        backup = switched_file.with_suffix(
            ".sent"
        )

        try:
            shutil.move(
                switched_file,
                backup
            )
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

            save_path = (
                path /
                file.filename
            )

            await file.save(
                save_path
            )

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