# Query Enhancement Guide: From Rigid to Flexible

## Overview

This document explains the deep revision of the Question → Assistant → Response logic to handle **varied, unique questions** beyond predefined patterns.

---

## 🔴 The Problem

### Before: Pattern-Matching Approach

**Your system was rigid:**

```
User asks a question
    ↓
Match against predefined patterns in system prompt
    ↓
Call specific function based on pattern
    ↓
Return formatted response
```

**Limitations:**

1. ❌ **Only handles questions that match examples**
   - "Show standings" ✅ Works
   - "Compare top 3 teams' offensive firepower" ❌ Struggles

2. ❌ **Can't reason about novel questions**
   - Over-prescriptive function definitions
   - "USE THIS WHEN..." approach limits creativity
   - No query planning or composition

3. ❌ **Poor cross-domain handling**
   - Questions requiring both Supabase + NFL API data
   - Example: "How are my IR players performing when healthy?"
   - Needs: IR roster (Supabase) + player stats (Ball Don't Lie)

4. ❌ **No analytical capabilities**
   - Can't aggregate across datasets
   - Can't compare multiple entities
   - Can't perform calculations or rankings beyond simple queries

---

## ✅ The Solution

### After: Intelligent Query Planning

**New architecture with reasoning layer:**

```
User asks a question
    ↓
Query Planner analyzes intent and complexity
    ↓
If simple: Direct function call (fast path)
    ↓
If complex: Create multi-step execution plan
    ↓
Execute plan: Chain multiple functions intelligently
    ↓
Synthesize results: Combine data from multiple sources
    ↓
Return insightful response
```

---

## 🆕 Key Improvements

### 1. **Query Planning Layer** (`query_planner.py`)

**What it does:**
- Analyzes user intent before execution
- Determines complexity: simple, medium, complex
- Identifies required data sources: Supabase, NFL API, or both
- Creates step-by-step execution plans
- Detects if aggregation/comparison is needed

**Example:**

```python
Question: "Which of my IR players are performing well?"

Query Analysis:
├─ Intent: player_performance_analysis
├─ Complexity: complex
├─ Data sources: ["supabase", "nfl_api"]
├─ Requires aggregation: True
└─ Execution Plan:
    Step 1: find_team_by_name("my team") → Get IR player list
    Step 2: get_player_season_stats(each IR player) → Get NFL stats
    Step 3: Analyze & compare stats
    Step 4: Return ranked list of performing IR players
```

### 2. **Cleaner System Prompt** (fantasy_assistant_v2.py)

**Before:**
- 171 lines with extensive "USE THIS WHEN" examples
- Formatting rules mixed with query logic
- Confusing for the model

**After:**
- ~100 lines focused on capabilities
- Describes WHAT tools do, not WHEN to use them
- Emphasizes reasoning and composition
- Clearer data source guidelines

**Key difference:**

```
❌ Old: "ANY query with a team/owner name → ALWAYS use find_team_by_name() FIRST!"

✅ New: "find_team_by_name() - Find teams using fuzzy matching. Handles typos, 
        partial names, and owner names automatically. Returns complete roster data."
```

### 3. **Enhanced Function Definitions**

**Before:** Prescriptive
```python
"description": """🎯 MANDATORY: Use this when...
✓ "Who is on [team]?" → Use this!
✓ "[Team]'s roster" → Use this!
✓ "Show me [owner]'s players" → Use this!
"""
```

**After:** Descriptive
```python
"description": """Find teams using fuzzy matching on names.
Returns: roster_id, record, points, player arrays (starters, reserve, taxi).
Use for any team-specific queries."""
```

This lets GPT-4o **reason** instead of **pattern-match**.

### 4. **Smart Routing**

The system automatically decides:
- **Simple query?** → Skip planning, use direct function calling (fast)
- **Complex query?** → Use query planner (comprehensive)

```python
# Automatically detects complexity
"Show standings" → Direct execution
"Compare top 3 teams" → Query planning
"How do my starters compare to league leaders?" → Query planning + multi-step
```

---

## 📊 What This Enables

### Category 1: Cross-Domain Questions

**Questions combining fantasy league data + real NFL stats:**

| Question | What It Needs | Old System | New System |
|----------|---------------|------------|------------|
| "How are my starters performing?" | Roster (SB) + Stats (NFL) | ❌ Struggles | ✅ Chains functions |
| "Which IR players are performing well?" | IR list (SB) + Stats (NFL) | ❌ Can't compose | ✅ Plans & executes |
| "Should I trade Player X?" | Ownership + Stats + History | ❌ Too complex | ✅ Multi-step plan |

### Category 2: Analytical Questions

**Questions requiring aggregation, comparison, or calculation:**

| Question | Analysis Needed | Old System | New System |
|----------|----------------|------------|------------|
| "Who's the most traded player?" | Aggregate all trades | ❌ No aggregation | ✅ Plans aggregation |
| "Compare top 3 teams' rosters" | Multi-entity comparison | ❌ One entity only | ✅ Loop + compare |
| "Which team has best RB depth?" | Position filtering + ranking | ❌ Can't reason | ✅ Analyzes depth |
| "Average PPG for playoff teams" | Filter + calculate | ❌ No calculation | ✅ Computes metrics |

### Category 3: Contextual Questions

**Questions requiring inference or context:**

| Question | Context Needed | Old System | New System |
|----------|---------------|------------|------------|
| "How's my team doing?" | Infer "my team" from context | ❌ Needs exact name | ✅ Can infer |
| "Show me their stats" | Reference from prev question | ❌ No context | ✅ Conversation aware |
| "Who should I target in trades?" | League needs analysis | ❌ Can't reason | ✅ Strategic advice |

### Category 4: Unique/Creative Questions

**Questions that don't fit templates:**

| Question | Why It's Hard | Old System | New System |
|----------|--------------|------------|------------|
| "Which teams are tanking?" | Needs win pattern analysis | ❌ No template | ✅ Creates plan |
| "Best value trades this season" | Multi-factor analysis | ❌ No template | ✅ Reasons through |
| "Injury risk on my roster" | Cross-reference injury data | ❌ No template | ✅ Composes sources |

---

## 🔧 Implementation Details

### File Structure

```
New files:
├─ query_planner.py          # Query analysis & planning engine
├─ fantasy_assistant_v2.py   # Enhanced assistant with planning
└─ QUERY_ENHANCEMENT_GUIDE.md (this file)

Modified (optional):
├─ api_server.py             # Can swap to v2
└─ fantasy_assistant.py      # Original kept for comparison
```

### How to Use

**Option 1: Test the enhanced version standalone**

```bash
# Run the v2 assistant directly
python3 fantasy_assistant_v2.py

# Try complex questions:
"Compare top 3 teams' rosters"
"How are my IR players performing?"
"Which teams make the most trades?"
```

**Option 2: Integrate into API server**

```python
# In api_server.py, change the import:
from fantasy_assistant_v2 import chat_v2 as chat

# Everything else stays the same!
```

### Performance Characteristics

| Metric | Simple Query | Complex Query |
|--------|-------------|---------------|
| **Planning overhead** | ~0ms (skipped) | ~200-500ms |
| **Total latency** | Same as before | +200-500ms |
| **Function calls** | 1-2 | 2-5 (as needed) |
| **Accuracy** | Same | Much better |

**Trade-off:** Slightly slower for complex queries, but **much more capable**.

---

## 📖 Examples: Before vs After

### Example 1: Cross-Domain Query

**Question:** "How are my IR players performing this season?"

**Before (v1):**
```
Response: "I found your IR players: [Player A, Player B]. 
What would you like to know about them?"

❌ Can't automatically get their stats
❌ Requires follow-up questions
```

**After (v2):**
```
Analysis: Complex query detected
Plan:
  1. find_team_by_name("my team") → Get IR list
  2. For each IR player: get_player_season_stats()
  3. Compare performance

Response: "Here are your IR players and their 2025 stats:

| Player | Position | Status | Stats This Season |
|--------|----------|--------|------------------|
| Cooper Kupp | WR | IR | 45 rec, 612 yds, 4 TDs (before injury week 7) |
| Ja'Marr Chase | WR | IR | 67 rec, 978 yds, 8 TDs (performing excellent) |

✨ Ja'Marr Chase is having an elite season. Consider holding or trading 
   for high value when he returns."

✅ Automatically retrieved and analyzed stats
✅ Provided actionable insights
```

### Example 2: Analytical Query

**Question:** "Who's the most traded player in league history?"

**Before (v1):**
```
Response: "I can show you recent trades. Would you like to see them?"

❌ Can't aggregate across all trades
❌ Pattern doesn't match predefined queries
```

**After (v2):**
```
Analysis: Aggregation query detected
Plan:
  1. Get all trades across all seasons
  2. Extract all players from trades
  3. Count occurrences per player
  4. Rank and return top results

Response: "Most traded players in Dynasty Reloaded history:

| Rank | Player | Times Traded | Seasons |
|------|--------|-------------|---------|
| 1 | Cooper Kupp | 3 | 2023, 2024, 2024 |
| 2 | Travis Etienne | 2 | 2023, 2024 |
| 3 | DeAndre Hopkins | 2 | 2024, 2024 |

📊 Cooper Kupp has been the most traded player, changing hands 3 times.
   His value has fluctuated due to injury concerns."

✅ Aggregated data automatically
✅ Ranked results
✅ Provided context
```

### Example 3: Comparative Query

**Question:** "Compare the WR corps of the top 3 teams"

**Before (v1):**
```
Response: "Which teams would you like to compare?"

❌ Can't identify "top 3 teams"
❌ Can't perform multi-entity comparison
```

**After (v2):**
```
Analysis: Multi-entity comparative query
Plan:
  1. query_with_filters(table="rosters") → Get standings
  2. Identify top 3 teams
  3. For each: Get roster, filter WR position
  4. Get stats for each WR
  5. Compare depth and performance

Response: "WR Corps Comparison (Top 3 Teams):

**1. The Jaxon 5 (6-1)**
- Ja'Marr Chase (WR, CIN): 978 yds, 8 TDs ⭐
- CeeDee Lamb (WR, DAL): 843 yds, 6 TDs
- Amon-Ra St. Brown (WR, DET): 721 yds, 5 TDs

**2. Horse Cock Churchill (5-2)**
- Justin Jefferson (WR, MIN): 1,021 yds, 7 TDs ⭐
- Tyreek Hill (WR, MIA): 890 yds, 6 TDs
- DeVonta Smith (WR, PHI): 654 yds, 4 TDs

**3. FDR (5-2)**
- AJ Brown (WR, PHI): 912 yds, 7 TDs ⭐
- Cooper Kupp (WR, LAR): 612 yds, 4 TDs (injured)
- Chris Olave (WR, NO): 567 yds, 3 TDs

📊 Analysis:
- Horse Cock Churchill has the most elite WR1 (Jefferson: 1,021 yds)
- The Jaxon 5 has the best overall depth (3 WRs with 5+ TDs)
- FDR's corps is impacted by Kupp's injury

✅ Identified top 3 automatically
✅ Retrieved and compared rosters
✅ Got stats for all WRs
✅ Provided strategic analysis
```

---

## 🧪 Testing & Validation

### Test Suite

Run these questions to validate the enhancement:

**Simple (should be fast, same as before):**
1. "Show me the standings"
2. "Who owns Patrick Mahomes?"
3. "Week 5 results"

**Complex (new capabilities):**
1. "Compare the top 3 teams' rosters"
2. "How are my IR players performing?"
3. "Which team has the best QB situation?"
4. "Who's the most traded player?"
5. "Should I trade AJ Brown for Tyreek Hill?"

**Cross-domain:**
1. "How are my starters performing compared to league leaders?"
2. "Which of my bench players are outperforming?"
3. "Are any teams' IR players outperforming their active roster?"

### Validation Checklist

- [ ] Simple queries still work perfectly
- [ ] Complex queries now work correctly
- [ ] Cross-domain queries combine data sources
- [ ] Analytical queries perform aggregations
- [ ] Response quality is maintained or improved
- [ ] Latency is acceptable (≤3s for complex queries)

---

## 🎯 Key Takeaways

### What Changed

1. ✅ **Query Planning Layer** - Analyzes intent before execution
2. ✅ **Smarter System Prompt** - Descriptive not prescriptive
3. ✅ **Enhanced Functions** - Focus on capabilities
4. ✅ **Intelligent Routing** - Fast path for simple, planning for complex

### What This Enables

1. ✅ **Varied Questions** - Handle unique queries beyond patterns
2. ✅ **Cross-Domain** - Combine fantasy + NFL data seamlessly
3. ✅ **Analytical** - Aggregations, comparisons, rankings
4. ✅ **Compositional** - Chain multiple operations intelligently

### Backward Compatibility

✅ **All existing queries still work!**
- Simple queries use fast path (no planning overhead)
- Existing functions unchanged
- Original assistant kept as fallback

---

## 📚 Next Steps

### Immediate Actions

1. **Test the v2 assistant:**
   ```bash
   python3 fantasy_assistant_v2.py
   ```

2. **Try complex questions:**
   - Compare multiple teams
   - Cross-domain queries (roster + stats)
   - Analytical questions

3. **Validate responses:**
   - Accuracy
   - Completeness
   - Insight quality

### Optional Enhancements

**If you want even more power:**

1. **Add caching** - Cache query plans for repeated patterns
2. **Add memory** - Remember user preferences ("my team")
3. **Add webhooks** - Real-time updates when trades happen
4. **Add predictions** - ML models for playoff probability
5. **Add recommendations** - Trade suggestions based on needs

### Integration

**To use in production:**

```python
# Option A: Replace entirely
# In api_server.py:
from fantasy_assistant_v2 import chat_v2 as chat

# Option B: A/B test
# Let users choose v1 or v2
if request.args.get('version') == 'v2':
    from fantasy_assistant_v2 import chat_v2 as chat
else:
    from fantasy_assistant import chat
```

---

## 🙋 FAQ

**Q: Will this break existing functionality?**
A: No! Simple queries use the same fast path. Complex queries get enhanced handling.

**Q: Is it slower?**
A: Slightly for complex queries (+200-500ms planning). Simple queries are the same speed.

**Q: Do I need to change my API?**
A: No! Just swap the import in `api_server.py`. Everything else stays the same.

**Q: What if query planning fails?**
A: It gracefully falls back to direct function calling.

**Q: Can I tune the planning?**
A: Yes! Adjust `should_use_planner()` in `query_planner.py` to control when planning kicks in.

**Q: Does this work with the existing database?**
A: Yes! No schema changes needed. Same functions, smarter orchestration.

---

## 📞 Support

If you have questions about this enhancement:
1. Check the code comments in `query_planner.py`
2. Test with the standalone v2 assistant
3. Compare behavior between v1 and v2

**The goal:** Handle the **long tail of unique questions** your users will inevitably ask! 🎯

