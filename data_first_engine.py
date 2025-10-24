"""
Data-First Query Engine

This module implements a "data-first" approach where we:
1. Analyze the question to identify ALL data requirements
2. Fetch ALL necessary data upfront in batch
3. Provide complete data context to LLM for pure analysis

This separates data retrieval from reasoning, allowing the LLM to act like
a sports analyst who has all the facts before providing analysis.
"""

from typing import Dict, Any, List, Optional
from openai import OpenAI
import json
from config import OPENAI_API_KEY, SLEEPER_LEAGUE_ID
from dynamic_queries import FUNCTION_MAP as SUPABASE_FUNCTION_MAP
from external_stats import EXTERNAL_FUNCTION_MAP
from logger_config import setup_logger

logger = setup_logger('data_first_engine')
client = OpenAI(api_key=OPENAI_API_KEY)


class DataRequirement:
    """Represents a piece of data needed to answer a question"""
    
    def __init__(
        self,
        data_type: str,
        function_name: str,
        parameters: Dict[str, Any],
        description: str
    ):
        self.data_type = data_type  # e.g., "team_trades", "player_stats", "standings"
        self.function_name = function_name
        self.parameters = parameters
        self.description = description
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "data_type": self.data_type,
            "function_name": self.function_name,
            "parameters": self.parameters,
            "description": self.description
        }


class DataContext:
    """Complete data context for answering a question"""
    
    def __init__(self, question: str):
        self.question = question
        self.requirements: List[DataRequirement] = []
        self.fetched_data: Dict[str, Any] = {}
        self.errors: List[str] = []
    
    def add_requirement(self, requirement: DataRequirement):
        """Add a data requirement"""
        self.requirements.append(requirement)
    
    def add_data(self, data_type: str, data: Any):
        """Store fetched data"""
        self.fetched_data[data_type] = data
    
    def add_error(self, error: str):
        """Record an error"""
        self.errors.append(error)
    
    def is_complete(self) -> bool:
        """Check if all required data has been fetched"""
        return len(self.fetched_data) == len(self.requirements) or len(self.errors) > 0
    
    def get_context_summary(self) -> str:
        """Get a summary of the data context for the LLM"""
        summary = f"Question: {self.question}\n\n"
        summary += "Available Data:\n"
        
        for data_type, data in self.fetched_data.items():
            # Create a concise summary of the data
            if isinstance(data, list):
                summary += f"- {data_type}: {len(data)} items\n"
            elif isinstance(data, dict):
                summary += f"- {data_type}: {len(data)} fields\n"
            else:
                summary += f"- {data_type}: Available\n"
        
        if self.errors:
            summary += f"\nErrors encountered: {len(self.errors)}\n"
        
        return summary


