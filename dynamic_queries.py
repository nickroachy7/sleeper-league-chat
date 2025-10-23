"""
Dynamic SQL Query Functions for OpenAI Assistant
Allows the AI to execute SQL queries directly against Supabase
"""

from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SLEEPER_LEAGUE_ID
from supabase import create_client, Client
from typing import List, Dict, Any
from logger_config import setup_logger
import json

logger = setup_logger('dynamic_queries')

# Lazy initialization of Supabase client
_supabase_client: Client = None


def get_supabase_client() -> Client:
    """Get or create Supabase client (lazy initialization)"""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    return _supabase_client


def execute_sql_query(query: str) -> List[Dict[str, Any]]:
    """
    Execute a raw SQL query against the Supabase database using PostgREST.
    
    This allows the AI to dynamically query the database without predefined functions.
    Only SELECT queries are supported for safety.
    
    Args:
        query: SQL query to execute (SELECT only)
        
    Returns:
        List of rows returned by the query
    """
    supabase = get_supabase_client()
    
    try:
        logger.info(f"Executing SQL query: {query[:200]}...")
        
        # Use the postgrest-py client to execute raw SQL
        # This works by calling the PostgREST RPC endpoint
        result = supabase.postgrest.rpc('exec_sql', {'sql': query}).execute()
        
        logger.info(f"Query returned {len(result.data) if result.data else 0} rows")
        return result.data if result.data else []
    
    except Exception as e:
        error_msg = f"Error executing SQL query: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Full query: {query}")
        return [{"error": error_msg, "query": query, "note": "You may need to use query_builder or direct table methods instead"}]


def list_tables() -> List[Dict[str, str]]:
    """
    List all tables in the public schema
    
    Returns:
        List of table names with descriptions
    """
    # Return known tables since we're working with a fantasy football database
    # This is more reliable than querying information_schema
    logger.info("Returning list of known tables")
    return [
        {"table_name": "leagues", "description": "League information including settings and current season"},
        {"table_name": "rosters", "description": "Team rosters and standings (wins, losses, points)"},
        {"table_name": "users", "description": "League members with display names and team names"},
        {"table_name": "matchups", "description": "Weekly matchup scores and results"},
        {"table_name": "transactions", "description": "All league transactions (trades, adds, drops, waivers)"},
        {"table_name": "players", "description": "NFL player information (names, positions, teams)"}
    ]


def describe_table(table_name: str) -> List[Dict[str, str]]:
    """
    Get column information for a specific table
    
    Args:
        table_name: Name of the table to describe
        
    Returns:
        List of columns with their types and descriptions
    """
    logger.info(f"Describing table: {table_name}")
    
    # Return known schema for common tables
    table_schemas = {
        "leagues": [
            {"column_name": "league_id", "data_type": "text", "description": "Unique league identifier"},
            {"column_name": "name", "data_type": "text", "description": "League name"},
            {"column_name": "season", "data_type": "text", "description": "Season year"},
            {"column_name": "status", "data_type": "text", "description": "League status (pre_draft, drafting, in_season, complete)"},
            {"column_name": "settings", "data_type": "jsonb", "description": "League settings including scoring and roster rules"}
        ],
        "rosters": [
            {"column_name": "roster_id", "data_type": "integer", "description": "Unique roster ID within league"},
            {"column_name": "league_id", "data_type": "text", "description": "League identifier"},
            {"column_name": "owner_id", "data_type": "text", "description": "User ID of team owner"},
            {"column_name": "wins", "data_type": "integer", "description": "Number of wins"},
            {"column_name": "losses", "data_type": "integer", "description": "Number of losses"},
            {"column_name": "ties", "data_type": "integer", "description": "Number of ties"},
            {"column_name": "fpts", "data_type": "integer", "description": "Total points for (integer part)"},
            {"column_name": "fpts_decimal", "data_type": "integer", "description": "Points for decimal part (divide by 100)"},
            {"column_name": "fpts_against", "data_type": "integer", "description": "Total points against"},
            {"column_name": "players", "data_type": "text[]", "description": "Array of ALL player IDs on roster (active + bench + IR + taxi)"},
            {"column_name": "starters", "data_type": "text[]", "description": "Array of player IDs in starting lineup"},
            {"column_name": "reserve", "data_type": "text[]", "description": "Array of player IDs on Injured Reserve (IR)"},
            {"column_name": "taxi", "data_type": "text[]", "description": "Array of player IDs on taxi squad"}
        ],
        "users": [
            {"column_name": "user_id", "data_type": "text", "description": "Unique user identifier"},
            {"column_name": "league_id", "data_type": "text", "description": "League identifier"},
            {"column_name": "display_name", "data_type": "text", "description": "User's display name"},
            {"column_name": "team_name", "data_type": "text", "description": "Custom team name"},
            {"column_name": "avatar", "data_type": "text", "description": "Avatar URL"}
        ],
        "matchups": [
            {"column_name": "matchup_id", "data_type": "integer", "description": "Matchup identifier (same ID means teams played each other)"},
            {"column_name": "roster_id", "data_type": "integer", "description": "Roster/team ID"},
            {"column_name": "league_id", "data_type": "text", "description": "League identifier"},
            {"column_name": "week", "data_type": "integer", "description": "Week number (1-18)"},
            {"column_name": "points", "data_type": "numeric", "description": "Points scored in this matchup"},
            {"column_name": "starters", "data_type": "text[]", "description": "Player IDs of starters"}
        ],
        "transactions": [
            {"column_name": "transaction_id", "data_type": "text", "description": "Unique transaction ID"},
            {"column_name": "league_id", "data_type": "text", "description": "League identifier"},
            {"column_name": "type", "data_type": "text", "description": "Type: trade, waiver, free_agent"},
            {"column_name": "status", "data_type": "text", "description": "Status: complete, failed, etc."},
            {"column_name": "week", "data_type": "integer", "description": "Week number when transaction occurred"},
            {"column_name": "creator", "data_type": "text", "description": "User ID who initiated transaction"},
            {"column_name": "roster_ids", "data_type": "integer[]", "description": "Rosters involved in transaction"},
            {"column_name": "adds", "data_type": "jsonb", "description": "Players added (player_id -> roster_id)"},
            {"column_name": "drops", "data_type": "jsonb", "description": "Players dropped (player_id -> roster_id)"},
            {"column_name": "draft_picks", "data_type": "jsonb", "description": "Draft picks involved"}
        ],
        "players": [
            {"column_name": "player_id", "data_type": "text", "description": "Unique player identifier"},
            {"column_name": "full_name", "data_type": "text", "description": "Player's full name"},
            {"column_name": "position", "data_type": "text", "description": "Position (QB, RB, WR, TE, etc.)"},
            {"column_name": "team", "data_type": "text", "description": "NFL team abbreviation"},
            {"column_name": "status", "data_type": "text", "description": "Player status (Active, Inactive, IR, etc.)"}
        ]
    }
    
    if table_name in table_schemas:
        return table_schemas[table_name]
    else:
        return [{"error": f"Unknown table: {table_name}. Use list_tables() to see available tables."}]


