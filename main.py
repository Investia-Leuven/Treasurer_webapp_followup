# Backend alert script for stock price threshold notifications
import os
from dotenv import load_dotenv
import yfinance as yf
import smtplib
from email.mime.text import MIMEText
from supabase import create_client

# Load environment variables
load_dotenv()
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
EMAIL_USER = os.environ.get('EMAIL_USER')
EMAIL_PASS = os.environ.get('EMAIL_PASS')

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def send_email(to_email, subject, body):
    msg = MIMEText(body)
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

def prepare_email_body(ticker, bear_price, bau_price, bull_price, pro_1, pro_2, pro_3, contra_1, contra_2, contra_3):
    return f"""Dear member,

Please check following stock {ticker}.

Bear price: {bear_price}
BAU price: {bau_price}
Bull price: {bull_price}

Investment Thesis:
Pros:
- {pro_1}
- {pro_2}
- {pro_3}
Cons:
- {contra_1}
- {contra_2}
- {contra_3}

Kind regards,
The Investia bot
"""

def check_prices():
    # Fetch all watchlist entries from Supabase
    try:
        response = supabase.table('stock_watchlist').select('*').execute()
        rows = response.data
    except Exception as e:
        print(f"Error fetching watchlist: {e}")
        return
    for row in rows:
        ticker = row.get('ticker')
        bear_price = row.get('bear_price')
        bau_price = row.get('bau_price')
        bull_price = row.get('bull_price')
        notified_bear = row.get('notified_bear')
        notified_bull = row.get('notified_bull')
        user_email = row.get('email')
        pro_1 = row.get('pro_1', '')
        pro_2 = row.get('pro_2', '')
        pro_3 = row.get('pro_3', '')
        contra_1 = row.get('contra_1', '')
        contra_2 = row.get('contra_2', '')
        contra_3 = row.get('contra_3', '')
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1d")
            if hist.empty:
                print(f"No data for {ticker}")
                continue
            last_close = hist['Close'][-1]
            subject = f"!! Check {ticker} | Investia bot"
            body = prepare_email_body(ticker, bear_price, bau_price, bull_price, pro_1, pro_2, pro_3, contra_1, contra_2, contra_3)
            # Bear threshold
            if bear_price is not None and last_close <= bear_price and not notified_bear:
                send_email(user_email, subject, body)
                # Update notified_bear
                supabase.table('stock_watchlist').update({'notified_bear': True}).eq('ticker', ticker).execute()
            # Bull threshold
            if bull_price is not None and last_close >= bull_price and not notified_bull:
                send_email(user_email, subject, body)
                # Update notified_bull
                supabase.table('stock_watchlist').update({'notified_bull': True}).eq('ticker', ticker).execute()
        except Exception as e:
            print(f"Error processing {ticker}: {e}")

if __name__ == "__main__":
    check_prices()