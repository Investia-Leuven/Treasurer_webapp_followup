# lib/ui/edit_stock.py

import streamlit as st
import time
from lib.db import update_stock, delete_stock

def edit_stock_section(df):
    with st.expander("Edit or Delete Stock Entry", expanded=False):
        selected_ticker = st.selectbox("Select Ticker to edit/delete", df["ticker"].tolist())
        selected_row = df[df["ticker"] == selected_ticker].iloc[0]

        # Editable fields
        edit_ticker = st.text_input("Ticker", value=selected_row["ticker"], key="edit_ticker")
        if edit_ticker != selected_ticker:
            st.warning("You are changing the primary key (Ticker). Be careful with this change.")

        col_email, col_thresh = st.columns([3, 1])
        with col_email:
            edit_email = st.text_input("Email", value=selected_row.get("email", ""), key="edit_email")
        with col_thresh:
            edit_daily_change_threshold = st.number_input(
                "Daily change notification %",
                value=float(selected_row.get("daily_change_threshold", 3.0)),
                key="edit_thresh", min_value=0.0, step=0.1
            )

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
                update_stock(selected_ticker, update_data)
                st.success("Updated")
                time.sleep(0.5)
                st.rerun()

        with col2:
            if st.button("Delete Stock"):
                delete_stock(selected_ticker)
                st.error("Deleted")
                time.sleep(0.5)
                st.rerun()