def query_with_filters(
    table: str,
    select_columns: str = "*",
    filters: Dict[str, Any] = None,
    order_column: str = None,
    order_desc: bool = False,
    limit: int = None
) -> List[Dict[str, Any]]:
    """
    Query a table with common filters using Supabase client.
    Simpler and safer than writing raw SQL.
    
    Args:
        table: Table name to query
        select_columns: Columns to select (default: "*")
        filters: Dict of column: value filters (e.g. {"league_id": "xxx", "week": 5})
        order_column: Column to order by
        order_desc: Whether to order descending (default: False)
        limit: Maximum number of rows to return
        
    Returns:
        List of rows matching the query
    """
    supabase = get_supabase_client()
    
    try:
        logger.info(f"Querying table {table} with filters: {filters}")
        
        # Start building query
        query = supabase.table(table).select(select_columns)
        
        # Apply filters
        if filters:
            for column, value in filters.items():
                query = query.eq(column, value)
        
        # Apply ordering
        if order_column:
            query = query.order(order_column, desc=order_desc)
        
        # Apply limit
        if limit:
            query = query.limit(limit)
        
        # Execute
        result = query.execute()
        logger.info(f"Query returned {len(result.data) if result.data else 0} rows")
        return result.data if result.data else []
    
    except Exception as e:
        error_msg = f"Error querying table {table}: {str(e)}"
        logger.error(error_msg)
        return [{"error": error_msg}]


def get_team_draft_picks(team_name_search: str = None, season: str = None) -> Dict[str, Any]:
    """
    Get all draft picks made by a specific team in a specific season's draft.
    Use this to answer questions like "who did X draft in 2024?"
    
    Args:
        team_name_search: Team name, owner name, or display name to search for
        season: Season year (e.g., '2023', '2024', '2025'). If not provided, uses current season.
        
    Returns:
        Dictionary with team info and list of draft picks
    """
    supabase = get_supabase_client()
    
    try:
        # Get league for the season
        if season:
            league_query = supabase.table('leagues').select('league_id, season').eq('season', season).execute()
            if not league_query.data:
                return {'error': f'No league found for season {season}'}
            league_id = league_query.data[0]['league_id']
        else:
            league_id = SLEEPER_LEAGUE_ID
        
        # Find the team using fuzzy search (but pass league_id if available)
        if season and league_id != SLEEPER_LEAGUE_ID:
            # For historical seasons, need to query the specific league
            result = supabase.table('rosters').select(
                'roster_id, users(user_id, display_name, team_name)'
            ).eq('league_id', league_id).execute()
            
            # Fuzzy match
            target_roster = None
            search_lower = team_name_search.lower().strip()
            for roster in result.data:
                user_data = roster.get('users', {})
                team_name = (user_data.get('team_name') or '').lower()
                display_name = (user_data.get('display_name') or '').lower()
                
                if search_lower in team_name or search_lower in display_name or team_name in search_lower or display_name in search_lower:
                    target_roster = roster
                    break
            
            if not target_roster:
                return {'error': f'Team not found for: {team_name_search}'}
            
            roster_id = target_roster['roster_id']
            team_name = user_data.get('team_name') or user_data.get('display_name')
            display_name = user_data.get('display_name')
        else:
            # Current season - use find_team_by_name
            team_result = find_team_by_name(team_name_search)
            if not team_result or team_result[0].get('error'):
                return {'error': f'Team not found for: {team_name_search}'}
            
            roster_id = team_result[0]['roster_id']
            team_name = team_result[0]['team_name']
            display_name = team_result[0]['display_name']
        
        # Get draft for this league
        draft_query = supabase.table('drafts').select('draft_id, season, type, status').eq('league_id', league_id).execute()
        if not draft_query.data:
            return {'error': f'No draft found for season {season or "current"}'}
        
        draft = draft_query.data[0]
        
        # Get all picks made by this roster in this draft
        picks_result = supabase.table('draft_picks').select(
            '*, players(full_name, position, team)'
        ).eq('draft_id', draft['draft_id']).eq('roster_id', roster_id).order('pick_no').execute()
        
        picks = []
        for pick in picks_result.data:
            player_data = pick.get('players', {})
            picks.append({
                'pick_no': pick['pick_no'],
                'round': pick['round'],
                'draft_slot': pick['draft_slot'],
                'player_name': player_data.get('full_name', 'Unknown'),
                'position': player_data.get('position'),
                'nfl_team': player_data.get('team'),
                'is_keeper': pick.get('is_keeper', False)
            })
        
        logger.info(f"Found {len(picks)} draft picks for {team_name} in {draft['season']}")
        
        return {
            'team_name': team_name,
            'display_name': display_name,
            'season': draft['season'],
            'draft_type': draft['type'],
            'draft_status': draft['status'],
            'total_picks': len(picks),
            'picks': picks
        }
        
    except Exception as e:
        logger.error(f"Error getting draft picks: {e}", exc_info=True)
        return {'error': str(e)}


def find_who_drafted_player(player_name_search: str, season: str = None) -> Dict[str, Any]:
    """
    Find who drafted a specific player in a specific season's draft.
    Use this to answer questions like "who drafted Cooper Kupp?" or "who picked up Patrick Mahomes in the original draft?"
    
    Args:
        player_name_search: Player name to search for
        season: Season year (e.g., '2023', '2024', '2025'). If not provided, searches current season.
        
    Returns:
        Dictionary with player info and which team drafted them
    """
    supabase = get_supabase_client()
    
    try:
        # First, find the player
        player_results = find_player_by_name(player_name_search, limit=1)
        if not player_results or player_results[0].get('error'):
            return {'error': f'Player not found: {player_name_search}'}
        
        player = player_results[0]
        player_id = player['player_id']
        
        # Get league for the season
        if season:
            league_query = supabase.table('leagues').select('league_id, season, name').eq('season', season).execute()
            if not league_query.data:
                return {'error': f'No league found for season {season}'}
            league_id = league_query.data[0]['league_id']
            season_name = league_query.data[0]['season']
        else:
            league_id = SLEEPER_LEAGUE_ID
            league_data = supabase.table('leagues').select('season, name').eq('league_id', league_id).execute()
            season_name = league_data.data[0]['season'] if league_data.data else 'current'
        
        # Get draft for this league
        draft_query = supabase.table('drafts').select('draft_id, season, type').eq('league_id', league_id).execute()
        if not draft_query.data:
            return {'error': f'No draft found for season {season or "current"}'}
        
        draft = draft_query.data[0]
        
        # Find the draft pick for this player
        pick_result = supabase.table('draft_picks').select(
            'pick_no, round, draft_slot, roster_id, is_keeper'
        ).eq('draft_id', draft['draft_id']).eq('player_id', player_id).execute()
        
        if not pick_result.data:
            return {
                'player_name': player['full_name'],
                'position': player['position'],
                'nfl_team': player['team'],
                'message': f'{player["full_name"]} was not drafted in the {season_name} draft (may have been added as free agent)'
            }
        
        pick = pick_result.data[0]
        
        # Get the team that drafted them
        roster_result = supabase.table('rosters').select(
            'roster_id, users(display_name, team_name)'
        ).eq('league_id', league_id).eq('roster_id', pick['roster_id']).execute()
        
        if not roster_result.data:
            return {'error': f'Could not find team for roster_id {pick["roster_id"]}'}
        
        roster = roster_result.data[0]
        user_data = roster.get('users', {})
        team_name = user_data.get('team_name') or user_data.get('display_name', f"Team {pick['roster_id']}")
        
        logger.info(f"Found that {team_name} drafted {player['full_name']} in {season_name}")
        
        return {
            'player_name': player['full_name'],
            'position': player['position'],
            'nfl_team': player['team'],
            'drafted_by_team': team_name,
            'drafted_by_owner': user_data.get('display_name'),
            'pick_number': pick['pick_no'],
            'round': pick['round'],
            'draft_slot': pick['draft_slot'],
            'season': draft['season'],
            'draft_type': draft['type'],
            'is_keeper': pick.get('is_keeper', False)
        }
        
    except Exception as e:
        logger.error(f"Error finding who drafted player: {e}", exc_info=True)
        return {'error': str(e)}


