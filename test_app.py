"""
LLM-focused Test Suite for Chain-of-Table Application
Tests LLM integration and reasoning functionality
"""

import os
import sys
import json
import time
from typing import List, Dict, Any

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all LLM-related modules can be imported"""
    print("🔧 Testing LLM-related imports...")
    
    try:
        from reasoner import ChainOfTableReasoner
        print("  ✅ reasoner imported successfully")
    except ImportError as e:
        print(f"  ❌ Failed to import reasoner: {e}")
        return False
    
    try:
        from request.request import ask_llm
        print("  ✅ request.request imported successfully")
    except ImportError as e:
        print(f"  ❌ Failed to import request.request: {e}")
        return False
    
    try:
        from prompts.dynamic_plan import get_next_operation
        from prompts.generate_args import get_operation_args
        from prompts.query import get_final_answer
        print("  ✅ prompt modules imported successfully")
    except ImportError as e:
        print(f"  ❌ Failed to import prompt modules: {e}")
        return False
    
    return True


def test_environment():
    """Test environment setup for LLM connectivity"""
    print("\n🌍 Testing LLM environment...")
    
    # Check if .env file exists
    env_path = ".env"
    if os.path.exists(env_path):
        print("  ✅ .env file found")
    else:
        print("  ⚠️  .env file not found (using system environment variables)")
    
    # Test Ollama connection (primary LLM)
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [model["name"] for model in models]
            print(f"  ✅ Ollama connected, available models: {model_names}")
            
            # Check if llama3.2 is available
            if any("llama3.2" in name for name in model_names):
                print("  ✅ llama3.2 model found")
            else:
                print("  ⚠️  llama3.2 model not found, will use available model")
        else:
            print(f"  ⚠️  Ollama responded with status {response.status_code}")
    except Exception as e:
        print(f"  ⚠️  Ollama connection failed: {e}")
        print("  ℹ️  Will fall back to other LLM providers or mock responses")
    
    # Check for API keys
    if os.getenv('OPENAI_API_KEY'):
        print("  ✅ OpenAI API key found")
    if os.getenv('ANTHROPIC_API_KEY'):
        print("  ✅ Anthropic API key found")
    
    return True


def test_llm_connection():
    """Test LLM connection"""
    print("\n🤖 Testing LLM connection...")
    
    try:
        from request.request import ask_llm
        
        # Simple test query
        test_query = "What is 2+2? Please respond with just the number."
        
        print("  🔄 Sending test query to LLM...")
        start_time = time.time()
        response = ask_llm(test_query)
        end_time = time.time()
        
        print(f"  ✅ LLM responded in {end_time - start_time:.2f} seconds")
        print(f"  📝 Response: {response[:200]}{'...' if len(response) > 200 else ''}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ LLM connection test failed: {e}")
        return False


def test_chain_of_table_basic():
    """Test basic Chain-of-Table functionality"""
    print("\n⛓️  Testing Chain-of-Table reasoning...")
    
    try:
        from reasoner import ChainOfTableReasoner
        from utils.table_io import load_table
        
        # Load table
        table = load_table("sample_table.json")
        
        # Create reasoner
        reasoner = ChainOfTableReasoner(max_steps=3, verbose=False)
        
        # Simple test question
        question = "How many cyclists are there in total?"
        
        print(f"  🔄 Processing question: '{question}'")
        start_time = time.time()
        results = reasoner.reason(table, question)
        end_time = time.time()
        
        print(f"  ✅ Reasoning completed in {end_time - start_time:.2f} seconds")
        print(f"  📝 Answer: {results.get('answer', 'No answer')}")
        print(f"  🔢 Steps executed: {results.get('steps', 0)}")
        
        if results.get('chain'):
            print(f"  🔗 Operations chain: {[op[0] if isinstance(op, tuple) else op for op in results['chain']]}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Chain-of-Table test failed: {e}")
        return False


def test_full_examples():
    """Test with multiple example questions"""
    print("\n📚 Testing multiple examples...")
    
    try:
        from reasoner import ChainOfTableReasoner
        from utils.table_io import load_table
        
        table = load_table("sample_table.json")
        reasoner = ChainOfTableReasoner(max_steps=5, verbose=False)
        
        test_questions = [
            "Who won the race?",
            "How many cyclists are there in total?",
            "What country has the most cyclists in the top 3?"
        ]
        
        results_summary = []
        
        for i, question in enumerate(test_questions, 1):
            print(f"  🔍 Example {i}: {question}")
            
            try:
                start_time = time.time()
                results = reasoner.reason(table, question)
                end_time = time.time()
                
                answer = results.get('answer', 'No answer')
                steps = results.get('steps', 0)
                
                print(f"    ⏱️  Time: {end_time - start_time:.2f}s")
                print(f"    📝 Answer: {answer}")
                print(f"    🔢 Steps: {steps}")
                
                results_summary.append({
                    'question': question,
                    'answer': answer,
                    'steps': steps,
                    'time': end_time - start_time,
                    'success': True
                })
                
            except Exception as e:
                print(f"    ❌ Failed: {e}")
                results_summary.append({
                    'question': question,
                    'success': False,
                    'error': str(e)
                })
        
        # Summary
        successful = sum(1 for r in results_summary if r.get('success', False))
        print(f"\n  📊 Summary: {successful}/{len(test_questions)} questions processed successfully")
        
        return successful == len(test_questions)
        
    except Exception as e:
        print(f"  ❌ Full examples test failed: {e}")
        return False


def test_main_module():
    """Test the main module functionality with LLM integration"""
    print("\n🚀 Testing main module with LLM...")
    
    try:
        # Test import
        import main
        print("  ✅ main.py imported successfully")
        
        # Check if sample table exists for LLM testing
        if os.path.exists("sample_table.json"):
            print("  ✅ sample_table.json found for LLM testing")
        else:
            print("  ❌ sample_table.json not found - needed for LLM reasoning tests")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Main module test failed: {e}")
        return False


def run_all_tests():
    """Run all tests and provide summary"""
    print("� CHAIN-OF-TABLE LLM TEST SUITE")
    print("=" * 50)
    print("Testing LLM integration and reasoning capabilities")
    
    tests = [
        ("Imports", test_imports),
        ("LLM Environment", test_environment),
        ("LLM Connection", test_llm_connection),
        ("Chain-of-Table Reasoning", test_chain_of_table_basic),
        ("Multiple LLM Examples", test_full_examples),
        ("Main Module", test_main_module)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Final summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if success:
            passed += 1
    
    print(f"\n🏆 OVERALL: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All LLM tests passed! Your Chain-of-Table LLM integration is working correctly!")
    elif passed >= len(results) * 0.7:
        print("⚠️  Most LLM tests passed. Some minor issues may need attention.")
    else:
        print("❌ Several LLM tests failed. Check your LLM configuration and connection.")
    
    return passed == len(results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
