#!/data/data/com.termux/files/usr/bin/bash

echo "🚀 --- ĐANG CÀI ĐẶT BOT VÀO HỆ THỐNG BOOT ---"

# 1. Cài đặt môi trường cơ bản
termux-setup-storage -y
pkg update -y && pkg install python curl -y
pip install discord.py

# 2. Tạo các folder cần thiết (nếu chưa có)
mkdir -p /sdcard/Download/Shouko/switched
mkdir -p /sdcard/Download/Shouko/Autoexec
mkdir -p ~/.termux/boot/

# 3. Tải bot.py về máy
BOT_PATH="/sdcard/Download/bot.py"
curl -L -o "$BOT_PATH" "https://raw.githubusercontent.com/mewAI36/bot-discord/refs/heads/main/bot.py"

# 4. TẠO FILE CHẠY TRONG FOLDER BOOT
BOOT_FILE="~/.termux/boot/start-bot.sh"
echo "#!/data/data/com.termux/files/usr/bin/bash" > $BOOT_FILE
echo "termux-wake-lock" >> $BOOT_FILE  # Giữ cho bot không bị ngủ khi tắt màn hình
echo "python $BOT_PATH" >> $BOOT_FILE

# Cấp quyền chạy cho file boot
chmod +x $BOOT_FILE

echo "✅ Đã nạp bot vào folder boot thành công!"
echo "🔄 Đang khởi động bot lần đầu..."
python $BOT_PATH
