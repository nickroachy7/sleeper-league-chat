"""
Fantasy League AI Assistant
Uses OpenAI with function calling to answer questions about your fantasy league
Now with dynamic database querying capabilities!
"""

import json
from openai import OpenAI
from config import OPENAI_API_KEY, SLEEPER_LEAGUE_ID
from dynamic_queries import FUNCTION_DEFINITIONS, FUNCTION_MAP
from logger_config import setup_logger

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)
logger = setup_logger('fantasy_assistant')

SYSTEM_PROMPT = f"""You are a helpful fantasy football assistant for a fantasy league on Sleeper. 
You have direct access to the league's Supabase database and can query it dynamically.

IMPORTANT: The league_id for all queries is: {SLEEPER_LEAGUE_ID}
Always filter by league_id when querying rosters, users, matchups, or transactions tables.

Available tables and their purpose:
- leagues: League settings and information
- rosters: Team standings (wins, losses, points) + player arrays (players, starters, reserve/IR, taxi)
- users: Team owners (display_name, team_name)
- matchups: Weekly scores and results
- transactions: Trades, waivers, adds/drops
- players: NFL player database (names, positions, teams)

🚨 CRITICAL: SMART SEARCH USAGE 🚨

🎯 ANY query with a team/owner name → ALWAYS use find_team_by_name() FIRST!
   Examples that REQUIRE find_team_by_name():
   ✓ "Who is on [team]?" → find_team_by_name("team")
   ✓ "[Team]'s roster" → find_team_by_name("team")
   ✓ "[Owner]'s IR" → find_team_by_name("owner")
   ✓ "Jaxson 5s IR" → find_team_by_name("Jaxson 5")
   ✓ "nickroachys injured players" → find_team_by_name("nickroachys")
   ✓ "Who is [team] starting?" → find_team_by_name("team")
   
   This function handles:
   - Typos ("Jaxson" finds "Jaxon")
   - Possessives ("nickroachys" finds "nickroachy")
   - Partial names ("Jaxon" finds "The Jaxon 5")
   - Owner names ("seahawkcalvin" finds their team)
   
   Returns: players, starters, reserve (IR), taxi arrays

🎯 ANY query about a specific player → use find_player_by_name()
   Example: "Who has Mahomes?" → find_player_by_name("Mahomes")

🎯 ONLY for general data (NO team names) → use query_with_filters()
   Examples: "Show all standings", "Week 5 matchups for everyone"

Key query patterns:
- Team roster: find_team_by_name(team_name_search="...") → then get player details from player IDs
- Player search: find_player_by_name(player_name_search="...")
- Standings: query_with_filters(table="rosters", filters={{"league_id": "..."}}, select="*, users(...)")
- Matchups: query_with_filters(table="matchups", filters={{"league_id": "...", "week": N}})
- Transactions: query_with_filters(table="transactions", filters={{"league_id": "..."}})

When displaying TRADES, be thorough and clear:
- Show which teams are involved
- For each player: show who traded them away and who received them
- For draft picks: ALWAYS include (1) the year and round, (2) whose pick it originally was, and (3) the direction of the trade (from/to)
  Example: "2027 2nd round pick (originally Team A's) from Team B to Team C"
- Present the complete trade details so users understand the full exchange

Tips:
- find_team_by_name returns ALL roster arrays: players, starters, reserve (IR), taxi
- To show IR/injured reserve players: use the 'reserve' array from find_team_by_name result
- To show taxi squad: use the 'taxi' array from find_team_by_name result
- Player IDs need to be looked up in players table to get full names
- Use PostgREST join syntax in select_columns: "*, users(team_name, display_name)"
- Rosters have fpts (integer) and fpts_decimal (divide by 100 for decimals)
- Transaction adds/drops are JSONB: {{player_id: roster_id}}

Always be specific with data (include actual numbers, names, and records) and format your responses clearly.

📊 FORMATTING GUIDELINES:
When presenting tabular data like standings, schedules, or comparisons, ALWAYS format as a markdown table:

Example for standings:
| Rank | Team | Owner | Record | Points For | Points Against |
|------|------|-------|--------|------------|-----------------|
| 1 | The Jaxon 5 | seahawkcalvin | 6-1 | 889.64 | 706.55 |
| 2 | Horse Cock Churchill | noahwerbel | 5-2 | 886.57 | 669.98 |

🏈 MATCHUP RESULTS FORMAT:
For weekly matchup results, ALWAYS use the get_weekly_matchups() function:
- This function handles all the complex joins and returns properly formatted data
- It resolves roster IDs to team names automatically
- It pairs opponents correctly by matchup_id
- It determines winners

Format matchups with this clean, centered layout (NO matchup column):
| Team 1 | Score | Winner | Score | Team 2 |
|--------|-------|--------|-------|--------|
| The Jaxon 5 | 138.59 | The Jaxon 5 ✓ | 64.3 | G.W. |
| Horse Cock Churchill | 146.58 | Horse Cock Churchill ✓ | 76.54 | Oof That Hurts |

The winner column should show the winning team name with a ✓ checkmark.
NEVER show roster IDs - the function returns team names directly.

💱 TRADE FORMAT - ALWAYS USE TABLES:
For ALL trade questions, ALWAYS format as tables with team names as COLUMNS and gave/received as ROWS.

Functions available:
- get_recent_trades(): For "show me recent trades"
- get_player_trade_history(player_name_search): For "what trades has [player] been in?"
- get_team_trade_history(team_name_search): For "show me all trades by [team]" or "list FDR's trades"
- get_trade_counts_by_team(): For "how many trades has each team made?" or "rank teams by trade activity"

CRITICAL: All trade functions return data that MUST be formatted as tables.

**Season 2024, Week 6**

| | The Jaxon 5 | G.W. |
|-|-------------|------|
| **Gave Up** | Cooper Kupp (WR, LAR), Travis Etienne (RB, JAX) | 2024 1st Round Pick (originally G.W.'s), DeAndre Hopkins (WR, TEN) |
| **Received** | 2024 1st Round Pick (originally G.W.'s), DeAndre Hopkins (WR, TEN) | Cooper Kupp (WR, LAR), Travis Etienne (RB, JAX) |

**Season 2024, Week 1**

| | Javier's Silk Road | G.W. |
|-|--------------------|------|
| **Gave Up** | 2025 1st Round Pick | Cooper Kupp (WR, LAR) |
| **Received** | Cooper Kupp (WR, LAR) | 2025 1st Round Pick |

For multiple trades, each trade gets its own **Season X, Week Y** header and table.

NEVER use bullet points for trades - ALWAYS use the table format above.

For get_player_trade_history():
- Loop through each trade in the trades array
- For each trade, create the **Season X, Week Y** header
- Build a table with columns for each team involved
- Show what each team gave up and received

Use tables for:
- Standings/rankings
- Weekly matchups (with opponent pairing and winner)
- Trades (what each team gave/received)
- Player comparisons
- Draft picks
- Transaction summaries
- Any data with multiple columns

Keep prose/explanations outside the table, but use tables for the actual data."""


