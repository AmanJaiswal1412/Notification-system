# Notification System

Admin manages every notification from **one screen on the website** - no need to open WhatsApp, Postmark or OneSignal to create templates.

- **Trigger** = any website event (login, logout, inactive for 1 day / 1 week, password reset, order placed…). One trigger = one row.
- **Channels** = WhatsApp (Cloud API sandbox), Email (Postmark / Brevo / Resend), Web Push (OneSignal, browser only). One channel = one column.
- **Template** = one cell (trigger × channel). Admin can create, edit, turn on/off and test-send from the cell.

| Part | Tech | Host |
|---|---|---|
| `backend/` | Python, Django, Django REST Framework | Render |
| `frontend/` | React (Vite), React Router | Vercel |

---

## Project structure

```
Notification-system/
├── render.yaml                      # Render blueprint (web service + Postgres)
├── backend/
│   ├── manage.py, requirements.txt, build.sh, .env.example
│   ├── config/                      # settings, urls, wsgi
│   └── apps/
│       ├── accounts/                # users, token auth, Profile(phone, last_seen)
│       │   └── views.py             # login/logout endpoints FIRE the triggers
│       └── notifications/
│           ├── models.py            # Trigger, Template, PushSubscription, NotificationLog
│           ├── views.py, serializers.py, urls.py   # admin APIs
│           ├── providers/           # one module per channel (whatsapp, email, webpush)
│           ├── services/
│           │   ├── dispatcher.py    # fire_trigger(): trigger -> enabled templates -> providers
│           │   └── rendering.py     # {{placeholder}} + variable mapping
│           ├── management/commands/ # seed_defaults, fire_inactivity_triggers
│           └── tests/
└── frontend/
    ├── package.json, vite.config.js, vercel.json, .env.example
    ├── public/OneSignalSDKWorker.js # service worker required by Web Push
    └── src/
        ├── api/                     # fetch client + auth/admin API modules
        ├── context/AuthContext.jsx
        ├── components/              # MatrixCell, TemplateModal, TestSendModal, ...
        ├── pages/                   # LoginPage, HomePage (the "website"), AdminPage, LogsPage
        └── lib/                     # OneSignal helper, toast hook
```

### How it works

