#!/bin/bash

# --- NEUROSCAN TELEGRAM WEBHOOK REGISTRATION ---

# ANSI color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. Load env variables from chat_backend/.env
ENV_FILE="chat_backend/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: chat_backend/.env file not found!${NC}"
    exit 1
fi

# Extract token
BOT_TOKEN=$(grep -E "^TELEGRAM_BOT_TOKEN=" "$ENV_FILE" | cut -d'=' -f2- | tr -d '"' | tr -d "'")

if [ -z "$BOT_TOKEN" ]; then
    echo -e "${RED}Error: TELEGRAM_BOT_TOKEN not found in $ENV_FILE${NC}"
    exit 1
fi

# 2. Get tunnel URL
TUNNEL_URL=$1
if [ -z "$TUNNEL_URL" ]; then
    echo -e "${YELLOW}Please enter your public HTTPS tunnel URL (e.g. https://xxxx.pinggy.link):${NC}"
    read -r TUNNEL_URL
fi

# Clean trailing slashes
TUNNEL_URL=$(echo "$TUNNEL_URL" | sed 's/\/$//')

# Basic validation
if [[ ! "$TUNNEL_URL" =~ ^https:// ]]; then
    echo -e "${RED}Error: The tunnel URL must start with https://${NC}"
    exit 1
fi

WEBHOOK_URL="${TUNNEL_URL}/webhook/telegram"

echo -e "\n${BLUE}=======================================${NC}"
echo -e "Registering webhook with Telegram..."
echo -e "Webhook URL: ${GREEN}${WEBHOOK_URL}${NC}"
echo -e "${BLUE}=======================================${NC}"

# 3. Call Telegram setWebhook API
RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"${WEBHOOK_URL}\"}")

OK=$(echo "$RESPONSE" | grep -o '"ok":true')

if [ -n "$OK" ]; then
    echo -e "${GREEN}✅ Webhook successfully registered with Telegram!${NC}"
    echo -e "Response: $RESPONSE"
else
    echo -e "${RED}❌ Failed to register webhook!${NC}"
    echo -e "Response: $RESPONSE"
    exit 1
fi

echo -e "\nChecking Webhook status..."
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo"
echo ""
echo -e "${BLUE}=======================================${NC}"
