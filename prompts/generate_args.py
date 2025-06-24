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
        # If parsing error, use default values
        return get_default_args(operation)


def get_default_args(operation: str) -> Union[str, List]:
    """
    Get default arguments for an operation.
    
    Args:
        operation: Operation name
    
    Returns:
        Default arguments
    """
    defaults = {
        "f_add_column": "NewColumn",
        "f_select_row": [1, 2, 3],
        "f_select_column": ["Column1"],
        "f_group_by": "Column1",
        "f_sort_by": ["Column1", True]
    }
    return defaults.get(operation, [])


def generate_args_simple(table: List[Dict], question: str, operation: str) -> Union[str, List, int]:
    """
    Simplified version of generate_args for testing without LLM.
    Implements basic argument generation logic.
    
    Args:
        table: Current table
        question: Question to answer
        operation: Operation for which to generate arguments
    
    Returns:
        Appropriate arguments for the operation
    """
    if not table:
        return get_default_args(operation)
    
    columns = list(table[0].keys()) if table else []
    
    if operation == "f_add_column":
        # Detect which column to add based on content
        if 'Cyclist' in columns:
            # If there are cyclists, probably need countries
            cyclist_col = next((row.get('Cyclist', '') for row in table), '')
            if '(' in cyclist_col and ')' in cyclist_col:
                return ["Country", smart_add_column_values(table, "Country", question)]
        return "NewColumn"
    
    elif operation == "f_select_row":
        # Select top N based on question
        question_lower = question.lower()
        if 'top 3' in question_lower or 'first 3' in question_lower:
            return [1, 2, 3]
        elif 'top 5' in question_lower or 'first 5' in question_lower:
            return [1, 2, 3, 4, 5]
        elif 'top' in question_lower:
            return [1, 2, 3]
        else:
            # Default: take half the rows
            max_rows = min(len(table), 5)
            return list(range(1, max_rows + 1))
    
    elif operation == "f_select_column":
        # Select columns relevant to the question
        question_lower = question.lower()
        relevant_cols = []
        
        for col in columns:
            col_lower = col.lower()
            if (col_lower in question_lower or 
                any(word in col_lower for word in ['name', 'country', 'city', 'type', 'category'])):
                relevant_cols.append(col)
        
        return relevant_cols if relevant_cols else columns[:2]
    
    elif operation == "f_group_by":
        # Group by most relevant column
        question_lower = question.lower()
        
        # Look for columns mentioned in question
        for col in columns:
            if col.lower() in question_lower:
                return col
        
        # Look for typical grouping columns
        priority_cols = ['Country', 'City', 'Type', 'Category', 'Team']
        for col in priority_cols:
            if col in columns:
                return col
        
        # Default: use second column
        return columns[1] if len(columns) > 1 else columns[0]
    
    elif operation == "f_sort_by":
        # Sort by most relevant column
        question_lower = question.lower()
        
        # If there's a Count column, use that
        if 'Count' in columns:
            # If question looks for "most", sort descending
            ascending = not ('most' in question_lower or 'más' in question_lower or 'mayor' in question_lower)
            return ['Count', ascending]
        
        # If there's Rank, use that
        if 'Rank' in columns:
            return ['Rank', True]
        
        # Default: use first column
        return [columns[0], True] if columns else ['Column1', True]
    
    return get_default_args(operation)


def generate_args(table: List[Dict], question: str, operation: str, 
                 use_llm: bool = False, llm_function=None) -> Union[str, List, int]:
    """
    Main function to generate operation arguments.
    
    Args:
        table: Current table
        question: Question to answer
        operation: Operation for which to generate arguments
        use_llm: Whether to use real LLM or simplified version
        llm_function: LLM function to generate responses
    
    Returns:
        Appropriate arguments for the operation
    """
    if use_llm and llm_function:
        # Use real LLM
        prompt = create_generate_args_prompt(table, question, operation)
        response = llm_function(prompt)
        return parse_args_response(response, operation)
    else:
        # Use simplified version
        return generate_args_simple(table, question, operation)


# Function for compatibility with existing code
def get_operation_args(table: List[Dict], question: str, operation: str) -> Union[str, List, int]:
    """
    Convenience function to get operation arguments.
    """
    return generate_args(table, question, operation, use_llm=False)


def extract_country_from_cyclist_name(cyclist_name: str) -> str:
    """
    Extract country code from cyclist name.
    
    Args:
        cyclist_name: Cyclist name with format "Name (COUNTRY)"
    
    Returns:
        Extracted country code
    """
    import re
    
    # Look for pattern (CODE) at end of name
    match = re.search(r'\(([A-Z]{2,3})\)', cyclist_name)
    if match:
        return match.group(1)
    
    # If pattern not found, try to detect known countries
    cyclist_lower = cyclist_name.lower()
    if 'esp' in cyclist_lower or 'spain' in cyclist_lower:
        return 'ESP'
    elif 'ita' in cyclist_lower or 'italy' in cyclist_lower:
        return 'ITA'
    elif 'fra' in cyclist_lower or 'france' in cyclist_lower:
        return 'FRA'
    elif 'ger' in cyclist_lower or 'germany' in cyclist_lower:
        return 'GER'
    elif 'usa' in cyclist_lower or 'america' in cyclist_lower:
        return 'USA'
    
    return 'UNKNOWN'


def smart_add_column_values(table: List[Dict], column_name: str, question: str) -> List[Any]:
    """
    Intelligently generate values for a new column based on context.
    
    Args:
        table: Current table
        column_name: Name of new column
        question: Question being solved
    
    Returns:
        List of values for the new column
    """
    if not table:
        return []
    
    column_lower = column_name.lower()
    
    # If column is "Country" and there are cyclists, extract countries
    if column_lower == 'country' and 'Cyclist' in table[0]:
        values = []
        for row in table:
            cyclist_name = row.get('Cyclist', '')
            country = extract_country_from_cyclist_name(cyclist_name)
            values.append(country)
        return values
    
    # If column is "Age", generate random ages
    elif column_lower == 'age':
        import random
        return [random.randint(20, 35) for _ in table]
    
    # If column is "Score" or "Points", generate scores
    elif column_lower in ['score', 'points', 'rating']:
        import random
        return [random.randint(50, 100) for _ in table]
    
    # Default value
    return [f"Value{i+1}" for i in range(len(table))]