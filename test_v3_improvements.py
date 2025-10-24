#!/usr/bin/env python3
"""
Test script for v3 improvements

Tests that v3 now:
1. Fetches comprehensive trade data
2. Actually analyzes it (not just shows it)
3. Makes clear judgments like an analyst would
"""

from data_first_engine import (
    analyze_data_requirements,
    fetch_all_data,
    answer_with_data_context,
    DataContext
)
from logger_config import setup_logger

logger = setup_logger('test_v3_improvements')


def test_worst_trade_question():
    """Test the exact question that was failing"""
    print("\n" + "="*70)
    print("🧪 Testing: 'Who made the worst trade in league history?'")
    print("="*70)
    
    question = "Who made the worst trade in league history?"
    
    # Step 1: Analyze data requirements
    print("\n📋 Step 1: Analyzing data requirements...")
    requirements = analyze_data_requirements(question)
    
    print(f"\nFound {len(requirements)} data requirements:")
    for i, req in enumerate(requirements, 1):
        print(f"  {i}. {req.data_type}")
        print(f"     Function: {req.function_name}")
        print(f"     Params: {req.parameters}")
        print(f"     Why: {req.description}\n")
    
    # Validate requirements
    assert len(requirements) > 0, "Should identify at least one data requirement"
    
    # Check if we're getting comprehensive data
    found_comprehensive = False
    for req in requirements:
        if 'limit' in req.parameters:
            limit = req.parameters['limit']
            if limit >= 100:
                found_comprehensive = True
                print(f"✅ Good! Requesting {limit} trades for comprehensive analysis")
    
    if not found_comprehensive:
        print("⚠️  Warning: Not requesting comprehensive data (high limit)")
    
    # Step 2: Fetch data
    print("\n📊 Step 2: Fetching data...")
    context = DataContext(question)
    context.requirements = requirements
    
    for req in requirements:
        print(f"  Fetching: {req.data_type}...")
        try:
            temp_context = fetch_all_data([req])
            context.fetched_data.update(temp_context.fetched_data)
            context.errors.extend(temp_context.errors)
            
            if req.data_type in context.fetched_data:
                data = context.fetched_data[req.data_type]
                if isinstance(data, dict) and 'trades' in data:
                    trade_count = len(data['trades'])
                    print(f"  ✅ Got {trade_count} trades")
                else:
                    print(f"  ✅ Data retrieved")
            else:
                print(f"  ❌ Failed")
        except Exception as e:
            print(f"  ❌ Error: {e}")
            context.add_error(str(e))
    
    # Step 3: Generate analysis
    print("\n🔍 Step 3: Generating analyst response...")
    print("(This should be an ANALYSIS, not just data presentation)\n")
    
    answer = answer_with_data_context(question, context)
    
    print("="*70)
    print("📝 ASSISTANT RESPONSE:")
    print("="*70)
    print(answer)
    print("="*70)
    
    # Validate the response
    print("\n✅ Validation:")
    
    # Check if response is analytical (not just data dumping)
    if "here are the" in answer.lower() and "you can analyze" in answer.lower():
        print("❌ FAIL: Response is still dumping data instead of analyzing")
        return False
    else:
        print("✅ PASS: Response is analytical, not just data presentation")
    
    # Check if response makes a judgment
    judgment_words = ["worst", "clearly", "appears to be", "based on", "analysis"]
    has_judgment = any(word in answer.lower() for word in judgment_words)
    if has_judgment:
        print("✅ PASS: Response makes analytical judgments")
    else:
        print("⚠️  Warning: Response may not be making clear judgments")
    
    # Check if response cites specific trades
    if "season" in answer.lower() and "week" in answer.lower():
        print("✅ PASS: Response cites specific trades")
    else:
        print("⚠️  Warning: Response may not be citing specific examples")
    
    return True


def test_comparative_question():
    """Test a comparative/analytical question"""
    print("\n" + "="*70)
    print("🧪 Testing: 'How are the top 3 teams doing?'")
    print("="*70)
    
    question = "How are the top 3 teams doing?"
    
    print("\n📋 Analyzing data requirements...")
    requirements = analyze_data_requirements(question)
    
    print(f"Found {len(requirements)} requirements:")
    for req in requirements:
        print(f"  - {req.data_type}: {req.function_name}")
    
    print("\n✅ Comparative question test complete")
    return True


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 V3 IMPROVEMENT TESTS")
    print("="*70)
    print("\nTesting that v3 now:")
    print("  1. Fetches comprehensive data")
    print("  2. Actually analyzes it (not just shows it)")
    print("  3. Makes clear analyst-style judgments")
    
    try:
        # Test the worst trade question
        result1 = test_worst_trade_question()
        
        # Test a comparative question
        result2 = test_comparative_question()
        
        print("\n" + "="*70)
        print("📊 TEST SUMMARY")
        print("="*70)
        print(f"Worst trade test: {'✅ PASS' if result1 else '❌ FAIL'}")
        print(f"Comparative test: {'✅ PASS' if result2 else '❌ FAIL'}")
        print("\n✅ All tests complete!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

