# Карта данных платформ

Какие поля публичной страницы блогера реально извлекаются и **каким способом** — для 8 площадок. Сгенерировано из параллельного исследования (8 агентов); эмпирика TikTok/Telegram/YouTube/VK подтверждена в этой сессии.

**Способ (method):** `HTML` = server-fetch публичного HTML · `JSON` = вшитый в страницу JSON · `Browser` = рендер JS во встроенном браузере · `API` = официальный API (ключ/токен).  
**Доверие (trust):** `verified` = с офиц. поверхности/рендера · `public` = публичная страница (может округлять/отставать) · `estimated` = вычислено/выведено.  
**P / S** — влияет на **Pulse** (живость) / **Score** (закупка).

## Сводка: что доступно по площадкам

| Площадка | Осн. способ | Подписчики | Повидео/пост-вовлечённость | Гео | РКН | Публично без ключа? |
|---|---|---|---|---|---|---|
| **Telegram** | HTML | ✅ | ✅ | ✅ | ✅ | ✅ (t.me/s/) |
| **TikTok** | JSON | ✅ | ✅ | ✅ | ✅ | ✅ (браузер) |
| **YouTube** | API | ✅ | ✅ | ✅ | ✅ | 🟡 (браузер: подписчики; точно — API) |
| **VK (VKontakte)** | API | ✅ | ✅ | ✅ | ✅ | ❌ (только API-токен) |
| **RuTube** | JSON | ✅ | ✅ | — | ✅ | ✅ (JSON rutube.ru/api) |
| **Дзен (Zen / dzen.ru — ex-Яндекс.Дзен, с 2022 принадлежит VK)** | JSON | ✅ | ✅ | — | — | 🟡 |
| **Одноклассники (OK.ru)** | HTML | ✅ | ✅ | ✅ | ✅ | 🟡 |
| **MAX (max.ru) — мессенджер VK/госэкосистемы; публичные КАНАЛЫ** | API | ✅ | ✅ | — | ✅ | 🟡 |


---

## Telegram

**Резюме.** Telegram is the most extraction-friendly of the studied platforms for basic public data: t.me/s/<channel> is clean server-rendered HTML (no JS, no login) giving name, @username, subscribers, description, and per-post text/date/views/reactions at high stability. Native gaps (categories, geo/language, ERR, citation index, reach, forwards, comment counts, subscriber history) are filled by the official Bot API/MTProto (structural fields) and the TGStat aggregator (analytics, trust=estimated). РКН mark and ad contacts live in the self-written description text; verification is a native badge.

- **Server-fetch:** works — PRIMARY method. GET https://t.me/s/<channel> returns full public HTML with no login: channel title, @username, subscribers/photos/videos/links counters, description (with link/mention/hashtag…
- **Browser:** works — the embedded headless browser renders t.me/s/<channel> and t.me/<channel> fully, but it is rarely needed: the /s/ feed is already server-side rendered HTML. Browser useful for lazy elements o…
- **Официальный API:** Three tiers. (1) Bot API via bot token: getChat(@username) works on PUBLIC channels WITHOUT the bot joining — returns title, username, description, invite_link, pinned_message, linked_chat_id, photo, available_reactions; getChatMemberCount…
- **Юр-заметка:** t.me/s/<channel> is publicly served HTML requiring no login; fetching it for manual, case-by-case due diligence is analogous to visiting a public web page and is low-risk. Keep it to human-rate, per-target lookups — Telegram's ToS and API …

