import os
import yfinance as yf
import smtplib
from email.mime.text import MIMEText
from lib.logging import log_event
from lib.config import EMAIL_USER, EMAIL_PASS, SMTP_HOST, SMTP_PORT
from lib.notifications.email_template import prepare_email_body
from lib.notifications.news import fetch_latest_news

def send_email(to_email, subject, body):
    """
    Sends an HTML email to the specified recipient.
    Logs the process and handles any exceptions that occur during sending.
    """
    log_event("INFO", "Preparing to send email", to=to_email, subject=subject, github_sha=os.getenv("GITHUB_SHA"))
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
    """
    Generates and sends notification emails for a specific stock ticker event.
    """
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

    news_items = fetch_latest_news(ticker)

    body = prepare_email_body(ticker, event_message, bear_price, bau_price, bull_price, pro_1, pro_2, pro_3, contra_1, contra_2, contra_3, news_items)
    recipients = set(mailing_emails)
    user_email = row.get('email')
    if user_email:
        recipients.add(user_email)
    for recipient in recipients:
        send_email(recipient, subject, body)
