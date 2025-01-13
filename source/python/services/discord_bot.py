#python/services/discord_bot.py

import discord
from discord.ext import commands, tasks
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv
import os
load_dotenv()
from solana_client import SolanaClient
from jupiter_client import JupiterClient


logger = logging.getLogger(__name__)

class TradingBot(commands.Bot):
    def __init__(self, config: Dict):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        self.config = config
        
    async def setup_hook(self):
        await self.add_cog(TradingCommands(self))
        
    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')

class TradingCommands(commands.Cog):
    def __init__(self, bot: TradingBot, solana_client: SolanaClient, jupiter_client: JupiterClient):
        self.bot = bot
        self.tracked_tokens = {}  # Example: {'BTC': {'alerts': [2.0], 'buy_price': 300}}
        self.solana_client = solana_client
        self.jupiter_client = jupiter_client
    
    @commands.command()
    async def list(self, ctx, *tokens):
        """Track a list of tokens"""
        self.tracked_tokens.update({token: {} for token in tokens})
        await ctx.send(f"Tracking tokens: {', '.join(tokens)}")
    
    @commands.command()
    async def buyprice(self, ctx, token: str, amount: float):
        """Buy token worth a specific amount in USD"""
        try:
            
            # Fetch the price of the token
            price = await self.solana_client.get_token_symbol_price(token)
            if price == 0.0:
                await ctx.send(f"Could not fetch the price for {token}.")
                return

            # Calculate the amount to buy
            amount_in_SOL = int(amount / price)  # Convert USD to SOL
            quote = await self.jupiter_client.get_quote(
                input_token="SOL",  # Assuming buying with SOL
                output_token=token,
                amount=amount_in_SOL
            )

            if not quote:
                await ctx.send(f"Failed to get a quote for {token}.")
                return

            # Execute the swap using Jupiter
            swap_result = await self.jupiter_client.submit_swap(quote)
            await ctx.send(f"Successfully bought {amount / price:.6f} {token} for ${amount:.2f}. Transaction: {swap_result['txId']}")
        except Exception as e:
            await ctx.send(f"Failed to execute buy: {e}")
    
    @commands.command()
    async def buyamt(self, ctx, token: str, quantity: float):
        """Buy a specific quantity of a token"""
        try:
            
            # Fetch the price of the token
            price = await self.solana_client.get_token_symbol_price(token)
            if price == 0.0:
                await ctx.send(f"Could not fetch the price for {token}.")
                return

            # Calculate the amount to buy
            amount_in_SOL = int(quantity / price)  # Convert USD to lamports
            quote = await self.jupiter_client.get_quote(
                input_token="SOL",  # Assuming buying with SOL
                output_token=token,
                amount=amount_in_SOL
            )

            if not quote:
                await ctx.send(f"Failed to get a quote for {token}.")
                return

            # Execute the swap using Jupiter
            swap_result = await self.jupiter_client.submit_swap(quote)
            await ctx.send(f"Successfully bought {amount / price:.6f} {token} for ${amount:.2f}. Transaction: {swap_result['txId']}")
        except Exception as e:
            await ctx.send(f"Failed to execute buy: {e}")

    @commands.command()
    async def sellprice(self, ctx, token: str, amount: float):
        """Sell token worth a specific amount in USD"""
        try:
            token_address = self.tracked_tokens.get(token.upper())
            if not token_address:
                await ctx.send(f"Token {token} not found in the token map.")
                return

            # Fetch the price of the token
            price = await self.solana_client.get_token_symbol_price(token_address)
            if price == 0.0:
                await ctx.send(f"Could not fetch the price for {token}.")
                return

            # Calculate the amount to sell
            amount_in_lamports = int(amount * 1e9 / price)  # Convert USD to lamports
            quote = await self.jupiter_client.get_quote(
                input_token=token_address,
                output_token="SOL",  # Assuming selling to SOL
                amount=amount_in_lamports
            )

            if not quote:
                await ctx.send(f"Failed to get a quote for {token}.")
                return

            # Execute the swap using Jupiter
            swap_result = await self.jupiter_client.submit_swap(quote)
            await ctx.send(f"Successfully sold {amount / price:.6f} {token} for ${amount:.2f}. Transaction: {swap_result['txId']}")
        except Exception as e:
            await ctx.send(f"Failed to execute sell: {e}")
    
    @commands.command()
    async def alerts(self, ctx, token: str, target: str):
        """Set an alert for a token price or multiplier"""
        target_price = None
        if "x" in target:
            multiplier = float(target.replace("x", ""))
            buy_price = self.tracked_tokens[token].get('buy_price')
            target_price = buy_price * multiplier if buy_price else None
        else:
            target_price = float(target)
        
        if target_price:
            self.tracked_tokens[token].setdefault('alerts', []).append(target_price)
            await ctx.send(f"Alert set for {token} at ${target_price:.2f}")
        else:
            await ctx.send("Set a buy price first with !buyprice")
    
    @commands.command()
    async def checkalerts(self, ctx):
        """Check all active alerts"""
        if not self.tracked_tokens:
            await ctx.send("No active alerts.")
            return
        alert_list = "\n".join([f"{token}: ${price:.2f}" for token, price in self.tracked_tokens.items()])
        await ctx.send(f"Active alerts:\n{alert_list}")
    
    @commands.command()
    async def checkprofit(self, ctx, token: str):
        """Check profit for a token"""
        if token not in self.tracked_tokens:
            await ctx.send(f"{token} is not being tracked. Use !list to track it.")
            return
        
        buy_price = self.tracked_tokens[token].get('buy_price')
        current_price = await self.solana_client.get_token_symbol_price(token)
        if buy_price:
            profit = (current_price - buy_price) / buy_price * 100
            await ctx.send(f"{token} profit: {profit:.2f}% (${current_price:.2f} vs ${buy_price:.2f})")
        else:
            await ctx.send("No buy price set for this token.")

    @commands.command()
    async def checkprice(self, ctx, token: str):
        """Check the current price of a token"""
        try:
            token_address = self.tracked_tokens.get(token.upper())
            if not token_address:
                await ctx.send(f"Token {token} not found in the token map.")
                return

            price = await self.solana_client.get_token_symbol_price(token_address)
            if price == 0.0:
                await ctx.send(f"Could not fetch the price for {token}.")
            else:
                await ctx.send(f"The current price of {token} is ${price:.2f}")
        except Exception as e:
            await ctx.send(f"Error checking price for {token}: {e}")

    @commands.command()
    async def buyprice(self, ctx, token: str, buy_price: float, sell_price: float = None):
        """Set auto buy/sell for a token"""
        self.tracked_tokens[token] = {'buy_price': buy_price, 'sell_price': sell_price}
        await ctx.send(f"Set buy price for {token} at ${buy_price:.2f}")
        if sell_price:
            await ctx.send(f"Will sell {token} at ${sell_price:.2f}")

    @tasks.loop(seconds=60)
    async def monitor_prices(self):
        
        channel_id = os.getenv('channel_id')
        for token, data in self.tracked_tokens.items():
            current_price = await self.solana_client.get_token_symbol_price(token)
            for alert_price in data.get('alerts', []):
                if current_price >= alert_price:
                    await self.bot.get_channel(channel_id).send(
                        f"{token} reached alert price: ${alert_price:.2f} (current: ${current_price:.2f})"
                    )
            if 'sell_price' in data and current_price >= data['sell_price']:
                # Execute sell logic here
                await self.bot.get_channel(channel_id).send(
                    f"Sold {token} at ${current_price:.2f} (target: ${data['sell_price']:.2f})"
                )