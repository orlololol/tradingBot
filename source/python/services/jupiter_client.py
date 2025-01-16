#python/services/jupiter_client.py

from typing import Dict, List, Optional
import logging
import aiohttp

logger = logging.getLogger(__name__)

class JupiterClient:
    def __init__(self, config: Dict):
        """Initialize Jupiter DEX client"""
        self.config = config
        self.base_url = "https://quote-api.jup.ag/v6"
        
    async def get_quote(self, 
                       input_token: str,
                       output_token: str,
                       amount: float) -> Dict:
        """Get swap quote from Jupiter"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/quote"
                params = {
                    "inputMint": input_token,
                    "outputMint": output_token,
                    "amount": str(int(amount * 1e9)),  # Convert to lamports
                    "slippageBps": self.config.get('slippage_bps', 50)
                }
                async with session.get(url, params=params) as response:
                    return await response.json()
        except Exception as e:
            logger.error(f"Failed to get Jupiter quote: {e}")
            return {}
            
    async def submit_swap(self, quote_response: Dict) -> Dict:
        """Submit swap transaction to Jupiter"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/swap"
                async with session.post(url, json=quote_response) as response:
                    return await response.json()
        except Exception as e:
            logger.error(f"Failed to submit swap: {e}")
            return {}