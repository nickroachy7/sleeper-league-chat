"""
League Query Functions for OpenAI Assistant
These functions can be called by the AI to answer questions about the fantasy league
"""

from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SLEEPER_LEAGUE_ID
from supabase import create_client, Client
from typing import List, Dict, Any, Optional

# Lazy initialization of Supabase client
_supabase_client: Client = None

def get_supabase_client() -> Client:
    """Get or create Supabase client (lazy initialization)"""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    return _supabase_client


def get_league_info() -> Dict[str, Any]:
    """Get basic league information"""
    supabase = get_supabase_client()
    result = supabase.table('leagues').select('*').eq('league_id', SLEEPER_LEAGUE_ID).execute()
    if result.data:
        return result.data[0]
    return {}


def get_standings() -> List[Dict[str, Any]]:
    """Get current league standings with team names"""
    supabase = get_supabase_client()
    query = """
        SELECT 
            r.roster_id,
            r.wins,
            r.losses,
            r.ties,
            r.fpts,
            r.fpts_against,
            u.display_name,
            u.team_name,
            u.avatar
        FROM rosters r
        LEFT JOIN users u ON r.owner_id = u.user_id
        WHERE r.league_id = :league_id
        ORDER BY r.wins DESC, r.fpts DESC
    """
    
    result = supabase.table('rosters').select(
        'roster_id, wins, losses, ties, fpts, fpts_against, users(display_name, team_name, avatar)'
    ).eq('league_id', SLEEPER_LEAGUE_ID).execute()
    
    standings = []
    for roster in result.data:
        user_data = roster.get('users', {})
        standings.append({
            'roster_id': roster['roster_id'],
            'team_name': user_data.get('team_name') or user_data.get('display_name', 'Unknown Team'),
            'display_name': user_data.get('display_name'),
            'wins': roster['wins'],
            'losses': roster['losses'],
            'ties': roster['ties'],
            'points_for': float(roster['fpts'] or 0) + (float(roster.get('fpts_decimal', 0) or 0) / 100),
            'points_against': float(roster['fpts_against'] or 0) + (float(roster.get('fpts_against_decimal', 0) or 0) / 100)
        })
    
    # Sort by wins (descending), then points for (descending)
    standings.sort(key=lambda x: (x['wins'], x['points_for']), reverse=True)
    return standings


def get_team_roster(team_name: str = None, display_name: str = None) -> Dict[str, Any]:
    """Get a specific team's roster with player details"""
    supabase = get_supabase_client()
    query = supabase.table('rosters').select(
        'roster_id, players, starters, reserve, taxi, wins, losses, fpts, users(display_name, team_name)'
    ).eq('league_id', SLEEPER_LEAGUE_ID)
    
    result = query.execute()
    
    # Find the team
    target_roster = None
    for roster in result.data:
        user_data = roster.get('users', {})
        roster_team_name = user_data.get('team_name', '').lower()
        roster_display_name = user_data.get('display_name', '').lower()
        
        if team_name and team_name.lower() in roster_team_name:
            target_roster = roster
            break
        elif display_name and display_name.lower() in roster_display_name:
            target_roster = roster
            break
    
    if not target_roster:
        return {'error': 'Team not found'}
    
    # Get player details
    player_ids = target_roster.get('players', [])
    if player_ids:
        players_result = supabase.table('players').select('*').in_('player_id', player_ids).execute()
        players_map = {p['player_id']: p for p in players_result.data}
    else:
        players_map = {}
    
    user_data = target_roster.get('users', {})
    return {
        'roster_id': target_roster['roster_id'],
        'team_name': user_data.get('team_name'),
        'display_name': user_data.get('display_name'),
        'record': f"{target_roster['wins']}-{target_roster['losses']}",
        'total_points': target_roster['fpts'],
        'starters': [
            {
                'player_id': pid,
                'name': players_map.get(pid, {}).get('full_name', 'Unknown'),
                'position': players_map.get(pid, {}).get('position', 'N/A'),
                'team': players_map.get(pid, {}).get('team', 'N/A')
            }
            for pid in target_roster.get('starters', [])
        ],
        'bench': [
            {
                'player_id': pid,
                'name': players_map.get(pid, {}).get('full_name', 'Unknown'),
                'position': players_map.get(pid, {}).get('position', 'N/A'),
                'team': players_map.get(pid, {}).get('team', 'N/A')
            }
            for pid in target_roster.get('players', []) if pid not in target_roster.get('starters', [])
        ]
    }


