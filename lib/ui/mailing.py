# lib/ui/mailing.py

import streamlit as st
import pandas as pd
from lib.db import (
    check_email_exists,
    add_email_to_mailing_list,
    fetch_mailing_list,
    delete_email_from_mailing_list,
)
from lib.utils import log_event

def mailing_list_section():
    with st.expander("Manage Mailing List", expanded=False):
        st.write("All emails in this list will receive all alerts in addition to the stock-specific email set above.")

        # Add new email
        new_email = st.text_input("New Email")
        if st.button("Add Email"):
            if new_email.strip() == "":
                st.warning("Email cannot be empty.")
            else:
                try:
                    if check_email_exists(new_email):
                        st.warning(f"{new_email} already exists in the mailing list.")
                    else:
                        add_email_to_mailing_list(new_email)
                        st.success(f"{new_email} added to mailing list.")
                except Exception as e:
                    log_event("ERROR", "Failed to add email", error=str(e))

        # Display mailing list
        try:
            mailing_df = fetch_mailing_list()
        except Exception as e:
            log_event("ERROR", "Failed to fetch mailing list", error=str(e))
            mailing_df = pd.DataFrame()

        if mailing_df.empty:
            st.write("Mailing list is empty.")
        else:
            st.dataframe(mailing_df)

            email_to_delete = st.selectbox("Select Email to delete", mailing_df["email"].tolist())
            if st.button("Delete Email"):
                delete_email_from_mailing_list(email_to_delete)
                st.warning(f"{email_to_delete} deleted from mailing list.")
                st.rerun()