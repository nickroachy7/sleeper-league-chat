"""
Fantasy League AI Assistant v2 - Enhanced with Query Planning

Key improvements:
1. Intelligent query planning for complex questions
2. Cleaner, more flexible system prompts
3. Better cross-domain query handling
4. Compositional reasoning for multi-step queries
"""

import json
from openai import OpenAI
from datetime import datetime
from config import OPENAI_API_KEY, SLEEPER_LEAGUE_ID
from dynamic_queries import FUNCTION_DEFINITIONS as SUPABASE_FUNCTIONS, FUNCTION_MAP as SUPABASE_FUNCTION_MAP
from external_stats import EXTERNAL_FUNCTION_DEFINITIONS, EXTERNAL_FUNCTION_MAP, get_current_nfl_season
from query_planner import smart_route_query, QueryIntent, QueryPlan
from logger_config import setup_logger

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)
logger = setup_logger('fantasy_assistant_v2')

# Get current date and NFL season for context
CURRENT_DATE = datetime.now().strftime("%B %d, %Y")
CURRENT_NFL_SEASON = get_current_nfl_season()

# Refactored system prompt - much more concise and flexible
SYSTEM_PROMPT_V2 = f"""You are an expert fantasy football assistant with access to comprehensive league and NFL data.

📅 CONTEXT:
- Date: {CURRENT_DATE}
- NFL Season: {CURRENT_NFL_SEASON}
- League ID: {SLEEPER_LEAGUE_ID}

🎯 YOUR CAPABILITIES:

**Fantasy League Data (Supabase)**
- League standings, rosters, and team information
- Player ownership and availability
- Trade history and draft results
- Weekly matchups and scores
- Multi-season historical data

**Real NFL Data (Ball Don't Lie API)**
- Current season player statistics
- Game-by-game performance
- NFL team standings
- Injury reports and status
- Statistical leaders

🧠 INTELLIGENT QUERY HANDLING:

**Data Source Selection:**
- Fantasy questions (ownership, trades, standings) → Use Supabase functions
- NFL stats questions (TDs, yards, performance) → Use Ball Don't Lie functions
- Hybrid questions → Use both intelligently

**Multi-Step Reasoning:**
For complex questions, break them down:
1. Identify what data is needed
2. Retrieve each piece
3. Combine and analyze
4. Present clear conclusions

**Examples:**

Simple:
- "Show standings" → get rosters with joins
- "AJ Brown's stats" → get_player_season_stats

Complex:
- "How are my starters doing?" → 
  1. Get my roster (find_team_by_name)
  2. Get starter IDs
  3. Look up each starter's NFL stats
  4. Compare to league leaders

Cross-domain:
- "Should I trade Player X?" →
  1. Get player's NFL stats (performance)
  2. Check trade history (value trends)
  3. Look at current owner's needs
  4. Provide analysis

📊 PRESENTATION:

**Use Tables For:**
- Standings, matchups, rosters
- Statistical comparisons
- Trade summaries
- Draft results

**Markdown Format:**
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data     | Data     | Data     |

**Be Conversational:**
- Explain your reasoning
- Provide context and insights
- Suggest follow-up questions when relevant

🔧 KEY FUNCTIONS:

**Team Lookup (Smart Search):**
- `find_team_by_name()` - handles typos, partial names, owner names

**Player Lookup:**
- `find_player_by_name()` - fuzzy search for any player
- Returns position, team, current owner

**NFL Stats:**
- `get_player_season_stats()` - cumulative season stats
- `get_player_game_stats()` - specific game performance
- `call_mcp_endpoint()` - access any NFL data endpoint

**Trade Analysis:**
- `get_recent_trades()` - latest trades with full details
- `get_player_trade_history()` - all trades for a player
- `get_team_trade_history()` - all trades by a team

**Matchups & Standings:**
- `get_weekly_matchups()` - formatted weekly results
- `query_with_filters()` - flexible table queries

Remember: You have access to ALL the tools you need. Be creative in combining them to answer unique questions!
"""

# Simplified function definitions - focus on WHAT not WHEN
def get_enhanced_function_definitions():
    """
    Get enhanced function definitions with better descriptions.
    Remove prescriptive "USE THIS WHEN" language and focus on capabilities.
    """
    # Clean up Supabase function descriptions
    enhanced_supabase = []
    for func in SUPABASE_FUNCTIONS:
        # Create a cleaner version
        clean_func = func.copy()
        
        # Simplify descriptions - remove the prescriptive examples
        if func["name"] == "find_team_by_name":
            clean_func["description"] = """Find a team using fuzzy matching on team name or owner name.
            
Handles typos, partial matches, and name variations automatically.
Returns complete team data including roster_id, record, points, and all player arrays (players, starters, reserve, taxi).
Perfect for any team-specific queries."""
        
        elif func["name"] == "find_player_by_name":
            clean_func["description"] = """Search for NFL players by name using fuzzy matching.
            
Returns player details: player_id, full_name, position, NFL team, status.
Handles partial names and variations (e.g., 'Mahomes' finds 'Patrick Mahomes')."""
        
        elif func["name"] == "get_recent_trades":
            clean_func["description"] = """Get recent trades with full details (teams, players, draft picks).
            
All names are automatically resolved:
- Team names (not roster IDs)
- Player names with position/team
- Draft picks with original owner

Perfect for trade history queries."""
        
        elif func["name"] == "get_weekly_matchups":
            clean_func["description"] = """Get weekly matchup results with team names, scores, and winners.
            
Returns properly formatted matchup data ready for display.
Automatically resolves roster IDs to team names and determines winners."""
        
        enhanced_supabase.append(clean_func)
    
    # External functions are already pretty clean, but let's enhance the main one
    enhanced_external = []
    for func in EXTERNAL_FUNCTION_DEFINITIONS:
        clean_func = func.copy()
        
        if func["name"] == "call_mcp_endpoint":
            clean_func["description"] = """Universal access to all NFL data via Ball Don't Lie MCP.
            
Use this for ANY NFL data not covered by specific functions:
- NFL team standings (nfl_get_standings)
- Injury reports (nfl_get_player_injuries)  
- Statistical leaders (nfl_get_leaders)
- Advanced stats (nfl_get_advanced_*_stats)
- Game results (nfl_get_games)

Provides access to 20+ NFL data endpoints. Flexible and powerful for unique queries."""
        
        enhanced_external.append(clean_func)
    
    return enhanced_supabase + enhanced_external


