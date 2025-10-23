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


def call_mcp_endpoint(endpoint_name: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Generic function to call ANY Ball Don't Lie MCP endpoint directly.
    
    This gives you access to ALL NFL data endpoints without needing specific wrapper functions.
    
    Available endpoints include:
    
    NFL TEAMS:
    - nfl_get_teams: Get all NFL teams (filter by conference, division)
    - nfl_get_team_by_id: Get specific team details
    
    NFL PLAYERS:
    - nfl_get_players: Search players (by name, position, team)
    - nfl_get_player_by_id: Get specific player details
    - nfl_get_active_players: Get only active players
    
    NFL GAMES:
    - nfl_get_games: Get games (filter by date, season, week, team)
    - nfl_get_game_by_id: Get specific game details
    
    NFL STATS:
    - nfl_get_stats: Get player game stats (filter by player, game, date, season, week)
    - nfl_get_season_stats: Get player season totals
    - nfl_get_advanced_rushing_stats: Advanced rushing analytics
    - nfl_get_advanced_passing_stats: Advanced passing analytics
    - nfl_get_advanced_receiving_stats: Advanced receiving analytics
    
    NFL STANDINGS:
    - nfl_get_standings: Get team standings (filter by season, conference, division)
    
    NFL LEADERS & INJURIES:
    - nfl_get_leaders: Get statistical leaders (by season, stat_type like 'pts', 'reb', etc.)
    - nfl_get_player_injuries: Get injury reports (filter by player, team)
    
    Args:
        endpoint_name: Name of the MCP endpoint to call (e.g., 'nfl_get_standings')
        parameters: Dictionary of parameters to pass to the endpoint
        
    Returns:
        Raw response from the MCP endpoint
        
    Examples:
        # Get standings
        call_mcp_endpoint("nfl_get_standings", {"season": 2025})
        
        # Search for a player
        call_mcp_endpoint("nfl_get_players", {"search": "Mahomes", "per_page": 5})
        
        # Get injury reports
        call_mcp_endpoint("nfl_get_player_injuries", {})
    """
    try:
        if parameters is None:
            parameters = {}
        
        logger.info(f"Calling MCP endpoint: {endpoint_name} with params: {parameters}")
        
        result = call_mcp_tool(endpoint_name, parameters)
        
        if 'error' in result:
            return result
        
        if not result.get('content'):
            return {'error': 'No data returned from endpoint'}
        
        # Parse and return the data
        data = json.loads(result['content'][0]['text'])
        return data
        
    except Exception as e:
        logger.error(f"Error calling MCP endpoint {endpoint_name}: {e}", exc_info=True)
        return {'error': str(e)}


def get_nfl_standings(season: int = None, conference: str = None, division: str = None) -> Dict[str, Any]:
    """
    Get current NFL team standings.
    Use this to answer questions like:
    - "What are the NFL standings?"
    - "Show me the AFC East standings"
    - "Who is leading the NFC?"
    
    Args:
        season: Season year (defaults to current season)
        conference: Filter by conference - "AFC" or "NFC"
        division: Filter by division - "NORTH", "SOUTH", "EAST", "WEST"
        
    Returns:
        NFL team standings with wins, losses, and rankings
    """
    try:
        if season is None:
            season = get_current_nfl_season()
        
        logger.info(f"Getting NFL standings for season {season}, conference: {conference or 'all'}, division: {division or 'all'}")
        
        params = {"season": season}
        if conference:
            params["conference"] = conference.upper()
        if division:
            params["division"] = division.upper()
        
        standings_result = call_mcp_tool("nfl_get_standings", params)
        
        if 'error' in standings_result:
            return standings_result
        
        if not standings_result.get('content'):
            return {'error': 'No standings data found'}
        
        standings_data = json.loads(standings_result['content'][0]['text'])
        
        if not standings_data.get('data'):
            return {'error': 'No standings available'}
        
        # Format the standings data
        teams = standings_data['data']
        
        # Group by conference and division
        standings = {
            'AFC': {'EAST': [], 'NORTH': [], 'SOUTH': [], 'WEST': []},
            'NFC': {'EAST': [], 'NORTH': [], 'SOUTH': [], 'WEST': []}
        }
        
        for team_data in teams:
            team_info = team_data.get('team', {})
            conf = team_info.get('conference')
            div = team_info.get('division')
            
            if conf and div:
                # Calculate win percentage
                wins = team_data.get('wins', 0)
                losses = team_data.get('losses', 0)
                ties = team_data.get('ties', 0)
                total_games = wins + losses + ties
                win_pct = wins / total_games if total_games > 0 else 0
                
                standings[conf][div].append({
                    'team': team_info.get('full_name'),
                    'abbreviation': team_info.get('abbreviation'),
                    'wins': wins,
                    'losses': losses,
                    'ties': ties,
                    'win_percentage': win_pct,
                    'overall_record': team_data.get('overall_record', ''),
                    'conference_record': team_data.get('conference_record', ''),
                    'division_record': team_data.get('division_record', ''),
                    'points_for': team_data.get('points_for', 0),
                    'points_against': team_data.get('points_against', 0),
                    'point_differential': team_data.get('point_differential', 0),
                    'playoff_seed': team_data.get('playoff_seed', 0),
                    'win_streak': team_data.get('win_streak', 0)
                })
        
        # Sort each division by win percentage (then by wins if tied)
        for conf in standings:
            for div in standings[conf]:
                standings[conf][div].sort(key=lambda x: (x['win_percentage'], x['wins']), reverse=True)
        
        return {
            'season': season,
            'standings': standings
        }
        
    except Exception as e:
        logger.error(f"Error getting NFL standings: {e}", exc_info=True)
        return {'error': str(e)}


def get_top_performers(position: str = None, stat_category: str = "passing_yards", limit: int = 10, season: int = None) -> Dict[str, Any]:
    """
    Get top performing NFL players by stat category for current season.
    Use this to answer questions like:
    - "Who are the top 10 performing QBs?"
    - "Show me the best running backs this season"
    - "Top 5 receivers by yards"
    
    Args:
        position: Position filter (e.g., "QB", "RB", "WR", "TE"). Leave empty for all positions.
        stat_category: Stat to rank by - options:
            - "passing_yards", "passing_touchdowns" (QBs)
            - "rushing_yards", "rushing_touchdowns" (RBs)
            - "receiving_yards", "receiving_touchdowns", "receptions" (WR/TE)
        limit: Number of players to return (default 10)
        season: Season year (defaults to current season)
        
    Returns:
        List of top performers with their stats
    """
    try:
        if season is None:
            season = get_current_nfl_season()
        
        logger.info(f"Getting top {limit} performers by {stat_category}, position: {position or 'all'}, season: {season}")
        
        # Get all active players with optional position filter
        params = {"per_page": 100}
        if position:
            params["position"] = position.upper()
        
        players_result = call_mcp_tool("nfl_get_players", params)
        
        if 'error' in players_result:
            return players_result
        
        if not players_result.get('content'):
            return {'error': 'No players found'}
        
        players_data = json.loads(players_result['content'][0]['text'])
        
        if not players_data.get('data'):
            return {'error': 'No players found'}
        
        # Get season stats for these players
        player_ids = [p['id'] for p in players_data['data'][:50]]  # Limit to first 50 to avoid too many requests
        
        stats_result = call_mcp_tool("nfl_get_season_stats", {
            "player_ids": player_ids,
            "season": season,
            "per_page": 100
        })
        
        if 'error' in stats_result:
            return stats_result
        
        if not stats_result.get('content'):
            return {'error': 'No stats found'}
        
        stats_data = json.loads(stats_result['content'][0]['text'])
        
        if not stats_data.get('data'):
            return {'error': 'No season stats available'}
        
        # Map stat_category to actual field names
        stat_field_map = {
            'passing_yards': 'passing_yards',
            'passing_touchdowns': 'passing_touchdowns',
            'passing_tds': 'passing_touchdowns',
            'rushing_yards': 'rushing_yards',
            'rushing_touchdowns': 'rushing_touchdowns',
            'rushing_tds': 'rushing_touchdowns',
            'receiving_yards': 'receiving_yards',
            'receiving_touchdowns': 'receiving_touchdowns',
            'receiving_tds': 'receiving_touchdowns',
            'receptions': 'receptions'
        }
        
        field_name = stat_field_map.get(stat_category.lower(), stat_category)
        
        # Sort by the requested stat
        sorted_players = sorted(
            stats_data['data'],
            key=lambda x: x.get(field_name, 0) or 0,
            reverse=True
        )[:limit]
        
        # Format the results
        results = []
        for rank, player_stat in enumerate(sorted_players, 1):
            player_info = player_stat.get('player', {})
            results.append({
                'rank': rank,
                'player_name': f"{player_info.get('first_name', '')} {player_info.get('last_name', '')}".strip(),
                'position': player_info.get('position_abbreviation', ''),
                'team': player_stat.get('team', {}).get('abbreviation', ''),
                'games_played': player_stat.get('games_played', 0),
                'stat_value': player_stat.get(field_name, 0) or 0,
                'stat_category': stat_category,
                'additional_stats': {
                    'passing_yards': player_stat.get('passing_yards', 0) or 0,
                    'passing_tds': player_stat.get('passing_touchdowns', 0) or 0,
                    'rushing_yards': player_stat.get('rushing_yards', 0) or 0,
                    'rushing_tds': player_stat.get('rushing_touchdowns', 0) or 0,
                    'receiving_yards': player_stat.get('receiving_yards', 0) or 0,
                    'receiving_tds': player_stat.get('receiving_touchdowns', 0) or 0,
                    'receptions': player_stat.get('receptions', 0) or 0
                }
            })
        
        return {
            'season': season,
            'position': position or 'All',
            'stat_category': stat_category,
            'top_performers': results
        }
        
    except Exception as e:
        logger.error(f"Error getting top performers: {e}", exc_info=True)
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
        "name": "call_mcp_endpoint",
        "description": """🚀 UNIVERSAL NFL DATA ACCESS - Call ANY Ball Don't Lie MCP endpoint directly.
        
        USE THIS for flexible queries and data that doesn't have a specific wrapper function.
        This gives you access to ALL NFL endpoints including standings, injuries, games, etc.
        
        AVAILABLE ENDPOINTS:
        
        📊 STANDINGS & TEAMS:
        • nfl_get_standings - Team standings (params: season, conference, division)
        • nfl_get_teams - All NFL teams (params: conference, division)
        • nfl_get_team_by_id - Specific team (params: id)
        
        🏈 PLAYERS:
        • nfl_get_players - Search players (params: search, position, team_ids, per_page)
        • nfl_get_player_by_id - Specific player (params: id)
        • nfl_get_active_players - Only active players (params: search, position)
        
        📅 GAMES:
        • nfl_get_games - Get games (params: dates, seasons, weeks, team_ids, postseason)
        • nfl_get_game_by_id - Specific game (params: id)
        
        📈 STATS:
        • nfl_get_stats - Player game stats (params: player_ids, game_ids, dates, seasons, weeks)
        • nfl_get_season_stats - Season totals (params: player_ids, season, postseason)
        • nfl_get_advanced_rushing_stats - Advanced rushing (params: season, week, player_id)
        • nfl_get_advanced_passing_stats - Advanced passing (params: season, week, player_id)
        • nfl_get_advanced_receiving_stats - Advanced receiving (params: season, week, player_id)
        
        🏆 LEADERS & INJURIES:
        • nfl_get_leaders - Statistical leaders (params: season, stat_type, cursor, per_page)
        • nfl_get_player_injuries - Injury reports (params: player_ids, team_ids, cursor, per_page)
        
        EXAMPLES:
        • Standings: call_mcp_endpoint("nfl_get_standings", {"season": 2025})
        • Injuries: call_mcp_endpoint("nfl_get_player_injuries", {})
        • Leaders: call_mcp_endpoint("nfl_get_leaders", {"season": 2025, "stat_type": "pts"})
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "endpoint_name": {
                    "type": "string",
                    "description": "Name of the MCP endpoint to call (e.g., 'nfl_get_standings', 'nfl_get_player_injuries')"
                },
                "parameters": {
                    "type": "object",
                    "description": "Parameters to pass to the endpoint as a JSON object. Examples: {'season': 2025}, {'search': 'Mahomes'}, {'team_ids': [14]}"
                }
            },
            "required": ["endpoint_name"]
        }
    },
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
    },
    {
        "name": "get_nfl_standings",
        "description": """Get current NFL team standings and rankings.
        
        USE THIS when user asks questions like:
        - "What are the NFL standings?"
        - "Show me the AFC East standings"
        - "Who is leading the NFC?"
        - "What's the current NFL playoff picture?"
        - "How are the Chiefs doing this season?"
        
        Returns complete standings with W-L records, rankings, and stats.
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "season": {
                    "type": "integer",
                    "description": "Optional: Season year. Automatically detects current season if not provided."
                },
                "conference": {
                    "type": "string",
                    "description": "Optional: Filter by conference - 'AFC' or 'NFC'"
                },
                "division": {
                    "type": "string",
                    "description": "Optional: Filter by division - 'EAST', 'WEST', 'NORTH', 'SOUTH'"
                }
            },
            "required": []
        }
    },
    {
        "name": "get_top_performers",
        "description": """Get top performing NFL players by stat category for current season.
        
        USE THIS when user asks questions like:
        - "Who are the top 10 performing QBs?"
        - "Show me the best running backs this season"
        - "Top 5 receivers by yards"
        - "Who are the leading passers?"
        - "Best fantasy RBs this year"
        
        Returns ranked list of players with their statistics.
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "position": {
                    "type": "string",
                    "description": "Position filter: 'QB', 'RB', 'WR', 'TE'. Leave empty for all positions."
                },
                "stat_category": {
                    "type": "string",
                    "description": "Stat to rank by: 'passing_yards', 'passing_touchdowns', 'rushing_yards', 'rushing_touchdowns', 'receiving_yards', 'receiving_touchdowns', 'receptions'. Default: 'passing_yards'"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of players to return (default 10, max 25)"
                },
                "season": {
                    "type": "integer",
                    "description": "Optional: Season year. Automatically detects current season if not provided."
                }
            },
            "required": []
        }
    }
]

# Map function names to actual functions
EXTERNAL_FUNCTION_MAP = {
    "call_mcp_endpoint": call_mcp_endpoint,
    "get_player_game_stats": get_player_game_stats,
    "get_player_season_stats": get_player_season_stats,
    "get_team_game_stats": get_team_game_stats,
    "compare_players": compare_players,
    "get_nfl_standings": get_nfl_standings,
    "get_top_performers": get_top_performers
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
