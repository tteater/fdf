# Telegram Price Tracker Bot (Production-Ready)

Async, modular, and scalable Telegram price tracker bot for Indian e-commerce platforms with affiliate conversion, scraper fallback chain, scheduler workers, and admin observability.

## Highlights

- Message-only UX: users paste product links directly (no `/track` command flow).
- Supported stores: Amazon India, Flipkart, Ajio, Myntra, Meesho, Nykaa, Reliance Digital, Croma, Tata Cliq, Snapdeal.
- Intelligent scraping fallback chain:
  - `aiohttp + BeautifulSoup` (primary)
  - `Scrapling` (anti-bot/JS fallback)
  - `Playwright` (final fallback)
- EarnKaro affiliate integration with graceful degradation.
- Async SQLAlchemy + PostgreSQL + Redis.
- APScheduler worker for automatic checks and daily summaries.
- Separate admin bot for stats and monitoring.
- Structured logging (console + rotating file).
- Alembic migrations.
- Dockerized multi-service deployment.

## Architecture

- `app/bots`: user bot + admin bot runners.
- `app/handlers`: aiogram routers for user flow and admin commands.
- `app/middlewares`: anti-spam rate limiting and DB session middleware.
- `app/services`: business logic (tracking, affiliate conversion, monitor, notifications, stats).
- `app/scrapers`: platform scrapers + fallback adapters + orchestrator.
- `app/database`: models, repositories, async session management.
- `app/schedulers`: recurring monitor jobs.
- `app/utils`: URL tools, formatting, charts.
- `alembic`: migration config and versions.

## Message-Only User Flow

1. User pastes URL in chat.
2. Bot auto-detects URL and platform.
3. Validates if product-like URL.
4. Scrapes product data.
5. Converts link via EarnKaro API.
6. Stores tracker + history.
7. Replies with tracking-started card.
8. Scheduler checks prices every interval.
9. Bot sends price-drop/back-in-stock alerts.

## Supported Alert Types

- Price drop alerts
- Back in stock alerts
- Massive discount alerts
- Daily summary alerts

## Admin Bot

Admin bot commands:

- `/stats` → total users, active trackers, failed trackers, uptime, scrape success rate, top stores, affiliate stats
- `/uptime` → uptime only

Events logged to DB + optional admin chat notifications:

- product added
- scraping failed
- tracking creation failures
- monitor job failures
- API/auth/rate-limit issues

## Scraper Fallback Design

`Normal Scraper -> Scrapling -> Playwright -> graceful failure`

The orchestrator captures each strategy failure and returns a unified error without crashing the bot.

## EarnKaro Integration

POST `https://ekaro-api.affiliaters.in/api/converter/public`

Headers:
- `Authorization: Bearer <token>`
- `Content-Type: application/json`

Body:
```json
{
  "deal": "{product_url}",
  "convert_option": "convert_only"
}
```

Handled cases:

- Success (`success=1`)
- Unauthorized (`401` / authenticate error)
- Rate limit (`429` / too many requests)
- Invalid/unsupported URLs
- Network/API failures

If conversion fails, the tracker still uses original URL.

## Project Structure

```text
.
├── app
│   ├── admin_bot
│   ├── bots
│   ├── core
│   ├── database
│   │   ├── models
│   │   └── repositories
│   ├── handlers
│   │   ├── admin
│   │   └── user
│   ├── middlewares
│   ├── schedulers
│   ├── scrapers
│   │   ├── fallback
│   │   └── platforms
│   ├── services
│   ├── utils
│   ├── main.py
│   ├── run_admin_bot.py
│   ├── run_scheduler.py
│   └── run_user_bot.py
├── alembic
│   └── versions
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Setup (Local)

1. Create env file:
```bash
cp .env.example .env
```
2. Fill Telegram and EarnKaro credentials.
3. Install dependencies:
```bash
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
playwright install chromium
```
4. Run migrations:
```bash
alembic upgrade head
```
5. Start processes (separate terminals):
```bash
python -m app.run_user_bot
python -m app.run_admin_bot
python -m app.run_scheduler
```

## Setup (Docker)

```bash
docker compose up -d --build
```

Includes: `postgres`, `redis`, migration job, `user-bot`, `admin-bot`, `scheduler`.

## Environment Variables

See `.env.example` for full list.

Critical:

- `TELEGRAM_BOT_TOKEN`
- `ADMIN_BOT_TOKEN`
- `ADMIN_CHAT_ID`
- `DATABASE_URL`
- `REDIS_URL`
- `EARNKARO_API_TOKEN`

## Security and Reliability Notes

- No hardcoded secrets
- Parametrized SQLAlchemy queries (SQL injection safe)
- User rate limiting middleware (anti-spam)
- Retries with exponential backoff
- Structured logging
- Graceful failure handling for scraping/API/database issues
- Healthcheck script for DB/Redis

## Scaling Notes

- Multi-process architecture (user bot/admin bot/scheduler)
- Repository + service abstractions for testability
- Add stores by implementing scraper class + registry entry
- Tune scheduler concurrency and DB pool for traffic growth

## Optional Enhancements Ready to Extend

- Celery worker variant
- Proxy rotation strategy
- Multi-language response templates
- Referral reward accounting
- Affiliate earnings estimation dashboards
- CSV export command/menu flow

## Testing Strategy (recommended)

- Unit tests for services/repositories/scraper parsing
- Integration tests for DB + scheduler
- Mocked Telegram/EarnKaro API tests
- Contract tests for platform selector accuracy

