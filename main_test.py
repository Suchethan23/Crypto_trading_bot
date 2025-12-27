from Bot.trading_bot import TradingBot

def main():
    """Main function to demonstrate bot usage"""
    
    # Initialize bot
    print("Initializing Delta Exchange Trading Bot...")
    bot = TradingBot()
    
    # Display account info
    bot.display_balance()
    bot.monitor_positions()
    
    # Example: Get market data
    print("\n=== Market Data Example ===")
    ticker = bot.client.get_ticker('PIUSD')
    print(f"BTC Price: {ticker.get('result', {}).get('mark_price')}")
    
    # Example trades (COMMENTED OUT - uncomment to execute)
    symbol = 'PIUSD'
    size = 1  # contracts
    
    # Market order example
    bot.execute_simple_trade(symbol, 'sell', size)
    
    # Limit order example
    # bot.execute_limit_trade(symbol, 'buy', size, limit_price=50000)
    
    # Stop loss example
    # bot.set_stop_loss(symbol, 'sell', size, stop_price=48000)
    
    # EXIT POSITION EXAMPLES:
    
    # Exit 100% of a position (market order)
    # bot.exit_position('PIUSD', percentage=100)
    
    # Exit 50% of a position (market order)
    # bot.exit_position('PIUSD', percentage=50)
    
    # Exit position with limit order (take profit)
    # bot.close_position_with_limit('PIUSD', limit_price=105000, percentage=100)
    
    # Exit ALL positions at once
    bot.exit_all_positions()
    
    print("\nBot initialized successfully!")
    print("Edit main.py to add your trading strategy.")


if __name__ == "__main__":
    main()