.PHONY: install migrate user-bot admin-bot scheduler run-all test docker-up docker-down

install:
	python3 -m pip install -r requirements.txt

migrate:
	alembic upgrade head

user-bot:
	python3 -m app.run_user_bot

admin-bot:
	python3 -m app.run_admin_bot

scheduler:
	python3 -m app.run_scheduler

run-all:
	python3 -m app.main

test:
	pytest -q

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down
