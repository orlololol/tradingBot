#python/services/solana_client.py

from typing import Dict, List, Optional
import logging
import aiohttp
from solana.rpc.async_api import AsyncClient
from solders.hash import Hash
from solders.keypair import Keypair
from solders.message import MessageV0
from solders.system_program import TransferParams, transfer
from solders.transaction import VersionedTransaction
from solders.pubkey import Pubkey

logger = logging.getLogger(__name__)

class SolanaClient:
    def __init__(self, config: Dict):
        """Initialize Solana client with configuration"""
        self.config = config
        self.client = AsyncClient(config['rpc_url'])
        self.token_map : Dict = config.get("token_map", {})  # Map token symbols to addresses
        
    async def get_token_account(self, token_address: str) -> Dict:
        """Get token account information"""
        try:
            pubkey = Pubkey.from_string(token_address)
            response = await self.client.get_account_info(pubkey)
            return response.value if response.value else {}
        except Exception as e:
            logger.error(f"Failed to get token account: {e}")
            return {}
            
    async def get_token_address_price(self, token_address: str) -> float:
        """Get current token price from Jupiter aggregator"""
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://price.jup.ag/v4/price?ids={token_address}"
                async with session.get(url) as response:
                    data = await response.json()
                    return float(data['data'][token_address]['price'])
        except Exception as e:
            logger.error(f"Failed to get token price: {e}")
            return 0.0
    
    async def get_token_symbol_price(self, token_symbol: str) -> float:
        """Get token price using Jupiter aggregator by symbol"""
        token_address = self.token_map.get(token_symbol.upper())
        if not token_address:
            raise ValueError(f"Token {token_symbol} not supported.")
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://price.jup.ag/v4/price?ids={token_address}"
                async with session.get(url) as response:
                    data = await response.json()
                    return float(data['data'][token_address]['price'])
        except Exception as e:
            logger.error(f"Failed to get token price for {token_symbol}: {e}")
            return 0.0

    async def get_token_supply(self, token_address: str) -> int:
        """Get token supply information"""
        try:
            pubkey = Pubkey.from_string(token_address)
            response = await self.client.get_token_supply(pubkey)
            return int(response.value.amount) if response.value else 0
        except Exception as e:
            logger.error(f"Failed to get token supply: {e}")
            return 0

    async def transfer_sol(self, sender: Keypair, receiver_address: str, amount_sol: float) -> str:
        """Transfer SOL from sender to receiver"""
        amount_lamports = int(amount_sol * 1e9)
        return await self._transfer_lamports(sender, receiver_address, amount_lamports)

    async def _transfer_lamports(self, sender: Keypair, receiver_address: str, amount_lamports: int) -> str:
        """
        Transfer SOL from sender to receiver using versioned transaction
        
        Args:
            sender: Keypair of the sender
            receiver_address: Receiver's public key as string
            amount_lamports: Amount to send in lamports (1 SOL = 1_000_000_000 lamports)
        
        Returns:
            Transaction signature
        """
        try:
            receiver = Pubkey.from_string(receiver_address)
            
            # Create the transfer instruction
            transfer_ix = transfer(
                TransferParams(
                    from_pubkey=sender.pubkey(),
                    to_pubkey=receiver,
                    lamports=amount_lamports
                )
            )
            
            # Get the latest blockhash
            blockhash_response = await self.client.get_latest_blockhash()
            blockhash = blockhash_response.value.blockhash
            
            # Create and compile the message
            message = MessageV0.try_compile(
                payer=sender.pubkey(),
                instructions=[transfer_ix],
                address_lookup_table_accounts=[],
                recent_blockhash=blockhash
            )
            
            # Create and sign the transaction
            transaction = VersionedTransaction(message, [sender])
            
            # Send the transaction
            result = await self.client.send_transaction(transaction)
            return result.value
            
        except Exception as e:
            logger.error(f"Failed to transfer SOL: {e}")
            raise