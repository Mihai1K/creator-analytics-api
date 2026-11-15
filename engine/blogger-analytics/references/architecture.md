# Intelligence Engine — архитектура

Это уже не «проверить блогера», а **система знаний**: блогер добавляется один раз, дальше движок
накапливает историю, объясняет изменения и отдаёт закупщику готовое решение с обоснованием.
Самый дорогой слой в продукте — не парсер, а вот эта надстройка над данными.

```
Blogger (URL)
    │
    ▼
Raw Data ─────────── extractors: telegram.py · tiktok.py(browser) · YouTube/VK API
    │                (server_html | browser_dom | embedded_json | official_api)
    ▼
Normalizer ───────── единая схема профиля (schema.md); пропуск ≠ 0
    │
    ▼
Confidence/Provenance ─ provenance.py: value·source·method·selector·confidence·reliability·updatedAt
    │                    reliability подтягивается из stress_test → reliability.json
    ▼
Quality Index ─────── quality.py: полнота×надёжность относительно ДОСТИЖИМОГО на площадке
    │                  (Telegram ~85 · логаут-TikTok ~38 · VK 0) — отдельно от Pulse
    ▼
Snapshots ─────────── snapshots.py: ProfileSnapshot на каждое обновление (followers/views/pulse/score/date)
    │                  → рост · падение · скачки · подозрительная динамика (накрутка)
    ▼
Analyzer / Score (FROZEN v1.0) ─ score.py: Pulse + 6 блоков (Audience/Activity/Engagement/Content/
    │                             Commercial/Risk) → TOTAL + вердикт. Формулы заморожены.
    ▼
Dynamics ──────────── объяснение движения: «Pulse ↓ 88→70 — −34% просмотров, −2 публикации/нед»
    │
    ▼
AI Report ─────────── текстом: почему покупать / почему нет / главные риски / что проверить вручную
    │                  + аудит медиакита (mediakit_audit.py): claimed vs факт → «устарел −71%»
    ▼
Buyer decision (PowerApp UI)
```

## Слои и файлы

| Слой | Файл | Статус |
|---|---|---|
| Извлечение | `telegram.py`, `tiktok.py`, extractors.md | ✅ (TG server; TikTok browser; YT/VK API) |
| Нормализация | schema.md | ✅ |
| Provenance | `provenance.py` | ✅ value·method·source·selector·confidence·reliability·updatedAt |
| Надёжность | `stress_test.py` → `reliability.json` | ✅ per-field fill-rate, авто-понижение |
| Quality Index | `quality.py` | ✅ отдельно от Pulse |
| История | `snapshots.py` | ✅ ProfileSnapshot + dynamics + причины Pulse |
| Скоринг | `score.py` **v1.0 FROZEN** | ✅ Pulse + 6 блоков |
| Медиакит-аудит | `mediakit_audit.py` | ✅ claimed vs факт |
| Фон | `update_runner.py` | ✅ add once → auto-update + alerts; cron/launchd |
| AI-отчёт | этап в SKILL.md (модель) | ✅ шаблон; генерится Claude |
| UI PowerApp | контракт (ниже) | ⏳ отдать как JSON-эндпоинт |

## Дорожная карта (по приоритету CTO)

1. **v1.0 заморожена** — Pulse/Score не менять, пока не накопится история. Любое изменение → bump VERSION с обоснованием на данных.
2. **Снимки включены** — `update_runner.py run` пишет ProfileSnapshot при каждом обновлении; динамика появляется со 2-го прогона.
3. **Фон** — `run` по cron/launchd (например ежечасно для Telegram; TikTok/YT/VK — по мере доступа к браузеру/ключам). Блогер добавляется один раз (`add`), дальше сам.
4. **UI PowerApp** — движок отдаёт по блогеру JSON: `{identity, size, score{blocks}, pulse, quality, provenance, dynamics, ai_report}` — карточка закупщика читает это, а не запускает парсер. Контракт зафиксировать до интеграции.

## Принцип, который делает это ценным
Не «максимум полей», а **честность + история + объяснение**. Недоступное = `недоступно` (не
`estimated`). Каждое поле знает свой источник и надёжность. Цифра всегда объяснена динамикой.
Именно это превращает набор чисел в систему, которой доверяет закупщик.
