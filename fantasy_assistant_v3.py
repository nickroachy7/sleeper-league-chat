"""
Fantasy League AI Assistant v3 - Data-First Architecture

Key innovation: Separate data gathering from analysis
1. Identify ALL data needs first
2. Fetch EVERYTHING upfront
3. Give complete context to LLM for pure analysis

This is like giving a sports analyst all the game stats BEFORE asking them
to write the analysis, rather than having them look up stats while writing.
"""

import json
from openai import OpenAI
from datetime import datetime
from config import OPENAI_API_KEY, SLEEPER_LEAGUE_ID
from data_first_engine import answer_question_data_first, analyze_data_requirements, fetch_all_data, DataContext
from logger_config import setup_logger

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)
logger = setup_logger('fantasy_assistant_v3')

# Get current date for context
CURRENT_DATE = datetime.now().strftime("%B %d, %Y")


def chat_v3(message: str, conversation_history: list = None, use_data_first: bool = True) -> tuple[str, list]:
    """
    Enhanced chat function with data-first approach.
    
    Args:
        message: User's message
        conversation_history: Previous conversation messages
        use_data_first: Whether to use data-first approach (default: True)
    
    Returns:
        (assistant_response, updated_conversation_history)
    """
    if conversation_history is None:
        conversation_history = []
    
    # Add user message
    conversation_history.append({"role": "user", "content": message})
    
    # Use data-first approach
    if use_data_first:
        logger.info(f"Using DATA-FIRST approach for: {message[:50]}...")
        
        try:
            # Get answer using data-first engine
            response = answer_question_data_first(message)
            
            # Add to conversation history
            conversation_history.append({
                "role": "assistant",
                "content": response
            })
            
            logger.info("✅ DATA-FIRST response generated successfully")
            return response, conversation_history
            
        except Exception as e:
            logger.error(f"Error in data-first approach: {e}", exc_info=True)
            # Fall back to direct response
            logger.info("Falling back to direct response...")
            
            fallback_response = f"I encountered an issue with the data-first approach: {str(e)}\n\nLet me try answering directly..."
            conversation_history.append({
                "role": "assistant",
                "content": fallback_response
            })
            return fallback_response, conversation_history
    else:
        # Direct response without data-first (legacy mode)
        logger.info(f"Using LEGACY mode for: {message[:50]}...")
        
        system_prompt = f"""You are a fantasy football assistant. Today is {CURRENT_DATE}.
        
Answer the user's question directly and concisely."""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                *conversation_history
            ],
            temperature=0.7
        )
        
        answer = response.choices[0].message.content
        conversation_history.append({
            "role": "assistant",
            "content": answer
        })
        
        return answer, conversation_history


def chat_loop_v3():
    """Interactive chat loop with data-first capabilities"""
    print("\n" + "="*70)
    print("🏈 FANTASY LEAGUE AI ASSISTANT v3.0 (Data-First)")
    print("="*70)
    print("\nHello! I'm your DATA-FIRST fantasy football assistant.")
    print("I fetch ALL the data I need BEFORE analyzing, like a real sports analyst!")
    print("\nKey improvement:")
    print("  ✅ Gets ALL data upfront")
    print("  ✅ Then analyzes with complete context")
    print("  ✅ No more incomplete answers!")
    print("\nTry asking:")
    print("  • 'Who has made the worst trade in league history?'")
    print("  • 'How are my IR players performing?'")
    print("  • 'Compare the rosters of playoff teams'")
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
            
            # Get response using data-first approach
            response, conversation_history = chat_v3(user_input, conversation_history)
            
            print(f"\n🤖 Assistant: {response}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Thanks for chatting!\n")
            break
        except Exception as e:
            logger.error(f"Error in chat loop: {e}", exc_info=True)
            print(f"\n❌ Error: {str(e)}")
            print("Please try again or type 'quit' to exit.\n")


def demo_data_first_approach():
    """Demonstrate the data-first approach with the example question"""
    print("\n" + "="*70)
    print("🎯 DEMO: Data-First Approach")
    print("="*70)
    
    question = "Who has made the worst trade in league history?"
    
    print(f"\nQuestion: {question}")
    print("\n" + "="*70)
    
    print("\nSTEP 1: Analyzing what data we need...")
    print("─" * 70)
    requirements = analyze_data_requirements(question)
    print(f"\nData requirements identified: {len(requirements)}")
    for i, req in enumerate(requirements, 1):
        print(f"  {i}. {req.data_type}")
        print(f"     Function: {req.function_name}")
        print(f"     Why: {req.description}")
    
    print("\n" + "="*70)
    print("STEP 2: Fetching ALL required data...")
    print("─" * 70)
    
    context = DataContext(question)
    context.requirements = requirements
    
    for req in requirements:
        print(f"\n  Fetching: {req.data_type}...")
        temp_context = fetch_all_data([req])
        context.fetched_data.update(temp_context.fetched_data)
        context.errors.extend(temp_context.errors)
        
        if req.data_type in context.fetched_data:
            data = context.fetched_data[req.data_type]
            if isinstance(data, list):
                print(f"  ✅ Got {len(data)} items")
            elif isinstance(data, dict):
                print(f"  ✅ Got {len(data)} fields")
            else:
                print(f"  ✅ Data retrieved")
        else:
            print(f"  ❌ Failed to retrieve")
    
    print("\n" + "="*70)
    print("STEP 3: Analyzing with COMPLETE data context...")
    print("─" * 70)
    print("\nNow the LLM has ALL the facts and can act like a sports analyst!")
    print("No more guessing or incomplete answers.\n")
    
    # Show what data we have
    print("Data available to analyst:")
    for data_type in context.fetched_data.keys():
        print(f"  ✅ {data_type}")
    
    print("\n" + "="*70)
    print("STEP 4: Generating expert analysis...")
    print("─" * 70)
    
    # Get the answer
    from data_first_engine import answer_with_data_context
    answer = answer_with_data_context(question, context)
    
    print(f"\n{answer}")
    
    print("\n" + "="*70)
    print("✅ Demo complete!")
    print("="*70)
    print("\nKey difference from v2:")
    print("  v2: Question → Call function → Reason → Call another → Reason → Answer")
    print("  v3: Question → Identify ALL needs → Fetch ALL data → Analyze → Answer")
    print("\nResult: Complete, accurate answers based on ALL relevant data!")
    print("="*70 + "\n")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        # Run the demo
        demo_data_first_approach()
    else:
        # Run the chat loop
        chat_loop_v3()

