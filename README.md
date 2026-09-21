# Treasurer_webapp_followup
Webapp connected to Supabase database that allows email notifications when a stock reaches its bear/bull case

# Treasurer WebApp Follow-Up

A Streamlit-based financial monitoring tool that connects to a Supabase database to track stock tickers and send email notifications based on price movements or thresholds. It includes a modular Streamlit UI, automated notification backend, and a mailing list system.

---

## 🚀 Features

- Monitor stock tickers and trigger notifications
- Configure bear, bull, and base price targets
- Send alerts on daily price changes
- Subscribe via mailing list or stock-specific email
- Modularised UI and backend logic for maintainability
- Fetch live data and news from Yahoo Finance
- Run background job to process notifications (`main.py`)
- Log all operations using structured JSON logs

---

## 🗂️ Project Structure Explained

This project is structured for clarity, testability, and maintainability.

```
📁 .streamlit/              # Streamlit-specific settings
📁 .github/workflows/       # GitHub deployment pipeline
📁 extra/                   # Static assets (images, PDFs)
📁 lib/                     # Core logic, APIs, UI modules
│
├── config.py              # Global constants from env vars
├── db.py                  # Supabase database interface
├── logging.py             # Unified logging helper
├── utils.py               # Misc. utilities
│
├── notifications/         # Email, processing & news logic
│   ├── email.py           # Sends emails, formats HTML
│   ├── news.py            # Fetches top Yahoo Finance news
│   └── processing.py      # Core logic for checking triggers
│
├── ui/                    # Modular Streamlit components
│   ├── forms.py           # Input form for adding stock
│   ├── stock_add.py       # Handles stock submission logic
│   ├── edit_stock.py      # UI to edit/delete stocks
│   ├── mailing.py         # Manage mailing list from UI
│   ├── header.py          # Top banner component
│   └── footer.py          # Footer banner
│
📄 main.py                 # CLI script to process alerts
📄 streamlit_app.py        # Main Streamlit UI entry point
📄 requirements.txt        # Python packages
📄 .env                    # Local environment config
📄 README.md               # You are here
```

### 🔄 How the Files Work Together

#### ✅ Streamlit UI (`streamlit_app.py`)
- Calls functions from `lib/ui/*` to render modular UI
- Uses `forms.py` to get input
- Submits data via `lib/db.py`
- Manages mailing list with `mailing.py`
- All logging goes through `lib/logging.py`

#### ✅ Background Processor (`main.py`)
- Loads environment via `lib/config.py`
- Fetches ticker list from `lib/db.py`
- For each row:
  - Runs `process_row()` from `notifications/processing.py`
  - This uses:
    - `yfinance` for live data
    - `news.py` for headlines
    - `email.py` for sending emails
- Logs structured events using `logging.py`

#### ✅ Notifications
- `processing.py` checks price thresholds and triggers
- `email.py` formats the HTML and sends via SMTP
- `news.py` extracts 3 headlines from Yahoo Finance for inclusion

#### ✅ Supabase Interface (`db.py`)
- Unified access point for:
  - Inserting, updating stocks
  - Managing mailing list
  - Fetching watchlist
- Used by both `streamlit_app.py` and `main.py`

---

## ⚙️ Configuration

### Required Environment Variables

Set either in `.env` (for local) or `.streamlit/secrets.toml` (for Streamlit Cloud):

```env
SUPABASE_URL=https://xyzcompany.supabase.co
SUPABASE_KEY=your-service-key

EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-app-password
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587

DAILY_CHANGE_THRESHOLD=4.0
MARKET_OPEN_HOUR_UTC=13
MARKET_OPEN_MINUTE_UTC=30
```

---

## 🖥️ Running Locally

To run the UI:
```bash
streamlit run streamlit_app.py
```

To run the alert processor manually:
```bash
python main.py
```

This can also be automated via GitHub Actions or any scheduler.

---

## 📨 Email Notification Triggers

| Type             | Trigger                                       |
|------------------|-----------------------------------------------|
| Bear case        | `last_close <= bear_price`                    |
| Bull case        | `last_close >= bull_price`                    |
| Daily change     | Abs(%) change >= threshold from yesterday     |

Each notification is sent only **once per condition** and is reset as follows:

- Bear/Bull: reset after 7 days if not updated
- Daily: reset next market day after open

---

## 📬 Mailing List

- Users can add/remove emails from a global mailing list
- Stored in the Supabase table `mailing_list`
- Every notification goes to stock-specific + global mailing emails

---

## ✉️ Email Content

Emails include:

- Type of alert (e.g., "Bear case hit")
- Current price
- Target prices (bear/base/bull)
- Investment thesis (Pros/Cons)
- Latest 3 news articles with links

Templates are generated in `notifications/email_template.py`.

---

## 🧪 Adding a Stock via UI

1. Enter ticker (validated via `yfinance`)
2. Define price thresholds: bear, base, bull
3. Optionally add:
   - Email for alerts
   - 3 pros and 3 cons
   - Daily price change threshold

All data is sent to Supabase for processing.

---

## 🧾 Dependencies

Install all packages with:

```bash
pip install -r requirements.txt
```

---

## 📄 License

MIT — Free to use, adapt and modify.

---

## 🙌 Acknowledgements

- [Streamlit](https://streamlit.io)
- [Supabase](https://supabase.com)
- [Yahoo Finance](https://finance.yahoo.com)
- [yfinance Python lib](https://pypi.org/project/yfinance/)