#!/data/data/com.termux/files/usr/bin/bash

echo "⚙️ --- ĐANG CÀI ĐẶT HỆ THỐNG MEW-BOT ALL-IN-ONE ---"

# 1. Cấp quyền storage và tạo môi trường
termux-setup-storage -y
pkg update -y && pkg install python curl -y
pip install discord.py

# 2. Tạo các folder làm việc
mkdir -p /sdcard/Download/Shouko/switched
mkdir -p /sdcard/Download/Shouko/Autoexec
BOOT_DIR="/data/data/com.termux/files/home/.termux/boot"
mkdir -p "$BOOT_DIR"

# 3. Tải file Bot (Thay link Raw của mày vào đây)
BOT_PATH="/sdcard/Download/bot.py"
BOT_RAW_LINK="https://raw.githubusercontent.com/mewAI36/bot-discord/refs/heads/main/bot.py"
curl -L -o "$BOT_PATH" "$BOT_RAW_LINK"

# 4. Tạo file tự chạy khi mở máy (Boot)
BOOT_FILE="$BOOT_DIR/start-bot.sh"
cat <<EOF > "$BOOT_FILE"
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
python $BOT_PATH
EOF

chmod +x "$BOOT_FILE"

echo "✅ Cài đặt xong! Đang chạy bot lần đầu..."
python "$BOT_PATH"
