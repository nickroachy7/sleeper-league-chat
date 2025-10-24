"""
Intelligent Query Planning Layer for Fantasy Assistant

This module acts as a reasoning layer between user questions and function execution.
It analyzes user intent, plans the necessary data retrieval steps, and orchestrates
multiple data sources intelligently.

Architecture:
    User Question → Query Planner → Data Retrieval Plan → Execute → Synthesize → Response
"""

from typing import Dict, Any, List, Optional, Tuple
from openai import OpenAI
import json
from config import OPENAI_API_KEY
from logger_config import setup_logger

logger = setup_logger('query_planner')
client = OpenAI(api_key=OPENAI_API_KEY)


class QueryIntent:
    """Structured representation of user query intent"""
    
    def __init__(
        self,
        intent_type: str,
        entities: Dict[str, Any],
        data_sources: List[str],
        complexity: str,
        requires_aggregation: bool = False,
        requires_comparison: bool = False
    ):
        self.intent_type = intent_type  # e.g., "roster_lookup", "player_stats", "trade_analysis"
        self.entities = entities  # e.g., {"team_name": "Jaxon 5", "player": "AJ Brown"}
        self.data_sources = data_sources  # ["supabase", "nfl_api"] or just ["supabase"]
        self.complexity = complexity  # "simple", "medium", "complex"
        self.requires_aggregation = requires_aggregation
        self.requires_comparison = requires_comparison
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent_type": self.intent_type,
            "entities": self.entities,
            "data_sources": self.data_sources,
            "complexity": self.complexity,
            "requires_aggregation": self.requires_aggregation,
            "requires_comparison": self.requires_comparison
        }


class QueryPlan:
    """Execution plan for answering a user query"""
    
    def __init__(
        self,
        steps: List[Dict[str, Any]],
        intent: QueryIntent,
        rationale: str
    ):
        self.steps = steps  # List of function calls with dependencies
        self.intent = intent
        self.rationale = rationale  # Explanation of the plan
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "steps": self.steps,
            "intent": self.intent.to_dict(),
            "rationale": self.rationale
        }


PLANNER_SYSTEM_PROMPT = """You are a query planning expert for a fantasy football AI assistant.

Your job is to analyze user questions and create an execution plan to answer them.

AVAILABLE DATA SOURCES:
1. **Supabase (Fantasy League Database)**: Contains league-specific data
   - Tables: leagues, rosters, users, matchups, transactions, players, drafts, draft_picks, traded_picks
   - Use for: standings, rosters, trades, drafts, ownership, matchups, team history
   
2. **Ball Don't Lie API (NFL Stats)**: Real-time NFL player and team statistics
   - Data: player game stats, season stats, team standings, injury reports, leaders
   - Use for: real NFL performance, touchdowns, yards, game results, NFL standings

QUERY ANALYSIS RULES:

1. **Fantasy League Questions** → Supabase only
   Examples:
   - "Who's in first place?" → standings from rosters
   - "Show me my roster" → team lookup
   - "Recent trades" → transactions table
   - "Who owns Mahomes?" → roster/player lookup

2. **Real NFL Stats Questions** → Ball Don't Lie only
   Examples:
   - "How many TDs did AJ Brown score?" → player stats
   - "What are the NFL standings?" → NFL standings API
   - "Is Mahomes injured?" → injury report

3. **Cross-Domain Questions** → Both sources
   Examples:
   - "How are my starters performing?" → rosters (Supabase) + player stats (Ball Don't Lie)
   - "Which IR players are performing well?" → IR list (Supabase) + stats (Ball Don't Lie)

4. **Complex Analysis** → Multiple steps
   Examples:
   - "Who's the most traded player?" → Get all trades, aggregate by player
   - "Compare top 3 teams' rosters" → Get standings, get rosters for top 3, compare
   - "Trade value analysis" → Get player stats + trade history + current ownership

OUTPUT FORMAT:
Return a JSON object with:
{
    "intent_type": "<category>",  // e.g., "roster_lookup", "player_stats", "trade_analysis", "comparative_analysis"
    "entities": {
        // Extracted entities like team names, player names, weeks, etc.
    },
    "data_sources": ["supabase" | "nfl_api"],
    "complexity": "simple" | "medium" | "complex",
    "requires_aggregation": true/false,
    "requires_comparison": true/false,
    "plan": {
        "steps": [
            {
                "step_number": 1,
                "action": "function_name",
                "parameters": {},
                "data_source": "supabase" | "nfl_api",
                "rationale": "Why this step is needed",
                "depends_on": [] // List of step numbers this depends on
            }
        ],
        "rationale": "Overall explanation of the plan"
    }
}

Be concise but complete. Focus on WHAT data is needed, not HOW to format the response.
"""


