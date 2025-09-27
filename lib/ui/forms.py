# lib/ui/forms.py

import streamlit as st
import yfinance as yf
from lib.utils import log_event

def validate_ticker(ticker: str) -> float | None:
    """
    Validates ticker symbol via yfinance and returns current price or None.
    """
    try:
        ticker_info = yf.Ticker(ticker)
        if not ticker_info.info or ticker_info.info.get("regularMarketPrice") is None:
            return None
        return ticker_info.info.get("regularMarketPrice")
    except Exception as e:
        log_event("ERROR", "Ticker validation failed", ticker=ticker, error=str(e))
        return None

def stock_input_form():
    """
    Renders the input form for stock entry.
    Returns all input values.
    """
    ticker = st.text_input("Ticker").upper()
    if ticker:
        price = validate_ticker(ticker)
        if price is None:
            log_event("WARN", "Ticker invalid or delisted", ticker=ticker)
            st.warning(
                "Ticker not found. Please enter a valid ticker symbol. "
                "Yahoo Finance tickers can slightly deviate, use the same ticker format as on their website."
            )
        else:
            st.success(f"{ticker} valid. Current price: {price:,.2f}")

    col_email, col_thresh = st.columns([3, 1])
    with col_email:
        email = st.text_input("Email", value="example@gmail.com")
    with col_thresh:
        daily_change_threshold = st.number_input("Daily change notification %", value=3.0, min_value=0.0, step=0.1)

    col1, col2, col3 = st.columns(3)
    with col1:
        bear = st.number_input("Bear Case (in USD)", value=0.0)
    with col2:
        bau = st.number_input("Base Case (BAU) (in USD)", value=0.0)
    with col3:
        bull = st.number_input("Bull Case (in USD)", value=0.0)

    st.write("**Investment Thesis**")
    pro_col, contra_col = st.columns(2)
    with pro_col:
        pro_1 = st.text_input("Pro 1")
        pro_2 = st.text_input("Pro 2")
        pro_3 = st.text_input("Pro 3")
    with contra_col:
        contra_1 = st.text_input("Contra 1")
        contra_2 = st.text_input("Contra 2")
        contra_3 = st.text_input("Contra 3")

    return ticker, bear, bau, bull, [pro_1, pro_2, pro_3], [contra_1, contra_2, contra_3], email, daily_change_threshold