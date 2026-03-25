# 🚀 Деплой Yoga Asana Bot на сервер 104.128.132.83

## 📋 Что готово:

✅ **Масштабируемая архитектура** - код разделен на модули  
✅ **Docker контейнеризация** - готовые Dockerfile и docker-compose.yml  
✅ **Скрипты деплоя** - автоматизация развертывания  
✅ **Мониторинг** - healthcheck и логирование  
✅ **Безопасность** - .gitignore и защита токена  

## 🎯 Быстрый деплой (рекомендуется)

### Шаг 1: Подготовьте .env файл
Убедитесь что `.env` файл содержит токен:
```env
BOT_TOKEN=your_telegram_bot_token_here
```

### Шаг 2: Первоначальная настройка сервера
```bash
# Подключитесь к серверу
ssh root@104.128.132.83

# Скачайте и выполните скрипт настройки
curl -fsSL https://raw.githubusercontent.com/your-username/Dharana-Asana_Bot/main/setup-server.sh | bash
```

### Шаг 3: Деплой проекта
**Из Windows (PowerShell):**
```powershell
# Из корня проекта
.\deploy.ps1
```

**Из Linux/Mac:**
```bash
# Из корня проекта
chmod +x deploy.sh
./deploy.sh
```

**Или вручную на сервере:**
```bash
ssh root@104.128.132.83
cd /opt/yoga-asana-bot
git clone https://github.com/your-username/Dharana-Asana_Bot.git .
nano .env  # добавьте токен
docker-compose up -d --build
```

## 📊 Проверка деплоя

### Статус контейнера:
```bash
ssh root@104.128.132.83 "cd /opt/yoga-asana-bot && docker-compose ps"
```

### Логи бота:
```bash
ssh root@104.128.132.83 "cd /opt/yoga-asana-bot && docker-compose logs -f yoga-bot"
```

### Перезапуск:
```bash
ssh root@104.128.132.83 "cd /opt/yoga-asana-bot && docker-compose restart"
```

## 🛠️ Управление через Makefile

```bash
# Показать все команды
make help

# Деплой
make deploy

# Проверить статус
make status

# Посмотреть логи
make logs

# Перезапустить
make restart

# Обновить
make update
```

## 📁 Структура на сервере

```
/opt/yoga-asana-bot/
├── src/                    # Исходный код
├── bot_data/              # Данные бота
├── logs/                  # Логи
├── docker-compose.yml      # Конфигурация Docker
├── .env                  # Токен бота
└── main.py              # Точка входа
```

## 🔧 Решение проблем

### Бот не отвечает:
```bash
# Проверьте логи
ssh root@104.128.132.83 "cd /opt/yoga-asana-bot && docker-compose logs yoga-bot"

# Проверьте токен
ssh root@104.128.132.83 "cd /opt/yoga-asana-bot && cat .env"

# Перезапустите
ssh root@104.128.132.83 "cd /opt/yoga-asana-bot && docker-compose restart"
```

### Проблемы с Docker:
```bash
# Проверьте статус Docker
ssh root@104.128.132.83 "systemctl status docker"

# Перезапустите Docker
ssh root@104.128.132.83 "systemctl restart docker"
```

## ✅ Что должно работать после деплоя:

1. ✅ Бот отвечает на /start
2. ✅ Каталог асан работает
3. ✅ Фотографии асан отображаются
4. ✅ Основы йоги и ступени работают
5. ✅ Автоматический перезапуск при падении
6. ✅ Логи пишутся в logs/

## 🔄 Обновление бота

```bash
# Простое обновление
make update

# Или вручную
ssh root@104.128.132.83 "cd /opt/yoga-asana-bot && git pull && docker-compose up -d --build"
```

## 📈 Мониторинг

### Базовые метрики:
```bash
# Использование ресурсов
ssh root@104.128.132.83 "docker stats"

# Место на диске
ssh root@104.128.132.83 "df -h /opt/yoga-asana-bot"
```

### Healthcheck:
Контейнер автоматически проверяет состояние каждые 30 секунд

## 🎉 Готово!

После выполнения этих шагов бот будет работать на сервере 104.128.132.83 и будет доступен 24/7 с автоматическим перезапуском.

**Ссылка для проверки:** Найдите бота в Telegram по @yogaasana_bot или используйте ваш токен для создания нового бота.
