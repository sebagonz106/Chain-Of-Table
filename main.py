"""
Chain-of-Table (CoT) - Main Algorithm
Complete implementation of step-by-step tabular reasoning
"""

import json
import argparse
import sys
from typing import List, Dict, Any, Union, Optional

from prompts.dynamic_plan import get_next_operation
from prompts.generate_args import get_operation_args
from prompts.query import get_final_answer
from utils.table_ops import apply_operation, format_table_as_pipe, validate_table
from utils.table_io import load_table, print_table, save_chain_results, validate_table_format


class ChainOfTableReasoner:
    """
    Main class for executing the Chain-of-Table algorithm
    """
    
    def __init__(self, max_steps: int = 10, verbose: bool = True):
        """
        Initialize the Chain-of-Table reasoner.
        
        Args:
            max_steps: Maximum number of steps allowed
            verbose: Whether to show detailed information
        """
        self.max_steps = max_steps
        self.verbose = verbose
        self.chain_history = []
        self.intermediate_tables = []
    
    def reason(self, table: List[Dict], question: str) -> Dict[str, Any]:
        """
        Execute the complete Chain-of-Table algorithm.
        
        Args:
            table: Initial table
            question: Question to answer
        
        Returns:
            Dictionary with the complete result
        """
        # Validate input
        if not validate_table(table):
            return {
                "error": "Invalid table",
                "answer": None,
                "chain": [],
                "tables": []
            }
        
        # Initialize
        current_table = table.copy()
        chain = ['[B]']  # Start
        tables = [current_table.copy()]
        
        if self.verbose:
            print("🚀 STARTING CHAIN-OF-TABLE")
            print("=" * 50)
            print(f"❓ Question: {question}")
            print(f"\n📊 Initial table:")
            print(format_table_as_pipe(current_table))
            print()
        
        # Main loop
        for step in range(self.max_steps):
            if self.verbose:
                print(f"--- STEP {step + 1} ---")
            
            # 1. DynamicPlan: Select operation
            operation = get_next_operation(current_table, question, chain)
            
            if self.verbose:
                print(f"🔧 Selected operation: {operation}")
            
            # Check if finished
            if operation == "[E]":
                if self.verbose:
                    print("✅ End of operation chain")
                break
            
            # 2. GenerateArgs: Generate arguments
            args = get_operation_args(current_table, question, operation)
            
            if self.verbose:
                print(f"📋 Arguments: {args}")
            
            # 3. Apply operation
            try:
                new_table = apply_operation(current_table, operation, args)
                current_table = new_table
                chain.append((operation, args))
                tables.append(current_table.copy())
                
                if self.verbose:
                    print(f"📊 Resulting table:")
                    print(format_table_as_pipe(current_table))
                    print()
            
            except Exception as e:
                if self.verbose:
                    print(f"❌ Error applying operation: {e}")
                break
        
        # Add end marker
        chain.append('[E]')
        
        # 4. Query: Generate final answer
        try:
            answer = get_final_answer(current_table, question)
        except Exception as e:
            if self.verbose:
                print(f"❌ Error generating answer: {e}")
            answer = "Could not generate answer"
        
        if self.verbose:
            print(f"🎯 FINAL ANSWER: {answer}")
            print(f"\n📝 Operation chain:")
            self._print_chain_summary(chain)
        
        # Save history
        self.chain_history = chain
        self.intermediate_tables = tables
        
        return {
            "answer": answer,
            "chain": chain,
            "tables": tables,
            "final_table": current_table,
            "steps": len([x for x in chain if isinstance(x, tuple)])
        }
    
    def _print_chain_summary(self, chain: List[Union[str, tuple]]) -> None:
        """Print a summary of the operation chain"""
        for i, step in enumerate(chain):
            if step == '[B]':
                print(f"  {i}. [B] - Start")
            elif step == '[E]':
                print(f"  {i}. [E] - End")
            elif isinstance(step, tuple):
                op, args = step
                print(f"  {i}. {op}({args})")
            else:
                print(f"  {i}. {step}")
    
    def get_step_by_step_explanation(self) -> str:
        """
        Generate a step-by-step explanation of the reasoning.
        
        Returns:
            String with detailed explanation
        """
        if not self.chain_history or not self.intermediate_tables:
            return "No history available"
        
        explanation = "STEP-BY-STEP EXPLANATION:\n"
        explanation += "=" * 30 + "\n\n"
        
        for i, (step, table) in enumerate(zip(self.chain_history, self.intermediate_tables)):
            if step == '[B]':
                explanation += f"STEP {i}: Start\n"
                explanation += f"Initial table:\n{format_table_as_pipe(table)}\n\n"
            elif step == '[E]':
                explanation += f"STEP {i}: End of reasoning\n\n"
            elif isinstance(step, tuple):
                op, args = step
                explanation += f"STEP {i}: Apply {op} with arguments {args}\n"
                explanation += f"Resulting table:\n{format_table_as_pipe(table)}\n\n"
        
        return explanation


def load_table_from_file(file_path: str) -> List[Dict]:
    """Load table from file using improved table_io"""
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


def demo():
    """Demo function with predefined examples"""
    print("🎭 CHAIN-OF-TABLE DEMO")
    print("=" * 40)
    
    examples = [
        {
            "question": "What country has the most cyclists in the top 3?",
            "description": "Question about grouping and counting"
        },
        {
            "question": "Who won the race?",
            "description": "Question about first place"
        },
        {
            "question": "How many cyclists are there in total?",
            "description": "Question about total count"
        }
    ]
    
    table = load_table_from_file('sample_table.json')
    reasoner = ChainOfTableReasoner(verbose=True)
    
    for i, example in enumerate(examples, 1):
        print(f"\n🔍 EXAMPLE {i}: {example['description']}")
        print("-" * 50)
        
        results = reasoner.reason(table, example['question'])
        
        print(f"\n📋 SUMMARY:")
        print(f"  Question: {example['question']}")
        print(f"  Answer: {results['answer']}")
        print(f"  Steps executed: {results['steps']}")
        print()


if __name__ == "__main__":
    # If run without arguments, show demo
    if len(sys.argv) == 1:
        demo()
    else:
        main()