def get_player_trade_history(player_name_search: str) -> Dict[str, Any]:
    """
    Get all trades involving a specific player across all seasons.
    Use this to answer questions like "what trades has Cooper Kupp been in?" or "who traded for Patrick Mahomes?"
    
    Args:
        player_name_search: Player name to search for
        
    Returns:
        Dictionary with player info and list of all trades involving them
    """
    supabase = get_supabase_client()
    
    try:
        # First, find the player
        player_results = find_player_by_name(player_name_search, limit=1)
        if not player_results or player_results[0].get('error'):
            return {'error': f'Player not found: {player_name_search}'}
        
        player = player_results[0]
        player_id = str(player['player_id'])
        
        logger.info(f"Searching for trades involving {player['full_name']} (ID: {player_id})")
        
        # Get all leagues to search across seasons
        leagues_result = supabase.table('leagues').select('league_id, season, name').order('season').execute()
        
        all_trades = []
        
        for league in leagues_result.data:
            league_id = league['league_id']
            season = league['season']
            
            # Query transactions for trades in this league
            transactions_result = supabase.table('transactions').select(
                'transaction_id, type, status, created, week, roster_ids, settings, adds, drops, draft_picks, waiver_budget'
            ).eq('league_id', league_id).eq('type', 'trade').eq('status', 'complete').execute()
            
            # Check each trade to see if our player is involved
            for txn in transactions_result.data:
                adds = txn.get('adds') or {}
                drops = txn.get('drops') or {}
                draft_picks = txn.get('draft_picks') or []
                roster_ids = txn.get('roster_ids') or []
                
                # Check if player is in adds or drops
                player_involved = False
                acquiring_roster_id = None
                trading_away_roster_id = None
                
                # Player was added to a team (acquired)
                if player_id in adds:
                    player_involved = True
                    acquiring_roster_id = adds[player_id]
                
                # Player was dropped from a team (traded away)
                if player_id in drops:
                    player_involved = True
                    trading_away_roster_id = drops[player_id]
                
                if player_involved:
                    # Start with empty teams_info, will populate as we go
                    teams_info = {}
                    
                    # Get player names for all players in the trade
                    all_player_ids = set(adds.keys()) | set(drops.keys())
                    player_names_map = {}
                    
                    if all_player_ids:
                        # Batch fetch all player names
                        players_result = supabase.table('players').select(
                            'player_id, full_name, position, team'
                        ).in_('player_id', list(all_player_ids)).execute()
                        
                        for p in players_result.data:
                            player_names_map[str(p['player_id'])] = {
                                'name': p['full_name'],
                                'position': p.get('position'),
                                'nfl_team': p.get('team')
                            }
                    
                    # Start with roster_ids but also include teams from player movements
                    # This ensures we catch all actual participants
                    all_roster_ids = set(roster_ids) if roster_ids else set()
                    
                    # Add teams that receive players
                    for pid, roster_id in adds.items():
                        all_roster_ids.add(roster_id)
                    
                    # Add teams that give up players
                    for pid, roster_id in drops.items():
                        all_roster_ids.add(roster_id)
                    
                    # For draft picks, add the receiver (owner_id) but NOT the original owner
                    for pick in draft_picks:
                        if pick.get('owner_id'):
                            all_roster_ids.add(pick.get('owner_id'))
                    
                    # Fetch team names for all roster IDs
                    for roster_id in all_roster_ids:
                        if roster_id not in teams_info:
                            roster_result = supabase.table('rosters').select(
                                'roster_id, users(display_name, team_name)'
                            ).eq('league_id', league_id).eq('roster_id', roster_id).execute()
                            
                            if roster_result.data:
                                user_data = roster_result.data[0].get('users', {})
                                teams_info[roster_id] = user_data.get('team_name') or user_data.get('display_name', f'Team {roster_id}')
                            else:
                                teams_info[roster_id] = f'Team {roster_id}'
                    
                    # Build what each team gave/received (same format as get_recent_trades)
                    teams_data = {}
                    for roster_id in all_roster_ids:
                        team_name = teams_info.get(roster_id, f"Team {roster_id}")
                        teams_data[roster_id] = {
                            'team_name': team_name,
                            'gave_up': [],
                            'received': []
                        }
                    
                    # Process player adds (what they received)
                    for pid, roster_id in adds.items():
                        if roster_id in teams_data:
                            player_info = player_names_map.get(pid, {'name': f'Player {pid}', 'position': None, 'nfl_team': None})
                            player_str = f"{player_info['name']}"
                            if player_info['position'] and player_info['nfl_team']:
                                player_str += f" ({player_info['position']}, {player_info['nfl_team']})"
                            teams_data[roster_id]['received'].append(player_str)
                    
                    # Process player drops (what they gave up)
                    for pid, roster_id in drops.items():
                        if roster_id in teams_data:
                            player_info = player_names_map.get(pid, {'name': f'Player {pid}', 'position': None, 'nfl_team': None})
                            player_str = f"{player_info['name']}"
                            if player_info['position'] and player_info['nfl_team']:
                                player_str += f" ({player_info['position']}, {player_info['nfl_team']})"
                            teams_data[roster_id]['gave_up'].append(player_str)
                    
                    # Process draft picks
                    for pick in draft_picks:
                        owner_id = pick.get('owner_id')  # Who receives the pick
                        roster_id_from = pick.get('roster_id')  # Original owner (may not be in this trade)
                        pick_year = pick.get('season')
                        pick_round = pick.get('round')
                        
                        original_owner = teams_info.get(roster_id_from, f"Team {roster_id_from}")
                        pick_str = f"{pick_year} Round {pick_round} Pick (originally {original_owner}'s)"
                        
                        # Add to receiver
                        if owner_id in teams_data:
                            teams_data[owner_id]['received'].append(pick_str)
                        
                        # Find who's giving up the pick - it's someone in this trade who's NOT the receiver
                        giving_up_teams = [rid for rid in all_roster_ids if rid != owner_id]
                        
                        # If there's only one other team, they're giving it up
                        if len(giving_up_teams) == 1:
                            teams_data[giving_up_teams[0]]['gave_up'].append(pick_str)
                        # If the original owner is in the trade and not the receiver, they're giving it up
                        elif roster_id_from in giving_up_teams:
                            teams_data[roster_id_from]['gave_up'].append(pick_str)
                        # Otherwise, try to infer or just add to first non-receiver
                        elif giving_up_teams:
                            teams_data[giving_up_teams[0]]['gave_up'].append(pick_str)
                    
                    # Build trade details in same format as get_recent_trades
                    trade_info = {
                        'season': season,
                        'week': txn.get('week'),
                        'transaction_id': txn.get('transaction_id'),
                        'teams': list(teams_data.values())
                    }
                    
                    all_trades.append(trade_info)
        
        logger.info(f"Found {len(all_trades)} trades involving {player['full_name']}")
        
        return {
            'player_name': player['full_name'],
            'position': player['position'],
            'nfl_team': player['team'],
            'total_trades': len(all_trades),
            'trades': all_trades
        }
        
    except Exception as e:
        logger.error(f"Error getting player trade history: {e}", exc_info=True)
        return {'error': str(e)}


