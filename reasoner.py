"""
Chain-of-Table (CoT) - Reasoner
Complete implementation of step-by-step tabular reasoner
"""

from typing import List, Dict, Any, Union

from prompts.dynamic_plan import dynamic_plan
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
        
        end = False
        # Main loop
        for step in range(self.max_steps):
            get_op = True
            excluded_ops = []
            while (get_op):
                if self.verbose:
                    print(f"--- STEP {step + 1} ---")
                
                # 1. DynamicPlan: Select operation
                operation = dynamic_plan(current_table, question, chain, self.max_steps, excluded_ops)
                
                if self.verbose:
                    print(f"🔧 Selected operation: {operation}")
                
                # Check if finished and avoiding infinite loops
                if operation == "[E]" or operation in excluded_ops:
                    operation = "[E]"
                    end = True
                    if self.verbose:
                        print("✅ End of operation chain")
                    break
                
                # 2. GenerateArgs: Generate arguments
                args = get_operation_args(current_table, question, operation)
                
                if self.verbose:
                    print(f"📋 Arguments: {args}")

                # 3. Smart validation: Check for conflicts and repetitions
                get_op = False
                retry_reason = ""
                
                # Check for duplicate column addition
                if operation == "f_add_column" and current_table:
                    current_columns = list(current_table[0].keys())
                    if isinstance(args, list) and len(args) >= 1:
                        proposed_column = args[0]
                        if proposed_column in current_columns:
                            get_op = True
                            excluded_ops.append("f_add_column")
                            retry_reason = f"Column '{proposed_column}' already exists in {current_columns}"
                
                # Check for repeated operation with same arguments
                if not get_op and len(chain) > 0:
                    last_op_args = (operation, str(args))  # Convert to string for comparison
                    for item in chain:
                        if isinstance(item, tuple) and len(item) == 2:
                            prev_op, prev_args = item
                            if (prev_op, str(prev_args)) == last_op_args:
                                get_op = True
                                excluded_ops.append(operation)
                                retry_reason = f"Operation {operation}({args}) was already performed"
                                break
                            
                # Check if we can already answer the question (for counting questions)
                if not get_op and current_table and len(current_table) > 0:
                    columns = list(current_table[0].keys())
                    # If we have Count column or question is about "most", we might have the answer
                    if "Count" in columns and ("most" in question.lower() or "highest" in question.lower() or "lowest" in question.lower() or "least" in question.lower()) and operation != "f_sort_by":
                        # Check if the table is in a format that can answer the question
                        count_values = [row.get("Count", 0) for row in current_table if "Count" in row]
                        if count_values and len(set(count_values)) > 1:  # Different counts exist
                            get_op = True
                            excluded_ops.append(operation)
                            retry_reason = "Answer is already available in the current table"
                
                # Perform retry if needed
                if get_op and self.verbose:
                    print(f"⚠️  Conflict detected: {retry_reason}")
                    print("🔄 Retrying with different operation...\n")

            if(end): break

            # 4. Apply operation
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
    
    def _retry_operation_selection(self, table: List[Dict], question: str, chain: List[Union[str, tuple]], excluded_ops: List[str]) -> str:
        """
        Retry operation selection with certain operations excluded.
        
        Args:
            table: Current table
            question: Question to answer  
            chain: Current operation chain
            excluded_ops: List of operations to exclude from selection
            
        Returns:
            Selected operation name
        """
        # Create a modified dynamic plan that excludes certain operations
        from prompts.dynamic_plan import create_dynamic_plan_prompt
        from utils.table_ops import get_available_operations
        from request.request import ask_llm
        
        # Get available operations and remove excluded ones
        available_ops = get_available_operations()
        filtered_ops = [op for op in available_ops if op not in excluded_ops]
        
        if not filtered_ops:
            return "[E]"  # No operations left, end
        
        # Create modified prompt with filtered operations
        table_str = format_table_as_pipe(table)
        
        # Format operation history  
        chain_str = self._format_chain_history(chain)
        current_steps = len(chain)
        
        # Extract current column names
        if table:
            current_columns = list(table[0].keys())
            columns_str = ", ".join(current_columns)
        else:
            columns_str = "None"
            
        candidates_str = ", ".join(filtered_ops)
        
        prompt = f"""You are an expert in tabular reasoning. Your task is to select the next atomic operations needed to solve a question about a table. In total, only {self.max_steps} operations can be used.

CURRENT TABLE:
{table_str}

CURRENT COLUMNS: {columns_str}

QUESTION:
{question}

OPERATION HISTORY:
{chain_str}

AVAILABLE OPERATIONS: {candidates_str}

IMPORTANT: Some operations have been excluded due to conflicts. Choose from the AVAILABLE OPERATIONS only.

Select the most appropriate operation to advance toward the answer.
Respond ONLY with the operation name, DO NOT INCLUDE arguments.

What is the next most appropriate operation?
OPERATION:"""
        
        response = ask_llm(prompt)
        
        # Parse response
        response = response.strip()
        lines = response.split('\n')
        for line in lines:
            if 'OPERATION:' in line:
                operation = line.split('OPERATION:')[-1].strip()
                return operation.split(',')[0].strip()
        
        # Fallback
        operation = response.split('\n')[-1].split(',')[0].strip()
        return operation.split('(')[0].strip()
    
    def _format_chain_history(self, chain: List[Union[str, tuple]]) -> str:
        """Helper method to format chain history"""
        if not chain:
            return "[B] (start)"
        
        history_parts = []
        for item in chain:
            if isinstance(item, str):
                if item == '[B]':
                    history_parts.append("[B] (start)")
                elif item == '[E]':
                    history_parts.append("[E] (end)")
                else:
                    history_parts.append(item)
            elif isinstance(item, tuple) and len(item) == 2:
                op, args = item
                if isinstance(args, list):
                    args_str = f"({', '.join(map(str, args))})"
                else:
                    args_str = f"({args})"
                history_parts.append(f"{op}{args_str}")
            else:
                history_parts.append(str(item))
        
        return " → ".join(history_parts)