# 🧘‍♂️ Yoga Asana Bot

Telegram-бот для энциклопедии йогических асан с каталогом, описаниями и фотографиями.

## ✨ Возможности

- 📚 **Каталог асан** - более 100 асан, классифицированных по типам
- 🖼️ **Фотографии** - качественные фото и миниатюры для каждой асаны
- 📝 **Подробные описания** - техника выполнения и польза асан
- 🎲 **Асана дня** - случайная асана для ежедневной практики
- 📖 **Основы йоги** - базовые понятия и термины
- 🔢 **8 ступеней йоги** - классическая система Аштанга-йоги
- 🔍 **Поиск по названию** - быстрый поиск асан по имени

## 🏗️ Архитектура проекта

```
src/
├── handlers/          # Обработчики сообщений и команд
│   ├── command_handlers.py
│   ├── callback_handlers.py
│   └── message_handlers.py
├── services/          # Бизнес-логика
│   └── data_service.py
├── models/            # Модели данных
│   └── data_models.py
└── utils/             # Утилиты
    └── keyboard_service.py
```

## 🚀 Быстрый старт

### Локальный запуск

1. **Клонируйте репозиторий**
   ```bash
   git clone <repository-url>
   cd Dharana-Asana_Bot
   ```

2. **Создайте виртуальное окружение**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # или
   venv\Scripts\activate     # Windows
   ```

3. **Установите зависимости**
   ```bash
   pip install -r requirements.txt
   ```

4. **Создайте файл .env**
   ```env
   BOT_TOKEN=your_telegram_bot_token_here
   ```

5. **Запустите бота**
   ```bash
   python main.py
   ```

### Docker запуск

1. **С помощью Docker Compose**
   ```bash
   docker-compose up -d
   ```

2. **Или с помощью Docker**
   ```bash
   docker build -t yoga-bot .
   docker run -d --name yoga-bot --env BOT_TOKEN=your_token yoga-bot
   ```

## 📁 Структура данных

```
bot_data/
├── catalog/           # Асаны по категориям
│   ├── sit_lie+/     # Асаны сидя и лёжа
│   ├── stay+/         # Асаны стоя
│   ├── hand+/         # Балансы на руках
│   ├── coup+/         # Перевёрнутые асаны
│   ├── sag+/          # Прогибы
│   └── power+/        # Силовые асаны
├── basics/            # Основы йоги
└── steps/             # 8 ступеней йоги
```

## 🔧 Конфигурация

### Переменные окружения

- `BOT_TOKEN` - токен Telegram бота (обязательно)

### Формат данных

**Асаны:**
- `имя_асаны.txt` - описание асаны
- `имя_асаны.jpg` - основное фото
- `имя_асаны.png` - миниатюра

**Основы йоги и ступени:**
- `название.txt` - текстовое описание
- `название.png` - изображение (опционально)

## 📝 Команды бота

- `/start` - запуск бота
- `/help` - справка
- `/what` - о возможностях бота
- `/info` - информация об асанах
- `/about_us` - об авторах проекта

## 🐳 Docker

### Сборка образа
```bash
docker build -t yoga-bot .
```

### Запуск с volume
```bash
docker run -d \
  --name yoga-bot \
  --env BOT_TOKEN=your_token \
  -v $(pwd)/bot_data:/app/bot_data \
  yoga-bot
```

## 🔧 Разработка

### Добавление новой асаны

1. Создайте папку для категории в `bot_data/catalog/`
2. Добавьте файлы:
   - `имя_асаны.txt` - описание
   - `имя_асаны.jpg` - фото
   - `имя_асаны.png` - миниатюра
3. Обновите `asana_descriptions` в `src/services/data_service.py`

### Добавление новой категории

1. В `src/services/data_service.py` добавьте описание в `asana_descriptions`
2. Создайте папку в `bot_data/catalog/`
3. Добавьте асаны в папку

## 🚀 Деплой

### На сервере с Docker

1. **Клонируйте репозиторий**
   ```bash
   git clone <repository-url>
   cd Dharana-Asana_Bot
   ```

2. **Настройте .env**
   ```bash
   cp .env.example .env
   # Отредактируйте .env с вашим токеном
   ```

3. **Запустите с Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Проверьте логи**
   ```bash
   docker-compose logs -f yoga-bot
   ```

### Без Docker

1. Установите зависимости: `pip install -r requirements.txt`
2. Настройте переменные окружения
3. Запустите: `python main.py`

## 🤝 Вклад в проект

1. Fork проекта
2. Создайте feature branch: `git checkout -b feature/new-feature`
3. Commit изменения: `git commit -am 'Add new feature'`
4. Push в branch: `git push origin feature/new-feature`
5. Создайте Pull Request

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. Подробности в файле LICENSE.

## 👥 Авторы

- **Олег** - автор проекта, фото, описание, идеи (@yogaolleg)
- **Ришидэв** - автор бота, идейный вдохновитель (@RrshiDev)

## 🙏 Благодарности

Проект является частью online-школы йоги [Dharana.ru](https://dharana.ru)

---

📧 Для связи и вопросов: [@yogaolleg](https://instagram.com/yogaolleg)
