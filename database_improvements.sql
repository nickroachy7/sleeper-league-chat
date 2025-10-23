-- Database Performance Improvements
-- Add indexes for frequently queried columns

-- Enable pg_trgm extension for fuzzy text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Players table indexes
-- GIN index for fuzzy player name searches (ILIKE queries)
CREATE INDEX IF NOT EXISTS idx_players_full_name_gin 
ON players USING gin(full_name gin_trgm_ops);

-- Index for position filtering
CREATE INDEX IF NOT EXISTS idx_players_position 
ON players(position) WHERE position IS NOT NULL;

-- Index for team filtering
CREATE INDEX IF NOT EXISTS idx_players_team 
ON players(team) WHERE team IS NOT NULL;

-- Composite index for position and team searches
CREATE INDEX IF NOT EXISTS idx_players_position_team 
ON players(position, team) WHERE position IS NOT NULL AND team IS NOT NULL;

-- Matchups table indexes
-- Index for week lookups (very common)
CREATE INDEX IF NOT EXISTS idx_matchups_week 
ON matchups(week);

-- Index for roster_id lookups
CREATE INDEX IF NOT EXISTS idx_matchups_roster_id 
ON matchups(roster_id);

-- Composite index for league + week queries
CREATE INDEX IF NOT EXISTS idx_matchups_league_week 
ON matchups(league_id, week);

-- Transactions table indexes
-- Index for transaction type filtering
CREATE INDEX IF NOT EXISTS idx_transactions_type 
ON transactions(type);

-- Index for week lookups
CREATE INDEX IF NOT EXISTS idx_transactions_week 
ON transactions(week) WHERE week IS NOT NULL;

-- Composite index for league + week queries
CREATE INDEX IF NOT EXISTS idx_transactions_league_week 
ON transactions(league_id, week);

-- Index for status filtering
CREATE INDEX IF NOT EXISTS idx_transactions_status 
ON transactions(status);

-- Rosters table indexes
-- Index for owner_id lookups
CREATE INDEX IF NOT EXISTS idx_rosters_owner_id 
ON rosters(owner_id);

-- Users table indexes  
-- Index for display name lookups
CREATE INDEX IF NOT EXISTS idx_users_display_name 
ON users(display_name);

-- Index for team name lookups
CREATE INDEX IF NOT EXISTS idx_users_team_name 
ON users(team_name) WHERE team_name IS NOT NULL;

-- Add updated_at index to all tables for cache invalidation
CREATE INDEX IF NOT EXISTS idx_leagues_updated_at ON leagues(updated_at);
CREATE INDEX IF NOT EXISTS idx_users_updated_at ON users(updated_at);
CREATE INDEX IF NOT EXISTS idx_rosters_updated_at ON rosters(updated_at);
CREATE INDEX IF NOT EXISTS idx_players_updated_at ON players(updated_at);
CREATE INDEX IF NOT EXISTS idx_matchups_updated_at ON matchups(updated_at);

-- Create view for standings (commonly queried)
CREATE OR REPLACE VIEW current_standings AS
SELECT 
    r.roster_id,
    r.wins,
    r.losses,
    r.ties,
    (r.fpts + COALESCE(r.fpts_decimal, 0)::numeric / 100) as total_points,
    (r.fpts_against + COALESCE(r.fpts_against_decimal, 0)::numeric / 100) as total_points_against,
    u.display_name,
    u.team_name,
    u.avatar,
    r.league_id
FROM rosters r
LEFT JOIN users u ON r.owner_id = u.user_id
ORDER BY r.wins DESC, total_points DESC;

-- Performance analysis queries (for monitoring)
COMMENT ON INDEX idx_players_full_name_gin IS 'Improves player name search performance';
COMMENT ON INDEX idx_matchups_week IS 'Improves weekly matchup queries';
COMMENT ON INDEX idx_transactions_league_week IS 'Improves transaction history queries';

-- Vacuum analyze to update statistics
VACUUM ANALYZE players;
VACUUM ANALYZE matchups;
VACUUM ANALYZE transactions;
VACUUM ANALYZE rosters;
VACUUM ANALYZE users;
VACUUM ANALYZE leagues;

-- Success message
DO $$ 
BEGIN 
    RAISE NOTICE '✅ Database indexes created successfully!';
    RAISE NOTICE '📊 Query performance should be significantly improved.';
END $$;





