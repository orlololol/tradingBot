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
        print("Config:", self.config)  # Debugging the config
        print("RPC URL:", config.get('rpc_url', 'Not found'))  # Safely check for 'rpc_url'
        self.client = AsyncClient(config['rpc_url'])
        
    async def get_token_account(self, token_address: str) -> Dict:
        """Get token account information"""
        try:
            pubkey = Pubkey.from_string(token_address)
            response = await self.client.get_account_info(pubkey)
            return response.value if response.value else {}
        except Exception as e:
            logger.error(f"Failed to get token account: {e}")
            return {}
            
    async def get_token_price(self, token_id: str, show_extra_info: bool = False) -> Optional[Dict]:
        """
        Get the price of a token using its symbol or address.
        
        Args:
            token_id (str): The symbol or address of the token (case-sensitive for addresses).
            show_extra_info (bool): Whether to include extra information in the response.
        
        Returns:
            Optional[Dict]: Price information or None if an error occurs.
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.jup.ag/price/v2?ids={token_id}&showExtraInfo={str(show_extra_info).lower()}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data: Dict = await response.json()
                        return data.get("data", {}).get(token_id, {})
                    else:
                        logger.error(f"Failed to fetch price for {token_id}: HTTP {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching token price for {token_id}: {e}")
            return None


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