def chat_v2(message: str, conversation_history: list = None) -> tuple[str, list]:
    """
    Enhanced chat function with query planning.
    
    Args:
        message: User's message
        conversation_history: Previous conversation messages
    
    Returns:
        (assistant_response, updated_conversation_history)
    """
    if conversation_history is None:
        conversation_history = [{"role": "system", "content": SYSTEM_PROMPT_V2}]
    
    # Add user message
    conversation_history.append({"role": "user", "content": message})
    
    # Analyze query to determine if we need planning
    routing = smart_route_query(message)
    
    if routing.get("use_planner") and routing.get("plan"):
        # Complex query - use planned approach
        logger.info(f"Using query planner for: {message[:50]}...")
        intent: QueryIntent = routing["intent"]
        plan: QueryPlan = routing["plan"]
        
        # Add planning context to the conversation
        planning_context = f"""
Query Analysis:
- Intent: {intent.intent_type}
- Data sources: {', '.join(intent.data_sources)}
- Complexity: {intent.complexity}

Execution plan ({len(plan.steps)} steps):
{plan.rationale}

Now execute this plan using the available functions.
"""
        conversation_history.append({
            "role": "assistant",
            "content": planning_context
        })
    else:
        logger.info(f"Using direct execution for: {message[:50]}...")
    
    # Merge all function definitions
    all_function_definitions = get_enhanced_function_definitions()
    all_function_map = {**SUPABASE_FUNCTION_MAP, **EXTERNAL_FUNCTION_MAP}
    
    # Convert function definitions to tools format
    tools = [{"type": "function", "function": func} for func in all_function_definitions]
    
    logger.debug(f"Using {len(tools)} tools for query")
    
    # Get response from OpenAI
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=conversation_history,
        tools=tools,
        tool_choice="auto",
        temperature=0.7  # Slightly higher for more natural responses
    )
    
    response_message = response.choices[0].message
    
    # Check if the model wants to call a function
    if response_message.tool_calls:
        # Add assistant's message to history
        conversation_history.append(response_message)
        
        # Execute each tool call
        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            logger.info(f"🔧 Calling: {function_name}({json.dumps(function_args, indent=2)})")
            
            # Call the actual function
            try:
                function_to_call = all_function_map[function_name]
                function_response = function_to_call(**function_args)
                
                logger.debug(f"Function response preview: {str(function_response)[:200]}...")
            except Exception as e:
                logger.error(f"Error calling {function_name}: {e}", exc_info=True)
                function_response = {"error": f"Function execution failed: {str(e)}"}
            
            # Add function response to conversation
            conversation_history.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": json.dumps(function_response)
            })
        
        # Get final response from the model
        second_response = client.chat.completions.create(
            model="gpt-4o",
            messages=conversation_history,
            temperature=0.7
        )
        
        final_message = second_response.choices[0].message
        conversation_history.append({
            "role": "assistant",
            "content": final_message.content
        })
        
        logger.info("✅ Generated response with function calls")
        return final_message.content, conversation_history
    
    else:
        # No function call needed
        conversation_history.append({
            "role": "assistant",
            "content": response_message.content
        })
        
        logger.debug("Response generated without tool calls")
        return response_message.content, conversation_history


def chat_loop_v2():
    """Interactive chat loop with enhanced capabilities"""
    print("\n" + "="*70)
    print("🏈 FANTASY LEAGUE AI ASSISTANT v2.0 (Enhanced)")
    print("="*70)
    print("\nHello! I'm your upgraded fantasy football assistant.")
    print("I can now handle more complex and varied questions!")
    print("\nTry asking:")
    print("  • Complex: 'Compare the top 3 teams' rosters'")
    print("  • Cross-domain: 'How are my IR players performing?'")
    print("  • Analytical: 'Which teams make the most trades?'")
    print("  • Basic: 'Show me the standings' (still works great!)")
    print("\nType 'quit' to exit.\n")
    print("="*70 + "\n")
    
    conversation_history = None
    
    while True:
        try:
            user_input = input("\n💬 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\n👋 Thanks for chatting! Good luck in your league!\n")
                break
            
            # Get response
            response, conversation_history = chat_v2(user_input, conversation_history)
            
            print(f"\n🤖 Assistant: {response}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Thanks for chatting!\n")
            break
        except Exception as e:
            logger.error(f"Error in chat loop: {e}", exc_info=True)
            print(f"\n❌ Error: {str(e)}")
            print("Please try again or type 'quit' to exit.\n")


if __name__ == "__main__":
    chat_loop_v2()

