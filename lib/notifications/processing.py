from datetime import datetime
import yfinance as yf
from lib.config import MARKET_OPEN_HOUR_UTC, MARKET_OPEN_MINUTE_UTC, DAILY_CHANGE_THRESHOLD
from lib.logging import log_event
from lib.notifications.email import notify_event
from lib.db import reset_notified_flags, update_notified_flags

def process_row(row, mailing_emails, updated_at_exists, now_utc):
    """
    Processes a single watchlist row: checks price thresholds and triggers notifications if conditions are met.
    Also handles resetting notification flags based on update age and daily notification logic.
    """
    ticker = row.get('ticker')
    bear_price = row.get('bear_price')
    bau_price = row.get('bau_price')
    bull_price = row.get('bull_price')
    notified_bear = row.get('notified_bear')
    notified_bull = row.get('notified_bull')
    updated_at_str = row.get('updated_at') if updated_at_exists else None

        # Reset stale flags if last update > 7 days
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
                reset_notified_flags(ticker, reset_fields)
                if 'notified_bear' in reset_fields:
                    notified_bear = False
                if 'notified_bull' in reset_fields:
                    notified_bull = False
        except Exception as e:
            log_event("ERROR", "Failed to parse updated_at", ticker=ticker, error=str(e))

    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="2d")
        if not stock.info or stock.info.get("regularMarketPrice") is None or hist.empty or len(hist) < 2:
            log_event("WARN", "Invalid or insufficient ticker data", ticker=ticker)
            return
        last_close = hist['Close'].iloc[-1]
        price_str = f"{last_close:,.2f}"
        previous_close = hist['Close'].iloc[-2]

        today_utc = now_utc.date()
        latest_price_date = hist.index[-1].date()
        if latest_price_date < today_utc:
            log_event("INFO", "Skipping notification due to outdated data", ticker=ticker)
            return

        after_open = (now_utc.hour > MARKET_OPEN_HOUR_UTC) or (now_utc.hour == MARKET_OPEN_HOUR_UTC and now_utc.minute >= MARKET_OPEN_MINUTE_UTC)
        is_weekend = now_utc.weekday() >= 5
        if is_weekend or not after_open:
            log_event("INFO", "Skipping notification due to market being closed", ticker=ticker)
            return

        if bear_price is not None and last_close <= bear_price and not notified_bear:
            notify_event(ticker, f"Bear case hit (close: {price_str})", row, mailing_emails)
            update_notified_flags(ticker, {'notified_bear': True})

        if bull_price is not None and last_close >= bull_price and not notified_bull:
            notify_event(ticker, f"Bull case hit (close: {price_str})", row, mailing_emails)
            update_notified_flags(ticker, {'notified_bull': True})

        notified_daily_change = row.get('notified_daily_change', False)
        last_daily_notify_date = row.get('last_daily_notify_date')
        last_notify_date_obj = None
        if last_daily_notify_date:
            try:
                last_notify_date_obj = datetime.fromisoformat(str(last_daily_notify_date)).date()
            except Exception:
                last_notify_date_obj = None

        weekday = now_utc.weekday()
        after_open = (now_utc.hour > MARKET_OPEN_HOUR_UTC) or (now_utc.hour == MARKET_OPEN_HOUR_UTC and now_utc.minute >= MARKET_OPEN_MINUTE_UTC)
        is_weekend = weekday >= 5
        can_reset_today = (not is_weekend) and after_open

        if last_notify_date_obj and last_notify_date_obj < today_utc and notified_daily_change and can_reset_today:
            try:
                reset_notified_flags(ticker, {'notified_daily_change': False})
                notified_daily_change = False
            except Exception as e:
                log_event("ERROR", "Reset daily notification failed", ticker=ticker, error=str(e))

        if previous_close != 0:
            daily_change = (last_close - previous_close) / previous_close * 100
            threshold = row.get('daily_change_threshold', DAILY_CHANGE_THRESHOLD)
            if daily_change >= threshold or daily_change <= -threshold:
                should_notify = (last_notify_date_obj is None or last_notify_date_obj < today_utc)
                if should_notify:
                    percent_str = f"{abs(daily_change):.2f}%"
                    if daily_change >= threshold:
                        notify_event(ticker, f"Price increase >{percent_str} (close: {price_str})", row, mailing_emails)
                    elif daily_change <= -threshold:
                        notify_event(ticker, f"Price decrease >{percent_str} (close: {price_str})", row, mailing_emails)
                    try:
                        update_notified_flags(ticker, {
                            'notified_daily_change': True,
                            'last_daily_notify_date': str(today_utc)
                        })
                    except Exception as e:
                        log_event("ERROR", "Failed to update daily notification flags", ticker=ticker, error=str(e))
    except Exception as e:
        log_event("ERROR", "Unhandled error during row processing", ticker=ticker, error=str(e))
