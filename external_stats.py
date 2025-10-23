"""
External NFL Statistics Functions using Ball Don't Lie MCP
Integrates real-time NFL player statistics into the fantasy assistant
"""

from logger_config import setup_logger
from typing import List, Dict, Any
import requests
import json
import re
from datetime import datetime

logger = setup_logger('external_stats')

# Ball Don't Lie MCP Configuration
BALL_DONT_LIE_MCP_URL = "https://mcp.balldontlie.io/mcp"
BALL_DONT_LIE_API_KEY = "f42bb8d2-2bf8-4714-842d-601a45628168"

# MCP client will be initialized when first used
_mcp_session = None


def get_current_nfl_season() -> int:
    """
    Determine the current NFL season based on the current date.
    NFL seasons run from September to February, so:
    - September-December: current year's season
    - January-August: previous year's season
    """
    now = datetime.now()
    if now.month >= 9:  # September or later
        return now.year
    else:  # January-August
        return now.year - 1


def get_current_date() -> str:
    """Get the current date in ISO format"""
    return datetime.now().date().isoformat()


def get_mcp_client():
    """Get or create HTTP session for Ball Don't Lie MCP API"""
    global _mcp_session
    if _mcp_session is None:
        _mcp_session = requests.Session()
        _mcp_session.headers.update({
            'Authorization': BALL_DONT_LIE_API_KEY,
            'Content-Type': 'application/json'
        })
    return _mcp_session


