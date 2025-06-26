"""
Prompt for DynamicPlan: Select the next operation to apply in Chain-of-Table
"""

from typing import List, Dict, Any, Union
import sys
import os

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.table_ops import format_table_as_pipe, get_available_operations
from request.request import ask_llm


def create_dynamic_plan_prompt(table: List[Dict], question: str, chain: List[Union[str, tuple]]) -> str:
    """
    Create the prompt for the LLM to select the next operation.
    
    Args:
        table: Current table
        question: Question to answer
        chain: History of applied operations
    
    Returns:
        String with formatted prompt
    """
    
    # Format current table
    table_str = format_table_as_pipe(table)
    
    # Format operation history
    chain_str = format_chain_history(chain)
    
    # Get candidate operations
    candidates = get_available_operations()
    candidates_str = ", ".join(candidates)
    
    prompt = f"""You are an expert in tabular reasoning. Your task is to select the next atomic operation to solve a question about a table.

CURRENT TABLE:
{table_str}

QUESTION:
{question}

OPERATION HISTORY:
{chain_str}

CANDIDATE OPERATIONS:
{candidates_str}

REASONING EXAMPLES:

Example 1:
Table: Rank | Cyclist
       1    | Alej. (ESP)
       2    | Davide (ITA)
       3    | Paolo (ITA)
       4    | Haimar  | ESP
Question: Which country had the most cyclists in the top 3?
History: [B]
→ I need to extract countries from cyclist names.
OPERATION: f_add_column

Example 2:
Table: Rank | Cyclist | Country
       1    | Alej.   | ESP
       2    | Davide  | ITA
       3    | Paolo   | ITA
       4    | Haimar  | ESP
Question: Which country had the most cyclists in the top 3?
History: [B], f_add_column(Country)
→ I need to select only the first 3 cyclists.
OPERATION: f_select_row

Example 3:
Table: Rank | Cyclist | Country
       1    | Alej.   | ESP
       2    | Davide  | ITA
       3    | Paolo   | ITA
Question: Which country had the most cyclists in the top 3?
History: [B], f_add_column(Country), f_select_row([1,2,3])
→ I need to group by country to count how many cyclists per country.
OPERATION: f_group_by

Example 4:
Table: Country | Count
       ITA     | 2
       ESP     | 1
Question: Which country had the most cyclists in the top 3?
History: [B], f_add_column(Country), f_select_row([1,2,3]), f_group_by(Country)
→ I already have the final result. I can answer the question.
OPERATION: [E]

INSTRUCTIONS:
1. Analyze the current table and question.
2. Consider the history of operations already applied.
3. Select the most appropriate operation to advance toward the answer.
4. If you can already answer the question with the current table, select [E].
5. Respond ONLY with the operation name.

What is the next most appropriate operation?
OPERATION:"""

    return prompt


def format_chain_history(chain: List[Union[str, tuple]]) -> str:
    """
    Format operation history for the prompt.
    
    Args:
        chain: List of applied operations
    
    Returns:
        Formatted string of history
    """
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


def parse_operation_response(response: str) -> str:
    """
    Parse LLM response to extract the operation.
    
    Args:
        response: Complete LLM response
    
    Returns:
        Extracted operation name
    """
    # Clean the response
    response = response.strip()
    
    # Look for lines containing "OPERATION:"
    lines = response.split('\n')
    for line in lines:
        if 'OPERATION:' in line:
            operation = line.split('OPERATION:')[-1].strip()
            return operation
    
    # If expected format not found, use last line
    return response.split('\n')[-1].strip()


def dynamic_plan(table: List[Dict], question: str, chain: List[Union[str, tuple]], 
                use_llm: bool = True, llm_function=ask_llm) -> str:
    """
    Main function to select the next operation.
    
    Args:
        table: Current table
        question: Question to answer
        chain: Operation history
        use_llm: Whether to use a real LLM (always True now)
        llm_function: LLM function to generate responses
    
    Returns:
        Name of next operation
    """
    if not llm_function:
        raise ValueError("LLM function is required. No fallback methods available.")
    
    # Always use LLM - no simplified version
    prompt = create_dynamic_plan_prompt(table, question, chain)
    response = llm_function(prompt)
    return parse_operation_response(response)


# Function for compatibility with existing code
def get_next_operation(table: List[Dict], question: str, chain: List[Union[str, tuple]]) -> str:
    """
    Convenience function to get the next operation using LLM.
    """
    from request.request import ask_llm
    return dynamic_plan(table, question, chain, use_llm=True, llm_function=ask_llm)