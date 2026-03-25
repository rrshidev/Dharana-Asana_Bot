# Makefile для Yoga Asana Bot

.PHONY: help install run build deploy clean logs restart status test

# Переменные
SERVER_IP = 104.128.132.83
PROJECT_DIR = /opt/yoga-asana-bot
SERVICE_NAME = yoga-bot

help: ## Показать эту справку
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Установить зависимости локально
	pip install -r requirements.txt

run: ## Запустить бота локально
	python main.py

build: ## Собрать Docker образ
	docker build -t yoga-bot .

test: ## Запустить тесты
	python -m pytest tests/ -v

deploy: ## Деплой на сервер
	@echo "🚀 Начинаем деплой на сервер $(SERVER_IP)..."
	./deploy.sh

setup-server: ## Первоначальная настройка сервера
	@echo "🔧 Настройка сервера $(SERVER_IP)..."
	scp setup-server.sh root@$(SERVER_IP):/tmp/
	ssh root@$(SERVER_IP) "chmod +x /tmp/setup-server.sh && /tmp/setup-server.sh"

logs: ## Посмотреть логи бота на сервере
	ssh root@$(SERVER_IP) "cd $(PROJECT_DIR) && docker-compose logs -f yoga-bot"

status: ## Проверить статус на сервере
	ssh root@$(SERVER_IP) "cd $(PROJECT_DIR) && docker-compose ps"

restart: ## Перезапустить бота на сервере
	ssh root@$(SERVER_IP) "cd $(PROJECT_DIR) && docker-compose restart yoga-bot"

stop: ## Остановить бота на сервере
	ssh root@$(SERVER_IP) "cd $(PROJECT_DIR) && docker-compose down"

update: ## Обновить бота на сервере
	@echo "🔄 Обновление бота..."
	ssh root@$(SERVER_IP) "cd $(PROJECT_DIR) && git pull origin main && docker-compose up -d --build"

clean: ## Очистить Docker образы
	docker system prune -f

backup: ## Создать бэкап данных
	@echo "💾 Создание бэкапа..."
	ssh root@$(SERVER_IP) "cd $(PROJECT_DIR) && tar -czf /tmp/bot-data-backup-$(shell date +%Y%m%d).tar.gz bot_data/"
	scp root@$(SERVER_IP):/tmp/bot-data-backup-$(shell date +%Y%m%d).tar.gz ./

dev: ## Запустить в режиме разработки
	BOT_TOKEN=$(shell cat .env) python main.py

lint: ## Проверить код линтером
	flake8 src/ --max-line-length=100 --ignore=E501,W503

format: ## Отформатировать код
	black src/
	isort src/

init: ## Инициализация проекта
	@echo "🚀 Инициализация проекта..."
	python -m venv venv
	@echo "Активируйте виртуальное окружение:"
	@echo "source venv/bin/activate  # Linux/Mac"
	@echo "venv\\Scripts\\activate     # Windows"
	@echo "Затем выполните: make install"

# Команды для разработки
dev-deps: ## Установить зависимости для разработки
	pip install -r requirements.txt
	pip install pytest black flake8 isort

test-coverage: ## Запустить тесты с покрытием
	python -m pytest tests/ --cov=src --cov-report=html

security-check: ## Проверить безопасность зависимостей
	pip install safety
	safety check

# Команды для продакшена
prod-build: ## Собрать продакшн образ
	docker build -f Dockerfile.prod -t yoga-bot:prod .

prod-deploy: ## Деплой в продакшн
	@echo "🚀 Продакшн деплой..."
	ENV=production ./deploy.sh
