"""
Streamlit web application for managing a stock watchlist with alert thresholds and email notifications.
"""
import streamlit as st
import pandas as pd
from lib.config import SUPABASE_URL, SUPABASE_KEY

# Import externalized logic for db, logging, header, and footer
from lib.db import insert_stock, get_all_stocks, check_ticker_exists
from lib.utils import log_event
from lib.ui.header import display_header
from lib.ui.footer import display_footer
from lib.ui.edit_stock import edit_stock_section
from lib.ui.mailing import mailing_list_section
from lib.ui.stock_add import add_stock_section

def main():
    """
    Main function to run the Streamlit app.
    Handles UI rendering, user inputs, and interactions with the database.
    """
    # Page configuration and UI setup
    st.set_page_config(page_title="Investia Stock Alert", page_icon="extra/investia_favicon.png", layout="wide")
    
    display_header()
    
    st.markdown(
        "<p style='color:darkblue;'>This web page allows to manage our watchlist, set price alerts, and configure a mailing list to receive notifications when a bear or bull case is reached or when a share price changes significantly.</p>",
        unsafe_allow_html=True
    )

    add_stock_section()

    # Display stock DataFrame
    try:
        df = get_all_stocks()
    except Exception as e:
        log_event("ERROR", "Failed to fetch watchlist", error=str(e))
        df = pd.DataFrame()
    st.dataframe(df)

    # Edit/Delete stock section
    if not df.empty:
        edit_stock_section(df)

    mailing_list_section()
    
    display_footer()

if __name__ == "__main__":
    main()