def get_weekly_matchups(week: int, season: str = None) -> Dict[str, Any]:
    """
    Get formatted weekly matchup results with team names and winners.
    Use this to answer questions like "show me week 5 results" or "what were the week 3 matchups?"
    
    Args:
        week: Week number (1-18)
        season: Season year (e.g., '2023', '2024', '2025'). If not provided, uses current season.
        
    Returns:
        Dictionary with formatted matchup results
    """
    supabase = get_supabase_client()
    
    try:
        # Get league for the season
        if season:
            league_query = supabase.table('leagues').select('league_id, season').eq('season', season).execute()
            if not league_query.data:
                return {'error': f'No league found for season {season}'}
            league_id = league_query.data[0]['league_id']
        else:
            league_id = SLEEPER_LEAGUE_ID
        
        # Get all matchups for this week
        matchups_result = supabase.table('matchups').select(
            'matchup_id, roster_id, points'
        ).eq('league_id', league_id).eq('week', week).order('matchup_id').execute()
        
        if not matchups_result.data:
            return {'error': f'No matchups found for week {week}'}
        
        # Get all rosters with user info for this league
        rosters_result = supabase.table('rosters').select(
            'roster_id, users(display_name, team_name)'
        ).eq('league_id', league_id).execute()
        
        # Create a map of roster_id to team info
        roster_map = {}
        for roster in rosters_result.data:
            user_data = roster.get('users', {})
            roster_map[roster['roster_id']] = {
                'team_name': user_data.get('team_name') or user_data.get('display_name', f"Team {roster['roster_id']}"),
                'display_name': user_data.get('display_name')
            }
        
        # Group matchups by matchup_id
        matchups_by_id = {}
        for matchup in matchups_result.data:
            matchup_id = matchup['matchup_id']
            if matchup_id not in matchups_by_id:
                matchups_by_id[matchup_id] = []
            
            team_info = roster_map.get(matchup['roster_id'], {'team_name': f"Team {matchup['roster_id']}"})
            matchups_by_id[matchup_id].append({
                'roster_id': matchup['roster_id'],
                'team_name': team_info['team_name'],
                'points': matchup['points']
            })
        
        # Format matchups with winners
        formatted_matchups = []
        for matchup_id, teams in matchups_by_id.items():
            if len(teams) == 2:
                team1, team2 = teams[0], teams[1]
                
                # Determine winner
                if team1['points'] > team2['points']:
                    winner = team1['team_name']
                elif team2['points'] > team1['points']:
                    winner = team2['team_name']
                else:
                    winner = "Tie"
                
                formatted_matchups.append({
                    'matchup_id': matchup_id,
                    'team1_name': team1['team_name'],
                    'team1_score': team1['points'],
                    'team2_name': team2['team_name'],
                    'team2_score': team2['points'],
                    'winner': winner
                })
        
        logger.info(f"Found {len(formatted_matchups)} matchups for week {week}")
        
        return {
            'week': week,
            'season': season or 'current',
            'total_matchups': len(formatted_matchups),
            'matchups': formatted_matchups
        }
        
    except Exception as e:
        logger.error(f"Error getting weekly matchups: {e}", exc_info=True)
        return {'error': str(e)}


def find_team_by_name(team_name_search: str) -> List[Dict[str, Any]]:
    """
    Find a team using fuzzy matching on team name or display name.
    Handles typos, partial matches, and variations.
    
    Args:
        team_name_search: Partial or full team name to search for
        
    Returns:
        List of matching teams with roster info and similarity score
    """
    supabase = get_supabase_client()
    
    try:
        logger.info(f"Searching for team matching: {team_name_search}")
        
        # Get all rosters with user info
        result = supabase.table('rosters').select(
            'roster_id, wins, losses, fpts, fpts_decimal, fpts_against, players, starters, reserve, taxi, users(user_id, display_name, team_name)'
        ).eq('league_id', SLEEPER_LEAGUE_ID).execute()
        
        if not result.data:
            return [{"error": "No teams found in league"}]
        
        # Fuzzy match against team names and display names
        matches = []
        search_lower = team_name_search.lower().strip()
        
        for roster in result.data:
            user_data = roster.get('users', {})
            team_name = user_data.get('team_name', '') or ''
            display_name = user_data.get('display_name', '') or ''
            
            team_name_lower = team_name.lower()
            display_name_lower = display_name.lower()
            
            # Calculate match scores
            score = 0
            
            # Exact match (highest priority)
            if search_lower == team_name_lower or search_lower == display_name_lower:
                score = 100
            # Contains exact search term
            elif search_lower in team_name_lower or search_lower in display_name_lower:
                score = 80
            # Search term contains the team name (e.g., "Jaxson" contains "Jaxon")
            elif team_name_lower in search_lower or display_name_lower in search_lower:
                score = 70
            # Check for partial word matches
            else:
                # Split into words and check for matches
                search_words = set(search_lower.split())
                team_words = set(team_name_lower.split())
                display_words = set(display_name_lower.split())
                
                team_overlap = len(search_words & team_words)
                display_overlap = len(search_words & display_words)
                
                if team_overlap > 0 or display_overlap > 0:
                    score = 50 + max(team_overlap, display_overlap) * 10
            
            # Also check character-level similarity for typos
            if score == 0:
                # Simple character overlap check
                team_chars = set(team_name_lower.replace(' ', ''))
                search_chars = set(search_lower.replace(' ', ''))
                
                if len(search_chars) > 0:
                    overlap = len(team_chars & search_chars)
                    char_similarity = (overlap / len(search_chars)) * 100
                    
                    if char_similarity > 60:  # More than 60% characters match
                        score = int(char_similarity * 0.4)  # Scale down
            
            if score > 0:
                matches.append({
                    'roster_id': roster['roster_id'],
                    'team_name': team_name,
                    'display_name': display_name,
                    'wins': roster['wins'],
                    'losses': roster['losses'],
                    'fpts': float(roster['fpts'] or 0) + (float(roster.get('fpts_decimal', 0) or 0) / 100),
                    'fpts_against': float(roster['fpts_against'] or 0),
                    'players': roster.get('players', []),
                    'starters': roster.get('starters', []),
                    'reserve': roster.get('reserve', []),
                    'taxi': roster.get('taxi', []),
                    'match_score': score
                })
        
        # Sort by match score descending
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        if matches:
            logger.info(f"Found {len(matches)} potential matches. Best match: {matches[0]['team_name']} (score: {matches[0]['match_score']})")
            # Return top 3 matches if score is close, otherwise just the best
            if len(matches) > 1 and matches[1]['match_score'] >= matches[0]['match_score'] * 0.8:
                return matches[:3]  # Multiple good matches
            else:
                return [matches[0]]  # Clear winner
        else:
            logger.warning(f"No team found matching: {team_name_search}")
            return [{"error": f"No team found matching '{team_name_search}'", "suggestion": "Try using a different name or check the standings"}]
    
    except Exception as e:
        error_msg = f"Error searching for team: {str(e)}"
        logger.error(error_msg)
        return [{"error": error_msg}]


def list_all_teams() -> List[Dict[str, str]]:
    """
    List all teams in the league with their names and owners.
    Useful as a fallback when team search fails.
    
    Returns:
        List of teams with team_name, display_name, and roster_id
    """
    supabase = get_supabase_client()
    
    try:
        logger.info("Listing all teams in league")
        
        result = supabase.table('rosters').select(
            'roster_id, users(display_name, team_name)'
        ).eq('league_id', SLEEPER_LEAGUE_ID).order('roster_id').execute()
        
        teams = []
        for roster in result.data:
            user_data = roster.get('users', {})
            teams.append({
                'roster_id': roster['roster_id'],
                'team_name': user_data.get('team_name') or user_data.get('display_name', 'Unknown'),
                'owner': user_data.get('display_name', 'Unknown')
            })
        
        logger.info(f"Found {len(teams)} teams")
        return teams
    
    except Exception as e:
        logger.error(f"Error listing teams: {str(e)}")
        return [{"error": str(e)}]


