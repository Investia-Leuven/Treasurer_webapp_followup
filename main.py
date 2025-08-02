from supabase import create_client

url = "https://fdnloyofposembrydoif.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZkbmxveW9mcG9zZW1icnlkb2lmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQxNTgwMDksImV4cCI6MjA2OTczNDAwOX0.upvUDNm_p5IzNZJvb_gkoUctA23-j7Cfmsqbao1hTNY"
supabase = create_client(url, key)

response = supabase.table("stock_watchlist").select("*").execute()
print(response.data)