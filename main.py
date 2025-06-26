"""
Chain-of-Table (CoT) - Main Algorithm
Complete implementation of step-by-step tabular reasoning
"""

import json
import argparse
import sys
from typing import List, Dict, Any

from utils.table_io import load_table, save_chain_results, validate_table_format
from reasoner import ChainOfTableReasoner

def load_table_from_file(file_path: str) -> List[Dict]:
    """Load table from file using table_io"""
    try:
        table = load_table(file_path)
        
        # Validate loaded table
        validation = validate_table_format(table)
        if not validation['is_valid']:
            print(f"⚠️  Table warnings:")
            for error in validation['errors']:
                print(f"  ❌ {error}")
        
        if validation['warnings']:
            for warning in validation['warnings']:
                print(f"  ⚠️  {warning}")
        
        print(f"✅ Table loaded: {validation['stats']['rows']} rows, {validation['stats']['columns']} columns")
        return table
        
    except Exception as e:
        print(f"❌ Error loading table: {e}")
        return []


def save_results(results: Dict[str, Any], output_path: str) -> None:
    """Save results to JSON file using table_io"""
    try:
        save_chain_results(results, output_path)
    except Exception as e:
        print(f"❌ Error saving results: {e}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Chain-of-Table Reasoning')
    parser.add_argument('--table', type=str, default='sample_table.json',
                       help='Path to JSON table file')
    parser.add_argument('--question', type=str, 
                       default='What country has the most cyclists in the top 3?',
                       help='Question to answer')
    parser.add_argument('--output', type=str, default='results.json',
                       help='Output file for results')
    parser.add_argument('--max-steps', type=int, default=10,
                       help='Maximum number of steps')
    parser.add_argument('--quiet', action='store_true',
                       help='Quiet mode (no detailed output)')
    
    args = parser.parse_args()
    
    # Load table
    table = load_table_from_file(args.table)
    if not table:
        print("❌ Could not load table")
        return
    
    # Create reasoner
    reasoner = ChainOfTableReasoner(
        max_steps=args.max_steps,
        verbose=not args.quiet
    )
    
    # Execute reasoning
    results = reasoner.reason(table, args.question)
    
    # Save results
    if args.output:
        save_results(results, args.output)
    
    # Show final result
    if args.quiet:
        print(f"Answer: {results['answer']}")
    
    return results

if __name__ == "__main__":
    main()