# 🔌 MCP Integration Guide: Ball Don't Lie API + Supabase

## Overview

Your AI assistant now has **dual data source support**:

1. **Supabase** → Fantasy league data (rosters, trades, standings)
2. **Ball Don't Lie MCP** → Real-time NFL player statistics

The AI automatically chooses the right data source based on the question!

---

## ✅ What's Already Done

I've set up the **integration framework** for you:

### Created Files:
- ✅ `external_stats.py` - External API functions (Ball Don't Lie)
- ✅ `MCP_INTEGRATION_GUIDE.md` - This guide

### Modified Files:
- ✅ `fantasy_assistant.py` - Updated to merge both function sets
  - Imports external functions
  - Merges function definitions
  - Updated system prompt with data source guidance

---

## 🔧 What You Need to Do

### Step 1: Connect Your Ball Don't Lie MCP

Open `external_stats.py` and replace the `get_mcp_client()` function with your actual MCP client initialization:

```python
def get_mcp_client():
    """Get or create MCP client for Ball Don't Lie API"""
    global _mcp_client
    if _mcp_client is None:
        # Replace this with your actual MCP initialization
        # Example (adjust based on your MCP setup):
        from your_mcp_library import BallDontLieClient
        _mcp_client = BallDontLieClient(
            api_key="your_api_key",  # if needed
            # other config...
        )
    return _mcp_client
```

### Step 2: Implement the MCP Function Calls

In `external_stats.py`, update each function to call your actual MCP. Here's an example for `get_player_game_stats()`:

```python
def get_player_game_stats(player_name: str, game_date: str = None) -> Dict[str, Any]:
    """Get NFL player statistics for a specific game"""
    try:
        logger.info(f"Getting game stats for {player_name}, date: {game_date or 'most recent'}")
        
        # Call your Ball Don't Lie MCP
        client = get_mcp_client()
        
        # Example call (adjust based on your MCP's actual API):
        response = client.get_player_stats(
            player_name=player_name,
            game_date=game_date,
            stat_type='game'
        )
        
        # Transform MCP response to our format
        return {
            'player_name': response.get('player_name'),
            'game_date': response.get('game_date'),
            'opponent': response.get('opponent'),
            'stats': {
                'passing_yards': response.get('passing_yards', 0),
                'passing_tds': response.get('passing_tds', 0),
                'rushing_yards': response.get('rushing_yards', 0),
                'rushing_tds': response.get('rushing_tds', 0),
                'receiving_yards': response.get('receiving_yards', 0),
                'receiving_tds': response.get('receiving_tds', 0),
                'receptions': response.get('receptions', 0),
                'targets': response.get('targets', 0)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting player game stats: {e}", exc_info=True)
        return {'error': str(e)}
```

### Step 3: Update Function Definitions (if needed)

If your Ball Don't Lie MCP returns different data or requires different parameters, update the function definitions in `EXTERNAL_FUNCTION_DEFINITIONS` at the bottom of `external_stats.py`.

### Step 4: Test It!

```bash
# Start your API server
python3 api_server.py

# In another terminal, test with CLI
python3 fantasy_assistant.py
```

Try questions like:
- "How many TDs did AJ Brown have last game?" (Ball Don't Lie)
- "Who owns AJ Brown?" (Supabase)
- "Show me the standings" (Supabase)
- "What are Patrick Mahomes' season stats?" (Ball Don't Lie)

---

## 🎯 How It Works

### Question Flow

```
User asks: "How many TDs did AJ Brown have last game?"
    ↓
OpenAI GPT-4o receives question + ALL available functions
    ↓
AI determines: This is a real NFL stats question
    ↓
AI calls: get_player_game_stats(player_name="AJ Brown")
    ↓
Function calls Ball Don't Lie MCP
    ↓
Returns: { touchdowns: 2, yards: 119, ... }
    ↓
AI formats natural response: "AJ Brown had 2 touchdowns and 119 receiving yards in his last game."
```

### Dual Data Source Logic

The AI automatically chooses based on question intent:

| Question Type | Data Source | Functions Used |
|---------------|-------------|----------------|
| "Who owns Mahomes?" | Supabase | `find_player_by_name()`, check rosters |
| "Mahomes' last game stats?" | Ball Don't Lie | `get_player_game_stats()` |
| "Show standings" | Supabase | `query_with_filters()` |
| "Compare AJ Brown vs Tyreek" | Ball Don't Lie | `compare_players()` |
| "Recent trades" | Supabase | `get_recent_trades()` |
| "Did Eagles score 30 points?" | Ball Don't Lie | `get_team_game_stats()` |

---

## 📊 Available External Functions

### 1. `get_player_game_stats(player_name, game_date=None)`
Get stats from a specific game or most recent game.

**Use cases:**
- "How many TDs did [player] have last game?"
- "What were [player]'s stats last week?"

### 2. `get_player_season_stats(player_name, season=None)`
Get cumulative season statistics.

**Use cases:**
- "How many yards does [player] have this season?"
- "Show me [player]'s 2024 stats"

### 3. `get_team_game_stats(team_abbreviation, week=None)`
Get NFL team statistics.

**Use cases:**
- "How did the Eagles do last week?"
- "Chiefs stats in week 7?"

### 4. `compare_players(player_name_1, player_name_2, stat_type)`
Compare two players' real NFL stats.

**Use cases:**
- "Who has more TDs, AJ Brown or Tyreek Hill?"
- "Compare Mahomes and Allen"

---

## 🔍 Adding More MCP Functions

To add more external data sources (weather, betting lines, etc.):

1. **Add function to `external_stats.py`:**
```python
def get_game_weather(team_name: str, week: int) -> Dict[str, Any]:
    """Get weather conditions for a game"""
    # Your implementation
    pass
```

2. **Add function definition:**
```python
EXTERNAL_FUNCTION_DEFINITIONS.append({
    "name": "get_game_weather",
    "description": "Get weather conditions for an NFL game...",
    "parameters": {
        "type": "object",
        "properties": {
            "team_name": {"type": "string"},
            "week": {"type": "integer"}
        },
        "required": ["team_name", "week"]
    }
})
```

3. **Add to function map:**
```python
EXTERNAL_FUNCTION_MAP["get_game_weather"] = get_game_weather
```

That's it! The AI will automatically have access to it.

---

## 🚀 Deployment Notes

### Environment Variables

If your MCP needs API keys, add them to `config.py`:

```python
# Ball Don't Lie MCP
BALL_DONT_LIE_API_KEY = os.getenv('BALL_DONT_LIE_API_KEY', 'your-key-here')
```

Then import in `external_stats.py`:

```python
from config import BALL_DONT_LIE_API_KEY
```

### Rate Limiting

Consider adding rate limiting for external API calls:

```python
import time
from functools import wraps

last_call_time = {}

def rate_limit(calls_per_minute=60):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            if func.__name__ in last_call_time:
                elapsed = now - last_call_time[func.__name__]
                min_interval = 60.0 / calls_per_minute
                if elapsed < min_interval:
                    time.sleep(min_interval - elapsed)
            
            result = func(*args, **kwargs)
            last_call_time[func.__name__] = time.time()
            return result
        return wrapper
    return decorator

@rate_limit(calls_per_minute=30)
def get_player_game_stats(player_name: str, game_date: str = None):
    # ... your implementation
```

### Caching

For better performance, consider caching MCP responses:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_player_game_stats_cached(player_name: str, game_date: str = None):
    return get_player_game_stats(player_name, game_date)
```

---

## 📝 Example Conversations

### Mixed Questions (Both Data Sources)

**User:** "Who owns AJ Brown and how many TDs did he have last game?"

**AI Actions:**
1. Calls `find_player_by_name("AJ Brown")` → Supabase
2. Checks rosters to find owner → Supabase
3. Calls `get_player_game_stats("AJ Brown")` → Ball Don't Lie
4. Combines responses

**Response:** "AJ Brown is owned by Team X (nickroachy). In his last game against the Cowboys, he had 2 touchdowns and 119 receiving yards."

---

## 🎉 Benefits

✅ **Single Interface** - Users ask natural questions, AI routes to right data source  
✅ **No Breaking Changes** - All existing Supabase queries still work  
✅ **Extensible** - Easy to add more external APIs/MCPs  
✅ **Intelligent Routing** - GPT-4o chooses the right data source automatically  
✅ **Real-Time Data** - Get actual NFL stats alongside fantasy league data  

---

## 🐛 Troubleshooting

### "MCP integration pending" in responses
- You need to implement the actual MCP client calls in `external_stats.py`

### AI uses wrong data source
- Update the system prompt in `fantasy_assistant.py` with clearer examples
- Add more descriptive function descriptions

### Import errors
- Make sure `external_stats.py` is in the same directory as `fantasy_assistant.py`
- Check that all dependencies are installed

### MCP connection errors
- Verify your MCP client initialization
- Check API keys and credentials
- Review MCP documentation for correct method names

---

## 📚 Next Steps

1. ✅ Implement MCP client in `get_mcp_client()`
2. ✅ Update each function to call actual MCP
3. ✅ Test with various questions
4. ✅ Deploy and enjoy!

**Need help?** Check your Ball Don't Lie MCP documentation for:
- Client initialization method
- API endpoint names
- Response format
- Authentication requirements

---

**Your AI assistant is now ready to answer both fantasy league AND real NFL stats questions! 🏈**

