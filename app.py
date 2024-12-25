from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
import logging

from config import Config
from cache_manager import CacheManager
from api_utils import validate_symbol, validate_date, get_options_chain

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Setup rate limiter
      
    
    
      
    
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[Config.API_RATE_LIMIT]
)

def safe_float(value):
    """Safely convert string to float."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid number format: {value}")

def handle_errors(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Internal error: {str(e)}")
            return jsonify({'error': 'Internal server error', 'details': str(e)}), 500
    return wrapper
      
    
    
      
    

@app.route('/')
def docs():
    """Render API documentation page."""
    return render_template('docs.html')

@app.route('/api/v1/options/<symbol>')
@handle_errors
@limiter.limit(Config.API_RATE_LIMIT)
@CacheManager.cached(Config.CACHE_TIMEOUT)
def get_options(symbol):
    """Get options chain data for a given symbol."""
    try:
        # Validate and process inputs
        symbol = validate_symbol(symbol)
        expiration = request.args.get('expiration')
        min_strike = safe_float(request.args.get('min_strike'))
        max_strike = safe_float(request.args.get('max_strike'))
        
        if expiration:
            expiration = validate_date(expiration)
        
        # Fetch options data
        data = get_options_chain(symbol, expiration, min_strike, max_strike)
        if not data:
            return jsonify({'error': f'No options data available for {symbol}'}), 404
            
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({'error': 'Rate limit exceeded'}), 429