DATA_REQUIREMENT_ANALYZER_PROMPT = """You are a data requirement analyzer for a fantasy football assistant.

Your job is to analyze a user's question and identify ALL data that needs to be fetched BEFORE attempting to answer.

AVAILABLE DATA SOURCES:

**Supabase (Fantasy League Database):**
- get_team_trade_history(team_name_search) - All trades by a specific team
- get_recent_trades(limit, season) - Recent trades in the league
- get_trade_counts_by_team() - Trade counts for all teams
- get_player_trade_history(player_name_search) - All trades involving a player
- find_team_by_name(team_name_search) - Find team roster
- find_player_by_name(player_name_search) - Find player info
- get_weekly_matchups(week, season) - Weekly matchup results
- query_with_filters(table, select_columns, filters, order_column, order_desc, limit) - Flexible queries
- And more...

**Ball Don't Lie API (NFL Stats):**
- get_player_season_stats(player_name, season) - Season stats for a player
- get_player_game_stats(player_name, game_date, season) - Game stats
- get_nfl_standings(season, conference, division) - NFL standings
- call_mcp_endpoint(endpoint_name, parameters) - Any NFL data endpoint

YOUR TASK:
Analyze the question and return a JSON array of data requirements. Each requirement should specify:
- data_type: A descriptive name for this data (e.g., "fdr_trades", "all_trade_counts")
- function_name: The function to call
- parameters: Parameters to pass to the function
- description: Why this data is needed

CRITICAL RULES:
1. Identify ALL data needed upfront - don't assume or leave gaps
2. Be thorough - if analyzing trades, get the actual trade data, not just counts
3. Consider what a sports analyst would need to fully answer the question
4. If the question asks about "worst" or "best", you need COMPREHENSIVE comparative data
5. For trade analysis, get as many trades as possible (use high limits like 200+)
6. Consider getting player performance data to evaluate trade outcomes

EXAMPLES:

Question: "Who has made the worst trade in league history?"
Requirements:
[
  {
    "data_type": "all_trades_comprehensive",
    "function_name": "get_recent_trades",
    "parameters": {"limit": 200},
    "description": "Get comprehensive trade history - need ALL trades to compare, not just recent ones"
  },
  {
    "data_type": "trade_counts_by_team",
    "function_name": "get_trade_counts_by_team",
    "parameters": {},
    "description": "Get trade activity by team for context on who trades most"
  }
]

NOTE: For "worst/best" questions, ALWAYS fetch comprehensive data (high limits), not just small samples!

Question: "How are my IR players performing?"
Requirements:
[
  {
    "data_type": "my_team_roster",
    "function_name": "find_team_by_name",
    "parameters": {"team_name_search": "my team"},
    "description": "Get my roster to identify IR players"
  },
  {
    "data_type": "player_stats_[player_id]",
    "function_name": "get_player_season_stats",
    "parameters": {"player_name": "[to be determined from IR list]"},
    "description": "Get season stats for each IR player"
  }
]

Return ONLY valid JSON array of requirements.
"""


