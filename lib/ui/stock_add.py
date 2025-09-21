# lib/ui/stock_add.py

import streamlit as st
import yfinance as yf
from lib.db import insert_stock, check_ticker_exists
from lib.utils import log_event
from lib.ui.forms import stock_input_form

def add_stock_section():
    """
    Handles the user interface and logic for adding a stock to the watchlist.
    Includes validation against Yahoo Finance and duplicate checking.
    """
    # Stock input form
    ticker, bear, bau, bull, pro_list, contra_list, email, daily_change_threshold = stock_input_form()

    if ticker.strip() != "":
        try:
            ticker_info = yf.Ticker(ticker)
            if not ticker_info.info or ticker_info.info.get("regularMarketPrice") is None:
                log_event("WARN", "Ticker invalid or delisted", ticker=ticker)
                st.warning(
                    "Ticker not found. Please enter a valid ticker symbol. "
                    "Yahoo Finance tickers can slightly deviate, use the same ticker format as on their website."
                )
            else:
                hist = ticker_info.history(period="1d")
                if not hist.empty:
                    current_price = ticker_info.info.get("regularMarketPrice")
                    st.success(f"{ticker} is a valid ticker symbol. Current price: ${current_price:,.2f}")
                else:
                    log_event("WARN", "No sufficient historical data", ticker=ticker)
                    st.warning("Ticker not found. Please enter a valid ticker symbol.")
        except Exception as e:
            log_event("ERROR", "Unhandled error during row processing", ticker=ticker, error=str(e))
            st.error(f"Error validating ticker: {e}")

    # Add stock logic
    if st.button("Add Stock"):
        if ticker.strip() == "":
            st.warning("Ticker cannot be empty. Please enter a valid ticker.")
        else:
            if check_ticker_exists(ticker):
                st.warning(f"{ticker} already exists in the watchlist. Please use a different ticker.")
            else:
                insert_stock(ticker, bear, bau, bull, pro_list, contra_list, email, daily_change_threshold)
                st.success(f"{ticker} added successfully!")