import logging
import sys
import os

# Add 'services' directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'source', 'python', 'services')))

from discord_bot import TradingBot

logging.basicConfig(level=logging.INFO)

from dotenv import load_dotenv
load_dotenv()
discord_token = os.getenv('discord_bot_token')

# Provide the bot configuration
config = {
    'token': discord_token  # Replace with your bot token
}

bot = TradingBot(config)

if __name__ == "__main__":
    bot.run(config['token'])
