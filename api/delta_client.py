"""
Core Delta Exchange API client with authentication
"""
import hmac
import hashlib
import time
import json
import requests
from typing import Dict, Optional
from config.config import Config


class DeltaExchangeClient:
    """Base client for Delta Exchange API with authentication"""
    
    def __init__(self, api_key: str = None, api_secret: str = None):
        self.api_key = api_key or Config.API_KEY
        self.api_secret = api_secret or Config.API_SECRET
        self.base_url = Config.BASE_URL
        
        if not self.api_key or not self.api_secret:
            raise ValueError("API credentials not found. Set them in .env file")
    
    def _generate_signature(self, method: str, signature_data: str, timestamp: str) -> str:
        """Generate HMAC-SHA256 signature"""
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            signature_data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _request(self, method: str, endpoint: str, params: Dict = None, 
                 data: Dict = None, auth: bool = True) -> Dict:
        """Make HTTP request to Delta Exchange API"""
        url = f"{self.base_url}{endpoint}"
        payload = json.dumps(data) if data else ""
        
        # Build query string for signature (sorted by key)
        query_string = ""
        if params:
            sorted_params = sorted(params.items())
            query_string = "?" + "&".join([f"{k}={v}" for k, v in sorted_params])
        
        # Generate headers
        if auth:
            timestamp = str(int(time.time()))
            # Signature format: method + timestamp + path + query_string + payload
            signature_data = method + timestamp + endpoint + query_string + payload
            signature = self._generate_signature(method, signature_data, timestamp)
            
            headers = {
                'api-key': self.api_key,
                'timestamp': timestamp,
                'signature': signature,
                'Content-Type': 'application/json'
            }
        else:
            headers = {'Content-Type': 'application/json'}
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                data=payload if data else None,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API Request Error: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            raise
