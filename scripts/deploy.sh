#!/bin/bash

# ServiceMJ (Tadbikor.uz) Deployment Script - AWS Amazon Linux 2023
# Antigravity Protocol bo'yicha AWS muhiti uchun moslashtirilgan.

echo "🚀 Tizim yangilanmoqda (Amazon Linux)..."
sudo dnf update -y

echo "🐳 Docker va xizmatlarni tekshirish..."
if ! command -v docker &> /dev/null; then
    echo "Docker o'rnatilmoqda..."
    sudo dnf install docker -y
    sudo systemctl enable docker
    sudo systemctl start docker
    sudo usermod -aG docker ec2-user
fi

# Agar docker-compose o'rnatilmagan bo'lsa
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose o'rnatilmoqda..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

echo "📂 Loyihani GitHub-dan yuklab olish (ServiceMJ)..."
if [ -d "ServiceHub" ]; then
    cd ServiceHub
    git pull origin main
else
    git clone https://github.com/DasturchiMadaminjon/ServiceHub.git
    cd ServiceHub
fi

echo "⚙️ .env faylini tekshirish..."
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
    echo "⚠️ .env yaratildi. Iltimos, uning ichidagi parollar va tokenlarni serverga moslang!"
fi

echo "🏗 Docker konteynerlar ishga tushirilmoqda (Klassik usul)..."
# AWS muhitidagi Buildx versiyasi xatoligini aylanib o'tish uchun:
sudo DOCKER_BUILDKIT=0 COMPOSE_DOCKER_CLI_BUILD=0 docker-compose up -d --build

echo "🔄 Migratsiyalar bajarilmoqda..."
sudo docker-compose exec web python manage.py migrate

echo "✅ ServiceMJ loyihasi muvaffaqiyatli ishga tushdi!"
echo "📍 API Hujjatlari: https://tadbikor.uz/swagger/"