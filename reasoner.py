"""
Chain-of-Table (CoT) - Reasoner
Complete implementation of step-by-step tabular reasoner
"""

from typing import List, Dict, Any, Union

from prompts.dynamic_plan import get_next_operation
from prompts.generate_args import get_operation_args
from prompts.query import get_final_answer
from utils.table_ops import apply_operation, format_table_as_pipe, validate_table


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