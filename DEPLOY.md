# 🚀 Инструкция по деплою Yoga Asana Bot

## 📋 Подготовка

### 1. Настройте репозиторий
```bash
# Добавьте удаленный репозиторий (если еще не добавлен)
git remote add origin https://github.com/your-username/Dharana-Asana_Bot.git
git push -u origin main
```

### 2. Подготовьте .env файл
Создайте `.env` файл с токеном бота:
```env
BOT_TOKEN=your_telegram_bot_token_here
```

## 🖥️ Первоначальная настройка сервера

### 1. Подключитесь к серверу
```bash
ssh root@104.128.132.83
```

### 2. Скачайте и запустите скрипт настройки
```bash
# Скачайте скрипты (если еще не на сервере)
git clone https://github.com/your-username/Dharana-Asana_Bot.git /tmp/deploy
cd /tmp/deploy

# Сделайте скрипты исполняемыми
chmod +x setup-server.sh deploy.sh

# Запустите первоначальную настройку
./setup-server.sh
```

### 3. Или выполните вручную
```bash
# Обновление системы
apt update && apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl enable docker
systemctl start docker

# Установка Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Создание директории проекта
mkdir -p /opt/yoga-asana-bot
cd /opt/yoga-asana-bot
```

## 🚀 Деплой проекта

### Способ 1: Автоматический деплой с локальной машины

```bash
# Из корневой директории проекта
chmod +x deploy.sh
./deploy.sh
```

### Способ 2: Ручной деплой на сервере

```bash
# Подключитесь к серверу
ssh root@104.128.132.83

# Перейдите в директорию проекта
cd /opt/yoga-asana-bot

# Клонируйте репозиторий
git clone https://github.com/your-username/Dharana-Asana_Bot.git .

# Создайте .env файл
nano .env
# Добавьте: BOT_TOKEN=your_telegram_bot_token_here

# Запустите бота
docker-compose up -d --build
```

## 📊 Проверка и мониторинг

### Проверка статуса
```bash
# На сервере
cd /opt/yoga-asana-bot
docker-compose ps
```

### Просмотр логов
```bash
# Последние 20 строк
docker-compose logs --tail=20 yoga-bot

# Следить за логами в реальном времени
docker-compose logs -f yoga-bot
```

### Перезапуск бота
```bash
docker-compose restart yoga-bot
```

### Обновление бота
```bash
cd /opt/yoga-asana-bot
git pull origin main
docker-compose up -d --build
```

## 🔧 Управление сервисом

### Создание systemd сервиса (для автозапуска)
```bash
# На сервере
cp yoga-bot.service /etc/systemd/system/
systemctl enable yoga-bot
systemctl start yoga-bot

# Проверка статуса
systemctl status yoga-bot
```

## 🛠️ Решение проблем

### Проблема: Бот не отвечает
```bash
# Проверьте логи
docker-compose logs yoga-bot

# Проверьте токен в .env
cat .env

# Перезапустите контейнер
docker-compose restart
```

### Проблема: Нет доступа к файлам
```bash
# Проверьте права на директории
ls -la bot_data/
chmod -R 755 bot_data/
```

### Проблема: Проблемы с Docker
```bash
# Проверьте статус Docker
systemctl status docker

# Перезапустите Docker
systemctl restart docker

# Очистите Docker
docker system prune -f
```

## 📁 Структура на сервере

```
/opt/yoga-asana-bot/
├── src/                    # Исходный код
├── bot_data/              # Данные бота
│   ├── catalog/           # Асаны по категориям
│   ├── basics/            # Основы йоги
│   └── steps/             # Ступени йоги
├── logs/                  # Логи приложения
├── docker-compose.yml      # Docker конфигурация
├── Dockerfile            # Docker образ
├── requirements.txt       # Зависимости Python
├── .env                 # Переменные окружения
└── main.py              # Точка входа
```

## 🔐 Безопасность

### Настройка файрвола
```bash
# Включите файрвол
ufw enable

# Разрешите SSH
ufw allow ssh

# Проверьте статус
ufw status
```

### Настройка SSH ключей
```bash
# На локальной машине
ssh-copy-id root@104.128.132.83

# Отключите парольную аутентификацию
nano /etc/ssh/sshd_config
# PasswordAuthentication no
systemctl restart ssh
```

## 📈 Мониторинг

### Базовые метрики
```bash
# Использование ресурсов
htop
df -h
docker stats

# Логи системы
journalctl -u docker -f
```

### Опционально: Продвинутый мониторинг
Раскомментируйте секцию с Prometheus в `docker-compose.yml` для продвинутого мониторинга.

## ✅ Проверка работоспособности

После деплоя проверьте:
1. ✅ Бот отвечает на команды в Telegram
2. ✅ Логи без ошибок
3. ✅ Контейнер работает (docker-compose ps)
4. ✅ Автоматический перезапуск работает

## 🆘 Поддержка

Если возникли проблемы:
1. Проверьте логи: `docker-compose logs yoga-bot`
2. Проверьте статус: `docker-compose ps`
3. Перезапустите: `docker-compose restart`
4. Обновите: `git pull && docker-compose up -d --build`
