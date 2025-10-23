#!/usr/bin/env python3
"""
Sleeper Data Sync Script
Fetches data from Sleeper API and syncs to Supabase database
"""

import requests
import json
import time
from datetime import datetime
from typing import Optional, Any
from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SLEEPER_LEAGUE_ID
from supabase import create_client, Client
from logger_config import setup_logger

# Setup logging
logger = setup_logger('sync_sleeper_data')

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

SLEEPER_API_BASE = "https://api.sleeper.app/v1"
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds


def make_request_with_retry(url: str, max_retries: int = MAX_RETRIES) -> Optional[Any]:
    """
    Make HTTP request with retry logic
    
    Args:
        url: URL to request
        max_retries: Maximum number of retry attempts
    
    Returns:
        JSON response data or None if all retries fail
    """
    for attempt in range(max_retries):
        try:
            logger.debug(f"Requesting {url} (attempt {attempt + 1}/{max_retries})")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout on attempt {attempt + 1}/{max_retries} for {url}")
            if attempt < max_retries - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed on attempt {attempt + 1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                raise
    return None


def fetch_league_data(league_id: str) -> dict:
    """Fetch league information from Sleeper API"""
    url = f"{SLEEPER_API_BASE}/league/{league_id}"
    return make_request_with_retry(url)


def fetch_users(league_id: str) -> list:
    """Fetch all users in the league"""
    url = f"{SLEEPER_API_BASE}/league/{league_id}/users"
    return make_request_with_retry(url)


def fetch_rosters(league_id: str) -> list:
    """Fetch all rosters in the league"""
    url = f"{SLEEPER_API_BASE}/league/{league_id}/rosters"
    return make_request_with_retry(url)


def fetch_matchups(league_id: str, week: int) -> list:
    """Fetch matchups for a specific week"""
    url = f"{SLEEPER_API_BASE}/league/{league_id}/matchups/{week}"
    return make_request_with_retry(url)


def fetch_transactions(league_id: str, week: int) -> list:
    """Fetch transactions for a specific week"""
    url = f"{SLEEPER_API_BASE}/league/{league_id}/transactions/{week}"
    return make_request_with_retry(url)


def fetch_all_players() -> dict:
    """Fetch all NFL players from Sleeper"""
    url = f"{SLEEPER_API_BASE}/players/nfl"
    return make_request_with_retry(url)


def sync_league(league_id: str):
    """Sync league data to Supabase"""
    logger.info(f"Fetching league data for {league_id}...")
    league_data = fetch_league_data(league_id)
    
    if not league_data:
        logger.error("Failed to fetch league data")
        raise ValueError("Could not fetch league data from Sleeper API")
    
    league_record = {
        'league_id': league_data['league_id'],
        'name': league_data['name'],
        'season': league_data['season'],
        'status': league_data['status'],
        'sport': league_data.get('sport', 'nfl'),
        'total_rosters': league_data['total_rosters'],
        'scoring_settings': league_data.get('scoring_settings'),
        'roster_positions': league_data.get('roster_positions'),
        'settings': league_data.get('settings'),
        'metadata': league_data.get('metadata'),
        'updated_at': datetime.now().isoformat()
    }
    
    try:
        result = supabase.table('leagues').upsert(league_record).execute()
        logger.info(f"✓ Synced league: {league_data['name']}")
    except Exception as e:
        logger.error(f"Failed to sync league to database: {e}", exc_info=True)
        raise
    
    return league_data


def sync_users(league_id: str):
    """Sync users to Supabase"""
    print(f"Fetching users...")
    users_data = fetch_users(league_id)
    
    user_records = []
    for user in users_data:
        user_record = {
            'user_id': user['user_id'],
            'league_id': league_id,
            'display_name': user['display_name'],
            'team_name': user.get('metadata', {}).get('team_name'),
            'avatar': user.get('avatar'),
            'metadata': user.get('metadata'),
            'updated_at': datetime.now().isoformat()
        }
        user_records.append(user_record)
    
    if user_records:
        result = supabase.table('users').upsert(user_records).execute()
        print(f"✓ Synced {len(user_records)} users")
    
    return user_records


def sync_rosters(league_id: str):
    """Sync rosters to Supabase"""
    print(f"Fetching rosters...")
    rosters_data = fetch_rosters(league_id)
    
    roster_records = []
    for roster in rosters_data:
        roster_record = {
            'roster_id': roster['roster_id'],
            'league_id': league_id,
            'owner_id': roster.get('owner_id'),
            'players': roster.get('players', []),
            'starters': roster.get('starters', []),
            'reserve': roster.get('reserve', []),
            'taxi': roster.get('taxi', []),
            'wins': roster.get('settings', {}).get('wins', 0),
            'losses': roster.get('settings', {}).get('losses', 0),
            'ties': roster.get('settings', {}).get('ties', 0),
            'fpts': roster.get('settings', {}).get('fpts', 0),
            'fpts_against': roster.get('settings', {}).get('fpts_against', 0),
            'fpts_decimal': roster.get('settings', {}).get('fpts_decimal', 0),
            'fpts_against_decimal': roster.get('settings', {}).get('fpts_against_decimal', 0),
            'waiver_position': roster.get('settings', {}).get('waiver_position'),
            'waiver_budget_used': roster.get('settings', {}).get('waiver_budget_used', 0),
            'total_moves': roster.get('settings', {}).get('total_moves', 0),
            'settings': roster.get('settings'),
            'metadata': roster.get('metadata'),
            'updated_at': datetime.now().isoformat()
        }
        roster_records.append(roster_record)
    
    if roster_records:
        result = supabase.table('rosters').upsert(roster_records).execute()
        print(f"✓ Synced {len(roster_records)} rosters")
    
    return roster_records


def sync_matchups(league_id: str, weeks: list = None):
    """Sync matchups for specified weeks"""
    if weeks is None:
        # Default to weeks 1-18 (full NFL season)
        weeks = range(1, 19)
    
    print(f"Fetching matchups for weeks {min(weeks)}-{max(weeks)}...")
    matchup_records = []
    
    for week in weeks:
        try:
            matchups_data = fetch_matchups(league_id, week)
            
            for matchup in matchups_data:
                matchup_record = {
                    'league_id': league_id,
                    'roster_id': matchup['roster_id'],
                    'matchup_id': matchup['matchup_id'],
                    'week': week,
                    'points': matchup.get('points', 0),
                    'players_points': matchup.get('players_points'),
                    'starters': matchup.get('starters', []),
                    'players': matchup.get('players', []),
                    'custom_points': matchup.get('custom_points'),
                    'updated_at': datetime.now().isoformat()
                }
                matchup_records.append(matchup_record)
            
            print(f"  ✓ Week {week}: {len(matchups_data)} matchups")
        except Exception as e:
            print(f"  ✗ Week {week}: {str(e)}")
    
    if matchup_records:
        result = supabase.table('matchups').upsert(matchup_records).execute()
        print(f"✓ Synced {len(matchup_records)} total matchups")
    
    return matchup_records


def sync_transactions(league_id: str, weeks: list = None):
    """Sync transactions for specified weeks"""
    if weeks is None:
        weeks = range(1, 19)
    
    print(f"Fetching transactions for weeks {min(weeks)}-{max(weeks)}...")
    transaction_records = []
    
    for week in weeks:
        try:
            transactions_data = fetch_transactions(league_id, week)
            
            for transaction in transactions_data:
                transaction_record = {
                    'transaction_id': transaction['transaction_id'],
                    'league_id': league_id,
                    'type': transaction.get('type'),
                    'status': transaction.get('status'),
                    'week': week,
                    'creator': transaction.get('creator'),
                    'adds': transaction.get('adds'),
                    'drops': transaction.get('drops'),
                    'draft_picks': transaction.get('draft_picks', []),
                    'waiver_budget': transaction.get('waiver_budget', []),
                    'settings': transaction.get('settings'),
                    'metadata': transaction.get('metadata'),
                    'roster_ids': transaction.get('roster_ids', []),
                    'created': transaction.get('created'),
                    'status_updated': transaction.get('status_updated')
                }
                transaction_records.append(transaction_record)
            
            if transactions_data:
                print(f"  ✓ Week {week}: {len(transactions_data)} transactions")
        except Exception as e:
            # Some weeks may not have transactions
            pass
    
    if transaction_records:
        result = supabase.table('transactions').upsert(transaction_records).execute()
        print(f"✓ Synced {len(transaction_records)} total transactions")
    
    return transaction_records


def sync_players(limit: int = None):
    """Sync player data to Supabase"""
    print(f"Fetching NFL players data (this may take a moment)...")
    players_data = fetch_all_players()
    
    player_records = []
    count = 0
    for player_id, player in players_data.items():
        if limit and count >= limit:
            break
            
        # Only sync relevant players (not free agents without positions)
        if player.get('position') in ['QB', 'RB', 'WR', 'TE', 'K', 'DEF']:
            player_record = {
                'player_id': player_id,
                'full_name': player.get('full_name'),
                'first_name': player.get('first_name'),
                'last_name': player.get('last_name'),
                'position': player.get('position'),
                'team': player.get('team'),
                'status': player.get('status'),
                'injury_status': player.get('injury_status'),
                'age': player.get('age'),
                'years_exp': player.get('years_exp'),
                'metadata': {
                    'number': player.get('number'),
                    'height': player.get('height'),
                    'weight': player.get('weight'),
                    'college': player.get('college'),
                    'fantasy_positions': player.get('fantasy_positions')
                },
                'updated_at': datetime.now().isoformat()
            }
            player_records.append(player_record)
            count += 1
    
    # Insert in batches to avoid timeout
    batch_size = 500
    total_synced = 0
    for i in range(0, len(player_records), batch_size):
        batch = player_records[i:i + batch_size]
        result = supabase.table('players').upsert(batch).execute()
        total_synced += len(batch)
        print(f"  ✓ Synced {total_synced}/{len(player_records)} players")
    
    print(f"✓ Synced {total_synced} total players")
    return player_records


def full_sync(league_id: str, current_week: int = 7):
    """Perform a full sync of all league data"""
    logger.info("="*60)
    logger.info("🏈 SLEEPER FANTASY LEAGUE DATA SYNC")
    logger.info("="*60)
    
    try:
        # Sync core data
        league_data = sync_league(league_id)
        
        sync_users(league_id)
        
        sync_rosters(league_id)
        
        # Sync matchups for completed weeks
        sync_matchups(league_id, weeks=range(1, current_week + 1))
        
        # Sync transactions
        sync_transactions(league_id, weeks=range(1, current_week + 1))
        
        # Sync player data
        logger.info("Syncing player database...")
        sync_players()
        
        logger.info("="*60)
        logger.info("✅ SYNC COMPLETE!")
        logger.info("="*60)
        logger.info(f"League: {league_data['name']}")
        logger.info(f"Season: {league_data['season']}")
        logger.info(f"Status: {league_data['status']}")
        logger.info("Your data is now ready in Supabase! 🚀")
        
    except Exception as e:
        logger.error("="*60)
        logger.error("❌ SYNC FAILED!")
        logger.error("="*60)
        logger.error(f"Error: {str(e)}", exc_info=True)
        logger.error("Please check the logs and try again.")
        raise


if __name__ == "__main__":
    # Run full sync
    full_sync(SLEEPER_LEAGUE_ID, current_week=7)

