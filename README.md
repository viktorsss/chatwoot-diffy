# Что это?
Коннектор, который запускает свои постгрю, редис, celery workers, фастапи сервер и телеметрию. Следит за всеми событиями в чатвуте и на нужные из них дёргает пайплайны в dify, выступая мостом между ними.

# Как это должно работать
- Слушаем все эвенты от чатвута, через ифы в зависимости от статуса диалога / автора сообщения решаем, что пропускать.
- Dify пайплайны триггерим ТОЛЬКО пока диалог в статусе pending.
- Тыкание эндпойнтов по изменению статуса / региона / прочего - всё из dify, пока никаких ключей нет, пердполагается что всё живёт в одной сети, где из внешнего мира мост недоступен.

# Чего пока нет
- Удаление диалогов в дифи (надо решить в какой момент делать)
- Создание своих диалогов (эндпойнты позволяют, но нужен айди контакта)

# Иметь в виду

После того как назначается тима бот уже не может сводобно дёргать эндпойнты с инфой о дилаоге, в том числе и custom attributes. При этом он даже может их апдейтить, но не читать.

При простановке всяких параметров по conversation_id счяитается, что это ответственность моста обработать "None" и им подобные значения, не делать запрос в чатвут и вернуть success статус dify-пайплайну.

Dify снэпшотит `inputs` для диалога в базе : https://github.com/langgenius/dify/issues/11140 Поэтому просто передавать туда статус не выйдет, он так и останется pending.

# Как деплоить

Важно : ссылку на вебхук надо прописать для Agent Bot в Super Admin консоли chatwoot : `Outgoing url
https://<ссылка на bridge>/api/v1/chatwoot-webhook`.

Ссылка на корень сервиса должна быть в env vars пайплайна в dify `bridge_api_url = https:///<ссылка на bridge>/api/v1`

Не забыть из нужного dify пайплайна/бота взять его апи ключ и прописать в энв как `DIFY_API_KEY`, именно по этому ключу dify не только впускает, но и понимает, какой пайплайн запускать.

Чтобы подключить инбокс к боту, надо его явныс образом его туда добавить, предварительно убедившись, что в Super Admin Console проставлена галка для Agent Bots для акка.

Админ юзер должен быть во всех тимах, чтобы для диалогов этих тим не ломался эндпойнт `get_conversation_data`


Дальше `docker-compose up` должно хватить.

# Как тестить
В health.py живёт совсем базовое.
При локальном деплое:
1) Убедиться что заполнен .env
2) прописать туда `TEST_CONVERSATION_ID=<айдишник дилога, видно в логах и dev tools браузера>`, написав боту со своего акка.
3) `uv pip install -e ".[dev]"` (uv прекрасный пакетный мендежер для питона на rust : https://docs.astral.sh/uv/getting-started/installation/)
4) `python -m pytest`

# Штуки для удобства

В setup_chatwoot_config.ipynb живёт пример как удобно по api залить команды и csutom attributes. Важно : нужны админ права для апи (в super admin console в чатвуте берётся ключ)

# Chatdify

A Python connector for integrating Chatwoot with Dify AI

## Monitoring & Error Tracking

This application uses **Sentry** for comprehensive error tracking, performance monitoring, and observability. The setup includes:

### Sentry Integrations

- **FastAPI Integration**: Captures HTTP errors, request data, middleware events, and performance traces
- **Starlette Integration**: Provides additional middleware and routing instrumentation
- **Celery Integration**: Monitors background task execution, errors, and distributed tracing
- **HTTPX Integration**: Instruments outgoing HTTP requests for tracing external API calls
- **SQLAlchemy Integration**: Captures SQL queries as breadcrumbs and spans for database monitoring
- **AsyncPG Integration**: Database connection monitoring for PostgreSQL
- **Logging Integration**: Captures logs as breadcrumbs and sends error-level logs as events

### Configuration

Configure Sentry via environment variables:

```bash
SENTRY_DSN=your_sentry_dsn_here
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.1
SENTRY_LOG_LEVEL=WARNING
SENTRY_ATTACH_STACKTRACE=True
SENTRY_SEND_DEFAULT_PII=False
```

### Features

- **Error Tracking**: Automatic capture of exceptions with full context
- **Performance Monitoring**: Transaction traces for HTTP requests and database queries
- **Breadcrumbs**: Contextual logs and events leading up to errors
- **Profiling**: Code-level performance insights during traces
- **Distributed Tracing**: End-to-end request tracking across services
- **Release Tracking**: Version-aware error reporting and deployments

For more details, see the [Sentry documentation](https://docs.sentry.io/platforms/python/).
