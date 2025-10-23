"""
Configuration for Fantasy League AI Assistant
Loads settings from environment variables for security
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Supabase Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Sleeper Configuration
SLEEPER_LEAGUE_ID = os.getenv('SLEEPER_LEAGUE_ID')

# Server Configuration
# Railway uses PORT environment variable, fallback to API_PORT or 5001
API_PORT = int(os.getenv('PORT', os.getenv('API_PORT', 5001)))
WEB_PORT = int(os.getenv('WEB_PORT', 3000))
FLASK_ENV = os.getenv('FLASK_ENV', 'production')

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'app.log')

# Validation - ensure critical config is set
required_vars = {
    'SUPABASE_URL': SUPABASE_URL,
    'SUPABASE_SERVICE_ROLE_KEY': SUPABASE_SERVICE_ROLE_KEY,
    'OPENAI_API_KEY': OPENAI_API_KEY,
    'SLEEPER_LEAGUE_ID': SLEEPER_LEAGUE_ID
}

missing_vars = [key for key, value in required_vars.items() if not value]
if missing_vars:
    raise ValueError(
        f"Missing required environment variables: {', '.join(missing_vars)}\n"
        f"Please create a .env file with these variables. See .env.example for template."
    )

