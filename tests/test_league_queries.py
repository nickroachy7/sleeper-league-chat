"""
Unit tests for league query functions
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from league_queries import (
    get_league_info,
    get_standings,
    get_team_roster,
    get_matchup_results,
    get_top_scorers,
    get_player_ownership,
    get_playoff_picture
)


@pytest.fixture
def mock_supabase():
    """Mock Supabase client"""
    with patch('league_queries.get_supabase_client') as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


class TestGetLeagueInfo:
    """Tests for get_league_info function"""
    
    def test_get_league_info_success(self, mock_supabase):
        """Test successful league info retrieval"""
        mock_supabase.table().select().eq().execute.return_value.data = [{
            'league_id': '123',
            'name': 'Test League',
            'season': '2025',
            'status': 'in_season'
        }]
        
        result = get_league_info()
        
        assert result['name'] == 'Test League'
        assert result['season'] == '2025'
    
    def test_get_league_info_empty(self, mock_supabase):
        """Test league info with no data"""
        mock_supabase.table().select().eq().execute.return_value.data = []
        
        result = get_league_info()
        
        assert result == {}


class TestGetStandings:
    """Tests for get_standings function"""
    
    def test_get_standings_sorts_correctly(self, mock_supabase):
        """Test that standings are sorted by wins then points"""
        mock_supabase.table().select().eq().execute.return_value.data = [
            {
                'roster_id': 1,
                'wins': 5,
                'losses': 2,
                'ties': 0,
                'fpts': 800,
                'fpts_against': 700,
                'users': {'team_name': 'Team A', 'display_name': 'User A'}
            },
            {
                'roster_id': 2,
                'wins': 6,
                'losses': 1,
                'ties': 0,
                'fpts': 750,
                'fpts_against': 650,
                'users': {'team_name': 'Team B', 'display_name': 'User B'}
            }
        ]
        
        result = get_standings()
        
        # Team B should be first (more wins)
        assert result[0]['team_name'] == 'Team B'
        assert result[0]['wins'] == 6
        assert result[1]['team_name'] == 'Team A'


class TestGetTeamRoster:
    """Tests for get_team_roster function"""
    
    def test_get_team_roster_found(self, mock_supabase):
        """Test finding a team roster by name"""
        roster_data = {
            'roster_id': 1,
            'wins': 5,
            'losses': 2,
            'fpts': 800,
            'starters': ['player1', 'player2'],
            'players': ['player1', 'player2', 'player3'],
            'users': {'team_name': 'Test Team', 'display_name': 'Test User'}
        }
        
        player_data = [
            {'player_id': 'player1', 'full_name': 'Player One', 'position': 'QB', 'team': 'KC'},
            {'player_id': 'player2', 'full_name': 'Player Two', 'position': 'RB', 'team': 'SF'},
            {'player_id': 'player3', 'full_name': 'Player Three', 'position': 'WR', 'team': 'BUF'}
        ]
        
        # Mock the roster query
        mock_supabase.table().select().eq().execute.return_value.data = [roster_data]
        
        # Mock the players query
        mock_supabase.table().select().in_().execute.return_value.data = player_data
        
        result = get_team_roster(team_name='Test')
        
        assert result['team_name'] == 'Test Team'
        assert result['record'] == '5-2'
        assert len(result['starters']) == 2
        assert len(result['bench']) == 1
    
    def test_get_team_roster_not_found(self, mock_supabase):
        """Test roster lookup for non-existent team"""
        mock_supabase.table().select().eq().execute.return_value.data = []
        
        result = get_team_roster(team_name='Nonexistent')
        
        assert 'error' in result
        assert result['error'] == 'Team not found'


class TestGetMatchupResults:
    """Tests for get_matchup_results function"""
    
    def test_get_matchup_results_pairs_teams(self, mock_supabase):
        """Test that matchups are correctly paired"""
        matchup_data = [
            {'roster_id': 1, 'matchup_id': 1, 'points': 120.5, 'week': 5},
            {'roster_id': 2, 'matchup_id': 1, 'points': 110.0, 'week': 5}
        ]
        
        roster_data = [
            {'roster_id': 1, 'users': {'team_name': 'Team A'}},
            {'roster_id': 2, 'users': {'team_name': 'Team B'}}
        ]
        
        mock_supabase.table().select().eq().eq().execute.return_value.data = matchup_data
        mock_supabase.table().select().eq().execute.return_value.data = roster_data
        
        result = get_matchup_results(week=5)
        
        assert len(result) == 1
        assert result[0]['winner'] == 'Team A'
        assert result[0]['team1_points'] == 120.5


class TestGetPlayerOwnership:
    """Tests for get_player_ownership function"""
    
    def test_get_player_ownership_found(self, mock_supabase):
        """Test finding player ownership"""
        player_data = [{
            'player_id': 'player123',
            'full_name': 'Patrick Mahomes',
            'position': 'QB',
            'team': 'KC'
        }]
        
        roster_data = [{
            'roster_id': 1,
            'players': ['player123', 'other_player'],
            'users': {'team_name': 'My Team', 'display_name': 'My User'}
        }]
        
        # Mock player search
        select_mock = MagicMock()
        select_mock.ilike().limit().execute.return_value.data = player_data
        mock_supabase.table.return_value.select.return_value = select_mock
        
        # Mock roster search
        mock_supabase.table().select().eq().execute.return_value.data = roster_data
        
        result = get_player_ownership('Mahomes')
        
        assert result['player'] == 'Patrick Mahomes'
        assert result['owned_by'] == 'My Team'


def test_get_playoff_picture(mock_supabase):
    """Test playoff picture generation"""
    standings_data = [
        {'roster_id': i, 'wins': 7-i, 'losses': i, 'ties': 0, 'fpts': 900-i*10, 'fpts_against': 800,
         'users': {'team_name': f'Team {i}', 'display_name': f'User {i}'}}
        for i in range(8)
    ]
    
    league_data = [{
        'settings': {'playoff_teams': 6}
    }]
    
    mock_supabase.table().select().eq().execute.return_value.data = standings_data
    mock_supabase.table().select().eq().execute.return_value.data = league_data
    
    result = get_playoff_picture()
    
    assert len(result['playoff_teams']) == 6
    assert len(result['bubble_teams']) == 2
    assert result['playoff_spots'] == 6


if __name__ == '__main__':
    pytest.main([__file__, '-v'])





