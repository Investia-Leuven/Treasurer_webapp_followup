# Backend alert script for stock price threshold notifications
import os
from dotenv import load_dotenv
import yfinance as yf
import smtplib
from email.mime.text import MIMEText
from supabase import create_client
from datetime import datetime, timezone

# Load environment variables
load_dotenv()
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
EMAIL_USER = os.environ.get('EMAIL_USER')
EMAIL_PASS = os.environ.get('EMAIL_PASS')

DAILY_CHANGE_THRESHOLD = 0.1  # percentage threshold for daily change notifications

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def send_email(to_email, subject, body):
    msg = MIMEText(body, "html")
    msg['Subject'] = subject
    msg['From'] = EMAIL_USER
    msg['To'] = to_email
    try:
        with smtplib.SMTP('smtp-auth.mailprotect.be', 587) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, [to_email], msg.as_string())
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")

def prepare_email_body(ticker, event_message, bear_price, bau_price, bull_price, pro_1, pro_2, pro_3, contra_1, contra_2, contra_3, news_items):
    news_html = ""
    if news_items:
        news_html += "<h3>Latest News:</h3><ul>"
        for item in news_items:
            title = item.get('title', 'No title')
            url = item.get('canonicalUrl', '#')
            news_html += f'<li><a href="{url}" target="_blank" rel="noopener noreferrer">{title}</a></li>'
        news_html += "</ul>"
    return f"""<html>
  <body>
    <p>Dear member,</p>
    <p>This is an alert from the <strong>Investia Bot</strong> regarding the stock <strong>{ticker}</strong>.</p>
    <p>Reason for this email: <em>{event_message}</em>.</p>
    <h3>Price Levels:</h3>
    <ul>
      <li>Bear price: {bear_price}</li>
      <li>BAU price: {bau_price}</li>
      <li>Bull price: {bull_price}</li>
    </ul>
    <h3>Investment Thesis:</h3>
    <p><strong>Pros:</strong></p>
    <ul>
      <li>{pro_1}</li>
      <li>{pro_2}</li>
      <li>{pro_3}</li>
    </ul>
    <p><strong>Cons:</strong></p>
    <ul>
      <li>{contra_1}</li>
      <li>{contra_2}</li>
      <li>{contra_3}</li>
    </ul>
    <p>This event may be related to recent news or market movements.</p>
    {news_html}
    <p>Have a nice day!</p>
    <p>Kind regards,<br>The Investia bot</p>
  </body>
</html>
"""

def notify_event(ticker, event_message, row, mailing_emails):
    subject = f"!! Check {ticker} | Investia bot"
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
        news = stock.news
        if news and isinstance(news, list):
            for item in news[:3]:
                content = item.get('content', {})
                title = content.get('title')
                url = content.get('canonicalUrl', {}).get('url')
                if title and url:
                    news_items.append({'title': title, 'canonicalUrl': url})
    except Exception as e:
        print(f"Error fetching news for {ticker}: {e}")

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
        print(f"Error fetching mailing list: {e}")
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
        print(f"Error fetching watchlist: {e}")
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
            print(f"Error parsing updated_at for {ticker}: {e}")
    elif not updated_at_exists:
        # If updated_at column does not exist, no reset is performed.
        # To enable automatic reset, add an 'updated_at' timestamp column to the 'stock_watchlist' table
        # with default value now() and update it on changes.
        pass

    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="2d")
        if hist.empty or len(hist) < 2:
            print(f"No sufficient data for {ticker}")
            return
        last_close = hist['Close'][-1]
        previous_close = hist['Close'][-2]
        # Check bear threshold
        if bear_price is not None and last_close <= bear_price and not notified_bear:
            notify_event(ticker, "Bear case hit", row, mailing_emails)
            supabase.table('stock_watchlist').update({'notified_bear': True}).eq('ticker', ticker).execute()
        # Check bull threshold
        if bull_price is not None and last_close >= bull_price and not notified_bull:
            notify_event(ticker, "Bull case hit", row, mailing_emails)
            supabase.table('stock_watchlist').update({'notified_bull': True}).eq('ticker', ticker).execute()

        # --- Begin new daily change notification logic ---
        # Get notified_daily_change and last_daily_notify_date from row
        notified_daily_change = row.get('notified_daily_change', False)
        last_daily_notify_date = row.get('last_daily_notify_date')
        # Compute today's date in UTC
        today_utc = now_utc.date()
        # Parse last_daily_notify_date if present
        last_notify_date_obj = None
        if last_daily_notify_date:
            try:
                last_notify_date_obj = datetime.fromisoformat(str(last_daily_notify_date)).date()
            except Exception:
                last_notify_date_obj = None
        # Reset notified_daily_change if last_daily_notify_date < today
        if last_notify_date_obj and last_notify_date_obj < today_utc and notified_daily_change:
            try:
                supabase.table('stock_watchlist').update({'notified_daily_change': False}).eq('ticker', ticker).execute()
                notified_daily_change = False
            except Exception as e:
                print(f"Error resetting notified_daily_change for {ticker}: {e}")

        # Now check daily change
        if previous_close != 0:
            daily_change = (last_close - previous_close) / previous_close * 100
            # Only notify if daily change >= DAILY_CHANGE_THRESHOLD% or <= -DAILY_CHANGE_THRESHOLD% and not notified today
            if (daily_change >= DAILY_CHANGE_THRESHOLD or daily_change <= -DAILY_CHANGE_THRESHOLD):
                should_notify = False
                # Check if not notified today
                if last_notify_date_obj is None or last_notify_date_obj < today_utc:
                    should_notify = True
                if should_notify:
                    if daily_change >= DAILY_CHANGE_THRESHOLD:
                        notify_event(ticker, f"Price increase >{DAILY_CHANGE_THRESHOLD}% today", row, mailing_emails)
                    elif daily_change <= -DAILY_CHANGE_THRESHOLD:
                        notify_event(ticker, f"Price decrease >{DAILY_CHANGE_THRESHOLD}% today", row, mailing_emails)
                    try:
                        supabase.table('stock_watchlist').update({
                            'notified_daily_change': True,
                            'last_daily_notify_date': str(today_utc)
                        }).eq('ticker', ticker).execute()
                    except Exception as e:
                        print(f"Error updating notified_daily_change for {ticker}: {e}")
    except Exception as e:
        print(f"Error processing {ticker}: {e}")

def main():
    mailing_emails = fetch_mailing_emails()
    rows, updated_at_exists = fetch_watchlist()
    now_utc = datetime.now(timezone.utc)
    for row in rows:
        process_row(row, mailing_emails, updated_at_exists, now_utc)

if __name__ == "__main__":
    main()