import yfinance as yf
from datetime import datetime, timedelta
import re
import logging
import time
import calendar

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_third_friday(date):
    """Check if the given date is the third Friday of its month."""
    c = calendar.monthcalendar(date.year, date.month)
    fridays = [week[calendar.FRIDAY] for week in c if week[calendar.FRIDAY] != 0]
    third_friday = fridays[2]
    return date.day == third_friday

def filter_valid_expirations(expirations):
    """Filter expiration dates to only include monthly contracts at least 30 days in future."""
    today = datetime.now().date()
    min_date = today + timedelta(days=30)
    
    valid_dates = []
    for exp in expirations:
        exp_date = datetime.strptime(exp, '%Y-%m-%d').date()
        # Check if date is at least 30 days in future and is third Friday
        if exp_date >= min_date and is_third_friday(exp_date):
            valid_dates.append(exp)
    
    return sorted(valid_dates)

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
    """Validate date string format and check if it's a valid trading date."""
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        today = datetime.now().date()
        min_date = today + timedelta(days=30)
        
        if date < today:
            raise ValueError("Expiration date cannot be in the past")
        if date < min_date:
            raise ValueError("Expiration date must be at least 30 days in the future")
        if not is_third_friday(date):
            raise ValueError("Only monthly options (third Friday of each month) are supported")
        
        return date
    except (ValueError, TypeError) as e:
        if "time data" in str(e):
            raise ValueError("Invalid date format. Use YYYY-MM-DD")
        raise ValueError(str(e))

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
            raise ValueError(f"No options available for {symbol}")
        
        # Filter for valid monthly expirations
        valid_expirations = filter_valid_expirations(expirations)
        if not valid_expirations:
            raise ValueError(f"No valid monthly options available for {symbol} (at least 30 days out)")
        
        logger.info(f"Available monthly expirations: {valid_expirations}")
        
        # Handle expiration date selection
        if expiration:
            exp_date = expiration.strftime('%Y-%m-%d')
            if exp_date not in valid_expirations:
                # Find closest available monthly expiration date
                available_dates = [datetime.strptime(d, '%Y-%m-%d').date() for d in valid_expirations]
                future_dates = [d for d in available_dates if d >= expiration]
                
                if not future_dates:
                    raise ValueError(f"No valid monthly options available for or after {exp_date}. Available dates: {', '.join(valid_expirations)}")
                
                closest_date = min(future_dates)
                exp_date = closest_date.strftime('%Y-%m-%d')
                logger.info(f"Requested date {expiration} not available, using closest monthly date: {exp_date}")
        else:
            # Use first available valid expiration date
            exp_date = valid_expirations[0]
            
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
            raise ValueError(f"Failed to fetch options chain for {symbol} at {exp_date}")
            
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
        raise
