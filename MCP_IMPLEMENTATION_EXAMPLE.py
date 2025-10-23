"""
Example Implementation: Ball Don't Lie MCP Integration

This file shows a CONCRETE example of how to implement the MCP calls.
Adjust based on your actual Ball Don't Lie MCP interface.
"""

# ============================================================================
# EXAMPLE 1: If your MCP is accessed via Cursor's MCP protocol
# ============================================================================

def get_player_game_stats_example_cursor_mcp(player_name: str, game_date: str = None):
    """
    Example if you're using Cursor's MCP protocol (most likely case)
    """
    try:
        # Cursor MCP tools are typically called directly
        # Check your mcp.json configuration for available tools
        
        # Example call (adjust based on your actual MCP tools):
        from mcp_client import call_mcp_tool  # This might be built-in
        
        response = call_mcp_tool(
            tool_name="ball_dont_lie_get_player_stats",
            parameters={
                "player_name": player_name,
                "game_date": game_date or "latest",
                "sport": "nfl"
            }
        )
        
        # Transform response to your format
        return {
            'player_name': response['player']['name'],
            'game_date': response['game']['date'],
            'stats': {
                'touchdowns': response['stats']['touchdowns'],
                'yards': response['stats']['yards'],
                'receptions': response['stats'].get('receptions', 0)
            }
        }
        
    except Exception as e:
        return {'error': str(e)}


# ============================================================================
# EXAMPLE 2: If Ball Don't Lie provides a Python SDK
# ============================================================================

def get_player_game_stats_example_sdk(player_name: str, game_date: str = None):
    """
    Example if Ball Don't Lie provides a Python SDK/library
    """
    try:
        # Import the SDK
        from ball_dont_lie import BallDontLieClient
        
        # Initialize client (do this once in get_mcp_client())
        client = BallDontLieClient(
            api_key="your_api_key_here",
            sport="nfl"
        )
        
        # Call the API
        if game_date:
            stats = client.players.get_game_stats(
                name=player_name,
                date=game_date
            )
        else:
            # Get most recent game
            stats = client.players.get_latest_game(
                name=player_name
            )
        
        # Return formatted response
        return {
            'player_name': stats.player_name,
            'game_date': stats.game_date,
            'opponent': stats.opponent_team,
            'stats': {
                'touchdowns': stats.touchdowns,
                'yards': stats.total_yards,
                'receptions': stats.receptions if hasattr(stats, 'receptions') else 0,
                'fantasy_points': stats.fantasy_points
            }
        }
        
    except Exception as e:
        return {'error': str(e)}


# ============================================================================
# EXAMPLE 3: If it's a REST API that you call directly
# ============================================================================

