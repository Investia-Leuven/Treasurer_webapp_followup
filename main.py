# Backend alert script for stock price threshold notifications
import os
import yfinance as yf
import smtplib
from email.mime.text import MIMEText
from supabase import create_client
from datetime import datetime, timezone, time
import json
from config import SUPABASE_URL, SUPABASE_KEY, EMAIL_USER, EMAIL_PASS, DAILY_CHANGE_THRESHOLD, SMTP_HOST, SMTP_PORT
from email_template import prepare_email_body

def log_event(level, message, **context):
    log = {"level": level, "message": message}
    log.update(context)
    print(json.dumps(log))

# --- runtime signature to prove which code ran ---
def _compute_file_sig():
    import hashlib, pathlib
    try:
        p = pathlib.Path(__file__)
        return hashlib.sha256(p.read_bytes()).hexdigest()[:12]
    except Exception:
        return "unknown"
# -------------------------------------------------

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def send_email(to_email, subject, body):
    log_event("INFO", "Preparing to send email", to=to_email, subject=subject)
    log_event("INFO", "Email subject in use", subject=subject, file_sig=_compute_file_sig(), github_sha=os.getenv("GITHUB_SHA"))
    msg = MIMEText(body, "html")
    msg['Subject'] = subject
    msg['From'] = EMAIL_USER
    msg['To'] = to_email
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, [to_email], msg.as_string())
            log_event("INFO", "Email sent", to=to_email, subject=subject)
    except Exception as e:
        log_event("ERROR", f"Failed to send email to {to_email}", error=str(e))

def notify_event(ticker, event_message, row, mailing_emails):
    subject = f"! Check {ticker} | Investia bot"
    bear_price = row.get('bear_price')
    bau_price = row.get('bau_price')
    bull_price = row.get('bull_price')
    pro_1 = row.get('pro_1', '')
    pro_2 = row.get('pro_2', '')
    pro_3 = row.get('pro_3', '')
    contra_1 = row.get('contra_1', '')
    contra_2 = row.get('contra_2', '')
    contra_3 = row.get('contra_3', '')

    # Fetch last 3 news items from yfinance, extracting from nested 'content' field
    news_items = []
    try:
        stock = yf.Ticker(ticker)
        raw_news = stock.news or []
        for item in raw_news[:3]:
            title = item.get("title") or item.get("content", {}).get("title")
            url = (item.get("link")
                   or item.get("url")
                   or item.get("canonicalUrl")
                   or item.get("content", {}).get("canonicalUrl", {}))
            if isinstance(url, dict):
                url = url.get("url")
            if title and url:
                news_items.append({"title": title, "canonicalUrl": url})
    except Exception as e:
        log_event("ERROR", "Failed to fetch news", ticker=ticker, error=str(e))

    body = prepare_email_body(ticker, event_message, bear_price, bau_price, bull_price, pro_1, pro_2, pro_3, contra_1, contra_2, contra_3, news_items)
    recipients = set(mailing_emails)
    user_email = row.get('email')
    if user_email:
        recipients.add(user_email)
    for recipient in recipients:
        send_email(recipient, subject, body)

def fetch_mailing_emails():
    try:
        mailing_response = supabase.table('mailing_list').select('email').execute()
        return [entry['email'] for entry in mailing_response.data if entry.get('email')]
    except Exception as e:
        log_event("ERROR", "Failed to fetch mailing list", error=str(e))
        return []

def fetch_watchlist():
    try:
        response = supabase.table('stock_watchlist').select('*').execute()
        rows = response.data
        updated_at_exists = False
        if rows and 'updated_at' in rows[0]:
            updated_at_exists = True
        return rows, updated_at_exists
    except Exception as e:
        log_event("ERROR", "Failed to fetch watchlist", error=str(e))
        return [], False

