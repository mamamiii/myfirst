class Config:
    # API Settings
    API_RATE_LIMIT = "100 per minute"
    CACHE_TIMEOUT = 300  # 5 minutes
    MAX_STRIKES = 50
    
    # Flask Settings
    SWAGGER_UI_THEME = "dark"
    JSON_SORT_KEYS = False
