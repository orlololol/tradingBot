# Run this program to check balance of bot's wallet

import asyncio
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey

async def check_wallet_balance(wallet_address: str):
    # Initialize the Solana client
    client = AsyncClient("https://api.mainnet-beta.solana.com")

    # Convert the wallet address to a Pubkey object
    public_key = Pubkey.from_string(wallet_address)

    try:
        # Fetch the wallet's balance
        response = await client.get_balance(public_key)
        lamports = response.value  # Balance in lamports
        sol = lamports / 1_000_000_000  # Convert lamports to SOL

        print(f"Wallet Address: {wallet_address}")
        print(f"Balance: {sol} SOL")
    except Exception as e:
        print(f"Error checking wallet balance: {e}")
    finally:
        # Close the client connection
        await client.close()

# Replace with your bot's wallet address
wallet_address = "CBgSHapnY6Ef2K7JpFDcGXzdGpFFNN3cLDgvFaofuBtL"

# Run the async function
asyncio.run(check_wallet_balance(wallet_address))
