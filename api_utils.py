import yfinance as yf
from datetime import datetime
import re
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_symbol(symbol):
    """Validate stock symbol format."""
    if not symbol or not re.match(r'^[A-Z]{1,5}$', symbol):
        raise ValueError("Invalid symbol format")
    
    # Verify if the symbol exists with retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            ticker = yf.Ticker(symbol)
            # Just check if we can get basic info
            if ticker.info:
                return symbol.upper()
            time.sleep(1)  # Add delay between retries
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed for {symbol}: {str(e)}")
            if attempt == max_retries - 1:
                logger.error(f"All attempts failed for symbol {symbol}")
                raise ValueError(f"Unable to verify symbol: {symbol}")
            time.sleep(2)  # Wait before retry
    
    return symbol.upper()

def validate_date(date_str):
    """Validate date string format."""
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        if date < datetime.now().date():
            raise ValueError("Expiration date must be in the future")
        return date
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid date format. Use YYYY-MM-DD: {str(e)}")

def get_options_chain(symbol, expiration=None, min_strike=None, max_strike=None):
    """Fetch options chain data from yfinance."""
    try:
        logger.info(f"Fetching options for {symbol}, exp: {expiration}, strikes: {min_strike}-{max_strike}")
        ticker = yf.Ticker(symbol)
        
        # Get available expiration dates with retry logic
        max_retries = 3
        expirations = None
        
        for attempt in range(max_retries):
            try:
                expirations = ticker.options
                if expirations:
                    break
                time.sleep(1)
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed to get expirations: {str(e)}")
                if attempt == max_retries - 1:
                    logger.error("Failed to get expirations after all retries")
                    return None
                time.sleep(2)
        
        if not expirations:
            logger.error(f"No options available for {symbol}")
            return None
            
        logger.info(f"Available expirations: {expirations}")
        
        # Use first available expiration if none specified
        exp_date = expiration.strftime('%Y-%m-%d') if expiration else expirations[0]
        if exp_date not in expirations:
            logger.error(f"Expiration {exp_date} not available for {symbol}")
            raise ValueError(f"Expiration date {exp_date} not available")
            
        # Fetch options chain with retry logic
        opts = None
        for attempt in range(max_retries):
            try:
                opts = ticker.option_chain(exp_date)
                if opts is not None:
                    break
                time.sleep(1)
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed to get options chain: {str(e)}")
                if attempt == max_retries - 1:
                    logger.error("Failed to get options chain after all retries")
                    return None
                time.sleep(2)
                
        if opts is None:
            logger.error(f"Failed to fetch options chain for {symbol} at {exp_date}")
            return None
            
        # Combine calls and puts
        calls = opts.calls.to_dict('records')
        puts = opts.puts.to_dict('records')
        
        # Filter by strike price if specified
        if min_strike is not None:
            calls = [c for c in calls if c['strike'] >= float(min_strike)]
            puts = [p for p in puts if p['strike'] >= float(min_strike)]
        if max_strike is not None:
            calls = [c for c in calls if c['strike'] <= float(max_strike)]
            puts = [p for p in puts if p['strike'] <= float(max_strike)]
            
        logger.info(f"Successfully fetched options chain for {symbol}")
        return {
            'symbol': symbol,
            'expiration': exp_date,
            'calls': calls,
            'puts': puts
        }
    except Exception as e:
        logger.error(f"Error fetching options chain: {str(e)}")
        return None
