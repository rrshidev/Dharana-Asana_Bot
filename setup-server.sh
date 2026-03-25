#!/bin/bash

# Скрипт первоначальной настройки сервера для Yoga Asana Bot
# Использование: ./setup-server.sh

set -e

# Конфигурация
PROJECT_DIR="/opt/yoga-asana-bot"
SERVICE_NAME="yoga-bot"

echo "🔧 Начинаем первоначальную настройку сервера..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

# Обновление системы
log "Обновление системы..."
apt update && apt upgrade -y

# Установка базовых пакетов
log "Установка базовых пакетов..."
apt install -y curl wget git htop unzip software-properties-common

# Установка Docker
log "Установка Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    usermod -aG docker root
    systemctl enable docker
    systemctl start docker
    log "Docker установлен и запущен"
else
    log "Docker уже установлен"
fi

# Установка Docker Compose
log "Установка Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    log "Docker Compose установлен"
else
    log "Docker Compose уже установлен"
fi

# Создание директории проекта
log "Создание директории проекта..."
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# Настройка файрвола
log "Настройка файрвола..."
ufw --force enable
ufw allow ssh
ufw allow 80
ufw allow 443

# Установка и настройка Nginx (опционально, для веб-интерфейса)
log "Установка Nginx..."
apt install -y nginx

# Создание конфига для Nginx
cat > /etc/nginx/sites-available/yoga-bot << 'EOF'
server {
    listen 80;
    server_name _;
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# Можно добавить конфиг для веб-интерфейса мониторинга в будущем
EOF

ln -sf /etc/nginx/sites-available/yoga-bot /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

# Создание директорий для логов
mkdir -p /opt/yoga-asana-bot/logs

# Установка утилит для мониторинга
log "Установка утилит для мониторинга..."
apt install -y ncdu iotop

# Очистка
log "Очистка..."
apt autoremove -y
apt autoclean
rm -f get-docker.sh

log "✅ Первоначальная настройка сервера завершена!"
log "📁 Директория проекта: $PROJECT_DIR"
log "🐳 Docker: $(docker --version)"
log "🔧 Docker Compose: $(docker-compose --version)"
log "🌐 Nginx: $(nginx -v)"

echo ""
echo "🚀 Следующие шаги:"
echo "1. Скопируйте проект в $PROJECT_DIR"
echo "2. Создайте .env файл с токеном бота"
echo "3. Запустите: docker-compose up -d"
echo ""
echo "📊 Полезные команды:"
echo "- Проверить статус: docker-compose ps"
echo "- Посмотреть логи: docker-compose logs -f yoga-bot"
echo "- Перезапустить: docker-compose restart"