def get_recent_trades(limit: int = 10, season: str = None) -> Dict[str, Any]:
    """
    Get recent trades with all names properly resolved (teams, players, draft picks).
    Use this for questions like "show me recent trades" or "what are the latest trades?"
    
    Args:
        limit: Maximum number of trades to return (default: 10)
        season: Season year (e.g., '2023', '2024', '2025'). If not provided, uses current season.
        
    Returns:
        Dictionary with formatted trade data
    """
    supabase = get_supabase_client()
    
    try:
        # Get league for the season
        if season:
            league_query = supabase.table('leagues').select('league_id, season').eq('season', season).execute()
            if not league_query.data:
                return {'error': f'No league found for season {season}'}
            league_id = league_query.data[0]['league_id']
        else:
            league_id = SLEEPER_LEAGUE_ID
            league_data = supabase.table('leagues').select('season').eq('league_id', league_id).execute()
            season = league_data.data[0]['season'] if league_data.data else 'current'
        
        # Get recent trades
        transactions_result = supabase.table('transactions').select(
            'transaction_id, type, status, created, week, roster_ids, adds, drops, draft_picks'
        ).eq('league_id', league_id).eq('type', 'trade').eq('status', 'complete').order('created', desc=True).limit(limit).execute()
        
        if not transactions_result.data:
            return {'message': f'No trades found for season {season}'}
        
        # Get all rosters with team names for this league
        rosters_result = supabase.table('rosters').select(
            'roster_id, users(display_name, team_name)'
        ).eq('league_id', league_id).execute()
        
        roster_map = {}
        for roster in rosters_result.data:
            user_data = roster.get('users', {})
            roster_map[roster['roster_id']] = user_data.get('team_name') or user_data.get('display_name', f"Team {roster['roster_id']}")
        
        formatted_trades = []
        
        for txn in transactions_result.data:
            adds = txn.get('adds') or {}
            drops = txn.get('drops') or {}
            draft_picks = txn.get('draft_picks') or []
            roster_ids = txn.get('roster_ids') or []
            
            # Get all unique player IDs
            all_player_ids = set(adds.keys()) | set(drops.keys())
            player_map = {}
            
            if all_player_ids:
                players_result = supabase.table('players').select(
                    'player_id, full_name, position, team'
                ).in_('player_id', list(all_player_ids)).execute()
                
                for p in players_result.data:
                    player_map[str(p['player_id'])] = {
                        'name': p['full_name'],
                        'position': p.get('position'),
                        'nfl_team': p.get('team')
                    }
            
            # Start with roster_ids but also include teams from player movements
            # This ensures we catch all actual participants
            all_roster_ids = set(roster_ids) if roster_ids else set()
            
            # Add teams that receive players
            for player_id, roster_id in adds.items():
                all_roster_ids.add(roster_id)
            
            # Add teams that give up players
            for player_id, roster_id in drops.items():
                all_roster_ids.add(roster_id)
            
            # For draft picks, add the receiver (owner_id) but NOT the original owner
            for pick in draft_picks:
                if pick.get('owner_id'):
                    all_roster_ids.add(pick.get('owner_id'))
            
            # Build what each team gave/received
            teams_data = {}
            for roster_id in all_roster_ids:
                team_name = roster_map.get(roster_id, f"Team {roster_id}")
                teams_data[roster_id] = {
                    'team_name': team_name,
                    'gave_up': [],
                    'received': []
                }
            
            # Process player adds (what they received)
            for player_id, roster_id in adds.items():
                if roster_id in teams_data:
                    player_info = player_map.get(player_id, {'name': f'Player {player_id}', 'position': None, 'nfl_team': None})
                    player_str = f"{player_info['name']}"
                    if player_info['position'] and player_info['nfl_team']:
                        player_str += f" ({player_info['position']}, {player_info['nfl_team']})"
                    teams_data[roster_id]['received'].append(player_str)
            
            # Process player drops (what they gave up)
            for player_id, roster_id in drops.items():
                if roster_id in teams_data:
                    player_info = player_map.get(player_id, {'name': f'Player {player_id}', 'position': None, 'nfl_team': None})
                    player_str = f"{player_info['name']}"
                    if player_info['position'] and player_info['nfl_team']:
                        player_str += f" ({player_info['position']}, {player_info['nfl_team']})"
                    teams_data[roster_id]['gave_up'].append(player_str)
            
            # Process draft picks
            for pick in draft_picks:
                owner_id = pick.get('owner_id')  # Who receives the pick
                roster_id_from = pick.get('roster_id')  # Original owner (may not be in this trade)
                pick_year = pick.get('season')
                pick_round = pick.get('round')
                
                original_owner = roster_map.get(roster_id_from, f"Team {roster_id_from}")
                pick_str = f"{pick_year} Round {pick_round} Pick (originally {original_owner}'s)"
                
                # Check if draft has occurred and resolve to actual player
                try:
                    # Get draft for this season
                    draft_result = supabase.table('drafts').select('draft_id, status').eq('league_id', league_id).eq('season', pick_year).execute()
                    
                    if draft_result.data and draft_result.data[0].get('status') == 'complete':
                        draft_id = draft_result.data[0]['draft_id']
                        
                        # The pick was used by owner_id (who received it in trade), not roster_id_from
                        # Query by the current owner and round to find what was drafted
                        draft_pick_result = supabase.table('draft_picks').select(
                            'player_id, pick_no, round, roster_id, players(full_name, position, team)'
                        ).eq('draft_id', draft_id).eq('round', pick_round).eq('roster_id', owner_id).execute()
                        
                        if draft_pick_result.data and draft_pick_result.data[0].get('players'):
                            player_data = draft_pick_result.data[0]['players']
                            player_name = player_data.get('full_name', 'Unknown Player')
                            player_pos = player_data.get('position', '')
                            player_team = player_data.get('team', '')
                            
                            # Update pick string to include drafted player
                            drafted_str = f"{player_name}"
                            if player_pos and player_team:
                                drafted_str += f" ({player_pos}, {player_team})"
                            
                            pick_str = f"{pick_year} Round {pick_round} Pick → {drafted_str} (originally {original_owner}'s)"
                except Exception as e:
                    logger.warning(f"Could not resolve draft pick to player: {e}")
                    # Keep original pick_str if resolution fails
                
                # Add to receiver
                if owner_id in teams_data:
                    teams_data[owner_id]['received'].append(pick_str)
                
                # Find who's giving up the pick - it's someone in this trade who's NOT the receiver
                # In a 2-team trade, it's the other team. In a 3+ team trade, we need more logic.
                giving_up_teams = [rid for rid in all_roster_ids if rid != owner_id]
                
                # If there's only one other team, they're giving it up
                if len(giving_up_teams) == 1:
                    teams_data[giving_up_teams[0]]['gave_up'].append(pick_str)
                # If the original owner is in the trade and not the receiver, they're giving it up
                elif roster_id_from in giving_up_teams:
                    teams_data[roster_id_from]['gave_up'].append(pick_str)
                # Otherwise, try to infer or just add to first non-receiver
                elif giving_up_teams:
                    teams_data[giving_up_teams[0]]['gave_up'].append(pick_str)
            
            # Format trade data
            trade_entry = {
                'season': season,
                'week': txn.get('week'),
                'transaction_id': txn.get('transaction_id'),
                'teams': list(teams_data.values())
            }
            
            # Log warning if any team has nothing
            for team in trade_entry['teams']:
                if not team['gave_up'] and not team['received']:
                    logger.warning(f"Trade {txn.get('transaction_id')} has team {team['team_name']} with no items")
            
            formatted_trades.append(trade_entry)
        
        logger.info(f"Found {len(formatted_trades)} recent trades")
        
        return {
            'season': season,
            'total_trades': len(formatted_trades),
            'trades': formatted_trades
        }
        
    except Exception as e:
        logger.error(f"Error getting recent trades: {e}", exc_info=True)
        return {'error': str(e)}


