"""
Prompt for GenerateArgs: Generate necessary arguments for a specific operation
"""

from typing import List, Dict, Any, Union
import sys
import os

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.table_ops import format_table_as_pipe


def create_generate_args_prompt(table: List[Dict], question: str, operation: str) -> str:
    """
    Create the prompt for the LLM to generate operation arguments.
    
    Args:
        table: Current table
        question: Question to answer
        operation: Operation for which to generate arguments
    
    Returns:
        String with formatted prompt
    """
    
    table_str = format_table_as_pipe(table)
    
    prompt = f"""You are an expert in tabular reasoning. Your task is to generate appropriate arguments for a specific operation in Chain-of-Table.

CURRENT TABLE:
{table_str}

QUESTION:
{question}

OPERATION TO EXECUTE:
{operation}

ARGUMENT EXAMPLES BY OPERATION:

EXAMPLE f_add_column:
Operation: f_add_column
Table: Rank | Cyclist
       1    | Alej. (ESP)
       2    | Davide (ITA)
Question: Which country had the most cyclists?
→ I need to extract countries from cyclist names
ARGUMENTS: Country

EXAMPLE f_select_row:
Operation: f_select_row
Table: Rank | Cyclist | Country
       1    | Alej.   | ESP
       2    | Davide  | ITA
       3    | Paolo   | ITA
       4    | Haimar  | ESP
Question: Which country had the most cyclists in the top 3?
→ I need only the first 3 rows
ARGUMENTS: [1, 2, 3]

EXAMPLE f_select_column:
Operation: f_select_column
Table: Rank | Cyclist | Country | Age
       1    | Alej.   | ESP     | 25
       2    | Davide  | ITA     | 28
Question: Which country had the most cyclists?
→ I only need columns relevant to the question
ARGUMENTS: ["Cyclist", "Country"]

EXAMPLE f_group_by:
Operation: f_group_by
Table: Rank | Cyclist | Country
       1    | Alej.   | ESP
       2    | Davide  | ITA
       3    | Paolo   | ITA
Question: Which country had the most cyclists?
→ I need to group by country to count
ARGUMENTS: Country

EXAMPLE f_sort_by:
Operation: f_sort_by
Table: Country | Count
       ESP     | 2
       ITA     | 3
Question: Which country had the most cyclists?
→ I need to sort by count descending to see the highest
ARGUMENTS: ["Count", false]

INSTRUCTIONS:
1. Analyze the current table and question.
2. Consider what arguments the operation "{operation}" needs to advance toward the answer.
3. For f_add_column: specify the name of the new column.
4. For f_select_row: specify row indices (1-indexed).
5. For f_select_column: specify column names.
6. For f_group_by: specify the column to group by.
7. For f_sort_by: specify the column and whether ascending (true) or descending (false).
8. Respond ONLY with arguments in the appropriate format.

What are the appropriate arguments for {operation}?
ARGUMENTS:"""

    return prompt


def parse_args_response(response: str, operation: str) -> Union[str, List, int]:
    """
    Parse LLM response to extract arguments.
    
    Args:
        response: Complete LLM response
        operation: Operation for which arguments were generated
    
    Returns:
        Parsed arguments in appropriate format
    """
    # Clean the response
    response = response.strip()
    
    # Look for lines containing "ARGUMENTS:"
    lines = response.split('\n')
    for line in lines:
        if 'ARGUMENTS:' in line:
            args_str = line.split('ARGUMENTS:')[-1].strip()
            break
    else:
        # If expected format not found, use last line
        args_str = response.split('\n')[-1].strip()
    
    # Parse according to operation type
    try:
        if operation == "f_add_column":
            # Expect a string
            return args_str.strip('"\'')
        
        elif operation == "f_select_row":
            # Expect a list of integers or an integer
            if '[' in args_str and ']' in args_str:
                # It's a list
                args_str = args_str.strip('[]')
                return [int(x.strip()) for x in args_str.split(',') if x.strip().isdigit()]
            else:
                # It's an integer
                return int(args_str) if args_str.isdigit() else [1, 2, 3]
        
        elif operation == "f_select_column":
            # Expect a list of strings or a string
            if '[' in args_str and ']' in args_str:
                # It's a list
                args_str = args_str.strip('[]')
                return [x.strip().strip('"\'') for x in args_str.split(',')]
            else:
                # It's a string
                return args_str.strip('"\'')
        
        elif operation == "f_group_by":
            # Expect a string
            return args_str.strip('"\'')
        
        elif operation == "f_sort_by":
            # Expect a list [column, ascending] or just column
            if '[' in args_str and ']' in args_str:
                # It's a list
                args_str = args_str.strip('[]')
                parts = [x.strip().strip('"\'') for x in args_str.split(',')]
                if len(parts) >= 2:
                    column = parts[0]
                    ascending = parts[1].lower() in ['true', 'ascending', 'asc']
                    return [column, ascending]
                else:
                    return parts[0]
            else:
                # It's just the column
                return args_str.strip('"\'')
        
        else:
            return args_str
    
    except Exception:
        # If parsing error, raise exception - no fallback
        raise ValueError(f"Failed to parse LLM response for operation {operation}: {response}")



def generate_args(table: List[Dict], question: str, operation: str, 
                 use_llm: bool = True, llm_function=None) -> Union[str, List, int]:
    """
    Main function to generate operation arguments using LLM.
    
    Args:
        table: Current table
        question: Question to answer
        operation: Operation for which to generate arguments
        use_llm: Whether to use real LLM (always True now)
        llm_function: LLM function to generate responses
    
    Returns:
        Appropriate arguments for the operation
    """
    if not llm_function:
        raise ValueError("LLM function is required. No fallback methods available.")
    
    # Always use LLM - no simplified version
    prompt = create_generate_args_prompt(table, question, operation)
    response = llm_function(prompt)
    return parse_args_response(response, operation)


# Function for compatibility with existing code
def get_operation_args(table: List[Dict], question: str, operation: str) -> Union[str, List, int]:
    """
    Convenience function to get operation arguments using LLM.
    """
    from request.request import ask_llm
    return generate_args(table, question, operation, use_llm=True, llm_function=ask_llm)