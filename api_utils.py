import yfinance as yf
from datetime import datetime
import re

def validate_symbol(symbol):
    """Validate stock symbol format."""
    if not re.match(r'^[A-Z]{1,5}$', symbol):
        raise ValueError("Invalid symbol format")
    return symbol.upper()

def validate_date(date_str):
    """Validate date string format."""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        raise ValueError("Invalid date format. Use YYYY-MM-DD")

def get_options_chain(symbol, expiration=None, min_strike=None, max_strike=None):
    """Fetch options chain data from yfinance."""
    ticker = yf.Ticker(symbol)
    
    # Get available expiration dates
    expirations = ticker.options
    if not expirations:
        return None
        
    # Use first available expiration if none specified
    exp_date = expiration if expiration else expirations[0]
    if exp_date not in expirations:
        return None
        
    # Fetch options chain
    opts = ticker.option_chain(exp_date)
    
    # Combine calls and puts
    calls = opts.calls.to_dict('records')
    puts = opts.puts.to_dict('records')
    
    # Filter by strike price if specified
    if min_strike:
        calls = [c for c in calls if c['strike'] >= min_strike]
        puts = [p for p in puts if p['strike'] >= min_strike]
    if max_strike:
        calls = [c for c in calls if c['strike'] <= max_strike]
        puts = [p for p in puts if p['strike'] <= max_strike]
        
    return {
        'symbol': symbol,
        'expiration': exp_date,
        'calls': calls,
        'puts': puts
    }
