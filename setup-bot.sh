#!/data/data/com.termux/files/usr/bin/bash

echo "🚀 --- HỆ THỐNG SETUP MEW-BOT TỰ ĐỘNG ---"

# 1. Cấp quyền và tạo folder
termux-setup-storage -y
pkg update -y && pkg install python curl -y
pip install discord.py
mkdir -p /sdcard/Download/Shouko/switched
mkdir -p /sdcard/Download/Shouko/Autoexec
mkdir -p ~/.termux/boot

# 2. HỎI TÊN MÁY VÀ TỰ TẠO FILE NAME.TXT
# Bước này chỉ chạy khi mày cài máy bằng installer
echo "------------------------------------------------"
read -p "📝 Nhập tên cho máy này (ví dụ: mew-1): " input_name
echo "$input_name" > /sdcard/Download/name.txt
echo "✅ Đã lưu tên máy: $input_name"
echo "------------------------------------------------"

# 3. Tải file Bot
BOT_PATH="/sdcard/Download/bot.py"
BOT_RAW_LINK="https://raw.githubusercontent.com/mewAI36/bot-discord/refs/heads/main/bot.py"
curl -L -o "$BOT_PATH" "$BOT_RAW_LINK"

# 4. Tạo file Boot (Chạy ngầm không cần input)
BOOT_FILE="$HOME/.termux/boot/start-bot.sh"
cat <<EOF > "$BOOT_FILE"
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
python $BOT_PATH
EOF
chmod +x "$BOOT_FILE"

echo "🔥 Cài đặt xong! Đang khởi động bot..."
python "$BOT_PATH"
