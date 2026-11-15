# Analytics API (`api.mediacentr.online`)

Backend **одного** продукта, а не второй сервис. Точки входа (`check.`, `app.`) ходят сюда, база и движок — общие.

## Принципы (не нарушать)

1. **Алгоритмы не копируются.** `engine_link.py` импортирует `telegram.py` / `score.py` из
   `.claude/skills/blogger-analytics/scripts/`. Реализация Pulse/Score ровно одна, `score.VERSION` заморожен на 1.0.
   Менять формулу → менять там и бампать VERSION.
2. **Raw никогда не теряем.** `CreatorCheck.raw_data` хранит сырой ответ площадки целиком → новую формулу можно
   пересчитать по истории без повторного обхода (t.me анти-флуд делает обход дорогим).
   Поэтому провайдер зовёт `fetch()` + `parse()` раздельно, а не `analyze()` (тот HTML выбрасывает).
3. **Детерминированный контур — без LLM.** fetch → normalize → pulse → score считается кодом.
   LLM (summary / recommendations / explanation) — отдельный слой сверху: его можно отключить, заменить, продать.
4. **Кэш обязателен, а не желателен.** t.me отказывает на повторный запрос через секунду (проверено).
   `DEFAULT_MAX_AGE = 6h`; slug резолвится офлайн, поэтому свежая проверка отдаётся вообще без сети.
5. **Открыто / закрыто.** `facts` (подписчики, просмотры, ER, частота) — публично и индексируемо.
   `verdict` (pulse / score / blocks / reasons) — за регистрацию: и юридически безопаснее (152-ФЗ,
   деловая репутация), и конвертирует.

## Запуск

```bash
cd "<корень проекта>"
python3 -m venv .venv && ./.venv/bin/pip install -r api/requirements.txt
./.venv/bin/uvicorn api.main:app --reload      # http://127.0.0.1:8000/docs
```

БД: по умолчанию SQLite (`./creators.db`). На VPS — Postgres:
```bash
export DATABASE_URL="postgresql+psycopg://user:pass@host/db"
```

## Эндпоинты

| Метод | Путь | Что |
|---|---|---|
| POST | `/check` | `{"url": "https://t.me/durov", "force": false}` → `facts` + `verdict` + `from_cache` |
| GET | `/creators` | последние проверенные авторы |
| GET | `/creators/{id}/history` | история проверок (динамика Pulse/Score) |
| GET | `/health` | + версия движка |

## Схема

- **Creator** — автор на площадке. Уникален по `(platform, external_id)`; повторная проверка переиспользует строку.
- **CreatorCheck** — одна проверка в один момент: `raw_data`, `normalized_data`, `pulse`, `score`, `report`,
  `engine_version`. История = много таких.
- **CreatorSnapshot** — не заводим, пока не понадобится отдельно от `CreatorCheck`.

## Совместимость

Код писан под **Python 3.9** (на рабочей машине только системный 3.9.6), на 3.11+ идёт без изменений.
Поэтому в моделях `Optional[...]`, а не `str | None` (SQLAlchemy резолвит аннотации в рантайме).

## Проверено вживую (2026-07-15, @durov)

| | |
|---|---|
| 1-я проверка | 1.32 с · 11.7M подписчиков · PULSE=50 SCORE=73 🟡 · raw 138 278 симв. |
| Повторная | **0.003 с из кэша** (×440), t.me не тронут, дубля Creator нет |
| `force=True` сразу | анти-флуд t.me → подтверждает п.4 |

## Дальше

- фронт `check.mediacentr.online` (статика поверх этого API)
- деплой на VPS (диск с запасом: ~138 КБ raw/проверка → ~1.4 ГБ на 10k; позже gzip ×8–10)
- провайдеры: TikTok (нужен браузер), RuTube (публичные api/), VK (только по токену)