def analyze_query(user_question: str) -> Tuple[QueryIntent, QueryPlan]:
    """
    Analyze a user question and create an execution plan.
    
    Args:
        user_question: The user's natural language question
        
    Returns:
        Tuple of (QueryIntent, QueryPlan)
    """
    try:
        logger.info(f"Analyzing query: {user_question[:100]}...")
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using mini for faster planning
            messages=[
                {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyze this question and create an execution plan:\n\n{user_question}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.3  # Low temperature for consistent planning
        )
        
        plan_json = json.loads(response.choices[0].message.content)
        
        # Parse into structured objects
        intent = QueryIntent(
            intent_type=plan_json["intent_type"],
            entities=plan_json["entities"],
            data_sources=plan_json["data_sources"],
            complexity=plan_json["complexity"],
            requires_aggregation=plan_json.get("requires_aggregation", False),
            requires_comparison=plan_json.get("requires_comparison", False)
        )
        
        plan = QueryPlan(
            steps=plan_json["plan"]["steps"],
            intent=intent,
            rationale=plan_json["plan"]["rationale"]
        )
        
        logger.info(f"Query analysis complete: {intent.intent_type} ({intent.complexity}), {len(plan.steps)} steps")
        logger.debug(f"Plan: {json.dumps(plan.to_dict(), indent=2)}")
        
        return intent, plan
        
    except Exception as e:
        logger.error(f"Error analyzing query: {e}", exc_info=True)
        # Fallback to direct execution
        return None, None


def should_use_planner(user_question: str) -> bool:
    """
    Determine if a question is complex enough to warrant query planning.
    
    Simple questions can skip planning and go directly to function calling.
    Complex questions benefit from planning.
    
    Args:
        user_question: The user's question
        
    Returns:
        True if planner should be used, False for direct execution
    """
    # Keywords indicating complexity
    complex_indicators = [
        "compare", "vs", "versus", "best", "worst", "most", "least",
        "average", "total", "rank", "top", "bottom",
        "analyze", "breakdown", "trend", "correlation",
        "should i", "recommend", "advice",
        "across", "all", "every", "each"
    ]
    
    # Questions that are typically complex
    question_lower = user_question.lower()
    
    # Check for multiple entities (likely needs multiple lookups)
    has_multiple_entities = (
        ("and" in question_lower or "," in user_question) and
        any(word in question_lower for word in ["player", "team", "stat", "trade"])
    )
    
    # Check for complex indicators
    has_complex_indicator = any(indicator in question_lower for indicator in complex_indicators)
    
    # Questions asking "how" often need multiple steps
    asks_how = question_lower.startswith("how") and len(question_lower.split()) > 5
    
    use_planner = has_multiple_entities or has_complex_indicator or asks_how
    
    logger.debug(f"Planner decision for '{user_question[:50]}...': {use_planner}")
    
    return use_planner


def smart_route_query(user_question: str) -> Dict[str, Any]:
    """
    Intelligently route a query: either use planning or direct execution.
    
    Args:
        user_question: The user's question
        
    Returns:
        Dictionary with routing decision and optional plan
    """
    if should_use_planner(user_question):
        intent, plan = analyze_query(user_question)
        return {
            "use_planner": True,
            "intent": intent,
            "plan": plan
        }
    else:
        return {
            "use_planner": False,
            "reason": "Simple query, using direct function calling"
        }


# Intent-based function mapping
# This maps intent types to primary functions to try first
INTENT_FUNCTION_MAP = {
    "roster_lookup": ["find_team_by_name", "query_with_filters"],
    "player_stats": ["get_player_season_stats", "get_player_game_stats"],
    "player_ownership": ["find_player_by_name", "query_with_filters"],
    "standings": ["query_with_filters"],
    "matchup_results": ["get_weekly_matchups"],
    "trade_history": ["get_recent_trades", "get_player_trade_history", "get_team_trade_history"],
    "draft_analysis": ["find_who_drafted_player", "get_team_draft_picks"],
    "nfl_standings": ["get_nfl_standings"],
    "comparative_analysis": ["query_with_filters", "get_player_season_stats"],
    "aggregation": ["query_with_filters", "get_trade_counts_by_team"]
}


def get_suggested_functions(intent: QueryIntent) -> List[str]:
    """
    Get a prioritized list of functions to use based on intent.
    
    Args:
        intent: The analyzed query intent
        
    Returns:
        List of function names in priority order
    """
    return INTENT_FUNCTION_MAP.get(intent.intent_type, [])


if __name__ == "__main__":
    # Test the query planner
    print("\n" + "="*70)
    print("🧪 Testing Query Planner")
    print("="*70)
    
    test_queries = [
        "Show me the current standings",  # Simple
        "Who has more TDs, AJ Brown or Tyreek Hill?",  # Complex comparison
        "How are my starters performing compared to league leaders?",  # Very complex
        "What's on my IR?",  # Simple
        "Analyze the trade history of the top 3 teams",  # Complex analysis
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        routing = smart_route_query(query)
        
        if routing["use_planner"]:
            print(f"   → Using PLANNER")
            if routing.get("plan"):
                print(f"   → Intent: {routing['intent'].intent_type}")
                print(f"   → Steps: {len(routing['plan'].steps)}")
        else:
            print(f"   → Direct execution: {routing['reason']}")
    
    print("\n✅ Test complete!")