def get_matchup_results(week: int) -> List[Dict[str, Any]]:
    """Get matchup results for a specific week"""
    supabase = get_supabase_client()
    result = supabase.table('matchups').select(
        'roster_id, matchup_id, points, week'
    ).eq('league_id', SLEEPER_LEAGUE_ID).eq('week', week).execute()
    
    # Get roster/user info
    rosters_result = supabase.table('rosters').select(
        'roster_id, users(display_name, team_name)'
    ).eq('league_id', SLEEPER_LEAGUE_ID).execute()
    
    rosters_map = {}
    for roster in rosters_result.data:
        user_data = roster.get('users', {})
        rosters_map[roster['roster_id']] = {
            'team_name': user_data.get('team_name') or user_data.get('display_name', 'Unknown'),
            'display_name': user_data.get('display_name')
        }
    
    # Group by matchup_id
    matchups_dict = {}
    for matchup in result.data:
        matchup_id = matchup['matchup_id']
        if matchup_id not in matchups_dict:
            matchups_dict[matchup_id] = []
        
        roster_id = matchup['roster_id']
        roster_info = rosters_map.get(roster_id, {})
        
        matchups_dict[matchup_id].append({
            'roster_id': roster_id,
            'team_name': roster_info.get('team_name', 'Unknown'),
            'points': float(matchup['points'] or 0)
        })
    
    # Format matchups
    matchups = []
    for matchup_id, teams in matchups_dict.items():
        if len(teams) == 2:
            winner = teams[0] if teams[0]['points'] > teams[1]['points'] else teams[1]
            loser = teams[1] if teams[0]['points'] > teams[1]['points'] else teams[0]
            
            matchups.append({
                'matchup_id': matchup_id,
                'week': week,
                'team1': teams[0]['team_name'],
                'team1_points': teams[0]['points'],
                'team2': teams[1]['team_name'],
                'team2_points': teams[1]['points'],
                'winner': winner['team_name']
            })
    
    return matchups


