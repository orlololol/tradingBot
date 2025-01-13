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
        self.token_map = config.get("token_map", {})  # Map token symbols to addresses
        
    async def get_quote(self, 
                       input_token: str,
                       output_token: str,
                       amount: float) -> Dict:
        """Get swap quote from Jupiter"""
        input_address = self.token_map.get(input_token.upper())
        output_address = self.token_map.get(output_token.upper())
        if not input_address or not output_address:
            raise ValueError("Invalid token symbols.")
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/quote"
                params = {
                    "inputMint": input_address,
                    "outputMint": output_address,
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