def get_team_trade_history(team_name_search: str) -> Dict[str, Any]:
    """
    Get all trades involving a specific team across all seasons.
    Use this to answer questions like "show me all trades by FDR" or "what trades has Team X made?"
    
    Args:
        team_name_search: Team name to search for (e.g., "FDR", "The Jaxon 5")
        
    Returns:
        Dictionary with all trades involving the team, in the same format as get_recent_trades
    """
    supabase = get_supabase_client()
    
    try:
        # Find the team first
        team_results = find_team_by_name(team_name_search)
        if not team_results:
            return {'error': f'Team not found: {team_name_search}'}
        
        team = team_results[0]
        user_id = team.get('user_id')
        team_name = team.get('team_name') or team.get('display_name')
        
        logger.info(f"Searching for trades involving {team_name} (user_id: {user_id})")
        
        # Get all leagues to search across seasons
        leagues_result = supabase.table('leagues').select('league_id, season, name').order('season').execute()
        
        all_trades = []
        
        for league in leagues_result.data:
            league_id = league['league_id']
            season = league['season']
            
            # Get the team's roster_id in this league
            roster_result = supabase.table('rosters').select(
                'roster_id'
            ).eq('league_id', league_id).eq('owner_id', user_id).execute()
            
            if not roster_result.data:
                continue  # Team not in this season
            
            team_roster_id = roster_result.data[0]['roster_id']
            
            # Get roster map for this league
            rosters_result = supabase.table('rosters').select(
                'roster_id, users(display_name, team_name)'
            ).eq('league_id', league_id).execute()
            
            roster_map = {}
            for roster in rosters_result.data:
                user_data = roster.get('users', {})
                roster_map[roster['roster_id']] = user_data.get('team_name') or user_data.get('display_name', f"Team {roster['roster_id']}")
            
            # Get all trades in this league that involve this team
            transactions_result = supabase.table('transactions').select(
                'transaction_id, type, status, created, week, roster_ids, adds, drops, draft_picks'
            ).eq('league_id', league_id).eq('type', 'trade').eq('status', 'complete').order('created', desc=True).execute()
            
            # Filter for trades involving this team
            for txn in transactions_result.data:
                roster_ids = txn.get('roster_ids') or []
                if team_roster_id not in roster_ids:
                    continue  # This team not involved in this trade
                
                adds = txn.get('adds') or {}
                drops = txn.get('drops') or {}
                draft_picks = txn.get('draft_picks') or []
                
                # Get all unique player IDs
                all_player_ids = set(adds.keys()) | set(drops.keys())
                player_map = {}
                
                if all_player_ids:
                    players_result = supabase.table('players').select(
                        'player_id, full_name, position, team'
                    ).in_('player_id', list(all_player_ids)).execute()
                    
                    for p in players_result.data:
                        player_map[str(p['player_id'])] = {
                            'name': p['full_name'],
                            'position': p.get('position'),
                            'nfl_team': p.get('team')
                        }
                
                # Build what each team gave/received (same logic as get_recent_trades)
                all_roster_ids = set(roster_ids) if roster_ids else set()
                for player_id, roster_id in adds.items():
                    all_roster_ids.add(roster_id)
                for player_id, roster_id in drops.items():
                    all_roster_ids.add(roster_id)
                for pick in draft_picks:
                    if pick.get('owner_id'):
                        all_roster_ids.add(pick.get('owner_id'))
                
                teams_data = {}
                for roster_id in all_roster_ids:
                    team_name_local = roster_map.get(roster_id, f"Team {roster_id}")
                    teams_data[roster_id] = {
                        'team_name': team_name_local,
                        'gave_up': [],
                        'received': []
                    }
                
                # Process player adds
                for player_id, roster_id in adds.items():
                    if roster_id in teams_data:
                        player_info = player_map.get(player_id, {'name': f'Player {player_id}', 'position': None, 'nfl_team': None})
                        player_str = f"{player_info['name']}"
                        if player_info['position'] and player_info['nfl_team']:
                            player_str += f" ({player_info['position']}, {player_info['nfl_team']})"
                        teams_data[roster_id]['received'].append(player_str)
                
                # Process player drops
                for player_id, roster_id in drops.items():
                    if roster_id in teams_data:
                        player_info = player_map.get(player_id, {'name': f'Player {player_id}', 'position': None, 'nfl_team': None})
                        player_str = f"{player_info['name']}"
                        if player_info['position'] and player_info['nfl_team']:
                            player_str += f" ({player_info['position']}, {player_info['nfl_team']})"
                        teams_data[roster_id]['gave_up'].append(player_str)
                
                # Process draft picks
                for pick in draft_picks:
                    owner_id = pick.get('owner_id')
                    roster_id_from = pick.get('roster_id')
                    pick_year = pick.get('season')
                    pick_round = pick.get('round')
                    
                    original_owner = roster_map.get(roster_id_from, f"Team {roster_id_from}")
                    pick_str = f"{pick_year} Round {pick_round} Pick (originally {original_owner}'s)"
                    
                    # Check if draft has occurred and resolve to actual player
                    try:
                        # Get draft for this season
                        draft_result = supabase.table('drafts').select('draft_id, status').eq('league_id', league_id).eq('season', pick_year).execute()
                        
                        if draft_result.data and draft_result.data[0].get('status') == 'complete':
                            draft_id = draft_result.data[0]['draft_id']
                            
                            # The pick was used by owner_id (who received it in trade), not roster_id_from
                            # Query by the current owner and round to find what was drafted
                            draft_pick_result = supabase.table('draft_picks').select(
                                'player_id, pick_no, round, roster_id, players(full_name, position, team)'
                            ).eq('draft_id', draft_id).eq('round', pick_round).eq('roster_id', owner_id).execute()
                            
                            if draft_pick_result.data and draft_pick_result.data[0].get('players'):
                                player_data = draft_pick_result.data[0]['players']
                                player_name = player_data.get('full_name', 'Unknown Player')
                                player_pos = player_data.get('position', '')
                                player_team = player_data.get('team', '')
                                
                                # Update pick string to include drafted player
                                drafted_str = f"{player_name}"
                                if player_pos and player_team:
                                    drafted_str += f" ({player_pos}, {player_team})"
                                
                                pick_str = f"{pick_year} Round {pick_round} Pick → {drafted_str} (originally {original_owner}'s)"
                    except Exception as e:
                        logger.warning(f"Could not resolve draft pick to player: {e}")
                        # Keep original pick_str if resolution fails
                    
                    if owner_id in teams_data:
                        teams_data[owner_id]['received'].append(pick_str)
                    
                    giving_up_teams = [rid for rid in all_roster_ids if rid != owner_id]
                    if len(giving_up_teams) == 1:
                        teams_data[giving_up_teams[0]]['gave_up'].append(pick_str)
                    elif roster_id_from in giving_up_teams:
                        teams_data[roster_id_from]['gave_up'].append(pick_str)
                    elif giving_up_teams:
                        teams_data[giving_up_teams[0]]['gave_up'].append(pick_str)
                
                # Format trade data
                trade_entry = {
                    'season': season,
                    'week': txn.get('week'),
                    'transaction_id': txn.get('transaction_id'),
                    'teams': list(teams_data.values())
                }
                
                all_trades.append(trade_entry)
        
        logger.info(f"Found {len(all_trades)} trades involving {team_name}")
        
        return {
            'team_name': team_name,
            'total_trades': len(all_trades),
            'trades': all_trades
        }
        
    except Exception as e:
        logger.error(f"Error getting team trade history: {e}", exc_info=True)
        return {'error': str(e)}


