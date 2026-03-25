# Deploy script for Yoga Asana Bot (PowerShell)
# Usage: .\deploy.ps1

param(
    [string]$ServerIP = "104.128.132.83",
    [string]$ProjectDir = "/opt/yoga-asana-bot",
    [string]$GitRepo = "https://github.com/your-username/Dharana-Asana_Bot.git"
)

Write-Host "🚀 Начинаем деплой Yoga Asana Bot на сервер $ServerIP..." -ForegroundColor Green

# Проверка соединения с сервером
Write-Host "Проверка соединения с сервером..." -ForegroundColor Yellow
try {
    $result = ssh root@$ServerIP "echo 'SSH соединение установлено'"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ SSH соединение установлено" -ForegroundColor Green
    } else {
        Write-Host "❌ Не удалось установить SSH соединение" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Ошибка SSH соединения: $_" -ForegroundColor Red
    exit 1
}

# Копирование .env файла если существует
if (Test-Path ".env") {
    Write-Host "Копирование .env файла на сервер..." -ForegroundColor Yellow
    scp .env root@$ServerIP`:$ProjectDir/
    Write-Host "✅ .env файл скопирован" -ForegroundColor Green
} else {
    Write-Host "⚠️ .env файл не найден. Необходимо создать его на сервере." -ForegroundColor Yellow
}

# Деплой на сервер
Write-Host "Выполнение деплоя на сервере..." -ForegroundColor Yellow
$sshCommand = @"
cd $ProjectDir

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    echo "Установка Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl enable docker
    systemctl start docker
fi

# Проверка наличия Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "Установка Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-`uname -s`-`uname -m`" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Клонирование или обновление репозитория
if [ -d .git ]; then
    echo "Обновление репозитория..."
    git pull origin main
else
    echo "Клонирование репозитория..."
    git clone $GitRepo .
fi

# Создание необходимых директорий
mkdir -p bot_data/catalog bot_data/basics bot_data/steps logs

# Остановка предыдущего контейнера
docker-compose down 2>/dev/null || true

# Сборка и запуск
docker-compose up -d --build

# Очистка
docker image prune -f

echo "✅ Бот запущен!"
"@

ssh root@$ServerIP $sshCommand

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Деплой успешно завершен!" -ForegroundColor Green
    Write-Host "🤖 Бот должен быть доступен в Telegram" -ForegroundColor Green
    Write-Host "📊 Для проверки логов: ssh root@$ServerIP 'cd $ProjectDir && docker-compose logs -f yoga-bot'" -ForegroundColor Cyan
} else {
    Write-Host "❌ Ошибка деплоя" -ForegroundColor Red
    exit 1
}