def analyze_data_requirements(question: str) -> List[DataRequirement]:
    """
    Analyze a question to identify all data requirements.
    
    Args:
        question: The user's question
        
    Returns:
        List of DataRequirement objects
    """
    try:
        logger.info(f"Analyzing data requirements for: {question[:100]}...")
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": DATA_REQUIREMENT_ANALYZER_PROMPT},
                {"role": "user", "content": f"Analyze this question and identify all data requirements:\n\n{question}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Parse into DataRequirement objects
        requirements = []
        if "requirements" in result:
            req_list = result["requirements"]
        elif isinstance(result, list):
            req_list = result
        else:
            # Try to find any array in the response
            for key, value in result.items():
                if isinstance(value, list):
                    req_list = value
                    break
            else:
                req_list = [result]
        
        for req in req_list:
            if isinstance(req, dict) and "function_name" in req:
                requirements.append(DataRequirement(
                    data_type=req.get("data_type", "unknown"),
                    function_name=req["function_name"],
                    parameters=req.get("parameters", {}),
                    description=req.get("description", "")
                ))
        
        logger.info(f"Identified {len(requirements)} data requirements")
        for req in requirements:
            logger.debug(f"  - {req.data_type}: {req.function_name}({req.parameters})")
        
        return requirements
        
    except Exception as e:
        logger.error(f"Error analyzing data requirements: {e}", exc_info=True)
        return []


def fetch_all_data(requirements: List[DataRequirement]) -> DataContext:
    """
    Fetch all required data in batch.
    
    Args:
        requirements: List of data requirements
        
    Returns:
        DataContext with all fetched data
    """
    context = DataContext(question="")
    
    # Merge function maps
    all_functions = {**SUPABASE_FUNCTION_MAP, **EXTERNAL_FUNCTION_MAP}
    
    for req in requirements:
        try:
            logger.info(f"Fetching {req.data_type}: {req.function_name}({req.parameters})")
            
            if req.function_name not in all_functions:
                error_msg = f"Function {req.function_name} not found"
                logger.error(error_msg)
                context.add_error(error_msg)
                continue
            
            # Call the function
            function = all_functions[req.function_name]
            data = function(**req.parameters)
            
            # Store the data
            context.add_data(req.data_type, data)
            
            # Check if this data reveals additional requirements
            # (e.g., IR player list reveals which players to get stats for)
            if req.data_type == "my_team_roster" and isinstance(data, list) and len(data) > 0:
                roster = data[0]
                ir_players = roster.get('reserve', [])
                
                if ir_players:
                    logger.info(f"Found {len(ir_players)} IR players, fetching their stats...")
                    # Fetch stats for each IR player
                    # Note: This requires resolving player IDs to names first
                    # For now, we'll document this as a secondary fetch
            
            logger.debug(f"Successfully fetched {req.data_type}")
            
        except Exception as e:
            error_msg = f"Error fetching {req.data_type}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            context.add_error(error_msg)
    
    return context


def answer_with_data_context(question: str, context: DataContext) -> str:
    """
    Answer the question using complete data context.
    The LLM acts as a sports analyst with all facts available.
    
    Args:
        question: The user's question
        context: Complete data context
        
    Returns:
        The answer
    """
    try:
        logger.info(f"Generating answer with complete data context")
        
        # Build the analyst prompt
        analyst_prompt = """You are an expert fantasy football analyst providing expert analysis.

CRITICAL: You are NOT just showing data - you are ANALYZING it and providing expert insights.

Your role:
- Analyze ALL the provided data thoroughly
- Make comparisons and evaluations
- Identify patterns and draw conclusions
- Provide specific recommendations or judgments
- Support your analysis with concrete data points

DO NOT:
- Just list the data without analysis
- Say "here is the data, you can analyze it"
- Avoid making judgments when asked for opinions
- Present raw data dumps

DO:
- Act like an ESPN analyst who has studied all the facts
- Make clear judgments based on the data (e.g., "the worst trade was...")
- Explain your reasoning with specific examples
- Compare multiple items and rank them
- Be confident in your analysis

Example of GOOD analysis:
"After analyzing all 50 trades, the worst trade was clearly Team A trading Player X for Player Y in Week 3. Here's why:
- Player X went on to score 250 points over the rest of the season (20 PPG)
- Player Y only scored 80 points (5 PPG) 
- This trade cost Team A approximately 170 fantasy points
- Team A missed playoffs by 50 points, so this trade directly led to their elimination"

Example of BAD analysis:
"Here are the trades in the league. You can analyze these to identify any that appear particularly uneven."

ALWAYS be the analyst, NEVER just show data."""

        # Build the data context message
        data_message = f"""QUESTION: {question}

COMPLETE DATA CONTEXT:

"""
        
        # Add all fetched data to the context with smart formatting
        for data_type, data in context.fetched_data.items():
            data_message += f"\n### {data_type.upper().replace('_', ' ')}\n"
            
            # Smart formatting based on data type
            if isinstance(data, dict) and 'trades' in data:
                # Format trade data more readably
                trades = data.get('trades', [])
                data_message += f"Total trades available: {len(trades)}\n\n"
                if len(trades) > 0:
                    data_message += "Trade details:\n"
                    for i, trade in enumerate(trades[:50], 1):  # Show up to 50 trades
                        data_message += f"\n{i}. Season {trade.get('season')}, Week {trade.get('week')}\n"
                        teams = trade.get('teams', [])
                        for team_data in teams:
                            team_name = team_data.get('team_name', 'Unknown')
                            received = team_data.get('received', [])
                            data_message += f"   - {team_name} received: {', '.join(received) if received else 'Nothing'}\n"
                    if len(trades) > 50:
                        data_message += f"\n... and {len(trades) - 50} more trades\n"
            elif isinstance(data, dict) and 'teams' in data:
                # Format team data
                teams = data.get('teams', [])
                data_message += f"Total teams: {len(teams)}\n\n"
                for team in teams:
                    data_message += f"- {team.get('team_name')}: {team.get('total_trades')} trades\n"
            else:
                # Default JSON format for other data
                # But limit size for very large datasets
                json_str = json.dumps(data, indent=2)
                if len(json_str) > 10000:  # If >10KB, truncate
                    data_message += f"```json\n{json_str[:10000]}\n... (truncated, {len(json_str)} chars total)\n```\n"
                else:
                    data_message += f"```json\n{json_str}\n```\n"
        
        if context.errors:
            data_message += f"\n### ERRORS ENCOUNTERED\n"
            for error in context.errors:
                data_message += f"- {error}\n"
        
        data_message += f"""\n\n{'='*70}
YOUR TASK AS ANALYST:
{'='*70}

You have ALL the data above. Now perform your expert analysis.

Specifically for this question "{question}":
1. Review ALL the data provided above thoroughly
2. Compare and evaluate each relevant item
3. Make a CLEAR judgment/recommendation
4. Support it with specific examples from the data
5. Present your findings confidently

Remember: You are the expert analyst. Don't just show data - ANALYZE it and provide insights!

Your analysis:"""
        
        # Get response from analyst
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": analyst_prompt},
                {"role": "user", "content": data_message}
            ],
            temperature=0.7
        )
        
        answer = response.choices[0].message.content
        
        logger.info("Successfully generated answer from data context")
        return answer
        
    except Exception as e:
        logger.error(f"Error generating answer: {e}", exc_info=True)
        return f"I encountered an error while analyzing the data: {str(e)}"


