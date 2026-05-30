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
    Path("/sdcard/Delta/Autoexecute"),
]

REPORT_DELAY = 8
MAX_LINES_PER_FILE = 5000

# --- 1. THÊM CONFIG ---
RESULT_KEEP_LATEST = 1

RESULT_DIR = (
    BASE_DIR /
    "all_result"
)

MERGED_FILE = (
    RESULT_DIR /
    "all_accounts.txt"
)

FINAL_ZIP = (
    BASE_DIR /
    "all_result.zip"
)

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

TOKEN = read_text(
    TOKEN_PATH
).strip()

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

    PREFIX, MACHINE_ID = (
        MY_NAME.split("-")
    )

    MACHINE_ID = int(
        MACHINE_ID
    )

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


# --- 2. REPLACE get_switched_file() -> get_switched_files() ---
def get_switched_files():

    if not SWITCHED_DIR.exists():
        return []

    return sorted([
        x
        for x in SWITCHED_DIR.iterdir()
        if (
            x.is_file()
            and
            x.suffix == ".txt"
        )
    ])


# --- 3. REPLACE count_accounts() ---
def count_accounts():

    cookie_count = count_lines(
        COOKIE_FILE
    )

    switched_count = 0

    switched_files = get_switched_files()

    for file in switched_files:

        switched_count += count_lines(
            file
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


# --- 6. REPLACE save_result_file() ---
async def save_result_file(
    machine_name: str,
    attachment: discord.Attachment
):

    machine_dir = (
        RESULT_DIR /
        machine_name
    )

    machine_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    old_dirs = sorted(
        [
            x for x in machine_dir.iterdir()
            if x.is_dir()
        ],
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )

    for old in old_dirs[
        RESULT_KEEP_LATEST:
    ]:

        try:
            shutil.rmtree(
                old,
                ignore_errors=True
            )
        except:
            pass

    zip_path = (
        machine_dir /
        attachment.filename
    )

    await attachment.save(
        zip_path
    )

    try:

        extract_name = (
            f"{int(time.time())}_"
            f"{attachment.filename.replace('.zip', '')}"
        )

        extract_dir = (
            machine_dir /
            extract_name
        )

        extract_dir.mkdir(
            exist_ok=True
        )

        with zipfile.ZipFile(
            zip_path,
            "r"
        ) as zipf:

            zipf.extractall(
                extract_dir
            )

        try:
            zip_path.unlink(
                missing_ok=True
            )
        except:
            pass

    except Exception as e:

        print(e)


# --- 7. THÊM merge_all_accounts() ---
def merge_all_accounts():

    RESULT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    merged_map = {}

    for machine_dir in RESULT_DIR.iterdir():

        if not machine_dir.is_dir():
            continue

        request_dirs = sorted(
            [
                x for x in machine_dir.iterdir()
                if x.is_dir()
            ],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        latest_dirs = request_dirs[
            :RESULT_KEEP_LATEST
        ]

        for request_dir in latest_dirs:

            for txt in request_dir.rglob("*.txt"):

                try:

                    file_key = txt.stem

                    if file_key not in merged_map:
                        merged_map[file_key] = set()

                    content = txt.read_text(
                        encoding="utf-8",
                        errors="ignore"
                    )

                    for line in content.splitlines():

                        line = line.strip()

                        if line:
                            merged_map[
                                file_key
                            ].add(line)

                except:
                    pass

    total_all = 0

    for file_key, accounts in merged_map.items():

        out_file = (
            RESULT_DIR /
            f"all_{file_key}.txt"
        )

        out_file.write_text(
            "\n".join(
                sorted(accounts)
            ) + "\n",
            encoding="utf-8"
        )

        total_all += len(accounts)

    return total_all


# --- 8. REPLACE make_final_zip() ---
def make_final_zip():

    if FINAL_ZIP.exists():

        FINAL_ZIP.unlink()

    with zipfile.ZipFile(
        FINAL_ZIP,
        "w",
        zipfile.ZIP_DEFLATED
    ) as zipf:

        for file in RESULT_DIR.glob(
            "all_*.txt"
        ):

            zipf.write(
                file,
                file.name
            )

    return FINAL_ZIP

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

    if not message.author.bot:
        return

    content = message.content

    if (
        message.attachments
        and
        content.startswith("📦")
    ):

        try:

            machine_name = (
                content
                .split("|")[0]
                .replace("📦", "")
                .strip()
            )

            attachment = (
                message.attachments[0]
            )

            await save_result_file(
                machine_name,
                attachment
            )

        except Exception as e:

            print(e)

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

            _, prefix, machine_name = (
                content.split("|")
            )

            if prefix != PREFIX:
                return

            if machine_name != MY_NAME:
                return

            if not message.attachments:
                return

            attachment = (
                message.attachments[0]
            )

            temp_path = (
                BASE_DIR /
                f"temp_cookie_{MY_NAME}.txt"
            )

            await attachment.save(
                temp_path
            )

            content = temp_path.read_text(
                encoding="utf-8",
                errors="ignore"
            )

            cookies = [
                x.strip()
                for x in content.splitlines()
                if x.strip()
            ]

            all_cookie = set()

            if COOKIE_FILE.exists():

                old = COOKIE_FILE.read_text(
                    encoding="utf-8",
                    errors="ignore"
                )

                all_cookie.update([
                    x.strip()
                    for x in old.splitlines()
                    if x.strip()
                ])

            all_cookie.update(cookies)

            COOKIE_FILE.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            COOKIE_FILE.write_text(
                "\n".join(
                    sorted(all_cookie)
                ) + "\n",
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
    # PUT SCRIPT
    # ==================================================

    elif content.startswith(
        "PUT_SCRIPT|"
    ):

        try:

            _, prefix = (
                content.split("|")
            )

            if prefix != PREFIX:
                return

            if not message.attachments:
                return

            attachment = (
                message.attachments[0]
            )

            saved = 0

            for path in AUTOEXEC_DIRS:

                try:

                    path.mkdir(
                        parents=True,
                        exist_ok=True
                    )

                    save_path = (
                        path /
                        attachment.filename
                    )

                    await attachment.save(
                        save_path
                    )

                    saved += 1

                except Exception as e:
                    print(e)

            print(
                f"✅ SCRIPT SAVED {saved}"
            )

        except Exception as e:
            print(e)

    # ==================================================
    # GET ALL REQUEST (--- 4. REPLACE GET_ALL_REQUEST ---)
    # ==================================================

    elif content.startswith(
        "GET_ALL_REQUEST|"
    ):

        try:

            _, prefix = (
                content.split("|")
            )

            if prefix != PREFIX:
                return

                        switched_files = get_switched_files()

            if not switched_files:
                return

            # Xếp hàng lần lượt dựa theo ID máy để tránh spam Discord Rate Limit
            delay = MACHINE_ID * 4 
            delay += random.randint(1, 3) 

            await asyncio.sleep(delay)

            for switched_file in switched_files:

                total = count_lines(
                    switched_file
                )

                if total <= 0:
                    continue

                success = await send_large_file(
                    message.channel,
                    switched_file,
                    MY_NAME
                )

                if success:

                    backup = (
                        switched_file.with_suffix(
                            ".sent"
                        )
                    )

                    try:

                        shutil.move(
                            switched_file,
                            backup
                        )

                    except Exception as e:
                        print(e)

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

    REPORT_SESSIONS[
        session_id
    ][MY_NAME] = make_machine_data()

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
# PUT COOKIE SPECIFIC MACHINE
# ==================================================

@bot.tree.command(
    name="put_cookie",
    description="Put cookie specific machine"
)
async def put_cookie(
    interaction: discord.Interaction,
    machine: str,
    file: discord.Attachment
):

    if machine != MY_NAME:
        return

    await interaction.response.defer()

    try:

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

        if not cookies:

            return await interaction.followup.send(
                "❌ File rỗng"
            )

        COOKIE_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        all_cookie = set()

        if COOKIE_FILE.exists():

            old = COOKIE_FILE.read_text(
                encoding="utf-8",
                errors="ignore"
            )

            all_cookie.update([
                x.strip()
                for x in old.splitlines()
                if x.strip()
                ])

        all_cookie.update(cookies)

        COOKIE_FILE.write_text(
            "\n".join(
                sorted(all_cookie)
            ) + "\n",
            encoding="utf-8"
        )

        await interaction.followup.send(
            (
                f"✅ Added `{len(cookies)}` cookie"
                f"\n🖥️ `{MY_NAME}`"
                f"\n🍪 Total `{len(all_cookie)}`"
            )
        )

    except Exception as e:

        await interaction.followup.send(
            f"❌ ERROR: {e}"
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

        if not cookies:

            return await interaction.followup.send(
                "❌ File rỗng"
            )

        chunks = [
            []
            for _ in range(
                total_machines
            )
        ]

        for index, cookie in enumerate(
            cookies
        ):

            machine_index = (
                index % total_machines
            )

            chunks[
                machine_index
            ].append(cookie)

        machine_names = [
            f"{prefix}-{i}"
            for i in range(
                1,
                total_machines + 1
            )
        ]

        sent = 0

        for machine_name, machine_cookies in zip(
            machine_names,
            chunks
        ):

            if not machine_cookies:
                continue

            temp_path = (
                BASE_DIR /
                f"temp_cookie_{machine_name}.txt"
            )

            temp_path.write_text(
                "\n".join(
                    machine_cookies
                ) + "\n",
                encoding="utf-8"
            )

            await interaction.channel.send(
                content=(
                    f"PUT_COOKIE|"
                    f"{prefix}|"
                    f"{machine_name}"
                ),
                file=discord.File(
                    temp_path,
                    filename=f"{machine_name}.txt"
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
                f"\n🖥️ `{total_machines}` machines"
            )
        )

    except Exception as e:

        await interaction.followup.send(
            f"❌ ERROR: {e}"
        )

# ==================================================
# PUT AUTOEXEC SPECIFIC MACHINE
# ==================================================

@bot.tree.command(
    name="put_autoexec",
    description="Put autoexec specific machine"
)
async def put_autoexec(
    interaction: discord.Interaction,
    machine: str,
    file: discord.Attachment
):

    if machine != MY_NAME:
        return

    await interaction.response.defer()

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

    await interaction.followup.send(
        (
            f"✅ Saved `{file.filename}`"
            f"\n🖥️ `{MY_NAME}`"
            f"\n📂 `{saved}` places"
        )
    )

# ==================================================
# PUT AUTOEXEC ALL
# ==================================================

@bot.tree.command(
    name="put_script_all",
    description="Put script all machine"
)
async def put_script_all(
    interaction: discord.Interaction,
    prefix: str,
    file: discord.Attachment
):

    if prefix != PREFIX:
        return

    await interaction.response.defer()

    await interaction.channel.send(
        content=f"PUT_SCRIPT|{prefix}",
        file=await file.to_file()
    )

    await interaction.followup.send(
        f"✅ Broadcasted `{file.filename}`"
    )

# ==================================================
# GET SPECIFIC MACHINE (--- 5. REPLACE /get ---)
# ==================================================

@bot.tree.command(
    name="get",
    description="Get switched specific machine"
)
async def get(
    interaction: discord.Interaction,
    machine: str
):

    if machine != MY_NAME:
        return

    await interaction.response.defer()

    switched_files = get_switched_files()

    if not switched_files:

        return await interaction.followup.send(
            "❌ Không có file"
        )

    total_all = 0
    sent_files = 0

    for switched_file in switched_files:

        total = count_lines(
            switched_file
        )

        if total <= 0:
            continue

        success = await send_large_file(
            interaction.channel,
            switched_file,
            MY_NAME
        )

        if success:

            total_all += total
            sent_files += 1

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
        (
            f"✅ Sent `{total_all}` acc"
            f"\n📂 Files `{sent_files}`"
            f"\n🖥️ `{MY_NAME}`"
        )
    )

# ==================================================
# GET ALL & AUTO EXPORT
# ==================================================

@bot.tree.command(
    name="get_all",
    description="Get switched all & auto export"
)
async def get_all(
    interaction: discord.Interaction,
    prefix: str,
    wait_time: int = 90 # Thời gian chờ các máy up file (tính bằng giây)
):

    if prefix != PREFIX:
        return

    await interaction.response.defer()

    # 1. Phát tín hiệu cho các máy tiến hành upload file
    await interaction.channel.send(
        f"GET_ALL_REQUEST|{prefix}"
    )

    await interaction.followup.send(
        f"📦 Đã yêu cầu tất cả các máy gửi file. Bot sẽ tự động gộp và xuất file tổng sau `{wait_time}` giây..."
    )

    # 2. Đợi các máy upload file và đợi sự kiện on_message xử lý tải file về RESULT_DIR
    await asyncio.sleep(
        wait_time
    )

    # 3. Chạy lệnh gộp tất cả file
    total = merge_all_accounts()

    zip_path = make_final_zip()

    files = list(
        RESULT_DIR.glob("all_*.txt")
    )

    if not files or total == 0:
        
        await interaction.channel.send(
            "❌ Không có dữ liệu nào được trả về hoặc gộp thành công sau thời gian chờ."
        )
        return

    # 4. Trả kết quả file tổng chứa tất cả account của mọi máy (đã phân tên)
    await interaction.channel.send(
        content=(
            f"✅ Hoàn tất Export `{len(files)}` files"
            f"\n📦 Tổng cộng gộp được `{total}` acc"
        ),
        file=discord.File(
            zip_path,
            filename="all_result.zip"
        )
    )


# ==================================================
# RUN
# ==================================================

bot.run(
    TOKEN,
    reconnect=True
)

