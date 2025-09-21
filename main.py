"""
Backend script for sending stock alert notifications based on price thresholds.
Fetches data from Supabase and uses Yahoo Finance to check conditions.
Sends email alerts for bear, bull, or daily change thresholds.
"""
# Backend alert script for stock price threshold notifications
import os
from datetime import datetime, timezone
from lib.config import MARKET_OPEN_HOUR_UTC, MARKET_OPEN_MINUTE_UTC
from lib.db import fetch_mailing_emails, fetch_watchlist
from lib.logging import log_event
from lib.notifications.processing import process_row

def main():
    """
    Main function orchestrates the alert job:
    - Fetches mailing emails and watchlist data
    - Gets current UTC time
    - Iterates over each watchlist row and processes it for potential notifications
    """
    mailing_emails = fetch_mailing_emails()
    rows, updated_at_exists = fetch_watchlist()
    now_utc = datetime.now(timezone.utc)
    log_event("INFO","Startup marker",github_sha=os.getenv("GITHUB_SHA"),utc_now=str(now_utc),weekday=now_utc.weekday(),market_open_hour_utc=MARKET_OPEN_HOUR_UTC,market_open_minute_utc=MARKET_OPEN_MINUTE_UTC)
    for row in rows:
        process_row(row, mailing_emails, updated_at_exists, now_utc)

if __name__ == "__main__":
    main()