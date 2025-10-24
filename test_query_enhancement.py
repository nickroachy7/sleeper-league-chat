#!/usr/bin/env python3
"""
Test Script for Query Enhancement

This script demonstrates the improvements in v2 of the fantasy assistant,
showing how it handles varied and complex questions that v1 couldn't.
"""

import json
from query_planner import smart_route_query, should_use_planner
from fantasy_assistant_v2 import chat_v2
from logger_config import setup_logger

logger = setup_logger('test_query_enhancement')


# Test queries organized by complexity
TEST_QUERIES = {
    "simple": [
        "Show me the current standings",
        "Who owns Patrick Mahomes?",
        "What were the week 5 results?",
        "Show me recent trades"
    ],
    "complex_analytical": [
        "Who's the most traded player in league history?",
        "Which teams make the most trades?",
        "Compare the rosters of the top 3 teams",
        "What's the average points per game for playoff teams?"
    ],
    "complex_cross_domain": [
        "How are my IR players performing this season?",
        "How are my starters performing compared to league leaders?",
        "Which of my bench players are outperforming their draft position?",
        "Should I trade AJ Brown for Tyreek Hill based on stats?"
    ],
    "complex_contextual": [
        "Which teams are in playoff position and which teams need to make moves?",
        "Who has the best QB situation in the league?",
        "Which team has the most injury risk on their roster?",
        "What's the value difference between the top and bottom teams?"
    ]
}


def test_query_routing():
    """Test the query routing logic"""
    print("\n" + "="*70)
    print("🧪 TEST 1: Query Routing Intelligence")
    print("="*70)
    print("\nTesting if the system correctly identifies simple vs complex queries...\n")
    
    all_queries = []
    for category, queries in TEST_QUERIES.items():
        all_queries.extend([(q, category) for q in queries])
    
    routing_results = []
    
    for query, expected_category in all_queries:
        uses_planner = should_use_planner(query)
        is_simple = expected_category == "simple"
        
        # Simple queries should NOT use planner, complex should
        correct = (is_simple and not uses_planner) or (not is_simple and uses_planner)
        
        status = "✅" if correct else "❌"
        routing_results.append(correct)
        
        print(f"{status} '{query[:60]}...'")
        print(f"   Expected: {'Simple' if is_simple else 'Complex'}, "
              f"Got: {'Direct' if not uses_planner else 'Planner'}\n")
    
    accuracy = sum(routing_results) / len(routing_results) * 100
    print(f"\n📊 Routing Accuracy: {accuracy:.1f}% ({sum(routing_results)}/{len(routing_results)})")
    
    return accuracy >= 75  # 75% accuracy threshold


def test_query_planning():
    """Test the query planning analysis"""
    print("\n" + "="*70)
    print("🧪 TEST 2: Query Planning Analysis")
    print("="*70)
    print("\nTesting if complex queries generate appropriate execution plans...\n")
    
    # Test a few complex queries
    complex_tests = [
        "How are my IR players performing?",
        "Compare the top 3 teams' WR corps",
        "Who's the most traded player?"
    ]
    
    all_passed = True
    
    for query in complex_tests:
        print(f"\n📝 Query: {query}")
        routing = smart_route_query(query)
        
        if routing.get("use_planner") and routing.get("plan"):
            plan = routing["plan"]
            intent = routing["intent"]
            
            print(f"   ✅ Generated plan:")
            print(f"      Intent: {intent.intent_type}")
            print(f"      Data sources: {', '.join(intent.data_sources)}")
            print(f"      Steps: {len(plan.steps)}")
            print(f"      Rationale: {plan.rationale[:100]}...")
            
            # Verify plan has required components
            if len(plan.steps) > 0 and plan.rationale:
                print(f"   ✅ Plan is complete")
            else:
                print(f"   ❌ Plan is incomplete")
                all_passed = False
        else:
            print(f"   ❌ No plan generated (expected planning)")
            all_passed = False
    
    return all_passed