def get_trade_counts_by_team() -> Dict[str, Any]:
    """
    Get total trade counts for all teams across all seasons, ranked from most to least.
    Use this for questions like "how many trades has each team made?" or "rank teams by trade activity"
    
    Returns:
        Dictionary with trade counts per team, sorted from most to least
    """
    supabase = get_supabase_client()
    
    try:
        # Get all leagues to search across all seasons
        leagues_result = supabase.table('leagues').select('league_id, season').order('season').execute()
        
        # Dictionary to accumulate trade counts per roster across seasons
        # Key is (roster_owner_id, team_name), value is count
        team_trade_counts = {}
        
        for league in leagues_result.data:
            league_id = league['league_id']
            season = league['season']
            
            # Get all trades for this league
            transactions_result = supabase.table('transactions').select(
                'transaction_id, roster_ids'
            ).eq('league_id', league_id).eq('type', 'trade').eq('status', 'complete').execute()
            
            # Get roster to user mapping for this league
            rosters_result = supabase.table('rosters').select(
                'roster_id, owner_id, users(user_id, display_name, team_name)'
            ).eq('league_id', league_id).execute()
            
            roster_to_owner = {}
            for roster in rosters_result.data:
                user_data = roster.get('users', {})
                owner_id = roster.get('owner_id') or user_data.get('user_id')
                team_name = user_data.get('team_name') or user_data.get('display_name', f"Team {roster['roster_id']}")
                roster_to_owner[roster['roster_id']] = {
                    'owner_id': owner_id,
                    'team_name': team_name
                }
            
            # Count trades for each roster
            for txn in transactions_result.data:
                roster_ids = txn.get('roster_ids') or []
                for roster_id in roster_ids:
                    if roster_id in roster_to_owner:
                        owner_info = roster_to_owner[roster_id]
                        owner_id = owner_info['owner_id']
                        team_name = owner_info['team_name']
                        
                        # Use owner_id as key to track across seasons
                        key = (owner_id, team_name)
                        if key not in team_trade_counts:
                            team_trade_counts[key] = 0
                        team_trade_counts[key] += 1
        
        # Convert to list and sort by count (most to least)
        trade_list = [
            {
                'team_name': team_name,
                'owner_id': owner_id,
                'total_trades': count
            }
            for (owner_id, team_name), count in team_trade_counts.items()
        ]
        
        # Sort by trade count descending
        trade_list.sort(key=lambda x: x['total_trades'], reverse=True)
        
        logger.info(f"Found trade counts for {len(trade_list)} teams")
        
        return {
            'total_teams': len(trade_list),
            'teams': trade_list
        }
        
    except Exception as e:
        logger.error(f"Error getting trade counts: {e}", exc_info=True)
        return {'error': str(e)}


