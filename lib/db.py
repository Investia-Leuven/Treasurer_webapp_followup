from supabase import create_client
from lib.config import SUPABASE_URL, SUPABASE_KEY
import pandas as pd

def get_supabase_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def insert_stock(ticker, bear, bau, bull, pro_list, contra_list, email, daily_change_threshold):
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

def get_all_stocks():
    response = supabase.table("stock_watchlist").select("*").execute()
    df = pd.DataFrame(response.data)
    if not df.empty:
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

def update_stock(selected_ticker, update_data):
    supabase.table("stock_watchlist").update(update_data).eq("ticker", selected_ticker).execute()

def delete_stock(selected_ticker):
    supabase.table("stock_watchlist").delete().eq("ticker", selected_ticker).execute()

def check_ticker_exists(ticker):
    res = supabase.table("stock_watchlist").select("ticker").eq("ticker", ticker).execute()
    return bool(res.data)

def fetch_mailing_list():
    res = supabase.table("mailing_list").select("*").execute()
    df = pd.DataFrame(res.data)
    if not df.empty:
        df = df.loc[:, ~df.columns.str.contains('date|time|created_at', case=False)]
        df.index += 1
    return df

def check_email_exists(email):
    res = supabase.table("mailing_list").select("email").eq("email", email).execute()
    return bool(res.data)

def add_email_to_mailing_list(email):
    supabase.table("mailing_list").insert({"email": email}).execute()

def delete_email_from_mailing_list(email):
    supabase.table("mailing_list").delete().eq("email", email).execute()

def reset_notified_flags(ticker):
    supabase.table("stock_watchlist").update({
        "notified_bear": False,
        "notified_bau": False,
        "notified_bull": False,
    }).eq("ticker", ticker).execute()

def update_notified_flags(ticker, bear=None, bau=None, bull=None):
    update_data = {}
    if bear is not None:
        update_data["notified_bear"] = bear
    if bau is not None:
        update_data["notified_bau"] = bau
    if bull is not None:
        update_data["notified_bull"] = bull
    if update_data:
        supabase.table("stock_watchlist").update(update_data).eq("ticker", ticker).execute()

def fetch_mailing_emails():
    res = supabase.table("mailing_list").select("email").execute()
    return [item["email"] for item in res.data]

def fetch_watchlist():
    response = supabase.table("stock_watchlist").select("*").execute()
    rows = response.data
    updated_at_exists = any("updated_at" in row for row in rows)
    return rows, updated_at_exists

supabase = get_supabase_client()