def answer_question_data_first(question: str) -> str:
    """
    Answer a question using the data-first approach.
    
    This is the main entry point that:
    1. Analyzes data requirements
    2. Fetches all data
    3. Provides complete context to analyst
    
    Args:
        question: The user's question
        
    Returns:
        The answer
    """
    logger.info(f"\n{'='*70}")
    logger.info(f"DATA-FIRST QUERY: {question}")
    logger.info(f"{'='*70}")
    
    # Step 1: Analyze data requirements
    logger.info("STEP 1: Analyzing data requirements...")
    requirements = analyze_data_requirements(question)
    
    if not requirements:
        logger.warning("No data requirements identified, falling back to direct answer")
        # Try to answer directly
        return answer_with_data_context(question, DataContext(question))
    
    logger.info(f"Identified {len(requirements)} data requirements")
    
    # Step 2: Fetch all data
    logger.info("STEP 2: Fetching all required data...")
    context = DataContext(question)
    context.requirements = requirements
    
    for req in requirements:
        context = fetch_all_data([req])  # Fetch one at a time for better error handling
    
    logger.info(f"Fetched {len(context.fetched_data)} data items")
    
    # Step 3: Answer with complete context
    logger.info("STEP 3: Analyzing data and generating answer...")
    answer = answer_with_data_context(question, context)
    
    logger.info(f"{'='*70}")
    logger.info("DATA-FIRST QUERY COMPLETE")
    logger.info(f"{'='*70}\n")
    
    return answer


if __name__ == "__main__":
    # Test the data-first engine
    print("\n" + "="*70)
    print("🧪 Testing Data-First Engine")
    print("="*70)
    
    test_question = "Who has made the worst trade in league history?"
    print(f"\nQuestion: {test_question}")
    
    print("\n1. Analyzing data requirements...")
    requirements = analyze_data_requirements(test_question)
    print(f"   Found {len(requirements)} requirements:")
    for req in requirements:
        print(f"   - {req.data_type}: {req.function_name}")
    
    print("\n2. Fetching data...")
    context = DataContext(test_question)
    context.requirements = requirements
    
    for req in requirements:
        temp_context = fetch_all_data([req])
        context.fetched_data.update(temp_context.fetched_data)
        context.errors.extend(temp_context.errors)
    
    print(f"   Fetched {len(context.fetched_data)} data items")
    
    print("\n3. Generating answer...")
    answer = answer_with_data_context(test_question, context)
    print(f"\nAnswer:\n{answer}")
    
    print("\n" + "="*70)
    print("✅ Test complete!")

