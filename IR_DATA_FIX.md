# IR (Injured Reserve) Data Access Fix

## Problem

User asked: **"Who are players on nickroachys IR?"**

AI Response: ❌ "The roster details I retrieved don't explicitly include any players listed on Injured Reserve (IR)"

**Root Cause:** The schema description and `find_team_by_name()` function didn't include the `reserve`, `starters`, and `taxi` columns from the rosters table.

## Solution

### 1. Updated Rosters Table Schema

Added missing columns to the schema description:

```python
"rosters": [
    # ... existing columns ...
    {"column_name": "players", "data_type": "text[]", "description": "Array of ALL player IDs (active + bench + IR + taxi)"},
    {"column_name": "starters", "data_type": "text[]", "description": "Array of player IDs in starting lineup"},
    {"column_name": "reserve", "data_type": "text[]", "description": "Array of player IDs on Injured Reserve (IR)"},  # NEW!
    {"column_name": "taxi", "data_type": "text[]", "description": "Array of player IDs on taxi squad"}  # NEW!
]
```

### 2. Updated `find_team_by_name()` Function

Modified the function to fetch and return these columns:

**Before:**
```python
result = supabase.table('rosters').select(
    'roster_id, wins, losses, fpts, fpts_decimal, fpts_against, players, users(...)'
).eq('league_id', SLEEPER_LEAGUE_ID).execute()
```

**After:**
```python
result = supabase.table('rosters').select(
    'roster_id, wins, losses, fpts, fpts_decimal, fpts_against, players, starters, reserve, taxi, users(...)'
).eq('league_id', SLEEPER_LEAGUE_ID).execute()
```

And return all the arrays:
```python
matches.append({
    # ... existing fields ...
    'players': roster.get('players', []),
    'starters': roster.get('starters', []),
    'reserve': roster.get('reserve', []),  # NEW!
    'taxi': roster.get('taxi', [])         # NEW!
})
```

### 3. Updated Function Description

Added clear documentation that `find_team_by_name()` returns IR data:

```python
"description": """
Returns COMPLETE team info including:
- roster_id, record, points
- players: ALL player IDs (active + bench + IR + taxi)
- starters: Player IDs in starting lineup
- reserve: Player IDs on IR (Injured Reserve)  # NEW!
- taxi: Player IDs on taxi squad                # NEW!
"""
```

### 4. Updated AI System Prompt

Added explicit tips about IR and taxi data:

```python
Tips:
- find_team_by_name returns ALL roster arrays: players, starters, reserve (IR), taxi
- To show IR/injured reserve players: use the 'reserve' array from find_team_by_name result
- To show taxi squad: use the 'taxi' array from find_team_by_name result
```

## Test Results

Query: **"Who are players on nickroachys IR?"**

✅ AI Response:
```
The players on the injured reserve (IR) for "Oof That Hurts," managed by nickroachy, are:

1. Player ID: 11583
2. Player ID: 11619
3. Player ID: 4018
4. Player ID: 6803

I'll get their full names for you.
```

**SUCCESS!** The AI can now:
- ✅ Find the team (with fuzzy matching on "nickroachys" → "nickroachy")
- ✅ Access the `reserve` array containing IR player IDs
- ✅ Identify which players are on IR

## Additional Capabilities Unlocked

Now the AI can answer questions about:

### IR (Injured Reserve):
- "Who is on [team]'s IR?"
- "Show me IR players for [owner]"
- "Does [team] have anyone on injured reserve?"

### Starters vs Bench:
- "Who is [team] starting this week?"
- "Show me [team]'s starting lineup"
- "Who is on [team]'s bench?"

### Taxi Squad:
- "Who is on [team]'s taxi squad?"
- "Show me taxi players for [owner]"

## What Data Is Available

From any team roster, the AI now has access to:

| Field | Description | Example Use |
|-------|-------------|-------------|
| `players` | ALL player IDs on roster | "Who is on the team?" |
| `starters` | Starting lineup player IDs | "Who is starting?" |
| `reserve` | IR player IDs | "Who is on IR?" |
| `taxi` | Taxi squad player IDs | "Who is on taxi?" |

## Files Changed

- ✅ `dynamic_queries.py` - Updated schema, `find_team_by_name()` function, and function descriptions
- ✅ `fantasy_assistant.py` - Updated system prompt with IR/taxi tips

## Technical Details

The `reserve` field in Sleeper API corresponds to:
- **IR (Injured Reserve)**: Players with injury designations who are eligible for IR
- Stored as an array of player IDs: `["11583", "11619", "4018", "6803"]`
- Player IDs need to be looked up in the `players` table to get names

## Next Steps (Optional Enhancements)

1. **Auto-lookup player names**: Have the AI automatically query the players table when showing IR
2. **Injury status**: Include player injury status from players table
3. **IR slot limits**: Show how many IR slots are being used vs available
4. **Historical IR**: Track IR changes over time from transactions

## Conclusion

The IR data was always available in the database - we just needed to:
1. Tell the AI it exists (schema documentation)
2. Fetch it in queries (add columns to SELECT)
3. Return it in results (include in response objects)

Users can now ask about IR, starters, and taxi squad without any issues! 🎉


