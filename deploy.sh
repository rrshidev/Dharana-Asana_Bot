#!/bin/bash

# Скрипт деплоя Yoga Asana Bot
# Использование: ./deploy.sh

set -e  # Выход при любой ошибке

# Конфигурация
SERVER_IP="104.128.132.83"
PROJECT_DIR="/opt/yoga-asana-bot"
SERVICE_NAME="yoga-bot"
GIT_REPO="https://github.com/your-username/Dharana-Asana_Bot.git"  # Замените на ваш репозиторий

echo "🚀 Начинаем деплой Yoga Asana Bot на сервер $SERVER_IP..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция вывода
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

# Проверка SSH соединения
log "Проверка соединения с сервером..."
if ! ssh root@$SERVER_IP "echo 'SSH соединение установлено'" 2>/dev/null; then
    error "Не удалось установить SSH соединение с сервером $SERVER_IP"
    exit 1
fi

# Создание директории проекта на сервере
log "Создание директории проекта..."
ssh root@$SERVER_IP "mkdir -p $PROJECT_DIR"

# Клонирование или обновление репозитория
log "Клонирование/обновление репозитория..."
ssh root@$SERVER_IP "
cd /opt
if [ -d yoga-asana-bot ]; then
    cd yoga-asana-bot
    git pull origin main
    log 'Репозиторий обновлен'
else
    git clone $GIT_REPO yoga-asana-bot
    log 'Репозиторий склонирован'
fi
"

# Копирование .env файла (если существует)
if [ -f .env ]; then
    log "Копирование .env файла на сервер..."
    scp .env root@$SERVER_IP:$PROJECT_DIR/
    log ".env файл скопирован"
else
    warn ".env файл не найден. Необходимо создать его на сервере."
fi

# Установка зависимостей и запуск
log "Установка зависимостей и запуск бота..."
ssh root@$SERVER_IP "
cd $PROJECT_DIR

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    log 'Установка Docker...'
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl enable docker
    systemctl start docker
fi

# Проверка наличия Docker Compose
if ! command -v docker-compose &> /dev/null; then
    log 'Установка Docker Compose...'
    curl -L \"https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Создание необходимых директорий
mkdir -p bot_data/catalog bot_data/basics bot_data/steps logs

# Остановка предыдущего контейнера
docker-compose down 2>/dev/null || true

# Сборка и запуск
docker-compose up -d --build

# Очистка
docker image prune -f

log 'Бот запущен!'
"

# Проверка статуса
log "Проверка статуса контейнера..."
ssh root@$SERVER_IP "
cd $PROJECT_DIR
docker-compose ps
docker-compose logs --tail=20 yoga-bot
"

log "✅ Деплой успешно завершен!"
log "🤖 Бот должен быть доступен в Telegram"
log "📊 Для проверки логов: ssh root@$SERVER_IP 'cd $PROJECT_DIR && docker-compose logs -f yoga-bot'"