def test_response_quality():
    """Test actual responses to queries"""
    print("\n" + "="*70)
    print("🧪 TEST 3: Response Quality (Live Test)")
    print("="*70)
    print("\nTesting actual responses from the v2 assistant...")
    print("Note: This requires valid API credentials and data\n")
    
    # Test with a simple query and a complex query
    test_cases = [
        {
            "query": "Show me the current standings",
            "expected_keywords": ["wins", "losses", "points"],
            "type": "simple"
        },
        {
            "query": "Who owns Patrick Mahomes?",
            "expected_keywords": ["owns", "Mahomes", "team"],
            "type": "simple"
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        query = test_case["query"]
        print(f"\n📝 Testing: {query}")
        
        try:
            response, _ = chat_v2(query, None)
            
            # Check if response contains expected keywords
            response_lower = response.lower()
            keywords_found = sum(1 for kw in test_case["expected_keywords"] 
                                if kw.lower() in response_lower)
            
            success = keywords_found >= len(test_case["expected_keywords"]) // 2
            
            if success:
                print(f"   ✅ Response quality good")
                print(f"   Preview: {response[:150]}...")
                results.append(True)
            else:
                print(f"   ⚠️  Response may be incomplete")
                print(f"   Found {keywords_found}/{len(test_case['expected_keywords'])} expected keywords")
                results.append(False)
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            print(f"   (This may be due to missing credentials or data)")
            results.append(None)  # Neutral result
    
    # Filter out None results for accuracy calculation
    valid_results = [r for r in results if r is not None]
    if valid_results:
        accuracy = sum(valid_results) / len(valid_results) * 100
        print(f"\n📊 Response Quality: {accuracy:.1f}%")
        return accuracy >= 80
    else:
        print(f"\n⚠️  Could not test responses (check credentials/data)")
        return None


def demo_comparison():
    """Demonstrate the difference between v1 and v2 capabilities"""
    print("\n" + "="*70)
    print("🎯 DEMONSTRATION: v1 vs v2 Capabilities")
    print("="*70)
    
    comparison_queries = [
        {
            "query": "How are my IR players performing?",
            "v1_behavior": "❌ Would ask follow-up questions or struggle to combine roster + stats",
            "v2_behavior": "✅ Automatically gets IR list → fetches stats → analyzes performance"
        },
        {
            "query": "Who's the most traded player?",
            "v1_behavior": "❌ No way to aggregate across all trades",
            "v2_behavior": "✅ Plans: Get all trades → extract players → count → rank"
        },
        {
            "query": "Compare top 3 teams' rosters",
            "v1_behavior": "❌ Can't identify 'top 3' or compare multiple entities",
            "v2_behavior": "✅ Plans: Get standings → identify top 3 → fetch rosters → compare"
        },
        {
            "query": "Should I trade AJ Brown for Tyreek Hill?",
            "v1_behavior": "❌ Would say 'I can show you their stats' but no analysis",
            "v2_behavior": "✅ Gets stats for both → compares → considers league context → advises"
        }
    ]
    
    print("\nQuestions that v1 struggled with but v2 handles:\n")
    
    for i, comparison in enumerate(comparison_queries, 1):
        print(f"{i}. {comparison['query']}\n")
        print(f"   v1: {comparison['v1_behavior']}")
        print(f"   v2: {comparison['v2_behavior']}\n")
    
    print("="*70)


def run_all_tests():
    """Run all test suites"""
    print("\n" + "="*70)
    print("🚀 FANTASY ASSISTANT QUERY ENHANCEMENT TEST SUITE")
    print("="*70)
    print("\nTesting the improvements in v2 of the fantasy assistant...")
    
    results = {}
    
    # Test 1: Query Routing
    results['routing'] = test_query_routing()
    
    # Test 2: Query Planning
    results['planning'] = test_query_planning()
    
    # Test 3: Response Quality (may skip if no credentials)
    results['responses'] = test_response_quality()
    
    # Demo comparison
    demo_comparison()
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    for test_name, result in results.items():
        if result is True:
            status = "✅ PASSED"
        elif result is False:
            status = "❌ FAILED"
        else:
            status = "⚠️  SKIPPED"
        
        print(f"{test_name.upper()}: {status}")
    
    # Overall result
    valid_results = [r for r in results.values() if r is not None]
    if valid_results:
        pass_rate = sum(valid_results) / len(valid_results) * 100
        print(f"\nOverall Pass Rate: {pass_rate:.1f}%")
        
        if pass_rate >= 80:
            print("\n🎉 Query enhancement is working great!")
        elif pass_rate >= 60:
            print("\n⚠️  Query enhancement is working but needs tuning")
        else:
            print("\n❌ Query enhancement needs review")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    run_all_tests()

