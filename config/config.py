import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    API_KEY = os.getenv("DELTA_API_KEY")
    API_SECRET = os.getenv("DELTA_API_SECRET")
    BASE_URL =  'https://api.india.delta.exchange'
    
    # Trading parameters
    DEFAULT_LEVERAGE = 1
    MAX_POSITION_SIZE = 1000  # USD
    RISK_PER_TRADE = 0.02  # 2% of capital