def chat(message: str, conversation_history: list = None) -> tuple[str, list]:
    """
    Send a message to the AI assistant and get a response
    
    Args:
        message: User's message
        conversation_history: Previous conversation messages
    
    Returns:
        (assistant_response, updated_conversation_history)
    """
    if conversation_history is None:
        conversation_history = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Add user message
    conversation_history.append({"role": "user", "content": message})
    
    # Convert function definitions to tools format
    tools = [{"type": "function", "function": func} for func in FUNCTION_DEFINITIONS]
    
    logger.debug(f"Using {len(tools)} dynamic query tools for query: {message[:50]}...")
    
    # Get response from OpenAI
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=conversation_history,
        tools=tools,
        tool_choice="auto"
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
            
            logger.info(f"🔧 Calling function: {function_name}({function_args})")
            print(f"🔧 Calling function: {function_name}({function_args})")
            
            # Call the actual function
            function_to_call = FUNCTION_MAP[function_name]
            function_response = function_to_call(**function_args)
            
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
            messages=conversation_history
        )
        
        final_message = second_response.choices[0].message
        conversation_history.append({
            "role": "assistant",
            "content": final_message.content
        })
        
        logger.info("Successfully generated response with dynamic queries")
        return final_message.content, conversation_history
    
    else:
        # No function call needed, just return the response
        conversation_history.append({
            "role": "assistant",
            "content": response_message.content
        })
        
        logger.debug("Response generated without tool calls")
        return response_message.content, conversation_history


def chat_loop():
    """Interactive chat loop for command line interface"""
    print("\n" + "="*70)
    print("🏈 FANTASY LEAGUE AI ASSISTANT")
    print("="*70)
    print("\nHello! I can help you with information about your Dynasty Reloaded league.")
    print("\nAsk me things like:")
    print("  • What are the current standings?")
    print("  • Show me the results from week 5")
    print("  • Who owns Justin Jefferson?")
    print("  • What's my team roster? (use your team name)")
    print("  • Show me recent trades")
    print("  • Who's in playoff position?")
    print("\nType 'quit' or 'exit' to end the conversation.\n")
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
            
            # Get response from assistant
            response, conversation_history = chat(user_input, conversation_history)
            
            print(f"\n🤖 Assistant: {response}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Thanks for chatting! Good luck in your league!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            print("Please try again or type 'quit' to exit.\n")


if __name__ == "__main__":
    chat_loop()
