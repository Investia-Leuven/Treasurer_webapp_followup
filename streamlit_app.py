import streamlit as st
import pandas as pd
import time
from supabase import create_client
import os
import yfinance as yf
import json
from config import SUPABASE_URL, SUPABASE_KEY, EMAIL_USER, EMAIL_PASS, DAILY_CHANGE_THRESHOLD, SMTP_HOST, SMTP_PORT
from email_template import prepare_email_body

def log_event(level, message, **context):
    log = {"level": level, "message": message}
    log.update(context)
    print(json.dumps(log))

def display_header():
    """Display the app header with logo and title."""
    st.markdown(
        """
        <style>
        .header-container {
            display: flex;
            align-items: center;
            position: sticky;
            top: 0;
            background-color: white;
            padding: 10px 0;
            border-bottom: 1px solid #ddd;
            z-index: 1000;
        }
        .header-title {
            font-size: 20px;
            font-weight: bold;
            color: #333;
            text-align: center;
            flex-grow: 1;
            margin-right: 60px;
        }
        .block-container {
            padding-top: 60px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 6, 1])
    with col1:
        st.image("logoinvestia.png", width=80)
    with col2:
        st.markdown(
            "<div class='header-title'>Investia - Stock alert manager (bèta)</div>",
            unsafe_allow_html=True
        )
    with col3:
        with open("investia_help.pdf", "rb") as pdf_file:
            st.download_button("Info", pdf_file, file_name="Investia_Help.pdf", use_container_width=True)

def display_footer():
    """Display sticky footer."""
    st.markdown("""
        <style>
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            text-align: center;
            background-color: white;
            padding: 10px;
            font-size: 0.85em;
            color: grey;
            z-index: 100;
            border-top: 1px solid #ddd;
        }
        </style>
        <div class="footer">
            <i>This is a bèta version. All rights reserved by Investia. 
            Suggestions or errors can be reported to Vince Coppens.</i>
        </div>
    """, unsafe_allow_html=True)

def insert_stock(ticker, bear, bau, bull, pro_list, contra_list, email, daily_change_threshold, supabase):
    """Insert a stock into the database."""
    data = {
        "ticker": ticker,
        "bear_price": bear,
        "bau_price": bau,
        "bull_price": bull,
        "pro_1": pro_list[0] if len(pro_list) > 0 else "",
        "pro_2": pro_list[1] if len(pro_list) > 1 else "",
        "pro_3": pro_list[2] if len(pro_list) > 2 else "",
        "contra_1": contra_list[0] if len(contra_list) > 0 else "",
        "contra_2": contra_list[1] if len(contra_list) > 1 else "",
        "contra_3": contra_list[2] if len(contra_list) > 2 else "",
        "email": email,
        "daily_change_threshold": daily_change_threshold,
    }
    supabase.table("stock_watchlist").insert(data).execute()

def get_all_stocks(supabase):
    """Return a DataFrame of all stocks, ticker first, 1-based index."""
    response = supabase.table("stock_watchlist").select("*").execute()
    df = pd.DataFrame(response.data)
    if not df.empty:
        # Drop columns containing 'date', 'time', or 'created_at'
        df = df.loc[:, ~df.columns.str.contains('date|time|created_at', case=False)]
        thesis_cols = [col for col in df.columns if col.startswith('pro_') or col.startswith('contra_')]
        main_cols = [col for col in df.columns if col not in thesis_cols]
        df = df[main_cols + thesis_cols]
        if "ticker" in df.columns:
            cols = df.columns.tolist()
            cols = ["ticker"] + [col for col in cols if col != "ticker"]
            df = df[cols]
        df.index = df.index + 1
    return df

def update_stock(selected_ticker, update_data, supabase):
    """Update a stock entry identified by selected_ticker."""
    supabase.table("stock_watchlist").update(update_data).eq("ticker", selected_ticker).execute()

def delete_stock(selected_ticker, supabase):
    """Delete a stock entry identified by selected_ticker."""
    supabase.table("stock_watchlist").delete().eq("ticker", selected_ticker).execute()

def main():
    st.set_page_config(page_title="Investia Stock Alert", page_icon="investia_favicon.png", layout="wide")
    display_header()
    st.markdown("")
    st.markdown(
        "<p style='color:darkblue;'>This web page allows to manage our watchlist, set price alerts, and configure a mailing list to receive notifications when a bear or bull case is reached or when a share price changes significantly.</p>",
        unsafe_allow_html=True
    )
    display_footer()

    # --- Load Supabase ---
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # --- Inputs pulled out of form for live update ---
    ticker = st.text_input("Ticker")
    ticker = ticker.upper()
    if ticker.strip() != "":
        try:
            ticker_info = yf.Ticker(ticker)
            if not ticker_info.info or ticker_info.info.get("regularMarketPrice") is None:
                log_event("WARN", "Ticker invalid or delisted", ticker=ticker)
                st.warning("Ticker not found. Please enter a valid ticker symbol. Yahoo Finance tickers can slightly deviate, use the same ticker format as on their website.")
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

    if st.button("Add Stock"):
        if ticker.strip() == "":
            st.warning("Ticker cannot be empty. Please enter a valid ticker.")
        else:
            # Check if ticker already exists
            exists_response = supabase.table("stock_watchlist").select("ticker").eq("ticker", ticker).execute()
            if exists_response.data and len(exists_response.data) > 0:
                st.warning(f"{ticker} already exists in the watchlist. Please use a different ticker.")
            else:
                pro_list = [pro_1, pro_2, pro_3]
                contra_list = [contra_1, contra_2, contra_3]
                insert_stock(ticker, bear, bau, bull, pro_list, contra_list, email, daily_change_threshold, supabase)
                st.success(f"{ticker} added successfully!")

    # --- Display DataFrame ---
    try:
        df = get_all_stocks(supabase)
    except Exception as e:
        log_event("ERROR", "Failed to fetch watchlist", error=str(e))
        df = pd.DataFrame()

    st.dataframe(df)

    if not df.empty:
        with st.expander("Edit or Delete Stock Entry", expanded=False):
            selected_ticker = st.selectbox("Select Ticker to edit/delete", df["ticker"].tolist())
            selected_row = df[df["ticker"] == selected_ticker].iloc[0]

            # Editable fields for all columns
            edit_ticker = st.text_input("Ticker", value=selected_row["ticker"], key="edit_ticker")
            if edit_ticker != selected_ticker:
                st.warning("You are changing the primary key (Ticker). Be careful with this change.")
            
            col_email, col_thresh = st.columns([3, 1])
            with col_email:
                edit_email = st.text_input("Email", value=selected_row.get("email", ""), key="edit_email")
            with col_thresh:
                edit_daily_change_threshold = st.number_input("Daily change notification %", value=float(selected_row.get("daily_change_threshold", 3.0)), key="edit_thresh", min_value=0.0, step=0.1)
            col1, col2, col3 = st.columns(3)
            with col1:
                edit_bear = st.number_input("Bear Case", value=float(selected_row["bear_price"]), key="edit_bear")
            with col2:
                edit_bau = st.number_input("Base Case (BAU)", value=float(selected_row["bau_price"]), key="edit_bau")
            with col3:
                edit_bull = st.number_input("Bull Case", value=float(selected_row["bull_price"]), key="edit_bull")

            st.write("**Investment Thesis**")
            pro_col, contra_col = st.columns(2)
            with pro_col:
                edit_pro_1 = st.text_input("Pro 1", value=selected_row.get("pro_1", ""), key="edit_pro_1")
                edit_pro_2 = st.text_input("Pro 2", value=selected_row.get("pro_2", ""), key="edit_pro_2")
                edit_pro_3 = st.text_input("Pro 3", value=selected_row.get("pro_3", ""), key="edit_pro_3")
            with contra_col:
                edit_contra_1 = st.text_input("Contra 1", value=selected_row.get("contra_1", ""), key="edit_contra_1")
                edit_contra_2 = st.text_input("Contra 2", value=selected_row.get("contra_2", ""), key="edit_contra_2")
                edit_contra_3 = st.text_input("Contra 3", value=selected_row.get("contra_3", ""), key="edit_contra_3")

            message = None
            col1, col2, _ = st.columns([1, 1, 7])
            with col1:
                if st.button("Update Stock"):
                    update_data = {
                        "ticker": edit_ticker,
                        "bear_price": edit_bear,
                        "bau_price": edit_bau,
                        "bull_price": edit_bull,
                        "pro_1": edit_pro_1,
                        "pro_2": edit_pro_2,
                        "pro_3": edit_pro_3,
                        "contra_1": edit_contra_1,
                        "contra_2": edit_contra_2,
                        "contra_3": edit_contra_3,
                        "email": edit_email,
                        "daily_change_threshold": edit_daily_change_threshold,
                    }
                    update_stock(selected_ticker, update_data, supabase)
                    st.success("Updated")
                    time.sleep(0.5)
                    st.rerun()
            with col2:
                if st.button("Delete Stock"):
                    delete_stock(selected_ticker, supabase)
                    st.error("Deleted")
                    time.sleep(0.5)
                    st.rerun()
            if message:
                getattr(st, message[0])(message[1])

    with st.expander("Manage Mailing List", expanded=False):
        st.write("All emails in this list will receive all alerts in addition to the stock-specific email set above.")

        new_email = st.text_input("New Email")
        if st.button("Add Email"):
            if new_email.strip() == "":
                st.warning("Email cannot be empty.")
            else:
                try:
                    # Check if email already exists
                    exists_response = supabase.table("mailing_list").select("email").eq("email", new_email).execute()
                    if exists_response.data and len(exists_response.data) > 0:
                        st.warning(f"{new_email} already exists in the mailing list.")
                    else:
                        supabase.table("mailing_list").insert({"email": new_email}).execute()
                        st.success(f"{new_email} added to mailing list.")
                except Exception as e:
                    log_event("ERROR", "Failed to fetch mailing list", error=str(e))

        try:
            # Fetch and display mailing list
            mailing_response = supabase.table("mailing_list").select("*").execute()
            mailing_df = pd.DataFrame(mailing_response.data)
            if not mailing_df.empty:
                # Drop columns containing 'date', 'time', or 'created_at'
                mailing_df = mailing_df.loc[:, ~mailing_df.columns.str.contains('date|time|created_at', case=False)]
                mailing_df.index = mailing_df.index + 1
        except Exception as e:
            log_event("ERROR", "Failed to fetch mailing list", error=str(e))
            mailing_df = pd.DataFrame()

        if mailing_df.empty:
            st.write("Mailing list is empty.")
        else:
            st.dataframe(mailing_df)

            email_to_delete = st.selectbox("Select Email to delete", mailing_df["email"].tolist())
            if st.button("Delete Email"):
                supabase.table("mailing_list").delete().eq("email", email_to_delete).execute()
                st.warning(f"{email_to_delete} deleted from mailing list.")

if __name__ == "__main__":
    main()
