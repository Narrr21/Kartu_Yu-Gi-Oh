# config.py

CACHE_FILE = "./json/card_cache.json"
PACK_URLS_FILE = "./json/pack_urls.json"
ICON_FILE = "icon.ico"

MAIN_SEARCH_PAGE_URL = "https://www.db.yugioh-card.com/yugiohdb/card_list.action?clm=1&wname=CardSearch"
MAX_PACKS_TO_SCRAPE = None
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

FUZZY_SCORE_CUTOFF_SINGLE = 60
FUZZY_SCORE_CUTOFF_MULTI = 50
MULTI_SEARCH_LIMIT = None