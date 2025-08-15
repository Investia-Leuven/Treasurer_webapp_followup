import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
EMAIL_USER = os.environ.get('EMAIL_USER')
EMAIL_PASS = os.environ.get('EMAIL_PASS')

SMTP_HOST = 'smtp-auth.mailprotect.be'
SMTP_PORT = 587

DAILY_CHANGE_THRESHOLD = 0.1  # percentage threshold for daily change notifications