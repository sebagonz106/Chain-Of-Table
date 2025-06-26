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


def dynamic_plan_simple(table: List[Dict], question: str, chain: List[Union[str, tuple]]) -> str:
    """
    Simplified version of dynamic_plan for testing without LLM.
    Implements basic operation selection logic.
    
    Args:
        table: Current table
        question: Question to answer
        chain: Operation history
    
    Returns:
        Name of next operation
    """
    # If no table, finish
    if not table:
        return "[E]"
    
    # Get only operations (without arguments) from history
    operations_applied = []
    for item in chain:
        if isinstance(item, tuple):
            operations_applied.append(item[0])
        elif isinstance(item, str) and item not in ['[B]', '[E]']:
            operations_applied.append(item)
    
    # Simple logic based on common pattern
    if not operations_applied:
        # First operation: usually add missing information
        columns = list(table[0].keys()) if table else []
        if 'Country' not in columns and any('(' in str(row.get('Cyclist', '')) for row in table):
            return "f_add_column"
        elif len(table) > 5:
            return "f_select_row"
        else:
            return "f_group_by"
    
    elif 'f_add_column' in operations_applied and 'f_select_row' not in operations_applied:
        # If we added column but didn't select rows, probably need to filter
        if len(table) > 3:
            return "f_select_row"
        else:
            return "f_group_by"
    
    elif 'f_select_row' in operations_applied and 'f_group_by' not in operations_applied:
        # If we selected rows, probably need to group
        columns = list(table[0].keys()) if table else []
        if 'Country' in columns or 'City' in columns or any('Category' in col for col in columns):
            return "f_group_by"
        else:
            return "[E]"
    
    elif 'f_group_by' in operations_applied and 'f_sort_by' not in operations_applied:
        # If we grouped, might need to sort
        columns = list(table[0].keys()) if table else []
        if 'Count' in columns:
            return "f_sort_by"
        else:
            return "[E]"
    
    else:
        # Default: finish
        return "[E]"


def dynamic_plan(table: List[Dict], question: str, chain: List[Union[str, tuple]], 
                use_llm: bool = False, llm_function=ask_llm) -> str:
    """
    Main function to select the next operation.
    
    Args:
        table: Current table
        question: Question to answer
        chain: Operation history
        use_llm: Whether to use a real LLM or simplified version
        llm_function: LLM function to generate responses
    
    Returns:
        Name of next operation
    """
    if use_llm and llm_function:
        # Use real LLM
        prompt = create_dynamic_plan_prompt(table, question, chain)
        response = llm_function(prompt)
        return parse_operation_response(response)
    else:
        # Use simplified version
        return dynamic_plan_simple(table, question, chain)


# Function for compatibility with existing code
def get_next_operation(table: List[Dict], question: str, chain: List[Union[str, tuple]]) -> str:
    """
    Convenience function to get the next operation.
    """
    return dynamic_plan(table, question, chain, use_llm=False)