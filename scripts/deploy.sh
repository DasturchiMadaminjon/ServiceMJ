#!/bin/bash

# ServiceHub.uz Deployment Script
# Bu skript Ubuntu serverida Docker-ni o'rnatadi va loyihani ishga tushiradi.

echo "🚀 Tizim yangilanmoqda..."
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release

echo "🐳 Docker o'rnatilmoqda..."
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

echo "📂 Loyihani GitHub-dan yuklab olish..."
# Agar papka mavjud bo'lsa yangilaydi, bo'lmasa klonlaydi
if [ -d "ServiceHub" ]; then
    cd ServiceHub
    git pull origin main
else
    git clone https://github.com/DasturchiMadaminjon/ServiceHub.git
    cd ServiceHub
fi

echo "⚙️ .env faylini yaratish..."
# Bu yerda .env faylini yaratib oling yoki qo'lda to'ldiring
if [ ! -f ".env" ]; then
    cat <<EOT >> .env
DEBUG=0
SECRET_KEY=$(openssl rand -hex 32)
ALLOWED_HOSTS=*
DATABASE_URL=postgres://admin:secretpass@db:5432/servicehub_db
CELERY_BROKER_URL=redis://redis:6379/0
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_ADMIN_CHAT_ID=your_chat_id_here
EOT
    echo "⚠️ .env yaratildi. Iltimos, Telegram tokenlarini o'zgartiring!"
fi

echo "🏗 Docker konteynerlar ishga tushirilmoqda..."
sudo docker compose up -d --build

echo "🔄 Migratsiyalar bajarilmoqda..."
sudo docker compose exec web python manage.py migrate

echo "✅ Deployment yakunlandi!"
echo "📍 Loyiha manzili: http://$(curl -s ifconfig.me):8000/swagger/"