def process_row(row, mailing_emails, updated_at_exists, now_utc):
    ticker = row.get('ticker')
    bear_price = row.get('bear_price')
    bau_price = row.get('bau_price')
    bull_price = row.get('bull_price')
    notified_bear = row.get('notified_bear')
    notified_bull = row.get('notified_bull')
    updated_at_str = row.get('updated_at') if updated_at_exists else None

    # Reset notified_bear and notified_bull if more than 7 days since updated_at
    if updated_at_exists and updated_at_str:
        try:
            updated_at = datetime.fromisoformat(updated_at_str.replace('Z', '+00:00'))
            days_since_update = (now_utc - updated_at).days
            reset_fields = {}
            if notified_bear and days_since_update > 7:
                reset_fields['notified_bear'] = False
            if notified_bull and days_since_update > 7:
                reset_fields['notified_bull'] = False
            if reset_fields:
                supabase.table('stock_watchlist').update(reset_fields).eq('ticker', ticker).execute()
                # Update local variables after reset
                if 'notified_bear' in reset_fields:
                    notified_bear = False
                if 'notified_bull' in reset_fields:
                    notified_bull = False
        except Exception as e:
            log_event("ERROR", "Failed to parse updated_at", ticker=ticker, error=str(e))
    elif not updated_at_exists:
        # If updated_at column does not exist, no reset is performed.
        # To enable automatic reset, add an 'updated_at' timestamp column to the 'stock_watchlist' table
        # with default value now() and update it on changes.
        pass

    try:
        stock = yf.Ticker(ticker)
        if not stock.info or stock.info.get("regularMarketPrice") is None:
            log_event("WARN", "Ticker invalid or delisted", ticker=ticker)
            return
        hist = stock.history(period="2d")
        if hist.empty or len(hist) < 2:
            log_event("WARN", "No sufficient historical data", ticker=ticker)
            return
        last_close = hist['Close'].iloc[-1]
        price_str = f"{last_close:,.2f}"
        previous_close = hist['Close'].iloc[-2]

        # --- Global market-day/open guard (applies to all notifications) ---
        today_utc = now_utc.date()
        latest_price_date = hist.index[-1].date()
        if latest_price_date < today_utc:
            log_event("INFO", "GUARD:data-not-updated", ticker=ticker,
                      latest_price_date=str(latest_price_date), today=str(today_utc))
            return
        try:
            open_hour = int(os.getenv("MARKET_OPEN_HOUR_UTC", "13"))
            open_minute = int(os.getenv("MARKET_OPEN_MINUTE_UTC", "30"))
        except Exception:
            open_hour, open_minute = 13, 30
        after_open = (now_utc.hour > open_hour) or (now_utc.hour == open_hour and now_utc.minute >= open_minute)
        is_weekend = now_utc.weekday() >= 5
        if is_weekend or not after_open:
            log_event("INFO", "GUARD:market-closed", ticker=ticker,
                      weekday=now_utc.weekday(), after_open=after_open)
            return

        # Check bear threshold
        if bear_price is not None and last_close <= bear_price and not notified_bear:
            notify_event(ticker, f"Bear case hit (close: {price_str})", row, mailing_emails)
            supabase.table('stock_watchlist').update({'notified_bear': True}).eq('ticker', ticker).execute()
        # Check bull threshold
        if bull_price is not None and last_close >= bull_price and not notified_bull:
            notify_event(ticker, f"Bull case hit (close: {price_str})", row, mailing_emails)
            supabase.table('stock_watchlist').update({'notified_bull': True}).eq('ticker', ticker).execute()

        # --- Begin new daily change notification logic ---
        # Reuse today_utc from the global guard above
        # Get notified_daily_change and last_daily_notify_date from row
        notified_daily_change = row.get('notified_daily_change', False)
        last_daily_notify_date = row.get('last_daily_notify_date')
        # Parse last_daily_notify_date if present
        last_notify_date_obj = None
        if last_daily_notify_date:
            try:
                last_notify_date_obj = datetime.fromisoformat(str(last_daily_notify_date)).date()
            except Exception:
                last_notify_date_obj = None
        # Reset notified_daily_change only on trading days and after market open (default 13:30 UTC)
        try:
            open_hour = int(os.getenv("MARKET_OPEN_HOUR_UTC", "13"))
            open_minute = int(os.getenv("MARKET_OPEN_MINUTE_UTC", "30"))
        except Exception:
            open_hour, open_minute = 13, 30

        weekday = now_utc.weekday()  # Monday=0 ... Sunday=6
        # Determine if current time is at/after the configured market open in UTC
        after_open = (now_utc.hour > open_hour) or (now_utc.hour == open_hour and now_utc.minute >= open_minute)
        is_weekend = weekday >= 5  # 5=Saturday, 6=Sunday
        can_reset_today = (not is_weekend) and after_open

        # Do NOT reset on Saturday/Sunday or before market open (esp. early Monday runs)
        if last_notify_date_obj and last_notify_date_obj < today_utc and notified_daily_change and can_reset_today:
            try:
                supabase.table('stock_watchlist').update({'notified_daily_change': False}).eq('ticker', ticker).execute()
                notified_daily_change = False
            except Exception as e:
                log_event("ERROR", "Reset daily notification failed", ticker=ticker, error=str(e))

        # Now check daily change
        if previous_close != 0:
            daily_change = (last_close - previous_close) / previous_close * 100
            threshold = row.get('daily_change_threshold', DAILY_CHANGE_THRESHOLD)
            # Only notify if daily change >= threshold% or <= -threshold% and not notified today
            if (daily_change >= threshold or daily_change <= -threshold):
                should_notify = False
                # Check if not notified today
                if last_notify_date_obj is None or last_notify_date_obj < today_utc:
                    should_notify = True
                if should_notify:
                    percent_str = f"{abs(daily_change):.2f}%"
                    if daily_change >= threshold:
                        notify_event(ticker, f"Price increase >{percent_str} (close: {price_str})", row, mailing_emails)
                    elif daily_change <= -threshold:
                        notify_event(ticker, f"Price decrease >{percent_str} (close: {price_str})", row, mailing_emails)
                    try:
                        supabase.table('stock_watchlist').update({
                            'notified_daily_change': True,
                            'last_daily_notify_date': str(today_utc)
                        }).eq('ticker', ticker).execute()
                    except Exception as e:
                        log_event("ERROR", "Failed to update daily notification flags", ticker=ticker, error=str(e))
    except Exception as e:
        log_event("ERROR", "Unhandled error during row processing", ticker=ticker, error=str(e))

def main():
    mailing_emails = fetch_mailing_emails()
    rows, updated_at_exists = fetch_watchlist()
    now_utc = datetime.now(timezone.utc)
    # Log a startup marker so we can verify exactly which code ran inside Actions
    try:
        open_hour = int(os.getenv("MARKET_OPEN_HOUR_UTC", "13"))
        open_minute = int(os.getenv("MARKET_OPEN_MINUTE_UTC", "30"))
    except Exception:
        open_hour, open_minute = 13, 30
    log_event(
        "INFO",
        "Startup marker",
        file_sig=_compute_file_sig(),
        github_sha=os.getenv("GITHUB_SHA"),
        utc_now=str(now_utc),
        weekday=now_utc.weekday(),
        market_open_hour_utc=open_hour,
        market_open_minute_utc=open_minute,
    )
    for row in rows:
        process_row(row, mailing_emails, updated_at_exists, now_utc)

if __name__ == "__main__":
    main()