def get_player_game_stats_example_rest(player_name: str, game_date: str = None):
    """
    Example if Ball Don't Lie is a REST API
    """
    import requests
    
    try:
        # Build API request
        base_url = "https://api.balldontlie.io/v1"  # Example URL
        endpoint = f"{base_url}/nfl/players/stats"
        
        params = {
            'player_name': player_name,
            'sport': 'nfl'
        }
        
        if game_date:
            params['date'] = game_date
        else:
            params['latest'] = True
        
        headers = {
            'Authorization': f'Bearer {YOUR_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(endpoint, params=params, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract relevant data
        game_stats = data['data'][0] if data['data'] else {}
        
        return {
            'player_name': game_stats.get('player_name'),
            'game_date': game_stats.get('game_date'),
            'stats': {
                'touchdowns': game_stats.get('touchdowns', 0),
                'yards': game_stats.get('total_yards', 0),
                'receptions': game_stats.get('receptions', 0)
            }
        }
        
    except requests.exceptions.RequestException as e:
        return {'error': f'API request failed: {str(e)}'}
    except Exception as e:
        return {'error': str(e)}


# ============================================================================
# EXAMPLE 4: GraphQL API
# ============================================================================

def get_player_game_stats_example_graphql(player_name: str, game_date: str = None):
    """
    Example if Ball Don't Lie uses GraphQL
    """
    import requests
    
    try:
        url = "https://api.balldontlie.io/graphql"
        
        query = """
        query GetPlayerStats($playerName: String!, $gameDate: String) {
            player(name: $playerName) {
                name
                gameStats(date: $gameDate) {
                    date
                    opponent
                    touchdowns
                    yards
                    receptions
                    targets
                }
            }
        }
        """
        
        variables = {
            'playerName': player_name,
            'gameDate': game_date
        }
        
        response = requests.post(
            url,
            json={'query': query, 'variables': variables},
            headers={'Authorization': f'Bearer {YOUR_API_KEY}'}
        )
        
        data = response.json()
        game = data['data']['player']['gameStats'][0]
        
        return {
            'player_name': data['data']['player']['name'],
            'game_date': game['date'],
            'opponent': game['opponent'],
            'stats': {
                'touchdowns': game['touchdowns'],
                'yards': game['yards'],
                'receptions': game['receptions'],
                'targets': game['targets']
            }
        }
        
    except Exception as e:
        return {'error': str(e)}


# ============================================================================
# HOW TO FIND OUT WHICH ONE YOU NEED
# ============================================================================

"""
To determine which implementation pattern to use:

1. Check your mcp.json file:
   - Look at ~/.cursor/mcp.json or your workspace .cursor/mcp.json
   - See what tools are defined for Ball Don't Lie

2. Check the Ball Don't Lie MCP documentation:
   - Look for initialization examples
   - Check function/method signatures
   - Review example usage

3. Common indicators:
   - Cursor MCP: Tools are defined in mcp.json
   - Python SDK: You `pip install ball-dont-lie` or similar
   - REST API: You make HTTP requests
   - GraphQL: Endpoint ends in /graphql

4. Test with a simple script:
   ```python
   # Try importing
   try:
       from ball_dont_lie import Client
       print("SDK available!")
   except ImportError:
       print("No SDK - likely REST or MCP")
   ```

5. Check your Cursor MCP configuration:
   - CMD/CTRL + SHIFT + P → "MCP: Show Available Tools"
   - This will show you what Ball Don't Lie functions are available
"""


# ============================================================================
# STEP-BY-STEP: Find Your MCP Interface
# ============================================================================

def find_mcp_interface():
    """
    Run this function to help determine your MCP setup
    """
    import os
    import json
    
    print("🔍 Searching for Ball Don't Lie MCP configuration...\n")
    
    # Check for mcp.json
    mcp_paths = [
        os.path.expanduser("~/.cursor/mcp.json"),
        os.path.join(os.getcwd(), ".cursor/mcp.json"),
        os.path.join(os.getcwd(), "mcp.json")
    ]
    
    for path in mcp_paths:
        if os.path.exists(path):
            print(f"✅ Found MCP config: {path}")
            try:
                with open(path, 'r') as f:
                    config = json.load(f)
                    print("\n📄 MCP Configuration:")
                    print(json.dumps(config, indent=2))
                    
                    # Look for Ball Don't Lie
                    if 'mcpServers' in config:
                        for name, server in config['mcpServers'].items():
                            if 'ball' in name.lower() or 'dont' in name.lower():
                                print(f"\n🎯 Found Ball Don't Lie MCP: {name}")
                                print(f"   Command: {server.get('command', 'N/A')}")
                                print(f"   Args: {server.get('args', 'N/A')}")
            except Exception as e:
                print(f"   ⚠️  Could not read config: {e}")
        else:
            print(f"❌ Not found: {path}")
    
    print("\n" + "="*70)
    print("Next steps:")
    print("1. Check Cursor's MCP panel (View → MCP)")
    print("2. Look for Ball Don't Lie available tools")
    print("3. Use the appropriate example above based on what you find")
    print("="*70)


# ============================================================================
# READY-TO-USE TEMPLATE (Copy this to external_stats.py)
# ============================================================================

def get_player_game_stats_TEMPLATE(player_name: str, game_date: str = None):
    """
    TEMPLATE: Copy this to external_stats.py and fill in the blanks
    """
    from logger_config import setup_logger
    logger = setup_logger('external_stats')
    
    try:
        logger.info(f"Getting game stats for {player_name}, date: {game_date or 'most recent'}")
        
        # ============================================================
        # STEP 1: Initialize/get your MCP client
        # ============================================================
        client = get_mcp_client()  # Your initialization from get_mcp_client()
        
        # ============================================================
        # STEP 2: Call the MCP method
        # Replace this with your actual MCP call
        # ============================================================
        # Option A: Direct method call
        # response = client.get_nfl_player_stats(player_name, game_date)
        
        # Option B: REST API
        # response = requests.get(f"{API_URL}/players/{player_name}/stats")
        
        # Option C: Cursor MCP tool
        # response = mcp_call("ball_dont_lie_player_stats", {"player": player_name})
        
        response = YOUR_MCP_CALL_HERE  # ← REPLACE THIS
        
        # ============================================================
        # STEP 3: Transform response to standard format
        # ============================================================
        return {
            'player_name': response['player_name'],  # Adjust based on actual response
            'game_date': response['game_date'],
            'opponent': response.get('opponent', 'N/A'),
            'stats': {
                'touchdowns': response['stats']['touchdowns'],
                'yards': response['stats']['total_yards'],
                'receptions': response['stats'].get('receptions', 0),
                # Add more stats as needed
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting player game stats: {e}", exc_info=True)
        return {'error': str(e)}


# ============================================================================
# RUN THIS TO HELP DEBUG
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🏈 Ball Don't Lie MCP Implementation Helper")
    print("="*70 + "\n")
    
    find_mcp_interface()
    
    print("\n" + "="*70)
    print("📚 Available examples above:")
    print("  1. Cursor MCP (most common)")
    print("  2. Python SDK")
    print("  3. REST API")
    print("  4. GraphQL API")
    print("="*70 + "\n")

