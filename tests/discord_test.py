import asyncio
import logging
import sys
import os

# Add 'services' directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'source', 'python', 'services')))

from discord_bot import TradingBot, TradingCommands
from solana_client import SolanaClient
from jupiter_client import JupiterClient

logging.basicConfig(level=logging.INFO)

from dotenv import load_dotenv
load_dotenv()
discord_token = os.getenv('discord_bot_token')

# Provide the bot configuration
discord_config = {
    'token': discord_token  # Replace with your bot token
}
config = {
    'rpc_url': "https://api.mainnet-beta.solana.com",
    'slippage_bps': 50,
}

bot = TradingBot(discord_config, config)

async def main():
    # Initialize clients
    solana_client = SolanaClient(config)
    jupiter_client = JupiterClient(config)

    # Add the cog to the bot
    await bot.add_cog(TradingCommands(bot, solana_client, jupiter_client))

    # Run the bot
    await bot.start(discord_config['token'])

# Run the bot with asyncio
asyncio.run(main())