1. A website event happens (e.g. `POST /api/auth/login/`) and the backend calls `fire_trigger("login", user)`.
2. The dispatcher loads the trigger and every template whose toggle is **on**.
3. Each template is rendered (`{{user.first_name}}`, or `{{1}}` via the template's variable mapping) and handed to that channel's provider.
4. Every attempt is stored in `NotificationLog` (admin → *Send log*). Provider failures never break the website request.

A trigger sends on a channel only if: the trigger is active, the cell has a template, its toggle is on, and the code fires that trigger.

To add a trigger fired by your own code: add a row in the admin UI (key e.g. `order_placed`) and call `fire_trigger("order_placed", user, {"order_id": 42})` where the event happens. Extra context keys can then be mapped to placeholders.

---

## Run locally

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # Windows: copy .env.example .env   (then fill in keys)
python manage.py migrate
python manage.py seed_defaults                         # admin user + triggers + starter templates
python manage.py runserver                             # http://localhost:8000
python manage.py test                                  # optional: run tests
```
Uses SQLite locally; set `DATABASE_URL` for Postgres.

### Frontend
```bash
cd frontend
npm install
cp .env.example .env                                   # set VITE_API_URL and VITE_ONESIGNAL_APP_ID
npm run dev                                            # http://localhost:5173
```

### Admin login
After `seed_defaults`: username **`admin`**, password **`admin12345`** (override with `ADMIN_USERNAME` / `ADMIN_PASSWORD` in `.env` **before** seeding - change it in production). The admin sees **Notification Settings** and **Send log** in the top bar. Regular users can self-register on the login page.

### Triggers built
| Key | Fires when | How |
|---|---|---|
| `login` | user signs in | `POST /api/auth/login/` |
| `logout` | user signs out | `POST /api/auth/logout/` |
| `inactive_1_day` | no visit for 1 day | `python manage.py fire_inactivity_triggers` (daily cron) |
| `inactive_1_week` | no visit for 7 days | same command |
| `password_reset` | user requests reset | `POST /api/auth/password-reset/` (button on website) |

`login` and `logout` are seeded with starter templates for all 3 channels (switched **off** until you turn them on). Inactivity users are matched on `Profile.last_seen` (updated on login and whenever the app loads) and notified once per absence.

---

## Sandbox setup (no real keys needed)

Put values in `backend/.env` (never commit it). Everything is also listed in `.env.example`.

### WhatsApp - Meta sandbox
1. Create a free account at developers.facebook.com → create an app → add the **WhatsApp** product.
2. From *API Setup* copy the **temporary access token** and **Phone number ID** (test number). Add your own phone to the test recipient list.
3. `.env`: `WHATSAPP_ACCESS_TOKEN`, `PHONE_NUMBER_ID`. The token expires often - regenerate when tests fail.
4. To create/sync custom templates from the admin panel also set `WHATSAPP_BUSINESS_ACCOUNT_ID` (WABA id, shown in API Setup).

Template flow in the admin UI: **Create template → Save & submit to Meta → Sync status until approved → Test send**. Quick smoke test: name the template `hello_world` and press Sync - Meta's sandbox pre-approves it.
WhatsApp only accepts numbered placeholders (`{{1}}`, `{{2}}`); map each to a value in the *Variable mapping* box. Users enter their phone (country code, digits only) on the website page.

### Email - Postmark (or another free provider)
Set `EMAIL_PROVIDER` to `postmark`, `brevo` or `resend`, then the matching variables:

| Provider | Variables |
|---|---|
| postmark | `POSTMARKAPP_TOKEN`, `POSTMARK_FROM_EMAIL` |
| brevo | `BREVO_API_KEY`, `BREVO_FROM_EMAIL` |
| resend | `RESEND_API_KEY`, `RESEND_FROM_EMAIL` |

The from-address must be a verified sender at the provider. **Provider used in this repo's default config: Postmark** - change `EMAIL_PROVIDER` if you use another (update this line).

### Web Push - OneSignal
1. Create a free OneSignal app of type **Website**, enable **Web Push** only.
2. `backend/.env`: `ONESIGNAL_APP_ID`, `ONESIGNAL_REST_API_KEY`. `frontend/.env`: `VITE_ONESIGNAL_APP_ID` (same app id).
3. Log in as any user, open the **Website** page and press **Enable Web Push**; allow notifications in the browser. The subscription id is saved against that user.

Localhost works for development (the SDK is initialised with `allowLocalhostAsSecureOrigin`). In OneSignal's site settings set the site URL to your frontend (localhost or Vercel URL).

---

## API summary

Auth header: `Authorization: Token <token>`.

| Method & path | Who | Purpose |
|---|---|---|
| `POST /api/auth/register/`, `/login/`, `/logout/` | public / user | Account + fires `login` / `logout` |
| `GET/PATCH /api/auth/me/` | user | Profile (phone) |
| `POST /api/auth/password-reset/` | public | Fires `password_reset` |
| `POST /api/push/subscribe/` | user | Save OneSignal subscription id |
| `GET/POST /api/admin/triggers/` (+ `PATCH /{id}/`) | admin | Matrix rows (each has `cells.whatsapp/email/push`) |
| `POST/PATCH /api/admin/templates/` | admin | Create / edit template |
| `POST /api/admin/templates/{id}/toggle/` | admin | Turn a channel on/off |
| `POST /api/admin/templates/{id}/test/` | admin | Test send (`{"recipient": "..."}` optional) |
| `POST /api/admin/templates/{id}/submit/` · `/sync/` | admin | WhatsApp approval flow |
| `GET /api/admin/logs/`, `/api/admin/variables/` | admin | Send log, placeholder keys |

---

## Deploy

### Backend → Render
1. Push the repo to GitHub. In Render choose **New → Blueprint** and select it (`render.yaml` creates the web service and a Postgres DB), or create a Python web service manually with root dir `backend`, build `./build.sh`, start `gunicorn config.wsgi:application`.
2. Fill the env vars marked *sync: false* (see `.env.example`). Set `CORS_ALLOWED_ORIGINS` to your Vercel URL (no trailing slash) and `ADMIN_PASSWORD` **before** the first deploy.
3. **Inactivity triggers:** add a Render **Cron Job** (same repo, root dir `backend`, same env vars), schedule `0 9 * * *`, command `python manage.py fire_inactivity_triggers`.

The free Render tier sleeps when idle, so the first request after a pause is slow.

### Frontend → Vercel
Import the repo, set root directory to `frontend`, framework *Vite*, and env vars `VITE_API_URL` (Render URL, no trailing slash) and `VITE_ONESIGNAL_APP_ID`. `vercel.json` handles SPA routing.

---

## Practice walkthrough (Tasks A-D)
1. Log in as admin → **Notification Settings**. On the **Login** row: create/edit the WhatsApp (submit + sync), Email and Web Push templates, turn each on, and **Test send** to your phone, email and browser.
2. Repeat on **Logout** (or an inactivity trigger) with different text.
3. Edit a template and test again; flip a toggle off/on.
4. Register a normal user (with phone), enable Web Push on the Website page, then log out and in - watch the notifications arrive and check **Send log**.

## Notes
- Do not commit `.env` or share tokens. Sandbox/free accounts only.
- Tokens are stored in `localStorage` in the browser - fine for this assignment; use httpOnly cookies for production.
- Notifications are sent in a background thread (`NOTIFICATIONS_ASYNC=True`). For high volume, swap in Celery/RQ behind `fire_trigger`.
- Mobile push is out of scope: Web Push (browser) only.