def get_top_scorers(week: int = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Get top scoring teams for a week or season"""
    supabase = get_supabase_client()
    if week:
        result = supabase.table('matchups').select(
            'roster_id, points, week'
        ).eq('league_id', SLEEPER_LEAGUE_ID).eq('week', week).order('points', desc=True).limit(limit).execute()
    else:
        # Season totals
        result = supabase.table('rosters').select(
            'roster_id, fpts, fpts_decimal'
        ).eq('league_id', SLEEPER_LEAGUE_ID).order('fpts', desc=True).limit(limit).execute()
    
    # Get roster/user info
    rosters_result = supabase.table('rosters').select(
        'roster_id, users(display_name, team_name)'
    ).eq('league_id', SLEEPER_LEAGUE_ID).execute()
    
    rosters_map = {}
    for roster in rosters_result.data:
        user_data = roster.get('users', {})
        rosters_map[roster['roster_id']] = {
            'team_name': user_data.get('team_name') or user_data.get('display_name', 'Unknown'),
            'display_name': user_data.get('display_name')
        }
    
    scorers = []
    for item in result.data:
        roster_id = item['roster_id']
        roster_info = rosters_map.get(roster_id, {})
        
        if week:
            points = float(item['points'] or 0)
        else:
            points = float(item['fpts'] or 0) + (float(item.get('fpts_decimal', 0) or 0) / 100)
        
        scorers.append({
            'team_name': roster_info.get('team_name', 'Unknown'),
            'display_name': roster_info.get('display_name'),
            'points': points,
            'week': week if week else 'Season'
        })
    
    return scorers


def get_recent_transactions(limit: int = 10, transaction_type: str = None) -> List[Dict[str, Any]]:
    """Get recent transactions (trades, adds, drops) with complete details"""
    supabase = get_supabase_client()
    query = supabase.table('transactions').select('*').eq('league_id', SLEEPER_LEAGUE_ID)
    
    if transaction_type:
        query = query.eq('type', transaction_type)
    
    result = query.order('created', desc=True).limit(limit).execute()
    
    # Get roster info to map roster_id to team names
    rosters_result = supabase.table('rosters').select(
        'roster_id, users(display_name, team_name)'
    ).eq('league_id', SLEEPER_LEAGUE_ID).execute()
    
    roster_to_team = {}
    for roster in rosters_result.data:
        user_data = roster.get('users', {})
        roster_to_team[roster['roster_id']] = user_data.get('team_name') or user_data.get('display_name', 'Unknown')
    
    # Get user info for creator
    users_result = supabase.table('users').select('user_id, display_name, team_name').eq('league_id', SLEEPER_LEAGUE_ID).execute()
    users_map = {u['user_id']: u for u in users_result.data}
    
    transactions = []
    for trans in result.data:
        creator_id = trans.get('creator')
        creator = users_map.get(creator_id, {})
        
        transaction_data = {
            'transaction_id': trans['transaction_id'],
            'type': trans['type'],
            'status': trans['status'],
            'week': trans.get('week'),
            'creator': creator.get('team_name') or creator.get('display_name', 'Unknown')
        }
        
        # For trades, show complete details
        if trans['type'] == 'trade':
            roster_ids = trans.get('roster_ids', [])
            transaction_data['teams_involved'] = [roster_to_team.get(rid, f'Team {rid}') for rid in roster_ids]
            
            # Process player movements
            adds = trans.get('adds') or {}  # player_id -> roster_id (receiving)
            drops = trans.get('drops') or {}  # player_id -> roster_id (sending)
            
            # Get player names
            player_ids = list(set(list(adds.keys()) + list(drops.keys())))
            if player_ids:
                players_result = supabase.table('players').select('player_id, full_name, position, team').in_('player_id', player_ids).execute()
                players_map = {p['player_id']: p for p in players_result.data}
                
                # Format player movements
                player_movements = []
                for player_id in adds.keys():
                    receiving_roster = adds[player_id]
                    sending_roster = drops.get(player_id)
                    player_info = players_map.get(player_id, {})
                    
                    player_movements.append({
                        'player': player_info.get('full_name', 'Unknown'),
                        'position': player_info.get('position', 'N/A'),
                        'nfl_team': player_info.get('team', 'N/A'),
                        'from_team': roster_to_team.get(sending_roster, f'Team {sending_roster}') if sending_roster else 'Unknown',
                        'to_team': roster_to_team.get(receiving_roster, f'Team {receiving_roster}')
                    })
                
                transaction_data['player_movements'] = player_movements
            
            # Process draft picks with complete ownership details
            draft_picks = trans.get('draft_picks', [])
            if draft_picks:
                draft_pick_details = []
                for pick in draft_picks:
                    roster_id = pick.get('roster_id')
                    previous_owner_id = pick.get('previous_owner_id')
                    owner_id = pick.get('owner_id')
                    season = pick.get('season')
                    round_num = pick.get('round')
                    
                    original_owner = roster_to_team.get(roster_id, f"Team {roster_id}")
                    from_team = roster_to_team.get(previous_owner_id, f"Team {previous_owner_id}")
                    to_team = roster_to_team.get(owner_id, f"Team {owner_id}")
                    
                    pick_detail = {
                        'season': season,
                        'round': round_num,
                        'original_owner': original_owner,
                        'from_team': from_team,
                        'to_team': to_team,
                        'description': f"{season} Round {round_num} (originally {original_owner})"
                    }
                    draft_pick_details.append(pick_detail)
                
                transaction_data['draft_picks'] = draft_pick_details
        
        else:
            # For non-trade transactions (waivers, free agents), use simpler format
            adds = trans.get('adds') or {}
            drops = trans.get('drops') or {}
            
            player_ids = list(set(list(adds.keys()) + list(drops.keys())))
            if player_ids:
                players_result = supabase.table('players').select('player_id, full_name, position').in_('player_id', player_ids).execute()
                players_map = {p['player_id']: p for p in players_result.data}
                
                if adds:
                    transaction_data['adds_formatted'] = [
                        {
                            'player': players_map.get(pid, {}).get('full_name', 'Unknown'),
                            'position': players_map.get(pid, {}).get('position', 'N/A')
                        }
                        for pid in adds.keys()
                    ]
                
                if drops:
                    transaction_data['drops_formatted'] = [
                        {
                            'player': players_map.get(pid, {}).get('full_name', 'Unknown'),
                            'position': players_map.get(pid, {}).get('position', 'N/A')
                        }
                        for pid in drops.keys()
                    ]
        
        transactions.append(transaction_data)
    
    return transactions


def search_player(name: str) -> List[Dict[str, Any]]:
    """Search for a player by name"""
    supabase = get_supabase_client()
    result = supabase.table('players').select('*').ilike('full_name', f'%{name}%').limit(10).execute()
    return result.data


def get_player_ownership(player_name: str) -> Dict[str, Any]:
    """Find which team owns a specific player"""
    supabase = get_supabase_client()
    # First find the player
    player_result = supabase.table('players').select('player_id, full_name, position, team').ilike('full_name', f'%{player_name}%').limit(1).execute()
    
    if not player_result.data:
        return {'error': 'Player not found'}
    
    player = player_result.data[0]
    player_id = player['player_id']
    
    # Find which roster has this player
    rosters_result = supabase.table('rosters').select(
        'roster_id, players, users(display_name, team_name)'
    ).eq('league_id', SLEEPER_LEAGUE_ID).execute()
    
    for roster in rosters_result.data:
        if player_id in roster.get('players', []):
            user_data = roster.get('users', {})
            return {
                'player': player['full_name'],
                'position': player['position'],
                'nfl_team': player['team'],
                'owned_by': user_data.get('team_name') or user_data.get('display_name', 'Unknown'),
                'roster_id': roster['roster_id']
            }
    
    return {
        'player': player['full_name'],
        'position': player['position'],
        'nfl_team': player['team'],
        'owned_by': 'Free Agent',
        'roster_id': None
    }


def get_playoff_picture() -> List[Dict[str, Any]]:
    """Get current playoff standings (top 6 teams)"""
    standings = get_standings()
    
    # Get league settings for playoff teams count
    league_info = get_league_info()
    playoff_spots = league_info.get('settings', {}).get('playoff_teams', 6)
    
    playoff_teams = standings[:playoff_spots]
    bubble_teams = standings[playoff_spots:playoff_spots+2] if len(standings) > playoff_spots else []
    
    return {
        'playoff_teams': playoff_teams,
        'bubble_teams': bubble_teams,
        'playoff_spots': playoff_spots
    }


def get_nfl_state() -> Dict[str, Any]:
    """Get current NFL state (current week, season, etc)"""
    supabase = get_supabase_client()
    result = supabase.table('nfl_state').select('*').order('created_at', desc=True).limit(1).execute()
    if result.data:
        return result.data[0]
    return {}


def get_traded_picks(season: str = None) -> List[Dict[str, Any]]:
    """Get all traded draft picks, optionally filtered by season"""
    supabase = get_supabase_client()
    query = supabase.table('traded_picks').select('*').eq('league_id', SLEEPER_LEAGUE_ID)
    
    if season:
        query = query.eq('season', season)
    
    result = query.order('season').order('round').execute()
    
    # Enhance with team names
    rosters = supabase.table('rosters').select('roster_id, users(display_name, team_name)').eq('league_id', SLEEPER_LEAGUE_ID).execute()
    roster_map = {}
    for roster in rosters.data:
        user_data = roster.get('users', {})
        roster_map[roster['roster_id']] = user_data.get('team_name') or user_data.get('display_name', f"Team {roster['roster_id']}")
    
    picks = []
    for pick in result.data:
        picks.append({
            'season': pick['season'],
            'round': pick['round'],
            'original_owner': roster_map.get(pick['roster_id'], f"Roster {pick['roster_id']}"),
            'current_owner': roster_map.get(pick['owner_id'], f"Roster {pick['owner_id']}"),
            'previous_owner': roster_map.get(pick['previous_owner_id'], f"Roster {pick['previous_owner_id']}") if pick.get('previous_owner_id') else None
        })
    
    return picks


def get_team_draft_capital(team_name: str = None, display_name: str = None, season: str = None) -> Dict[str, Any]:
    """Get all draft picks owned by a specific team"""
    supabase = get_supabase_client()
    
    # Find the team's roster_id
    query = supabase.table('rosters').select('roster_id, users(display_name, team_name)').eq('league_id', SLEEPER_LEAGUE_ID)
    rosters_result = query.execute()
    
    target_roster_id = None
    target_team_name = None
    for roster in rosters_result.data:
        user_data = roster.get('users', {})
        roster_team_name = user_data.get('team_name', '').lower()
        roster_display_name = user_data.get('display_name', '').lower()
        
        if team_name and team_name.lower() in roster_team_name:
            target_roster_id = roster['roster_id']
            target_team_name = user_data.get('team_name') or user_data.get('display_name')
            break
        elif display_name and display_name.lower() in roster_display_name:
            target_roster_id = roster['roster_id']
            target_team_name = user_data.get('team_name') or user_data.get('display_name')
            break
    
    if not target_roster_id:
        return {'error': 'Team not found'}
    
    # Get all picks owned by this team
    query = supabase.table('traded_picks').select('*').eq('league_id', SLEEPER_LEAGUE_ID).eq('owner_id', target_roster_id)
    if season:
        query = query.eq('season', season)
    
    result = query.order('season').order('round').execute()
    
    # Build roster map for original owners
    roster_map = {}
    for roster in rosters_result.data:
        user_data = roster.get('users', {})
        roster_map[roster['roster_id']] = user_data.get('team_name') or user_data.get('display_name', f"Team {roster['roster_id']}")
    
    picks = []
    for pick in result.data:
        picks.append({
            'season': pick['season'],
            'round': pick['round'],
            'original_owner': roster_map.get(pick['roster_id'], f"Roster {pick['roster_id']}"),
            'is_own_pick': pick['roster_id'] == target_roster_id
        })
    
    return {
        'team_name': target_team_name,
        'roster_id': target_roster_id,
        'picks': picks
    }


def get_draft_results(draft_id: str = None) -> Dict[str, Any]:
    """Get draft results showing all picks"""
    supabase = get_supabase_client()
    
    # Get the draft (or most recent one if not specified)
    if draft_id:
        draft_query = supabase.table('drafts').select('*').eq('draft_id', draft_id)
    else:
        draft_query = supabase.table('drafts').select('*').eq('league_id', SLEEPER_LEAGUE_ID).order('created_at', desc=True).limit(1)
    
    draft_result = draft_query.execute()
    if not draft_result.data:
        return {'error': 'No draft found'}
    
    draft = draft_result.data[0]
    
    # Get all picks for this draft
    picks_result = supabase.table('draft_picks').select('*, players(full_name, position, team)').eq('draft_id', draft['draft_id']).order('pick_no').execute()
    
    # Get roster/user mapping
    rosters = supabase.table('rosters').select('roster_id, users(display_name, team_name)').eq('league_id', SLEEPER_LEAGUE_ID).execute()
    roster_map = {}
    for roster in rosters.data:
        user_data = roster.get('users', {})
        roster_map[roster['roster_id']] = user_data.get('team_name') or user_data.get('display_name', f"Team {roster['roster_id']}")
    
    picks = []
    for pick in picks_result.data:
        player_data = pick.get('players', {})
        picks.append({
            'pick_no': pick['pick_no'],
            'round': pick['round'],
            'draft_slot': pick['draft_slot'],
            'team': roster_map.get(pick['roster_id'], f"Roster {pick['roster_id']}"),
            'player_name': player_data.get('full_name', 'Unknown'),
            'position': player_data.get('position'),
            'nfl_team': player_data.get('team'),
            'is_keeper': pick.get('is_keeper', False)
        })
    
    return {
        'draft_id': draft['draft_id'],
        'season': draft['season'],
        'type': draft['type'],
        'status': draft['status'],
        'picks': picks
    }


def get_team_draft_picks(team_name: str = None, display_name: str = None, season: str = None) -> Dict[str, Any]:
    """Get all draft picks made by a specific team in a specific season"""
    supabase = get_supabase_client()
    
    # Find the team's roster_id and user info
    if season:
        # Get league for specific season
        league_query = supabase.table('leagues').select('league_id').eq('season', season).execute()
        if not league_query.data:
            return {'error': f'No league found for season {season}'}
        league_id = league_query.data[0]['league_id']
    else:
        league_id = SLEEPER_LEAGUE_ID
    
    # Get rosters and users for that league
    query = supabase.table('rosters').select('roster_id, owner_id, users(user_id, display_name, team_name, username)').eq('league_id', league_id)
    rosters_result = query.execute()
    
    target_roster_id = None
    target_user_info = None
    for roster in rosters_result.data:
        user_data = roster.get('users', {})
        roster_team_name = (user_data.get('team_name') or '').lower()
        roster_display_name = (user_data.get('display_name') or '').lower()
        roster_username = (user_data.get('username') or '').lower()
        
        if team_name and team_name.lower() in roster_team_name:
            target_roster_id = roster['roster_id']
            target_user_info = user_data
            break
        elif display_name and display_name.lower() in roster_display_name:
            target_roster_id = roster['roster_id']
            target_user_info = user_data
            break
        elif display_name and roster_username and display_name.lower() in roster_username:
            target_roster_id = roster['roster_id']
            target_user_info = user_data
            break
    
    if not target_roster_id:
        return {'error': f'Team not found for {team_name or display_name}'}
    
    # Get draft for this league
    draft_query = supabase.table('drafts').select('*').eq('league_id', league_id).execute()
    if not draft_query.data:
        return {'error': f'No draft found for season {season or "current"}'}
    
    draft = draft_query.data[0]
    
    # Get all picks made by this roster in this draft
    picks_result = supabase.table('draft_picks').select('*, players(full_name, position, team)').eq('draft_id', draft['draft_id']).eq('roster_id', target_roster_id).order('pick_no').execute()
    
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
    
    return {
        'team_name': target_user_info.get('team_name') or target_user_info.get('display_name'),
        'display_name': target_user_info.get('display_name'),
        'username': target_user_info.get('username'),
        'season': draft['season'],
        'draft_type': draft['type'],
        'picks': picks
    }


def get_playoff_bracket() -> Dict[str, Any]:
    """Get current playoff bracket matchups"""
    supabase = get_supabase_client()
    
    result = supabase.table('playoff_brackets').select('*').eq('league_id', SLEEPER_LEAGUE_ID).order('bracket_type').order('round').execute()
    
    if not result.data:
        return {'message': 'Playoffs have not started yet'}
    
    # Get roster/user mapping
    rosters = supabase.table('rosters').select('roster_id, users(display_name, team_name)').eq('league_id', SLEEPER_LEAGUE_ID).execute()
    roster_map = {}
    for roster in rosters.data:
        user_data = roster.get('users', {})
        roster_map[roster['roster_id']] = user_data.get('team_name') or user_data.get('display_name', f"Team {roster['roster_id']}")
    
    winners_bracket = []
    losers_bracket = []
    
    for matchup in result.data:
        matchup_info = {
            'round': matchup['round'],
            'matchup_id': matchup['matchup_id'],
            'team_1': roster_map.get(matchup['team_1_roster_id'], 'TBD') if matchup.get('team_1_roster_id') else 'TBD',
            'team_2': roster_map.get(matchup['team_2_roster_id'], 'TBD') if matchup.get('team_2_roster_id') else 'TBD',
            'team_1_points': float(matchup['team_1_points']) if matchup.get('team_1_points') else None,
            'team_2_points': float(matchup['team_2_points']) if matchup.get('team_2_points') else None,
            'winner': roster_map.get(matchup['winner_roster_id']) if matchup.get('winner_roster_id') else None
        }
        
        if matchup['bracket_type'] == 'winners':
            winners_bracket.append(matchup_info)
        else:
            losers_bracket.append(matchup_info)
    
    return {
        'winners_bracket': winners_bracket,
        'losers_bracket': losers_bracket
    }


# Function definitions for OpenAI Assistant
FUNCTION_DEFINITIONS = [
    {
        "name": "get_league_info",
        "description": "Get basic information about the fantasy league including name, season, settings",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_standings",
        "description": "Get current league standings with wins, losses, and points for all teams",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_team_roster",
        "description": "Get a specific team's roster including all players, starters, and bench",
        "parameters": {
            "type": "object",
            "properties": {
                "team_name": {
                    "type": "string",
                    "description": "The team name to look up"
                },
                "display_name": {
                    "type": "string",
                    "description": "The display name of the team owner"
                }
            },
            "required": []
        }
    },
    {
        "name": "get_matchup_results",
        "description": "Get matchup results for a specific week showing scores and winners",
        "parameters": {
            "type": "object",
            "properties": {
                "week": {
                    "type": "integer",
                    "description": "The week number (1-18)"
                }
            },
            "required": ["week"]
        }
    },
    {
        "name": "get_top_scorers",
        "description": "Get the top scoring teams for a specific week or the entire season",
        "parameters": {
            "type": "object",
            "properties": {
                "week": {
                    "type": "integer",
                    "description": "The week number (optional, omit for season totals)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of teams to return (default 10)"
                }
            },
            "required": []
        }
    },
    {
        "name": "get_recent_transactions",
        "description": "Get recent transactions including trades, adds, and drops",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of transactions to return (default 10)"
                },
                "transaction_type": {
                    "type": "string",
                    "description": "Filter by type: 'trade', 'waiver', 'free_agent' (optional)"
                }
            },
            "required": []
        }
    },
    {
        "name": "search_player",
        "description": "Search for a player by name",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Player name or partial name to search for"
                }
            },
            "required": ["name"]
        }
    },
    {
        "name": "get_player_ownership",
        "description": "Find which team owns a specific player",
        "parameters": {
            "type": "object",
            "properties": {
                "player_name": {
                    "type": "string",
                    "description": "Name of the player to look up"
                }
            },
            "required": ["player_name"]
        }
    },
    {
        "name": "get_playoff_picture",
        "description": "Get the current playoff picture showing which teams are in playoff position",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_nfl_state",
        "description": "Get current NFL state including current week, season, and season type",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_traded_picks",
        "description": "Get all traded draft picks across all seasons or for a specific season",
        "parameters": {
            "type": "object",
            "properties": {
                "season": {
                    "type": "string",
                    "description": "Season year to filter by (e.g., '2025', '2026'), optional"
                }
            },
            "required": []
        }
    },
    {
        "name": "get_team_draft_capital",
        "description": "Get all draft picks owned by a specific team for future drafts",
        "parameters": {
            "type": "object",
            "properties": {
                "team_name": {
                    "type": "string",
                    "description": "The team name to look up"
                },
                "display_name": {
                    "type": "string",
                    "description": "The display name of the team owner"
                },
                "season": {
                    "type": "string",
                    "description": "Season year to filter by (e.g., '2025', '2026'), optional"
                }
            },
            "required": []
        }
    },
    {
        "name": "get_draft_results",
        "description": "Get draft results showing all picks made in a draft",
        "parameters": {
            "type": "object",
            "properties": {
                "draft_id": {
                    "type": "string",
                    "description": "Specific draft ID (optional, will use most recent if omitted)"
                }
            },
            "required": []
        }
    },
    {
        "name": "get_playoff_bracket",
        "description": "Get the current playoff bracket showing all playoff matchups, winners and losers brackets",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_team_draft_picks",
        "description": "Get all draft picks made by a specific team in a specific season's draft. Use this to answer questions like 'who did X draft in 2024?'",
        "parameters": {
            "type": "object",
            "properties": {
                "team_name": {
                    "type": "string",
                    "description": "The team name to look up"
                },
                "display_name": {
                    "type": "string",
                    "description": "The display name or username of the team owner"
                },
                "season": {
                    "type": "string",
                    "description": "Season year (e.g., '2023', '2024', '2025')"
                }
            },
            "required": []
        }
    }
]

# Map function names to actual functions
FUNCTION_MAP = {
    "get_league_info": get_league_info,
    "get_standings": get_standings,
    "get_team_roster": get_team_roster,
    "get_matchup_results": get_matchup_results,
    "get_top_scorers": get_top_scorers,
    "get_recent_transactions": get_recent_transactions,
    "search_player": search_player,
    "get_player_ownership": get_player_ownership,
    "get_playoff_picture": get_playoff_picture,
    "get_nfl_state": get_nfl_state,
    "get_traded_picks": get_traded_picks,
    "get_team_draft_capital": get_team_draft_capital,
    "get_draft_results": get_draft_results,
    "get_playoff_bracket": get_playoff_bracket,
    "get_team_draft_picks": get_team_draft_picks
}

