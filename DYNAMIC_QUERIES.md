# Dynamic Query System

## Overview

The assistant now uses **dynamic database queries** instead of predefined functions. This gives the AI much more flexibility to answer complex questions without you having to write new functions for every query pattern.

## What Changed

### Before
- Had 9 predefined functions (`get_standings`, `get_team_roster`, `get_matchup_results`, etc.)
- Each function had hardcoded SQL queries
- Adding new query capabilities required writing new Python functions

### After  
- Has 3 flexible functions that the AI can use dynamically:
  - `list_tables()` - See what tables exist
  - `describe_table(table_name)` - See columns and types for a table
  - `query_with_filters(table, filters, ...)` - Query any table with custom filters

## How It Works

1. **User asks a question**: "What are the current standings?"

2. **AI decides which tools to use**:
   - It knows the database schema (from the system prompt)
   - It calls `query_with_filters()` with the right parameters

3. **Query is executed**:
   ```python
   query_with_filters(
       table="rosters",
       select_columns="*, users(team_name, display_name)",  # PostgREST join syntax
       filters={"league_id": "1180365427496943616"},
       order_column="wins",
       order_desc=True
   )
   ```

4. **Results are returned** and formatted by the AI

## Key Features

### PostgREST Joins
The AI can fetch related data in a single query using PostgREST syntax:
```python
select_columns="*, users(team_name, display_name)"
# This joins the users table and includes team_name and display_name
```

### Flexible Filtering
```python
filters={
    "league_id": "xxx",
    "week": 5,
    "type": "trade"
}
```

### Sorting and Limiting
```python
order_column="wins",
order_desc=True,
limit=10
```

## Benefits

1. **More Flexible**: AI can answer questions you didn't anticipate
2. **Less Code**: No need to maintain dozens of query functions
3. **Easier Updates**: Just update table schemas if database changes
4. **More Natural**: AI constructs queries based on what the user asks

## File Structure

- `dynamic_queries.py` - Core query functions and schema definitions
- `fantasy_assistant.py` - OpenAI integration using dynamic queries
- `league_queries.py` - OLD predefined functions (can be removed if no longer needed)

## Example Queries the AI Can Now Handle

- "Show me all trades from week 5"
- "Which teams have the most points against?"
- "Find all transactions involving player X"
- "Show matchups where teams scored over 100 points"
- "List all QBs on rosters in our league"

The AI figures out how to query the database dynamically!

## Comparison to MCP Approach

You asked about using Supabase MCP. While MCP is powerful, it's designed for **client-side AI tools** (like Cursor, Claude Desktop) that run locally and can spawn processes.

Our approach gives you the **same flexibility** (dynamic SQL queries) but:
- ✅ Works with your existing OpenAI setup
- ✅ No need for local MCP process management  
- ✅ Runs in your Python API server
- ✅ Easier to deploy and scale

## Testing

Test the assistant:
```bash
python3 fantasy_assistant.py
```

Then try queries like:
- "What tables are available?"
- "Show me the current standings"
- "What were the matchup results from week 6?"
- "Show me recent trades"

## Next Steps

If you want even more power, you could:
1. Add a `execute_raw_sql()` function (with safety checks)
2. Add more complex filter operations (ILIKE, IN, etc.)
3. Add aggregation functions (SUM, AVG, COUNT)

But the current system should handle 90% of your queries!


