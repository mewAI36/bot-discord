#!/data/data/com.termux/files/usr/bin/bash

clear

echo "━━━━━━━━━━━━━━━━━━━━"
echo "   DISCORD BOT SETUP"
echo "━━━━━━━━━━━━━━━━━━━━"

sleep 1

echo ""
echo "[1/5] Updating packages..."
pkg update -y && pkg upgrade -y

echo ""
echo "[2/5] Installing dependencies..."
pkg install -y \
python \
git \
curl \
wget

echo ""
echo "[3/5] Installing python modules..."
pip install --upgrade pip
pip install -U \
discord.py \
requests

echo ""
echo "[4/5] Setting up bot..."

mkdir -p ~/bot-discord
cd ~/bot-discord || exit

curl -fsSL https://raw.githubusercontent.com/mewAI36/bot-discord/main/main.py -o main.py

echo ""
echo "[5/5] Finished!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━"
echo " Run bot:"
echo " python main.py"
echo "━━━━━━━━━━━━━━━━━━━━"
