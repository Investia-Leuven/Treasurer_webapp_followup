# lib/ui/header.py

import streamlit as st

def display_header():
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
        st.image("extra/logoinvestia.png", width=80)
    with col2:
        st.markdown(
            "<div class='header-title'>Investia - Stock alert manager (bèta)</div>",
            unsafe_allow_html=True
        )
    with col3:
        with open("extra/investia_help.pdf", "rb") as pdf_file:
            st.download_button("Info", pdf_file, file_name="Investia_Help.pdf", use_container_width=True)
    
    st.markdown("")