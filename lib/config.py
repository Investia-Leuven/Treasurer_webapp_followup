import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
EMAIL_USER = os.environ.get('EMAIL_USER')
EMAIL_PASS = os.environ.get('EMAIL_PASS')

SMTP_HOST = 'smtp-auth.mailprotect.be'
SMTP_PORT = 587

DAILY_CHANGE_THRESHOLD = float(os.environ.get("DAILY_CHANGE_THRESHOLD", 4.0))
MARKET_OPEN_HOUR_UTC = int(os.environ.get("MARKET_OPEN_HOUR_UTC", "10"))
MARKET_OPEN_MINUTE_UTC = int(os.environ.get("MARKET_OPEN_MINUTE_UTC", "30"))