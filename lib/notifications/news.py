import yfinance as yf
from lib.logging import log_event

def fetch_latest_news(ticker, limit=3):
    """
    Fetches the latest news articles for the given ticker from Yahoo Finance.
    Returns a list of dictionaries with 'title' and 'canonicalUrl' keys.
    """
    news_items = []
    try:
        stock = yf.Ticker(ticker)
        raw_news = stock.news or []
        for item in raw_news[:limit]:
            title = item.get("title") or item.get("content", {}).get("title")
            url = (item.get("link")
                   or item.get("url")
                   or item.get("canonicalUrl")
                   or item.get("content", {}).get("canonicalUrl", {}))
            if isinstance(url, dict):
                url = url.get("url")
            if title and url:
                news_items.append({"title": title, "canonicalUrl": url})
    except Exception as e:
        log_event("ERROR", "Failed to fetch news", ticker=ticker, error=str(e))
    return news_items