| Поле | Способ | Стаб. | Доверие | P | S | Заметка |
|---|---|---|---|:-:|:-:|---|
| name | HTML | high | verified | · | · | Display title of the channel. Also present via all official APIs; server_html is simplest… |
| username | HTML | high | verified | · | · | @handle. Channels can hold multiple active usernames (MTProto active_usernames / TGStat a… |
| bio/description | HTML | high | public | · | ✓ | Self-written. Carries the highest-value due-diligence signal: РКН mark, ad-manager contac… |
| avatar | HTML | high | public | · | · | Profile photo URL. Channel may use an animated/video profile photo; still exposed as an i… |
| followers/subscribers | HTML | high | verified | · | ✓ | Core buying metric. /s counter is often the full number (e.g. 23 845) or abbreviated; get… |
| views | HTML | high | public | ✓ | ✓ | Per-post view counts on the /s feed (abbreviated K/M). Average reach and 12/24/48h ad-rea… |
| pinned_posts | API | med | verified | · | · | Reliable via getChat.pinned_message. The /s feed shows a pinned service label inconsisten… |
| recent_posts | HTML | high | public | ✓ | ✓ | Last ~16-20 posts with full text, entities, media type, forwarded-from, reply, and link-p… |
| post_dates | HTML | high | verified | ✓ | · | Exact ISO timestamps per post. Combined with sequential message ids (data-post) lets you … |
| posting_frequency | HTML | high | estimated | ✓ | ✓ | Computed metric (posts/day, gaps, last-active). High input stability but the frequency fi… |
| links | HTML | high | public | · | ✓ | All outbound links in bio and posts, plus rich link-preview cards (site name/title/descri… |
| geo/country | API | med | estimated | · | ✓ | Not a native Telegram public field. TGStat classifies country/audience geography heuristi… |
| РКН-отметка | HTML | med | public | · | ✓ | Telegram has no native РКН field. Detected as text in the owner's description (server_htm… |
| verification | HTML | high | verified | · | ✓ | Native Telegram verified checkmark rendered in HTML. MTProto additionally exposes scam/fa… |
| contacts (email/tg) | HTML | med | public | · | ✓ | Ad/booking contact almost always in the description ('по рекламе @...', email). Self-decl… |
| external_links (other socials) | HTML | med | public | · | ✓ | Cross-platform footprint for building a unified creator profile. Extract from bio links a… |
| categories/topics | API | med | estimated | · | ✓ | No native category on the public page. TGStat assigns a curated category (aggregator judg… |
| reactions | HTML | high | public | ✓ | ✓ | Emoji-level breakdown with counts per post, directly on the /s feed. Enables reaction-mix… |
| ER/ERR | API | med | estimated | ✓ | ✓ | Public HTML lets you compute a partial ER (reactions/views) since it lacks forwards+comme… |
| forwards/reposts | API | med | estimated | ✓ | ✓ | Per-post forward counts are not rendered in the /s HTML. TGStat provides forward volumes … |
| comments | API | low | estimated | ✓ | ✓ | The /s feed does not show per-post comment counts. Comments exist only if a discussion gr… |
| citation_index | API | med | estimated | · | ✓ | How often the channel is mentioned/forwarded by other channels (>100 = authoritative per … |
| reach_metrics | API | med | estimated | ✓ | ✓ | Reach (not just raw views) used to price ad placements; adv_post_reach_48h is the standar… |
| subscriber_history/growth | API | med | estimated | ✓ | ✓ | Growth curve exposes nakrutka (subscriber spikes not matched by view/reach growth) and gi… |
| linked_chat_id | API | high | verified | · | ✓ | Presence of a discussion group = comments enabled = a healthier engagement surface; also … |
| media_mix/content_types | HTML | high | public | · | ✓ | Content format distribution and video durations, straight from the /s feed. Useful for ma… |
| post_ids/total_post_count | HTML | high | verified | ✓ | ✓ | Highest visible message id approximates lifetime post volume; id gaps across the feed rev… |
| available_reactions_set | API | med | public | · | · | Which reactions the channel permits (all / custom subset / disabled). Minor context field. |
| counters (photos/videos/files/links) | HTML | med | public | · | ✓ | Lifetime media/link totals shown alongside subscribers. Coarse content-volume profile; no… |

_Недоступно публично: cover, following, likes_total, premium_share/watch_time._

**Антифрод-сигналы (Telegram):**
- Views-to-subscribers ratio far below niche norm (e.g. avg views < 8-10% of subscribers) → dead or bought subscribers; the classic Telegram nakrutka tell.
- Subscriber spikes in TGStat history not matched by parallel growth in views/reach → purchased subscribers or giveaway churn.
- Reactions-per-view and ERR abnormally low for the niche (<2-3%) → passive or bot audience.
- Citation index (TGStat ci_index) near zero despite a large subscriber base → no organic mentions, audience likely inflated.
- Comments/discussion disabled (no linked_chat_id) on a supposedly large engaged channel → hides weak real engagement.
- Elevated views only on paid/ad posts vs organic posts → bought views targeted at advertiser-facing placements.
- Recent channel creation date (TGStat created_at / low max message id) combined with high subscriber count → bought growth.
- Message-id gaps showing heavy post deletion → scrubbing of failed or flagged ad content.
- Uniform / suspiciously round reaction counts, or reactions clustered on a single emoji → reaction farming.
- Inbound forwards concentrated from known mutual-PR / ad-exchange networks (TGStat forwards/mentions) → traffic bought via exchanges rather than organic.
- MTProto scam/fake/restricted flags set, or РКН marking absent for a monetized RU channel → compliance and trust risk.


---

## TikTok

**Резюме.** Оптимальный путь для due-diligence: рендерящий браузер открывает публичный профиль → извлекаем вшитый __UNIVERSAL_DATA_FOR_REHYDRATION__ (userInfo.user + userInfo.stats + itemList) как первоисточник точных чисел, плюс read_page для оверлеев просмотров на плитках. Простой HTTP-fetch ненадёжен (заглушка). Масштабные/точные данные — официальный Research API (одобрение) или Display API (согласие создателя). Профиль НЕ показывает публично: агрегированные просмотры профиля, watch-time, демографию аудитории, счётчик репостов — это только приватная TikTok Analytics владельца.

- **Server-fetch:** partial/gated — в сыром HTML вшит богатый JSON (__UNIVERSAL_DATA_FOR_REHYDRATION__, legacy SIGI_STATE) со ВСЕМИ полями профиля и первой страницей видео. НО простой server-fetch без JS/заголовков/куки…
- **Browser:** works — встроенный headless-браузер с JS полностью рендерит публичный профиль (@handle, nickname, подписки/подписчики/лайки, bio, аватар, сетка последних видео с оверлеем просмотров через read_page).…
- **Официальный API:** gated — (1) Research API: query_user_info + query_videos + followers/following/pinned/reposted/liked/comments, точные метрики, НО только одобренным исследователям, некоммерческое использование, гео-ограничения (изначально US/EU-акценты). (…
- **Юр-заметка:** TikTok ToS и robots.txt запрещают автоматический скрейпинг и обход анти-бот защиты; массовый сбор — нарушение. Трактуем работу как РУЧНУЮ due-diligence: открываем ПУБЛИЧНЫЙ профиль через собственный браузер, низкий объём, без обхода CAPTCH…

| Поле | Способ | Стаб. | Доверие | P | S | Заметка |
|---|---|---|---|:-:|:-:|---|
| name (nickname / отображаемое имя) | JSON | high | verified | · | ✓ | Свободно задаётся создателем; часто содержит эмодзи/позиционирование. Дублируется во всех… |
| username (@handle / uniqueId) | JSON | high | verified | · | · | Первичный ключ сущности. Меняется редко. Для API-пагинации нужен ещё secUid (см. ниже). |
| bio / description (signature) | JSON | high | verified | · | ✓ | Ключевое поле для парсинга: РКН-отметка, рекламный контакт, ссылки на другие соцсети, поз… |
| avatar | JSON | high | verified | · | · | URL на CDN (истекающие подписи). Полезен для реверс-поиска/детекции стоковых фото. |
| followers / subscribers (followerCount) | JSON | high | verified | · | ✓ | В браузере округление, в JSON/API точное число. Сток-метрика охвата → влияет на закупку, … |
| following (followingCount) | JSON | high | verified | · | ✓ | Соотношение following/followers — антифрод-сигнал (масс-фолловинг у ботоферм). |
| likes_total (heartCount / heart) | JSON | high | verified | · | ✓ | Кумулятивная сумма лайков по всем видео. Проверка консистентности: heartCount ~ сумма dig… |
| video_count (videoCount) | JSON | high | verified | ✓ | ✓ | Объём продакшена. В связке с датами → интенсивность выпуска. |
| views (per-video playCount) | JSON | high | verified | ✓ | ✓ | Главная метрика охвата поста. В браузере плитки ленивые (med), в JSON/API точно (high). А… |
| per-video likes (diggCount) | JSON | high | verified | ✓ | ✓ | На плитке в браузере не показывается — только на странице видео; из JSON достаётся сразу. |
| per-video comments (commentCount) | JSON | high | verified | ✓ | ✓ | Комментарии могут быть отключены создателем (0). Тексты комментов — только через Research… |
| per-video shares (shareCount) | JSON | high | verified | ✓ | ✓ | Аналог 'репостов' на уровне поста (виральность). |
| per-video saves / bookmarks (collectCount) | JSON | med | verified | ✓ | ✓ | Иногда отсутствует в старых снапшотах JSON. Сильный сигнал полезности контента. |
| ER (engagement rate) | JSON | med | estimated | ✓ | ✓ | Расчётная. Не поле площадки — вычисляется из per-video stats. Ключевой антифрод/качество-… |
| pinned_posts (закреплённые) | JSON | med | verified | · | ✓ | Что создатель сам выставил витриной (часто лучшие/брендированные интеграции) — сигнал поз… |
| recent_posts (лента последних видео) | JSON | high | verified | ✓ | ✓ | Первая страница — high из вшитого JSON. Глубокая пагинация требует secUid+cursor (браузер… |
| post_dates (createTime) | JSON | high | verified | ✓ | · | В браузерной сетке дата не видна (только на странице видео) → берём из JSON. Основа для r… |
| posting_frequency (частота выпуска) | JSON | med | estimated | ✓ | · | Расчётная (постов/неделю, регулярность). Зависит от окна выборки. Прямой признак 'живости… |
| links (bio-ссылка / сайт) | JSON | high | verified | · | ✓ | Один слот сайта (доступен не всем аккаунтам). ВАЖНО: bioLink.risk — собственный скам-риск… |
| external_links (другие соцсети: IG/YT/TG) | JSON | low | estimated | · | ✓ | Структурные IG/YT-линки непостоянны; надёжнее регексом по signature (@, t.me/, instagram.… |
| contacts (email / telegram) | JSON | low | estimated | · | ✓ | Нет структурного публичного поля email. Достаётся только если создатель вписал контакт в … |
| geo / country (region) | JSON | med | public | · | ✓ | region = регион РЕГИСТРАЦИИ аккаунта, НЕ гео аудитории и не точная локация. Демография ау… |
| РКН-отметка | JSON | low | public | · | ✓ | Не структурное поле — саморегистрируемая пометка создателя в bio. Важно для юр.чистоты РФ… |
| verification (галочка) | JSON | high | verified | · | ✓ | Официальная верификация TikTok (не путать с текстовыми 'галочками' в нике). |
| categories / topics | JSON | med | estimated | · | ✓ | Явная категория только у бизнес-аккаунтов; иначе выводится из топ-хэштегов/звуков. Основа… |
| hashtags / mentions (по постам) | JSON | high | verified | · | ✓ | Тематический отпечаток и коллаборации (@упоминания брендов/блогеров). |
| music / sound (по постам) | JSON | high | verified | ✓ | · | Флаг original sound (авторский звук) и участие в трендах. Косвенный сигнал типа контента. |
| video_duration | JSON | high | verified | · | · | Формат контента (короткие vs длинные). Watch-time/удержание публично НЕ раскрываются. |
| TikTok Shop / seller (ttSeller, commerceUser) | JSON | med | verified | · | ✓ | Индикатор коммерческого/продающего аккаунта (TikTok Shop / Business). Сигнал монетизации … |
| privateAccount (флаг приватности) | JSON | high | verified | · | ✓ | Гейтинг: если true → itemList пуст, посты/просмотры недоступны, анализ невозможен. Провер… |
| secUid (внутренний стабильный ID) | JSON | high | verified | · | · | Не метрика, а технический ключ: нужен для пагинации ленты и вызовов внутренних эндпоинтов… |

_Недоступно публично: cover / banner, watch-time / avg view duration / демография аудитории, reposts count (счётчик репостов профиля), premium-доля / citation index (индекс цитирования)._

**Антифрод-сигналы (TikTok):**
- bioLink.risk — собственный скам-риск-флаг TikTok на bio-ссылке (прямо в embedded_json, готовый сигнал)
- Соотношение following/followers: аномально высокое число подписок при больших подписчиках → масс-фолловинг/ботоферма
- Разрыв followerCount ↔ playCount: много подписчиков, но просмотры последних видео на порядки ниже → накрученные подписчики
- Likes/Views вне нормального коридора (обычно ~3–15%): <2% или >30% diggCount/playCount → накрутка лайков или мёртвая аудитория
- Comments/Likes аномально низкое или комментарии отключены при высоких охватах → искусственная активность
- Консистентность heartCount ↔ сумма diggCount по постам и videoCount: расхождение указывает на манипуляции/удалённый контент
- Кластеризация просмотров: у всех видео подозрительно одинаковый playCount (ровные 'полки') → ботовый трафик
- verified=false при заявленной 'галочке' в нике — попытка выдать себя за верифицированного
- region (страна регистрации) не совпадает с языком контента/заявленной аудиторией
- privateAccount=true или очень мало видео при огромном followerCount → купленный/перепроданный аккаунт
- Резкие всплески подписчиков — требуют серии снапшотов во времени (одиночный fetch не ловит; движку нужен трекинг)
- Шаблонные/дублирующиеся комментарии — детектируются только через Research API comments-эндпоинт
- collectCount≈0 при высоких лайках — контент 'лайкают', но не сохраняют → слабая органика/накрутка


---

## YouTube

**Резюме.** Best engine design: YouTube Data API v3 as the authoritative source for all counts/metadata (channels.list + uploads-playlist enumeration + batched videos.list), plus the headless browser ONLY for fields the API does not expose — external/social Links, the verified badge, and any creator self-labels (РКН/contacts) in visible text. Avoid page-scraping for numbers the API already gives precisely and ToS-compliantly. Watch-time, retention, audience demographics and revenue/Premium share are OWNER-only (YouTube Analytics API, OAuth) and unavailable for third-party public analysis.

- **Server-fetch:** partial — a plain GET of youtube.com/@handle returns HTML with a large embedded ytInitialData / ytInitialPlayerResponse JSON blob (embedded_json) containing most header + video-grid fields, but it is…
- **Browser:** works — built-in headless browser with JS renders the channel header at youtube.com/@handle or /channel/<id>: display name, @handle, subscriber count (rounded, e.g. '405K subscribers'), video count, …
- **Официальный API:** works and is the recommended path — YouTube Data API v3 with an API key. Key endpoints: channels.list (snippet, statistics, brandingSettings, contentDetails, topicDetails, status), playlistItems.list (enumerate the uploads playlist cheaply…
- **Юр-заметка:** The YouTube Data API v3 (API key, default 10,000 quota units/day) is the ToS-compliant path and should be the primary source for all counts and metadata; it explicitly authorizes programmatic read access. Rendering the public channel page …

| Поле | Способ | Стаб. | Доверие | P | S | Заметка |
|---|---|---|---|:-:|:-:|---|
| name | API | high | verified | · | · | Identity field. API is authoritative; browser DOM mirrors it. |
| username | API | high | verified | · | · | customUrl returns the @handle for eligible channels. Canonical channelId (UC...) also ret… |
| bio/description | API | high | verified | · | ✓ | Primary source to parse for contacts, other socials, РКН self-label, topics. localization… |
| avatar | API | high | verified | · | · | CDN URLs. Presence of custom avatar is a low-signal quality cue. |
| cover/banner | API | high | verified | · | · | Base URL that YouTube resizes; append =w{n} for sizes. |
| followers/subscribers | API | high | verified | ✓ | ✓ | API value is ROUNDED DOWN to 3 significant figures (e.g. 405000, not 405512). Browser tex… |
| views (channel total) | API | high | verified | ✓ | ✓ | Lifetime total video views across the channel. Combine with videoCount for avg-views-per-… |
| video_count | API | high | verified | ✓ | ✓ | Counts PUBLIC uploads only. Basis for posting cadence and avg-views math. |
| channel_created / join_date | API | high | verified | · | ✓ | Account age. Young channel + very high subs is an anti-fraud cue. |
| pinned_posts / featured video | API | med | public | · | ✓ | unsubscribedTrailer is the closest API analog to a 'pinned' item. Pinned community posts … |
| recent_posts (videos) | API | high | verified | ✓ | ✓ | Uploads-playlist enumeration is the cheap, stable way to page all uploads. Avoid search.l… |
| post_dates | API | high | verified | ✓ | · | Exact ISO timestamps via API vs. fuzzy relative dates in DOM. Drives recency and cadence. |
| posting_frequency | API | high | estimated | ✓ | ✓ | Computed (e.g. uploads/last 30d, median gap). Not a raw field. Long silence or erratic ga… |
| links / external_links (other socials) | Browser | med | public | · | ✓ | Confirmed absent from Data API v3 (brandingSettings has no links field). Only reliably ob… |
| geo/country | API | med | public | · | ✓ | Self-declared and OFTEN EMPTY. It is the creator's country, NOT audience geo (audience ge… |
| РКН-отметка | API | low | estimated | · | ✓ | YouTube has NO native РКН marking. Only present if the creator writes it themselves in th… |
| verification (badge) | Browser | med | public | · | ✓ | No official-API field for the verification/official-artist badge. Detect via rendered DOM… |
| categories/topics | API | med | public | · | ✓ | topicCategories gives coarse niche (Wikipedia URLs). keywords (space-separated, ≤500 char… |
| per_video_views | API | high | verified | ✓ | ✓ | Exact integer via API vs rounded in DOM. NOTE: for Shorts (since 2025-03-31) a 'view' = e… |
| per_video_likes | API | high | verified | ✓ | ✓ | Core engagement input. likes/views ratio is a key authenticity metric (bought views → nea… |
| per_video_comments | API | high | verified | ✓ | ✓ | Count via statistics; commentThreads.list (public) returns text/author/likeCount for sent… |
| engagement_rate (ER) | API | high | estimated | ✓ | ✓ | Computed from API stats. YouTube has no reposts/shares in public API, so ER = likes+comme… |
| duration / format mix (Shorts vs long) | API | high | verified | · | ✓ | ≤ ~60s (or #shorts) ≈ Short. Drives content-strategy classification and correct view-metr… |
| live status / concurrent viewers | API | med | verified | ✓ | · | concurrentViewers only meaningful during an active broadcast. Indicates live/streamer for… |
| thumbnails / hasCustomThumbnail | API | high | verified | · | ✓ | Custom thumbnails on most videos = production-quality signal. |
| language | API | med | public | · | ✓ | Often empty; when present helps infer audience language/market alongside country. |
| madeForKids | API | high | verified | · | ✓ | Kids-directed channels have comments/ads restrictions → material for ad-buy suitability. |

_Недоступно публично: following, likes_total, contacts (email/tg), dislikeCount, watch_time / retention / audience_demographics, premium_share / revenue, citation_index._

**Антифрод-сигналы (YouTube):**
- avg-views-per-video (viewCount/videoCount) wildly below subscriberCount, or subs >> typical views → likely purchased subscribers
- like-to-view ratio near zero on high-view videos → bought/incentivized views (organic YouTube long-form is typically ~2-5% likes/views)
- comment-to-view ratio near zero, or comments disabled, on otherwise 'viral' numbers
- subscriberCount hidden (hiddenSubscriberCount=true) → deliberate opacity, downgrade trust
- channel age (snippet.publishedAt) very recent vs very high subscriberCount → bought growth
- view distribution concentrated in 1-2 videos while the rest are near-zero → single fluke / bought spike, not sustained reach
- Shorts-heavy channels: Short 'views' (each start/replay since 2025-03-31) inflate viewCount vs long-form — normalize before comparing ER
- commentThreads.list content that is generic/repetitive/emoji-only across many videos → bot-comment farm
- erratic or long-idle posting cadence (from publishedAt series) contradicting a 'growing' subscriber claim
- engagement bought unevenly: high likes but near-zero comments (or vice versa) — genuine engagement usually correlates
- time-series divergence: poll subscriberCount/viewCount over days; sudden step-jumps with no matching upload/view growth signal artificial injection
- self-declared country/language inconsistent with comment-language and title language → possible bought international audience


---

## VK (VKontakte)

**Резюме.** VK для стороннего аналитика фактически «API-only»: публичный веб закрыт логином и анти-ботом, а официальный VK API отдаёт почти все нужные поля по токену. Богатые метрики (охват, пол/возраст, источники переходов) доступны лишь владельцу через stats.get. Агрегированного 'всего лайков' в VK нет — считается суммированием по wall.get.

- **Server-fetch:** blocked — простой GET на vk.com/vk.ru редиректит на логин, WebFetch/server-fetch отдаёт 'unable to fetch vk.com'. Полезного публичного HTML или встроенного JSON (как __UNIVERSAL_DATA__ у TikTok) на в…
- **Browser:** gated — vk.com отдаёт login-wall и агрессивный анти-бот; headless-навигация встроенного браузера вышла по таймауту (эмпирика сессии). Публичный профиль/сообщество в DOM не рендерится без залогина. Мо…
- **Официальный API:** primary path — api.vk.com/method/<method>?...&access_token=<token>&v=5.199. Публичное чтение по сервисному или пользовательскому токену VK-приложения: groups.getById, users.get, wall.get, wall.getComments, video.get, groups.getMembers. sta…
- **Юр-заметка:** Публичный веб-скрейпинг vk.com нарушает Правила VK и технически заблокирован (login-wall + анти-бот; браузер/сервер-fetch падают). Санкционированный путь — официальный VK API (api.vk.com) с access_token из VK-приложения: сервисный ключ для…

| Поле | Способ | Стаб. | Доверие | P | S | Заметка |
|---|---|---|---|:-:|:-:|---|
| name | API | high | public | · | · | Базовое отображаемое имя. Всегда присутствует. |
| username | API | high | public | · | · | Короткий адрес vk.com/<screen_name>. Стабилен, служит ключом для повторных запросов. |
| bio_description | API | high | public | · | · | В описании/статусе часто самодекларация РКН, рекламный контакт (tg/@, email), внешние ссы… |
| avatar | API | high | public | · | · | Прямые CDN-URL нескольких размеров. |
| cover | API | med | public | · | · | Поле cover есть в актуальной версии API (v5.x); возвращается только если обложка включена… |
| followers_subscribers | API | high | verified | · | ✓ | Ключевая метрика закупки — размер аудитории. Для сообщества members_count, для персональн… |
| following | API | med | public | · | ✓ | Только для персональных страниц. counters может быть скрыт приватностью. Соотношение подп… |
| views | API | high | public | ✓ | ✓ | Самая близкая к охвату метрика без админ-доступа. Присутствует на постах сообществ; может… |
| pinned_posts | API | high | public | · | · | Закреплённый пост часто содержит оффер/прайс/контакт рекламодателя. |
| recent_posts | API | high | public | ✓ | ✓ | Ядро анализа: контент, форматы (video/photo/link/market), частота рекламных вставок. Закр… |
| post_dates | API | high | public | ✓ | · | Точные даты/время публикаций для расчёта каденса и свежести. |
| posting_frequency | API | med | estimated | ✓ | · | Не нативное поле — производная от дат. Длинные паузы = падение живости/риск мёртвого кана… |
| links | API | high | public | · | · | Блок внешних ссылок сообщества (name+url) и поле сайта. |
| geo_country | API | med | public | · | ✓ | Часто пустое (не заполнено владельцем). Гео аудитории (реальное) — только в stats.get у а… |
| rkn_mark | API | low | estimated | · | ✓ | Официального API-флага РКН/иноагента нет. Извлекается text-mining'ом описания/статуса; UI… |
| verification | API | high | verified | · | ✓ | Синяя галочка VK. Признак подлинности/значимости аккаунта. |
| contacts | API | med | public | · | · | Публичны только если владелец их выставил. Email/телефон менеджера часто в contacts сообщ… |
| external_links | API | med | public | · | · | Кросс-платформенные соцсети блогера для оценки суммарного охвата. У пользователей — поле … |
| categories_topics | API | high | public | · | ✓ | activity даёт нишу сообщества (напр. 'Блог', 'Красота'). Релевантность ниши продукту — фа… |
| likes_per_post | API | high | public | ✓ | ✓ | Legacy-метрика, присутствует всегда. Базовый вход в расчёт ER. |
| reactions | API | med | public | ✓ | ✓ | Расширенные реакции (сердце/огонь и т.п.) поверх лайков; зависят от версии API и включённ… |
| reposts | API | high | public | ✓ | ✓ | Сильный сигнал вовлечённости/виральности; входит в ER. |
| comments | API | high | public | ✓ | ✓ | Счётчик всегда, тексты — если комментарии открыты. Анализ тональности/ботности комментов … |
| engagement_rate | API | med | estimated | ✓ | ✓ | Производная метрика (не нативная). ER к охвату (views) точнее ER к подписчикам; аномально… |
| counters_content | API | med | public | · | · | Объём контента и наличие market/товаров — контекст масштаба. Часть счётчиков требует прав… |
| online_last_seen | API | med | public | ✓ | · | Только персональные страницы. Свежий last_seen = живой автор. Может скрываться приватност… |
| video_views | API | med | public | ✓ | ✓ | Для видеоблогеров/VK Клипов. watch-time (время досмотра) публично НЕ отдаётся. |
| audience_quality_deactivated | API | med | estimated | · | ✓ | Доля deactivated/banned среди подписчиков = оценка ботности/мёртвых аккаунтов. getMembers… |
| ban_info | API | low | public | · | ✓ | Наличие ban_info — стоп-фактор закупки. |
| wall_access_flags | API | high | public | · | · | Определяет, доступна ли стена для анализа. is_closed>0 или can_see_all_posts=0 → wall.get… |
| followers_growth | API | med | estimated | ✓ | ✓ | Динамика прироста считается своим движком через регулярный поллинг; резкие скачки = накру… |

_Недоступно публично: likes_total, reach_demographics, premium_share_citation_index._

**Антифрод-сигналы (VK (VKontakte)):**
- views/members: низкое отношение просмотров поста к числу подписчиков → накрученные/мёртвые подписчики
- ER к охвату vs ER к подписчикам: расхождение указывает на разбавленную аудиторию
- Доля deactivated/banned в groups.getMembers → боты/собачки в подписной базе
- Аномальное соотношение лайки/комментарии/репосты (много лайков при нуле комментов = накрутка реакций)
- Соотношение подписки/подписчики у персональной страницы → масс-фолловинг ради ответных подписок
- Провалы в каденсе постинга (posting_frequency) и резкое падение views на свежих постах → угасающий канал
- Скачки members_count/followers_count в таймсерии без роста охвата → закупка подписчиков
- Отсутствие verified при заявленной крупной аудитории
- Ban_info != null или age_limits/жалобы → рисковый аккаунт
- Комментарии выключены (comments.can_post=0) при закупке под нативную рекламу → нельзя оценить реакцию
- Однотипные/ботные тексты в wall.getComments → накрученная вовлечённость
- Views.count отсутствует на постах (старый/личный профиль) → нельзя верифицировать охват, повышенный риск


---

## RuTube

**Резюме.** RuTube — самая «щедрая» из площадок для due-diligence: недокументированный, но открытый публичный JSON REST (rutube.ru/api/*) отдаёт подписчиков, суммарные и повидеовые просмотры, число видео, дату создания канала, верификацию, РКН-регистрацию (10k+/Госуслуги), описание, аватар/обложку, полную ленту видео с датами, теги, категории, возрастной рейтинг, флаги платного/клубного контента и полное число + тексты комментариев — server-side, без браузера и ключа. Пробелы: лайки/дизлайки видео, репосты, watch-time, гео и список подписок пользователя публично НЕ отдаются. МЕТОД: в терминах чек-листа маркирую эти /api/-эндпоинты как embedded_json = «структурированный JSON, извлекаемый server-side без рендер-браузера и без ключа»; это отдельные JSON REST-эндпоинты (НЕ вшитый в HTML блок и НЕ документированный ключевой API) — точные URL указаны в notes каждого поля. browser_dom оставлен как запасной путь для видимых на странице чисел.

- **Server-fetch:** works (главный путь) — ПРОСТОЙ server-side GET к недокументированным JSON-эндпоинтам rutube.ru/api/* возвращает богатый JSON БЕЗ браузера, БЕЗ логина и БЕЗ ключа (в отличие от TikTok/VK). Ключевые: /…
- **Browser:** works — встроенный headless-браузер рендерит SSR-страницу канала/видео (Next.js). get_page_text отдаёт отображаемое имя, подписчиков, число видео, описание, а на видео — заголовок, просмотры (напр. «…
- **Официальный API:** none для статистики. Официального stats/subscriber API с ключом нет. Есть полу-официальный партнёрский «витринный» API (rutube/ShowcaseTutorial: /api/feeds/<slug>, /api/metainfo/tv/<id>/video) для построения витрин, не для аналитики блогер…
- **Юр-заметка:** Эндпоинты rutube.ru/api/* недокументированы, но публичны и отдают данные без авторизации; тем не менее Пользовательское соглашение RuTube запрещает автоматизированный массовый сбор и обход анти-бот механизмов. Трактуем доступ как РУЧНУЮ du…

| Поле | Способ | Стаб. | Доверие | P | S | Заметка |
|---|---|---|---|:-:|:-:|---|
| name | JSON | high | verified | · | · | Отображаемое имя канала. Недокументированный публичный JSON-эндпоинт, server GET без ключ… |
| username | JSON | high | verified | · | · | У RuTube канал = числовой user_id + необязательный vanity-хэндл (short_url). Хэндл 'rutub… |
| bio_description | JSON | high | public | · | ✓ | Свободный текст. Часто содержит внешние ссылки, рекламный контакт, ссылку на Госуслуги (д… |
| avatar | JSON | high | verified | · | · | Прямой CDN-URL. appearance.default_image = дефолтная заглушка — если avatar_image совпада… |
| cover | JSON | high | verified | · | · | Обложка/шапка канала + фоновый цвет. CDN pic.rtbcdn.ru. |
| subscribers | JSON | high | verified | · | ✓ | Точное число подписчиков, отдаётся площадкой. Ключевая метрика закупки. Пример RUTUBE=221… |
| channel_total_views | JSON | high | verified | · | ✓ | Кумулятивные просмотры всех видео канала (пример RUTUBE=131.9M). hits/subscribers и hits/… |
| video_count | JSON | high | verified | ✓ | ✓ | Число опубликованных видео. Вместе с date_joined даёт средний темп загрузки за всю истори… |
| date_joined | JSON | high | verified | · | ✓ | Дата создания канала = возраст. Молодой канал с большим subscribers_count — антифрод-сигн… |
| channel_last_update | JSON | med | public | ✓ | · | Метка последнего обновления профиля/канала. Приблизительный сигнал живости; точнее живост… |
| verification | JSON | high | verified | · | ✓ | is_official = верифицированный/официальный канал. Значимо для доверия и закупки. kind_sig… |
| rkn_registration | JSON | high | verified | · | ✓ | АНАЛОГ РКН-отметки на RuTube: is_ten_thousand=true означает канал 10k+, обязанный к регис… |
| external_links | JSON | low | estimated | · | ✓ | Ссылки на другие соцсети/сайты приходится извлекать регэкспом из description. Нет гаранти… |
| contacts_email_tg | JSON | low | estimated | · | ✓ | Email/Telegram для рекламы — если блогер указал в описании. Парсинг текста; часто отсутст… |
| categories_topics | JSON | med | estimated | · | ✓ | На уровне канала отдельной категории нет — тематику выводим агрегацией категорий/тегов по… |
| monetization_donations | JSON | high | public | · | ✓ | Зрелость монетизации канала: включены ли донаты, есть ли платный/клубный контент. RuTube-… |
| channel_type | JSON | high | public | · | · | Тип канала (пользователь vs ТВ-шоу/витрина). is_reborn_channel — канал, перенесённый/импо… |
| recent_posts | JSON | high | verified | ✓ | ✓ | Полная лента видео канала с пагинацией — ядро pulse-анализа. Каждая карточка несёт свои п… |
| post_dates | JSON | high | verified | ✓ | · | Точные даты загрузки/публикации каждого видео. Основа расчёта активности и свежести. |
| posting_frequency | JSON | med | estimated | ✓ | ✓ | Считается из дат ленты (видео/нед., регулярность, всплески/провалы). trust=estimated (выч… |
| video_views | JSON | high | verified | ✓ | ✓ | Точные просмотры каждого видео, отдаёт площадка. Медиана свежих hits vs subscribers — клю… |
| video_title | JSON | high | verified | · | · | Заголовок видео (контекст тематики/оформления). |
| video_description | JSON | high | public | · | ✓ | Описание видео. Здесь встречаются рекламные пометки/erid (маркировка рекламы), ссылки и х… |
| thumbnail_preview | JSON | high | verified | · | · | Обложки/превью видео (CDN). Оформление, не метрика. |
| duration | JSON | high | verified | · | ✓ | Длительность. Формат (короткие vs длинные) и прокси для потенциального watch-time; сам wa… |
| tags | JSON | high | public | · | ✓ | Теги/хэштеги видео (all_tags может быть большим, 100+). Тематика и brand-safety. Переизбы… |
| category | JSON | high | verified | · | ✓ | Официальная категория RuTube (Развлечения, Игры и т.п.). Стабильная тематическая метка. |
| age_rating | JSON | high | verified | · | ✓ | Возрастной рейтинг (0/6/12/16/18+) и флаг взрослого контента — прямой сигнал brand-safety… |
| live_status | JSON | high | verified | ✓ | · | Прямые эфиры/трансляции — сигнал активного формата. |
| premium_paid_share | JSON | high | public | · | ✓ | Аналог «премиум-доли»: доля платного/клубного контента среди видео (вычисляется по ленте)… |
| content_origin | JSON | high | public | · | ✓ | Оригинальный vs лицензионный/переупакованный контент. Высокая доля is_licensed/не-origina… |
| comments_count | JSON | high | verified | ✓ | ✓ | Точное число комментариев видео (пример 1556). Отдельный эндпоинт (в /api/video/<vid>/ ег… |
| comments_content | JSON | high | public | ✓ | ✓ | Тексты, авторы, лайки/дизлайки и ответы по каждому комментарию + закреплённый коммент. По… |
| engagement_rate | JSON | med | estimated | ✓ | ✓ | ER считаем из просмотров и комментариев. Ограничение: лайки/дизлайки самого видео публичн… |
| chapters_streams | JSON | high | verified | · | · | Технические данные плеера: главы, наличие DRM, качества/HLS-DASH манифесты. Для аналитики… |
| video_ids_embed | JSON | high | verified | · | · | Идентификаторы и embed для связывания карточек. feed_name/feed_url привязывают видео к ви… |

_Недоступно публично: following, likes_total, geo_country, pinned_posts, video_likes_dislikes, reposts_shares, watch_time_retention, citation_index._

**Антифрод-сигналы (RuTube):**
- subscribers_count vs channel hits: слишком низкие суммарные просмотры на подписчика (hits/subscribers) при большом числе подписчиков — вероятная накрутка подписки
- Медиана свежих повидеовых hits vs subscribers_count: устойчиво низкий охват (напр. <2-5% подписчиков) — мёртвые/накрученные подписчики
- date_joined vs subscribers_count: молодой канал с большим числом подписчиков — резкий неорганический рост
- comments_count/hits (comment-rate): аномально низкий для больших просмотров = возможно накрученные просмотры; аномально высокий с однотипными текстами = комментные боты
- Разнообразие авторов комментариев (уникальные user.id) и паттерн replies/likes_number — низкое разнообразие/шаблонность = бот-активность
- Кластеризация publication_ts: пакетная заливка множества видео в узком окне после долгого простоя — искусственная активность/перепрогрев
- hits высок, но publication_ts последних видео старые и channel_last_update давно — «остаточный» трафик мёртвого канала
- Доля is_licensed / не is_original_content / is_reborn_channel в ленте: агрегатор/реаплоадер, аудитория не авторская
- Переизбыток all_tags (кейворд-стаффинг) и нерелевантные теги — накрутка выдачи
- avatar_image/cover совпадают с appearance.default_image (генерик) и пустой bio — низкоусиленный/фейковый канал
- is_official=false при заявке на 'официальность' + отсутствие is_ten_thousand при >10k заявленных подписчиков — расхождение с реестром РКН (Госуслуги), сигнал недостоверности
- Разброс просмотров между видео: одно-два аномально высоких hits при общем низком фоне — точечная накрутка/реклама, а не органика


---

## Дзен (Zen / dzen.ru — ex-Яндекс.Дзен, с 2022 принадлежит VK)

**Резюме.** Публично и надёжно берётся ТОЛЬКО через свой браузер (JS-рендеринг) либо через недокументированный JSON /api/v3/launcher/export. Богатые данные вшиты в SSR-HTML: инлайн-скрипт с ssrData/MICRO_APP_SSR_DATA (channel node: subscribers, is_verified, isPremiumAuthor, isDonationEnabled, logo, colors) + <script id="channel-microdata" type="application/ld+json"> (Schema.org ItemList последних постов). Из публичного видно: подписчики, имя, @slug, описание, аватар, последние посты (заголовок/сниппет/обложка/дата/время чтения), просмотры ВИДЕО. Скрыты: просмотры/дочитывания статей (в JSON приходит 0), доход, демография, karma — только в Студии владельца.

- **Server-fetch:** partial — прямой fetch человекочитаемого URL dzen.ru/<slug> без браузера отдаёт 302-редирект на sso.passport.yandex.ru (антибот/автологин), т.е. HTML-страница закрыта для наивного парсинга. НО недоку…
- **Browser:** works — встроенный headless Chrome с JS полностью рендерит публичную страницу канала dzen.ru/<slug>. get_page_text отдаёт: имя, «N подписчиков», описание, вкладки (Лента материалов/Видео/Статьи/Ролик…
- **Официальный API:** none — официального публичного API для статистики каналов у Дзена нет. Owner-only editor-api (zen.yandex.ru/editor-api/v2/... , dzen.ru/api/v4/...) и Студия требуют session_id владельца из кук (нельзя использовать чужие). Эндпоинт launcher…
- **Юр-заметка:** Дзен (dzen.ru; бывш. Яндекс.Дзен, с 2022 — актив VK) в пользовательском соглашении запрещает автоматизированный сбор/скрейпинг и обход антибот-защиты. На практике: прямой server-fetch человекочитаемого URL канала (dzen.ru/<slug>) отдаёт 30…

| Поле | Способ | Стаб. | Доверие | P | S | Заметка |
|---|---|---|---|:-:|:-:|---|
| name (название канала) | JSON | high | verified | · | · | Отображаемое имя. Дублируется в browser_dom и в launcher/export. Задаётся платформой/авто… |
| username / slug | JSON | high | verified | · | · | У Дзена нет @-хэндла как в TikTok/YouTube. Есть vanity-slug (dzen.ru/misly) ИЛИ техническ… |
| bio / description | JSON | high | public | · | ✓ | Свободный текст автора. Здесь же обычно позиционирование, регалии (пример: «КФН, преподав… |
| avatar (логотип) | JSON | high | verified | · | · | Хостинг avatars.dzeninfra.ru. Есть флаг isStubLogo (заглушка) — косвенный признак низкоус… |
| cover (обложка/шапка) | JSON | med | public | · | · | Полноценного баннера-обложки как у YouTube/VK у канала нет — есть OG-картинка для шеринга… |
| followers / subscribers (подписчики) | JSON | high | verified | ✓ | ✓ | ГЛАВНАЯ публичная метрика Дзена — единственная агрегированная цифра, показываемая всем. Т… |
| views — ВИДЕО/Ролики | JSON | med | public | ✓ | ✓ | Для видео и Роликов (шортсы) реальный публичный счётчик просмотров есть и в DOM, и в JSON… |
| pinned_posts (закреплённые) | Browser | med | public | · | · | Дзен поддерживает закреплённые публикации. Видно в браузере; отдельный флаг в item-JSON. … |
| recent_posts (последние публикации) | JSON | high | verified | ✓ | · | JSON-LD ItemList — самый стабильный публичный источник (SEO-микроразметка): заголовок, об… |
| post_dates (даты постов) | JSON | high | public | ✓ | · | На ленте — относительные, на карточке статьи — точная дата. В JSON есть unix-подобные мет… |
| posting_frequency (частота постинга) | JSON | med | estimated | ✓ | · | Производная метрика (постов в неделю, регулярность, всплески). Не отдаётся готовой — счит… |
| links (внешние ссылки в контенте) | Browser | med | public | · | ✓ | Ссылки встречаются в теле публикаций и в bio, но структурного поля «links» у канала нет —… |
| verification (верификация) | JSON | high | verified | · | ✓ | Булев флаг верификации канала. Также is_verified в source из launcher/export. |
| categories / topics / hashtags | JSON | med | public | · | ✓ | Тематика канала уровня платформы публично не подписана явно; извлекается из хэштегов и ми… |
| is_premium_author (Дзен Про / монетизация) | JSON | med | verified | · | ✓ | Платформо-специфично. Флаг премиум-автора/участия в монетизации — сигнал зрелости и легит… |
| isDonationEnabled (донаты/чаевые «Стеллы») | JSON | med | verified | · | ✓ | Платформо-специфично. Включены ли донаты — признак монетизируемого/активного автора. |
| comments_per_post (кол-во комментариев) | JSON | med | public | ✓ | ✓ | Счётчик комментариев по посту в embedded JSON. У проверенного поста 0. visibleComments мо… |
| read_time (время чтения) | JSON | high | public | · | · | Оценка длины материала. Прокси для объёма/качества лонгридов. |
| content_type_mix (Статьи/Видео/Ролики/Посты) | JSON | med | public | ✓ | ✓ | Соотношение форматов. Много Роликов (шортсы) = дешёвый накрутистый охват; лонгриды/видео … |
| account_age / first_publication | JSON | low | estimated | · | ✓ | Прямого поля «дата создания канала» на публичной странице нет; оценивается по архиву пост… |
| is_indexable / is_agree_to_share_data / isStubLogo / colors | JSON | med | verified | · | ✓ | Служебные флаги оформления/видимости. is_indexable=false (канал не индексируется), заглуш… |

_Недоступно публично: following (подписки канала), likes_total (суммарные лайки канала), views — СТАТЬИ/посты, geo / country, РКН-отметка / иноагент, contacts (email / tg для рекламы), external_links (другие соцсети), reactions / likes_per_post (нравится), viewsTillEnd / pageViews (дочитывания), watch_time / доля дочитываний / доход / демография, ER (engagement rate), reposts / shares (репосты), citation_index (индекс цитирования)._

**Антифрод-сигналы (Дзен (Zen / dzen.ru — ex-Яндекс.Дзен, с 2022 принадлежит VK)):**
- Подписчики есть, а активности нет: точное число subscribers в SSR при commentsCount≈0 и нулевых/скрытых просмотрах статей — классический признак накрученных подписчиков
- Диспропорция видео-просмотров и подписчиков: item.views (публичны для видео/Роликов) сильно ниже или аномально выше числа подписчиков → накрутка показов или мёртвая аудитория
- Перекос в сторону Роликов (шортсы) вместо статей/видео — дешёвый накрутистый охват; смотрим content_type_mix
- isStubLogo=true + дефолтные logo/title/headerBackgroundColor + пустое описание — низкоусилийный технический канал
- is_verified=false и isPremiumAuthor=false и isDonationEnabled=false одновременно — канал не монетизирован и не подтверждён (ниже доверие для закупки)
- commentsEnabled=false или visibleComments='subscribe_visible' — комментарии выключены/спрятаны, скрывается реальное соц-доказательство
- Резкий рост подписчиков при коротком архиве (account_age по самому раннему посту) — купленная аудитория
- is_indexable=false / is_agree_to_share_data=false — канал закрыт от индексации и шеринга данных, ограниченная прозрачность
- Всплески постинга (posting_frequency) пачками с последующими провалами — нагонка активности под рекламную интеграцию
- Отсутствие внешних соцсетей/контактов при заявке на рекламу — проверять первоисточники (кросс-сверка с TikTok/Telegram/YouTube того же автора)
- Просмотры статей публично приходят 0 (скрыты платформой) — нельзя верить скриншотам просмотров из Студии без независимой проверки; сверять с видео-охватом
- Дешёвые дочитывания: короткие read_time-материалы массово — контент под алгоритм, а не под аудиторию


---

## Одноклассники (OK.ru)

**Резюме.** OK-группы — самая сильная и стабильная поверхность: server_html открытых групп богат (счётчики + лента + вовлечённость) и не требует логина; REST API уточняет точные счётчики и метаданные. Глубокая аналитика (охват/ER/демография/тренды) закрыта — только для администратора самой группы. Личные профили ограничены приватностью и малопригодны для парсинга.

- **Server-fetch:** works (open groups) — сырой server-rendered HTML открытых групп отдаётся БЕЗ логина и БЕЗ JS: og:title/og:description/og:image, имя группы, members_count (участники), описание, ссылка на сайт, послед…
- **Browser:** works (open groups) — встроенный headless-браузер рендерит открытые группы ok.ru/<group>: отображаемое имя, число участников, описание, ленту постов с реакциями/комментами/репостами, превью участнико…
- **Официальный API:** apiok.ru REST API по OAuth access_token зарегистрированного приложения. По токену: group.getInfo (поля GroupBeanFields), group.getCounters (базовые счётчики), users.getInfo (UserInfoField), stream/mediatopic. Глубокая статистика групп — gr…
- **Юр-заметка:** Правила OK.ru запрещают автоматизированный сбор данных, массовый скрейпинг и обход технических ограничений/анти-бота. Легитимный путь к структурированным данным — официальный REST API apiok.ru по OAuth access_token зарегистрированного прил…

| Поле | Способ | Стаб. | Доверие | P | S | Заметка |
|---|---|---|---|:-:|:-:|---|
| name | HTML | high | public | · | · | Идентификация. Через official_api trust=verified. Для профилей users.getInfo name/first_n… |
| username/shortname | HTML | high | public | · | · | Не у всех групп есть vanity-alias; тогда только числовой group_id в URL. |
| group_id/uid | API | high | verified | · | · | Ключ для всех API-вызовов. В HTML извлекается из data-group-id / ссылок. |
| bio/description | HTML | high | public | · | ✓ | Часто содержит рекламный контакт, РКН-текст, ссылки на другие соцсети — источник для cont… |
| avatar | HTML | high | public | · | · | Прямой URL картинки. Для профилей users.getInfo pic50x50..pic1024x768, picgif/picmp4 (ани… |
| cover | Browser | med | public | · | · | У групп обложка задаётся через main_photo/оформление; отдельного стабильного API-поля обл… |
| followers/subscribers (members_count) | HTML | high | public | · | ✓ | Главная метрика размера. В OK у групп это 'участники'. Через group.getInfo/getCounters tr… |
| followers_count (подписчики ленты) | API | med | verified | · | ✓ | Отдельно от members: подписчики на ленту без вступления. Не всегда показывается в HTML. |
| following (friends_count) | API | med | verified | · | · | Для групп малоинформативно; для личных профилей — число друзей. |
| views (просмотры постов/видео) | Browser | med | public | ✓ | ✓ | Публично видны просмотры видео и части постов. Агрегированный охват/показы по чужой групп… |
| pinned_posts | HTML | med | public | ✓ | · | Сам закреп виден публично; числовой счётчик закрепов — админский. |
| recent_posts (лента топиков) | HTML | high | public | ✓ | ✓ | Текст, медиа, ссылки. Для открытых групп стабильно. stream.get отдаёт ленту по gid (нужен… |
| post_dates | HTML | high | public | ✓ | · | Основа для расчёта posting_frequency и свежести контента. |
| posting_frequency | HTML | med | estimated | ✓ | ✓ | Вычисляется движком; напрямую площадкой не отдаётся. |
| links (внешние ссылки) | HTML | high | public | · | ✓ | Ссылка на сайт группы в API отдельным полем; прочие ссылки — из текста описания/постов. |
| geo/country | API | med | verified | · | ✓ | Указывается не всеми группами. Гео аудитории (а не самой группы) — только group.getStatPe… |
| РКН-отметка | API | med | public | · | ✓ | Для физлиц есть прямое поле rkn_mark. Для групп — обычно текстовая пометка в описании/наз… |
| verification/официальная страница | Browser | med | estimated | · | ✓ | Официальный/верифицированный бейдж виден визуально; стабильного публичного API-поля verif… |
| contacts (email/tg) | HTML | med | public | · | ✓ | Email/Telegram обычно указаны текстом в bio. Личный email профиля через users.getInfo — т… |
| external_links (другие соцсети) | HTML | med | public | · | ✓ | Извлекается регэкспом из текста; помогает связать личность блогера между площадками. |
| categories/topics | API | med | verified | · | ✓ | Тематическая категория группы (тип сообщества). В HTML тоже отображается, но менее структ… |
| reactions (Класс! и расширенные реакции) | HTML | high | public | ✓ | ✓ | Ключевой сигнал вовлечённости в OK: базовый 'Класс!' плюс набор реакций (Ого/Смешно/Ух ты… |
| comments_count | HTML | high | public | ✓ | ✓ | Счётчик виден публично; сами комментарии открытых групп читаемы. Отключённые комментарии … |
| reshares/reposts_count | HTML | med | public | ✓ | ✓ | Репосты — популярная накрутка в OK (репост-сети). Считать с осторожностью. |
| ER (engagement rate) | HTML | med | estimated | ✓ | ✓ | Считается движком. Ориентир нормы OK: классы ~2-4% от просмотров; сильный отрыв = накрутк… |
| content_counts (фото/видео/музыка/товары) | API | high | verified | · | ✓ | Базовые счётчики публичны/по токену. Объём контента = зрелость канала. Часть счётчиков (з… |
| created (возраст группы) | API | high | verified | · | ✓ | Дата создания — сигнал доверия/накрутки (молодая группа с большими цифрами подозрительна). |
| access_type/community/business | API | high | verified | · | ✓ | Определяет публичную видимость: closed-группа = server_html/DOM недоступны, верификация м… |
| premium/VIP/business (профиль) | API | med | verified | · | · | Только для личных профилей; статусный маркер, слабо влияет на закупку. |
| online/last_online (профиль) | API | med | verified | ✓ | · | Только для физлиц и с учётом приватности; для групп неприменимо. |
| members_preview (превью участников) | HTML | med | public | · | ✓ | Дублирующиеся/пустые аватары в превью — косвенный признак ботосети. Полный список участни… |

_Недоступно публично: likes_total (сумма классов), audience_demographics (пол/возраст/гео), reach/engagement/feedback/ER_official/trends._

**Антифрод-сигналы (Одноклассники (OK.ru)):**
- Развитый рынок накрутки OK (vc.ru/DTF: ТОП-25 сервисов): дёшево докупаются участники, 'классы', комментарии и репосты — как ботами, так и мотивированными сетями; крупные ровные цифры при слабой ленте подозрительны.
- 'Мёртвые души': аудитория OK в среднем старше и содержит много неактивных/заброшенных аккаунтов → members_count систематически завышен относительно реальных просмотров/реакций.
- ER-аномалия: в OK классы органично ~2-4% от просмотров; резкий перекос (много классов при малых просмотрах/комментах, или наоборот) = накрутка.
- Диспропорция участники >> просмотры постов/охват: подписчики куплены, органический охват низкий.
- Реакции/классы приходят burst-ом в первые минуты после публикации (боты) — видно по таймингу.
- Комментарии отключены, либо однотипный эмодзи/шаблонный спам под постами вместо живого обсуждения.
- Репосты без роста просмотров и из 'пустых' аккаунтов — типичная репост-накрутка OK.
- Резкие скачки members_count в истории (group.getStatTrends для админа, либо по внешним снимкам во времени) без соответствующего роста активности.
- Дублирующиеся/шаблонные аватары и имена в превью участников — признак ботоводческой сетки.
- Нерелевантная гео/возраст аудитории (group.getStatPeople, если доступ есть) относительно тематики.
- Молодая дата создания группы (created_ms) при больших счётчиках — красный флаг.
- Closed-группа со скрытыми счётчиками: server_html/DOM недоступны, метрики невозможно независимо верифицировать → повышенный риск.


---

## MAX (max.ru) — мессенджер VK/госэкосистемы; публичные КАНАЛЫ

**Резюме.** MAX — самая закрытая площадка набора: публичного скрейпа страницы нет вообще. Два рабочих пути: (a) официальный Bot API, но лишь для каналов, куда добавлен ваш бот (свой канал или с согласия блогера) — даёт verified подписчиков, per-post views, посты/даты/ссылки; (b) сторонние агрегаторы — для чужих блогеров, но числа estimated. ER/реакции — только из залогиненного UI приложения или как оценка агрегатора.

- **Server-fetch:** fails — max.ru/ и max.ru/<nickname> уходят в connection timeout из non-RU вантажа (гео/анти-бот); аналога t.me/s/<ch> (публичный HTML-вьювер) у MAX НЕТ. Реальный server_html-путь — сторонние агрегато…
- **Browser:** gated — НЕТ анонимной публичной страницы. web.max.ru открывается только по QR-логину из мобильного приложения; после входа в свой аккаунт подписчик видит в UI: имя, @nickname, описание, число подписч…
- **Официальный API:** MAX Bot API — botapi.max.ru / platform-api2.max.ru, токен в заголовке Authorization (bearer bot token; передача токена в query отключена). GET /chats/{chatId} -> Chat{chat_id,type,status,title,icon.url,last_event_time,participants_count,ow…
- **Юр-заметка:** MAX: у публичного канала НЕТ анонимной веб-страницы. max.ru гео/анти-бот-закрыт (server-fetch таймаутит из non-RU), а web.max.ru пускает только по QR-логину из мобильного приложения — это персональная сессия, а не публичная поверхность. Оф…

| Поле | Способ | Стаб. | Доверие | P | S | Заметка |
|---|---|---|---|:-:|:-:|---|
| name | API | high | verified | · | · | API verified, но требует бота в канале. Публичная альтернатива без согласия блогера — тол… |
| username / nickname | API | high | verified | · | · | Бизнес-каналы кодируют тип юрлица в суффиксе ника: idNNN_biz (орг/ИП), se<orgid>_biz (сам… |
| bio / description | API | med | verified | · | · | Часто несёт РКН/маркировку, рекламный контакт (@ник/почта) и внешние ссылки — главный ист… |
| avatar (icon) | API | high | verified | · | · | У канала только иконка. |
| followers / subscribers | API | high | verified | · | ✓ | Точное значение только через бота-в-канале или свой залогиненный UI; агрегаторские числа … |
| views (per-post) | API | med | verified | · | ✓ | ЕДИНСТВЕННАЯ пост-метрика в Bot API: schemes.go stat={views:int}. Никаких likes/reactions… |
| avg_views / reach (охват) | HTML | med | estimated | · | ✓ | Охват в агрегаторах смоделирован; verified-версия — усреднить stat.views по постам, если … |
| pinned_posts | API | med | verified | · | · | Возвращается по спец-запросу; в UI виден залогиненному подписчику. |
| recent_posts | API | med | verified | ✓ | · | Требует бота-в-канале или залогиненной сессии; анонимного доступа к постам нет. Каждый Me… |
| post_dates | API | high | verified | ✓ | · | Прямой вход в recency Pulse. |
| posting_frequency | API | med | estimated | ✓ | · | Считается локально из дат; вход в frequency Pulse. |
| external_links (др. соцсети) | API | med | verified | · | · | Парсить URL и @-хэндлы из описания и текста постов (markup содержит форматирование/ссылки… |
| contacts (email/tg) | API | med | public | · | · | Рекламная почта/@ник обычно в описании канала. |
| РКН / маркировка / регистрация | Browser | low | estimated | · | ✓ | Публичный канал в MAX вообще не создать без Digital ID; A+ (импортированные) каналы требу… |
| verification / офиц. бейдж | Browser | low | public | · | · | В объекте Chat Bot API поля verified НЕТ — только визуальный бейдж (гос/бизнес/верифиц.).… |
| categories / topics | HTML | med | estimated | · | · | Проставляется агрегатором, не платформой; в Bot API отсутствует. |
| ER / ERR | HTML | med | estimated | · | ✓ | Оценочный. Для VK-подобной ленты ориентир healthy-band уточнять; вход в антифрод. У MAX н… |
| reactions (эмодзи+счётчики) | Browser | med | public | · | ✓ | РЕАКЦИЙ В Bot API НЕТ (нет reaction-полей/событий — подтверждено сравнением с TG Bot API)… |
| citation_index (ИЦ) | HTML | med | estimated | · | ✓ | Оценка по методологии агрегатора (сколько раз канал цитируют другие) — сигнал органическо… |
| subscriber_growth (24ч/30д) | HTML | med | estimated | ✓ | ✓ | Динамика подписчиков — и живость (Pulse), и антифрод (резкий скачок без роста охвата = на… |
| messages_count (всего постов) | API | high | verified | · | · | Требует бота-в-канале. Малый messages_count при огромных подписчиках = припаркованный/нак… |
| last_event_time (последняя активность) | API | high | verified | ✓ | · | Прокси свежести последнего события/поста, если недоступна лента постов; вход в recency Pu… |
| is_public | API | high | verified | · | · | Подтверждает, что канал публичный (у диалогов всегда false). Плюс owner_id (числовой id с… |
| participants / member last_activity | API | low | verified | · | · | Админ-скоуп; для крупных каналов список ограничен. Может служить прокси живости аудитории… |

_Недоступно публично: cover / banner, following, likes_total (кумулятивные), geo / country, reposts / forwards (per-post), comments, premium_share / watch_time._

**Антифрод-сигналы (MAX (max.ru) — мессенджер VK/госэкосистемы; публичные КАНАЛЫ):**
- ERR/реакции сильно выше здорового бэнда относительно числа подписчиков -> накрутка вовлечённости
- Ср. охват (views/subs) неправдоподобно низкий при больших подписчиках (dead-audience: <~3%) -> купленные подписчики
- Резкий скачок 'Прирост 24ч/30д' в агрегаторе без соответствующего роста охвата -> накрутка подписчиков
- stat.views (Bot API) плохо бьётся с объёмом реакций в UI (много просмотров, почти нет реакций или наоборот)
- Реакции однородны/круглые числа или всплеск одного эмодзи -> искусственная активность
- Индекс цитируемости (ИЦ) агрегатора ≈0 при заявленном большом охвате -> нет органических упоминаний
- Расхождение заявленных в медиаплане подписчиков с Chat.participants_count (API) или числом агрегатора
- Большие подписчики при крошечном messages_count и/или устаревшем last_event_time -> припаркованный/мёртвый канал
- 'Публичный' канал не находится поиском по нику/ссылке или создан без Digital ID -> подозрение на фейк/непубличность
- Заявленный охват недостижим для форматов односторонних каналов (нет комментариев) при отсутствии данных о просмотрах