def find_player_by_name(player_name_search: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Find players using fuzzy matching on player names.
    Handles partial names, typos, and variations.
    
    Args:
        player_name_search: Partial or full player name to search for
        limit: Maximum number of results to return
        
    Returns:
        List of matching players with details
    """
    supabase = get_supabase_client()
    
    try:
        logger.info(f"Searching for player matching: {player_name_search}")
        
        # Use ilike for case-insensitive partial match
        search_pattern = f"%{player_name_search}%"
        
        result = supabase.table('players').select(
            'player_id, full_name, position, team, status'
        ).ilike('full_name', search_pattern).limit(limit).execute()
        
        if result.data and len(result.data) > 0:
            logger.info(f"Found {len(result.data)} players matching: {player_name_search}")
            return result.data
        else:
            logger.warning(f"No players found matching: {player_name_search}")
            return [{"error": f"No players found matching '{player_name_search}'"}]
    
    except Exception as e:
        error_msg = f"Error searching for player: {str(e)}"
        logger.error(error_msg)
        return [{"error": error_msg}]


# Function definitions for OpenAI Assistant
FUNCTION_DEFINITIONS = [
    {
        "name": "find_team_by_name",
        "description": """🎯 MANDATORY: Find a team using fuzzy matching. ALWAYS USE THIS for ANY team-related query.
        
        WHEN TO USE (Required for ALL of these):
        ✓ "Who is on [team name]?" → Use this!
        ✓ "Show me [team name]'s roster" → Use this!
        ✓ "What's on [team name]'s IR?" → Use this! (then show reserve array)
        ✓ "[Team name]'s injured players" → Use this! (then show reserve array)
        ✓ "Who does [owner name] have on IR?" → Use this! (then show reserve array)
        ✓ "[Owner name]'s starters" → Use this! (then show starters array)
        ✓ Any question mentioning a team or owner name → Use this!
        
        Handles ALL name variations:
        - Typos: "Jaxson 5" finds "The Jaxon 5" ✓
        - Partial: "Jaxon" finds "The Jaxon 5" ✓
        - Missing words: "Jaxon 5" finds "The Jaxon 5" ✓
        - Possessives: "nickroachys" finds "nickroachy" ✓
        - Owner names: "seahawkcalvin" finds their team ✓
        
        Returns COMPLETE team info including:
        - roster_id, record, points
        - players: ALL player IDs (active + bench + IR + taxi)
        - starters: Player IDs in starting lineup
        - reserve: Player IDs on IR (Injured Reserve) ← Use this for IR questions!
        - taxi: Player IDs on taxi squad
        
        NEVER try to filter teams with query_with_filters - ALWAYS use this function instead!
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "team_name_search": {
                    "type": "string",
                    "description": "Team name, partial name, or owner name to search for"
                }
            },
            "required": ["team_name_search"]
        }
    },
    {
        "name": "list_all_teams",
        "description": """List ALL teams in the league with their names and owners.
        
        Use this if:
        - find_team_by_name() returns no matches
        - User asks "what teams are in the league?"
        - You need to show all available team names to help user
        
        Returns: List of all teams with team_name and owner name.
        """,
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "find_player_by_name",
        "description": """Find players using fuzzy matching. USE THIS when user asks about specific players.
        
        Handles partial names and variations:
        - "Mahomes" finds "Patrick Mahomes"
        - "CeeDee" finds "CeeDee Lamb"
        - "Jefferson" finds all players with Jefferson in name
        
        Returns up to 5 matching players with position, team, and status.
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "player_name_search": {
                    "type": "string",
                    "description": "Player name or partial name to search for"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results to return (default 5)"
                }
            },
            "required": ["player_name_search"]
        }
    },
    {
        "name": "get_team_draft_picks",
        "description": """Get all draft picks made by a specific team in a specific season's draft.
        
        USE THIS when user asks questions like:
        - "Who did [team/owner] draft in [year]?"
        - "What did [team] draft in the 2024 draft?"
        - "Show me [owner]'s draft picks from 2023"
        
        Returns complete draft information including all players picked, their positions, teams, and draft slots.
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "team_name_search": {
                    "type": "string",
                    "description": "Team name, owner name, or display name to search for (e.g., 'nickroachy', 'Oof That Hurts')"
                },
                "season": {
                    "type": "string",
                    "description": "Season year (e.g., '2023', '2024', '2025'). Leave empty for current season."
                }
            },
            "required": ["team_name_search"]
        }
    },
    {
        "name": "find_who_drafted_player",
        "description": """Find who drafted a specific player in a draft.
        
        USE THIS when user asks questions like:
        - "Who drafted Cooper Kupp?"
        - "Who picked Patrick Mahomes in the original draft?"
        - "Which team drafted [player name]?"
        
        For "original draft" or "startup draft", use season='2023'.
        
        Returns which team drafted the player, what pick number, round, etc.
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "player_name_search": {
                    "type": "string",
                    "description": "Player name to search for (e.g., 'Cooper Kupp', 'Mahomes', 'CeeDee Lamb')"
                },
                "season": {
                    "type": "string",
                    "description": "Season year (e.g., '2023' for original/startup draft, '2024', '2025'). Leave empty for current season."
                }
            },
            "required": ["player_name_search"]
        }
    },
    {
        "name": "get_player_trade_history",
        "description": """Get all trades involving a specific player across all seasons.
        
        USE THIS when user asks questions like:
        - "What trades has Cooper Kupp been in?"
        - "Who traded for Patrick Mahomes?"
        - "Has [player] been traded?"
        - "Show me all trades involving [player]"
        
        Returns complete trade history including which teams traded, when, what else was in the trade, etc.
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "player_name_search": {
                    "type": "string",
                    "description": "Player name to search for (e.g., 'Cooper Kupp', 'Mahomes', 'CeeDee Lamb')"
                }
            },
            "required": ["player_name_search"]
        }
    },
    {
        "name": "get_weekly_matchups",
        "description": """Get formatted weekly matchup results with team names, scores, and winners.
        
        USE THIS when user asks questions like:
        - "Show me week 5 results"
        - "What were the week 3 matchups?"
        - "Who won in week 7?"
        - "Week 2 scores"
        
        Returns properly formatted matchup data with team names resolved and winner indicated.
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "week": {
                    "type": "integer",
                    "description": "Week number (1-18)"
                },
                "season": {
                    "type": "string",
                    "description": "Season year (e.g., '2023', '2024', '2025'). Leave empty for current season."
                }
            },
            "required": ["week"]
        }
    },
    {
        "name": "get_recent_trades",
        "description": """Get recent trades with ALL names properly resolved automatically.
        
        USE THIS when user asks questions like:
        - "Show me recent trades"
        - "What are the latest trades?"
        - "Recent trades in the league"
        
        This function automatically resolves:
        - Roster IDs → Team names (e.g., "The Jaxon 5", "G.W.")
        - Player IDs → Player names with position/team (e.g., "Cooper Kupp (WR, LAR)")
        - Draft picks with original owner (e.g., "2024 1st Round Pick (originally G.W.'s)")
        
        Returns fully formatted trade data ready for display. NO additional lookups needed.
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of trades to return (default: 10)"
                },
                "season": {
                    "type": "string",
                    "description": "Season year (e.g., '2023', '2024', '2025'). Leave empty for current season."
                }
            },
            "required": []
        }
    },
    {
        "name": "get_team_trade_history",
        "description": """Get all trades involving a specific team across all seasons.
        
        USE THIS when user asks questions like:
        - "Show me all trades by FDR"
        - "What trades has Team X made?"
        - "List all of [team name]'s trades"
        - "Can you show me FDR's trade history?"
        
        Returns complete trade history for the team in the same table format as get_recent_trades.
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "team_name_search": {
                    "type": "string",
                    "description": "Team name to search for (e.g., 'FDR', 'The Jaxon 5', 'G.W.')"
                }
            },
            "required": ["team_name_search"]
        }
    },
    {
        "name": "get_trade_counts_by_team",
        "description": """Get total trade counts for all teams across ALL seasons, ranked from most to least.
        
        USE THIS when user asks questions like:
        - "How many trades has each team made?"
        - "Rank teams by trade activity"
        - "Who makes the most trades?"
        - "Trade count by team"
        - "Most/least active traders"
        
        Returns all teams with their total trade counts, sorted from most trades to least.
        Automatically tracks teams across all seasons using owner_id.
        """,
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "list_tables",
        "description": "List all available tables in the database.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "describe_table",
        "description": "Get detailed column information for a specific table including data types and descriptions",
        "parameters": {
            "type": "object",
            "properties": {
                "table_name": {
                    "type": "string",
                    "description": "Name of the table to describe (e.g. rosters, users, matchups)"
                }
            },
            "required": ["table_name"]
        }
    },
    {
        "name": "query_with_filters",
        "description": """Query a table with filters. This is the main function to get data.
        
        Examples:
        - Get standings: table="rosters", filters={"league_id": "xxx"}, order_column="wins", order_desc=True
        - Get week 5 matchups: table="matchups", filters={"league_id": "xxx", "week": 5}
        - Get recent trades: table="transactions", filters={"league_id": "xxx", "type": "trade"}, limit=10
        - Get user info: table="users", filters={"league_id": "xxx"}
        - Get specific player: table="players", filters={"full_name": "Patrick Mahomes"} (use ILIKE in filters)
        
        Note: You can select related data using PostgREST syntax like: select_columns="*, users(team_name, display_name)"
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "table": {
                    "type": "string",
                    "description": "Table name to query"
                },
                "select_columns": {
                    "type": "string",
                    "description": "Columns to select (default: *). Can use PostgREST joins like '*, users(team_name)'"
                },
                "filters": {
                    "type": "object",
                    "description": "Dictionary of column: value filters (e.g. {\"league_id\": \"xxx\", \"week\": 5})",
                    "additionalProperties": True
                },
                "order_column": {
                    "type": "string",
                    "description": "Column to sort by"
                },
                "order_desc": {
                    "type": "boolean",
                    "description": "Sort descending (default: false)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of rows to return"
                }
            },
            "required": ["table"]
        }
    }
]

# Map function names to actual functions
FUNCTION_MAP = {
    "find_team_by_name": find_team_by_name,
    "list_all_teams": list_all_teams,
    "find_player_by_name": find_player_by_name,
    "get_team_draft_picks": get_team_draft_picks,
    "find_who_drafted_player": find_who_drafted_player,
    "get_player_trade_history": get_player_trade_history,
    "get_weekly_matchups": get_weekly_matchups,
    "get_recent_trades": get_recent_trades,
    "get_team_trade_history": get_team_trade_history,
    "get_trade_counts_by_team": get_trade_counts_by_team,
    "list_tables": list_tables,
    "describe_table": describe_table,
    "query_with_filters": query_with_filters
}


# Helper: Get the league ID from config
def get_league_id() -> str:
    """Get the league ID from config for use in queries"""
    return SLEEPER_LEAGUE_ID


if __name__ == "__main__":
    # Test the functions
    print("\n" + "="*70)
    print("🧪 Testing Dynamic Query Functions")
    print("="*70)
    
    print("\n📋 Available Tables:")
    tables = list_tables()
    for table in tables:
        print(f"  • {table.get('table_name')}: {table.get('description', 'No description')}")
    
    print("\n🔍 Describing 'rosters' table:")
    columns = describe_table('rosters')
    for col in columns[:5]:  # Show first 5 columns
        print(f"  • {col.get('column_name')} ({col.get('data_type')})")
    
    print("\n✅ Test complete!")