def call_mcp_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call a Ball Don't Lie MCP tool
    
    Args:
        tool_name: Name of the MCP tool to call
        arguments: Arguments to pass to the tool
        
    Returns:
        Tool response data
    """
    try:
        session = get_mcp_client()
        
        # MCP protocol request format
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        response = session.post(BALL_DONT_LIE_MCP_URL, json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        if 'error' in result:
            logger.error(f"MCP error: {result['error']}")
            return {'error': result['error'].get('message', 'Unknown MCP error')}
        
        return result.get('result', {})
        
    except requests.exceptions.RequestException as e:
        logger.error(f"MCP request failed: {e}")
        return {'error': f'MCP request failed: {str(e)}'}
    except Exception as e:
        logger.error(f"Unexpected error calling MCP: {e}", exc_info=True)
        return {'error': str(e)}


def get_player_game_stats(player_name: str, game_date: str = None, season: int = None) -> Dict[str, Any]:
    """
    Get NFL player statistics for a specific game or most recent game.
    Use this to answer questions like:
    - "How many TDs did AJ Brown have last game?"
    - "What did Travis Kelce score last week?"
    - "Did Mahomes throw for 300 yards?"
    
    Args:
        player_name: Player name to look up (e.g., "AJ Brown", "Patrick Mahomes")
        game_date: Optional date in YYYY-MM-DD format. If not provided, gets most recent game.
        season: Optional season year. If not provided, uses current NFL season.
        
    Returns:
        Dictionary with player stats from the specified game
    """
    try:
        if season is None:
            season = get_current_nfl_season()
        
        logger.info(f"Getting game stats for {player_name}, season: {season}, date: {game_date or 'most recent'}")
        
        # Step 1: Search for the player to get their ID
        # Try multiple name formats (e.g., "AJ Brown" vs "A.J. Brown")
        search_variations = [player_name]
        formatted_name = None
        
        # If name has capital letters without periods, try adding periods (AJ → A.J.)
        if re.match(r'^[A-Z]{2}\s', player_name):
            # Add periods: "AJ Brown" → "A.J. Brown"
            formatted_name = '.'.join(player_name[0:2]) + '.' + player_name[2:]
            search_variations.append(formatted_name)
        
        # Also try just the last name
        last_name = player_name.split()[-1]
        if last_name != player_name:
            search_variations.append(last_name)
        
        player_data = None
        for search_term in search_variations:
            logger.info(f"Trying search term: {search_term}")
            player_search = call_mcp_tool("nfl_get_players", {"search": search_term, "per_page": 10})
            
            if 'error' in player_search:
                continue
            
            if not player_search.get('content') or len(player_search['content']) == 0:
                continue
            
            # Parse the MCP response
            temp_data = json.loads(player_search['content'][0]['text'])
            
            if temp_data.get('data') and len(temp_data['data']) > 0:
                # If we searched by full name, take first result
                if search_term == player_name or (formatted_name and search_term == formatted_name):
                    player_data = temp_data
                    break
                # If we searched by last name, find best match
                else:
                    # Look for a player matching the original name
                    # Normalize by removing periods and comparing
                    normalized_search = player_name.replace('.', '').replace(' ', '').lower()
                    for p in temp_data['data']:
                        first = p.get('first_name', '')
                        last = p.get('last_name', '')
                        full = f"{first} {last}".strip()
                        normalized_player = full.replace('.', '').replace(' ', '').lower()
                        
                        # Check if normalized names match
                        if normalized_search in normalized_player or normalized_player in normalized_search:
                            player_data = {'data': [p]}
                            logger.info(f"Matched '{player_name}' to '{full}'")
                            break
                    if player_data:
                        break
        
        if not player_data or not player_data.get('data') or len(player_data['data']) == 0:
            return {'error': f'Player not found: {player_name}. Try using last name only or full name with proper formatting.'}
        
        player = player_data['data'][0]
        player_id = player['id']
        player_full_name = f"{player.get('first_name', '')} {player.get('last_name', '')}".strip()
        
        logger.info(f"Found player: {player_full_name} (ID: {player_id})")
        
        # Step 2: Get player stats
        stats_params = {
            "player_ids": [player_id],
            "seasons": [season],  # Get current season data
            "per_page": 10  # Get recent games
        }
        
        if game_date:
            stats_params["dates"] = [game_date]
        
        stats_result = call_mcp_tool("nfl_get_stats", stats_params)
        
        if 'error' in stats_result:
            return stats_result
        
        if not stats_result.get('content'):
            return {'error': 'No stats found'}
        
        stats_data = json.loads(stats_result['content'][0]['text'])
        
        if not stats_data.get('data') or len(stats_data['data']) == 0:
            return {
                'player_name': player_full_name,
                'message': f'No game stats found for {player_full_name}' + (f' on {game_date}' if game_date else ' in recent games')
            }
        
        # Get the most recent game stats (sort by date descending to get newest first)
        games = stats_data['data']
        # Sort by game date (most recent first)
        try:
            games_sorted = sorted(games, key=lambda x: x.get('game', {}).get('date', ''), reverse=True)
            game_stats = games_sorted[0]
        except:
            # If sorting fails, just use first result
            game_stats = stats_data['data'][0]
        
        # Extract relevant stats
        # Determine opponent team
        game_info = game_stats.get('game', {})
        home_team = game_info.get('home_team', {}).get('abbreviation', '')
        visitor_team = game_info.get('visitor_team', {}).get('abbreviation', '')
        player_team = game_stats.get('team', {}).get('abbreviation', '')
        opponent = visitor_team if player_team == home_team else home_team
        
        return {
            'player_name': player_full_name,
            'game_date': game_info.get('date'),
            'week': game_info.get('week'),
            'opponent': opponent or 'N/A',
            'stats': {
                'passing_yards': game_stats.get('passing_yards', 0) or 0,
                'passing_tds': game_stats.get('passing_touchdowns', 0) or 0,
                'rushing_yards': game_stats.get('rushing_yards', 0) or 0,
                'rushing_tds': game_stats.get('rushing_touchdowns', 0) or 0,
                'receiving_yards': game_stats.get('receiving_yards', 0) or 0,
                'receiving_tds': game_stats.get('receiving_touchdowns', 0) or 0,
                'receptions': game_stats.get('receptions', 0) or 0,
                'targets': game_stats.get('receiving_targets', 0) or 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting player game stats: {e}", exc_info=True)
        return {'error': str(e)}


def get_player_season_stats(player_name: str, season: int = None) -> Dict[str, Any]:
    """
    Get NFL player statistics for an entire season.
    Use this to answer questions like:
    - "How many yards does AJ Brown have this season?"
    - "What are Patrick Mahomes' season stats?"
    - "Show me Travis Kelce's 2024 stats"
    
    Args:
        player_name: Player name to look up
        season: Season year (e.g., 2024, 2025). If not provided, uses current NFL season.
        
    Returns:
        Dictionary with cumulative season statistics
    """
    try:
        # Default to current NFL season
        if season is None:
            season = get_current_nfl_season()
        
        logger.info(f"Getting season stats for {player_name}, season: {season}")
        
        # Step 1: Search for the player (using same smart search as game stats)
        search_variations = [player_name]
        formatted_name = None
        
        if re.match(r'^[A-Z]{2}\s', player_name):
            formatted_name = '.'.join(player_name[0:2]) + '.' + player_name[2:]
            search_variations.append(formatted_name)
        
        last_name = player_name.split()[-1]
        if last_name != player_name:
            search_variations.append(last_name)
        
        player_data = None
        for search_term in search_variations:
            player_search = call_mcp_tool("nfl_get_players", {"search": search_term, "per_page": 10})
            
            if 'error' in player_search:
                continue
            
            if not player_search.get('content') or len(player_search['content']) == 0:
                continue
            
            temp_data = json.loads(player_search['content'][0]['text'])
            
            if temp_data.get('data') and len(temp_data['data']) > 0:
                if search_term == player_name or (formatted_name and search_term == formatted_name):
                    player_data = temp_data
                    break
                else:
                    normalized_search = player_name.replace('.', '').replace(' ', '').lower()
                    for p in temp_data['data']:
                        first = p.get('first_name', '')
                        last = p.get('last_name', '')
                        full = f"{first} {last}".strip()
                        normalized_player = full.replace('.', '').replace(' ', '').lower()
                        
                        if normalized_search in normalized_player or normalized_player in normalized_search:
                            player_data = {'data': [p]}
                            break
                    if player_data:
                        break
        
        if not player_data or not player_data.get('data') or len(player_data['data']) == 0:
            return {'error': f'Player not found: {player_name}'}
        
        player = player_data['data'][0]
        player_id = player['id']
        player_full_name = f"{player.get('first_name', '')} {player.get('last_name', '')}".strip()
        
        # Step 2: Get player season stats
        stats_result = call_mcp_tool("nfl_get_season_stats", {
            "player_ids": [player_id],
            "season": season
        })
        
        if 'error' in stats_result:
            return stats_result
        
        if not stats_result.get('content'):
            return {'error': 'No season stats found'}
        
        stats_data = json.loads(stats_result['content'][0]['text'])
        
        if not stats_data.get('data') or len(stats_data['data']) == 0:
            return {
                'player_name': player_full_name,
                'season': season,
                'message': f'No season stats found for {player_full_name} in {season}'
            }
        
        season_stats = stats_data['data'][0]
        
        # Calculate total touchdowns
        total_tds = ((season_stats.get('passing_touchdowns', 0) or 0) + 
                     (season_stats.get('rushing_touchdowns', 0) or 0) + 
                     (season_stats.get('receiving_touchdowns', 0) or 0))
        
        # Calculate total yards
        total_yards = ((season_stats.get('passing_yards', 0) or 0) + 
                       (season_stats.get('rushing_yards', 0) or 0) + 
                       (season_stats.get('receiving_yards', 0) or 0))
        
        games_played = season_stats.get('games_played', 0) or 0
        yards_per_game = total_yards / games_played if games_played > 0 else 0
        
        return {
            'player_name': player_full_name,
            'season': season,
            'games_played': games_played,
            'stats': {
                'passing_yards': season_stats.get('passing_yards', 0) or 0,
                'passing_tds': season_stats.get('passing_touchdowns', 0) or 0,
                'rushing_yards': season_stats.get('rushing_yards', 0) or 0,
                'rushing_tds': season_stats.get('rushing_touchdowns', 0) or 0,
                'receiving_yards': season_stats.get('receiving_yards', 0) or 0,
                'receiving_tds': season_stats.get('receiving_touchdowns', 0) or 0,
                'receptions': season_stats.get('receptions', 0) or 0,
                'total_touchdowns': total_tds,
                'total_yards': total_yards,
                'yards_per_game': round(yards_per_game, 1)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting player season stats: {e}", exc_info=True)
        return {'error': str(e)}


def get_team_game_stats(team_abbreviation: str, week: int = None) -> Dict[str, Any]:
    """
    Get NFL team statistics for a specific week/game.
    Use this to answer questions like:
    - "How did the Eagles do last week?"
    - "What were the Chiefs' stats in week 7?"
    
    Args:
        team_abbreviation: NFL team abbreviation (e.g., "PHI", "KC", "SF")
        week: Week number. If not provided, gets most recent game.
        
    Returns:
        Dictionary with team statistics
    """
    try:
        logger.info(f"Getting team stats for {team_abbreviation}, week: {week or 'most recent'}")
        
        # TODO: Implement team stats when needed
        return {
            'team': team_abbreviation,
            'week': week or 'most_recent',
            'message': 'Team stats not yet implemented. Focus is on player stats currently.'
        }
        
    except Exception as e:
        logger.error(f"Error getting team stats: {e}", exc_info=True)
        return {'error': str(e)}


def compare_players(player_name_1: str, player_name_2: str, stat_type: str = "season") -> Dict[str, Any]:
    """
    Compare statistics between two NFL players.
    Use this to answer questions like:
    - "Who has more TDs, AJ Brown or Tyreek Hill?"
    - "Compare Patrick Mahomes and Josh Allen"
    
    Args:
        player_name_1: First player name
        player_name_2: Second player name
        stat_type: "season" for season totals, "game" for most recent game
        
    Returns:
        Dictionary comparing both players' statistics
    """
    try:
        logger.info(f"Comparing {player_name_1} vs {player_name_2} ({stat_type})")
        
        if stat_type == "season":
            player1_stats = get_player_season_stats(player_name_1)
            player2_stats = get_player_season_stats(player_name_2)
        else:
            player1_stats = get_player_game_stats(player_name_1)
            player2_stats = get_player_game_stats(player_name_2)
        
        return {
            'player_1': player1_stats,
            'player_2': player2_stats,
            'comparison_type': stat_type
        }
        
    except Exception as e:
        logger.error(f"Error comparing players: {e}", exc_info=True)
        return {'error': str(e)}


# Function definitions for OpenAI Assistant
EXTERNAL_FUNCTION_DEFINITIONS = [
    {
        "name": "get_player_game_stats",
        "description": """Get real-time NFL player statistics for a specific game using Ball Don't Lie API.
        
        USE THIS when user asks questions like:
        - "How many TDs did AJ Brown have last game?"
        - "What did Travis Kelce score last week?"
        - "Did Mahomes throw for 300 yards?"
        - "How many yards did [player] get in their last game?"
        
        This provides ACTUAL NFL game statistics, not fantasy league data.
        Use this for real-world performance questions, not fantasy roster questions.
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "player_name": {
                    "type": "string",
                    "description": "NFL player name (e.g., 'AJ Brown', 'Patrick Mahomes', 'Travis Kelce')"
                },
                "game_date": {
                    "type": "string",
                    "description": "Optional: Specific game date in YYYY-MM-DD format. Leave empty for most recent game."
                },
                "season": {
                    "type": "integer",
                    "description": "Optional: NFL season year (e.g., 2024, 2025). Automatically detects current season if not provided."
                }
            },
            "required": ["player_name"]
        }
    },
    {
        "name": "get_player_season_stats",
        "description": """Get cumulative NFL player statistics for an entire season.
        
        USE THIS when user asks questions like:
        - "How many yards does AJ Brown have this season?"
        - "What are Patrick Mahomes' season stats?"
        - "Show me Travis Kelce's 2024 stats"
        - "Who has more season TDs?"
        
        Provides season-long totals and averages from the Ball Don't Lie API.
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "player_name": {
                    "type": "string",
                    "description": "NFL player name"
                },
                "season": {
                    "type": "integer",
                    "description": "Optional: Season year (e.g., 2024, 2025). Automatically detects current season if not provided."
                }
            },
            "required": ["player_name"]
        }
    },
    {
        "name": "get_team_game_stats",
        "description": """Get NFL team statistics for a specific week/game.
        
        USE THIS when user asks questions like:
        - "How did the Eagles do last week?"
        - "What were the Chiefs' stats in week 7?"
        - "Did the 49ers score 30 points?"
        
        Provides real NFL team performance data.
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "team_abbreviation": {
                    "type": "string",
                    "description": "NFL team abbreviation (e.g., 'PHI', 'KC', 'SF', 'DAL')"
                },
                "week": {
                    "type": "integer",
                    "description": "Week number. Leave empty for most recent game."
                }
            },
            "required": ["team_abbreviation"]
        }
    },
    {
        "name": "compare_players",
        "description": """Compare real NFL statistics between two players.
        
        USE THIS when user asks questions like:
        - "Who has more TDs, AJ Brown or Tyreek Hill?"
        - "Compare Patrick Mahomes and Josh Allen"
        - "AJ Brown vs CeeDee Lamb stats"
        
        Returns side-by-side comparison of player statistics.
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "player_name_1": {
                    "type": "string",
                    "description": "First player name"
                },
                "player_name_2": {
                    "type": "string",
                    "description": "Second player name"
                },
                "stat_type": {
                    "type": "string",
                    "description": "'season' for season totals or 'game' for most recent game",
                    "enum": ["season", "game"]
                }
            },
            "required": ["player_name_1", "player_name_2"]
        }
    }
]

# Map function names to actual functions
EXTERNAL_FUNCTION_MAP = {
    "get_player_game_stats": get_player_game_stats,
    "get_player_season_stats": get_player_season_stats,
    "get_team_game_stats": get_team_game_stats,
    "compare_players": compare_players
}


if __name__ == "__main__":
    # Test the functions
    print("\n" + "="*70)
    print("🧪 Testing External Stats Functions")
    print("="*70)
    
    print("\n📊 Test: Get Player Game Stats")
    result = get_player_game_stats("AJ Brown")
    print(f"  Result: {result}")
    
    print("\n✅ Test complete!")
