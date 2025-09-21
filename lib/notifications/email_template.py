def prepare_email_body(ticker, event_message, bear_price, bau_price, bull_price,
                       pro_1, pro_2, pro_3, contra_1, contra_2, contra_3, news_items):
    news_html = ""
    if news_items:
        news_html += "<h3>Latest News:</h3><ul>"
        for item in news_items:
            title = item.get('title', 'No title')
            url = item.get('canonicalUrl', '#')
            news_html += f'<li><a href="{url}" target="_blank" rel="noopener noreferrer">{title}</a></li>'
        news_html += "</ul>"

    return f"""<html>
  <body>
    <p>Dear member,</p>
    <p>This is an alert from the <strong>Investia Bot</strong> regarding the stock <strong>{ticker}</strong>.</p>
    <p>Reason for this email: <em>{event_message}</em>.</p>
    <h3>Price Levels:</h3>
    <ul>
      <li>Bear price: {bear_price}</li>
      <li>BAU price: {bau_price}</li>
      <li>Bull price: {bull_price}</li>
    </ul>
    <h3>Investment Thesis:</h3>
    <p><strong>Pros:</strong></p>
    <ul>
      <li>{pro_1}</li>
      <li>{pro_2}</li>
      <li>{pro_3}</li>
    </ul>
    <p><strong>Cons:</strong></p>
    <ul>
      <li>{contra_1}</li>
      <li>{contra_2}</li>
      <li>{contra_3}</li>
    </ul>
    <p>This event may be related to recent news or market movements.</p>
    {news_html}
    <p>Have a nice day!</p>
    <p>Kind regards,<br>The Investia bot</p>
  </body>
</html>
"""