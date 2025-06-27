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
    
    # Extract current column names
    if table:
        current_columns = list(table[0].keys())
        columns_str = ", ".join(current_columns)
    else:
        columns_str = "None"
    
    prompt = f"""You are an expert in tabular reasoning. Your task is to generate appropriate arguments for a specific operation in Chain-of-Table.

CURRENT TABLE:
{table_str}

CURRENT COLUMNS: {columns_str}

QUESTION:
{question}

OPERATION TO EXECUTE:
{operation}

ARGUMENT EXAMPLES BY OPERATION:

EXAMPLE f_add_column:
Operation: f_add_column
Table: Rank | Cyclist
       1    | Alejandro (ESP)
       2    | Davide (ITA)
       3    | Paolo (ITA)
       4    | Haimar (ESP)
Question: Which country had the most cyclists?
→ I need to extract countries from cyclist names and create a Country column
ARGUMENTS: ["Country", ["ESP", "ITA", "ITA", "ESP"]]

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
→ I only need columns relevant to the question, which are Cyclist and Country
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
1. Look at the CURRENT COLUMNS to see what columns already exist in the table.
2. For f_add_column: 
    - Only create columns that DO NOT already exist in CURRENT COLUMNS.
    - If it is requested for a column that already exists, this is an error - the operation should not be performed.
    - You MUST provide both the column name AND the actual values for each row in the table.
    - Extract/generate the exact value for each row in the current table.
3. Output format by operation:
   - f_add_column: [column_name, [values_for_each_row]] (e.g., ["Country", ["ESP", "ITA", "FRA"]])
   - f_select_row: List of row numbers (e.g., [1, 2, 3])  
   - f_select_column: List of column names (e.g., ["Name", "Country"])
   - f_group_by: Just the column name (e.g., Country)
   - f_sort_by: [column_name, ascending] (e.g., ["Count", false])
4. CRITICAL: The current table has {len(table)} rows. For f_add_column you must provide exactly {len(table)} values in your list, one for each row.
5. IMPORTANT: Respond with ONLY the arguments for {operation}, NO explanations or examples for other operations.

What are the appropriate arguments for {operation}?
ARGUMENTS:"""

    return prompt


def parse_args_response(response: str, operation: str) -> Union[str, List, int]:
    """
    Parse LLM response to extract arguments for the specific operation.
    
    Args:
        response: Complete LLM response
        operation: Operation for which arguments were generated
    
    Returns:
        Parsed arguments in appropriate format
    """
    # Clean the response
    response = response.strip()
    lines = response.split('\n')
    args_str = ""
    
    # Strategy 1: Look for "ARGUMENTS:" pattern (most reliable)
    for line in lines:
        if 'ARGUMENTS:' in line:
            args_str = line.split('ARGUMENTS:')[-1].strip()
            if args_str:  # Only break if we actually found content after ARGUMENTS:
                break
    
    # Strategy 2: If single line response, it's probably just the arguments
    if not args_str and len(lines) == 1:
        args_str = lines[0].strip()
    
    # Strategy 3: Look for lines that look like arguments (start with [ or ")
    if not args_str:
        for line in lines:
            line = line.strip()
            if line and (line.startswith('[') or line.startswith('"')) and len(line) > 2:
                args_str = line
                break
    
    # Strategy 4: Take the last non-empty, meaningful line as fallback
    if not args_str:
        for line in reversed(lines):
            line = line.strip()
            if line and len(line) > 1:
                # Skip lines that are clearly not arguments
                if not any(skip_word in line.lower() for skip_word in ['→', 'arguments', 'operation', 'table:']):
                    args_str = line
                    break
    
    if not args_str:
        raise ValueError(f"Could not extract arguments for {operation} from LLM response: {response}")
    
    # Parse according to operation type
    return _parse_operation_args(args_str, operation)


def _parse_operation_args(args_str: str, operation: str) -> Union[str, List, int]:
    """
    Parse the argument string based on the operation type.
    
    Args:
        args_str: Raw argument string extracted from LLM response
        operation: Operation type
        
    Returns:
        Parsed arguments in appropriate format
    """
    try:
        if operation == "f_add_column":
            # Expect [column_name, [values]] format
            import json
            
            # Try to parse as JSON first
            try:
                parsed = json.loads(args_str)
                if isinstance(parsed, list) and len(parsed) >= 2:
                    column_name = parsed[0]
                    values = parsed[1] if isinstance(parsed[1], list) else [parsed[1]]
                    return [column_name, values]
                elif isinstance(parsed, list) and len(parsed) == 1:
                    # Only column name provided - this is an error for f_add_column
                    column_name = parsed[0]
                    raise ValueError(f"f_add_column requires both column name AND values. Only got column name: {column_name}")
                else:
                    column_name = str(parsed)
                    raise ValueError(f"f_add_column requires both column name AND values. Only got: {column_name}")
            except json.JSONDecodeError:
                # If not valid JSON, try to extract manually
                # Look for pattern: ["ColumnName", ["val1", "val2", ...]]
                if '[' in args_str and ',' in args_str:
                    # Try to extract the two parts
                    parts = args_str.strip('[]').split(',', 1)
                    if len(parts) >= 2:
                        column_name = parts[0].strip().strip('"\'')
                        values_part = parts[1].strip()
                        
                        # Parse the values part
                        if values_part.startswith('[') and values_part.endswith(']'):
                            values_str = values_part.strip('[]')
                            values = [v.strip().strip('"\'') for v in values_str.split(',')]
                            return [column_name, values]
                        else:
                            # Single value
                            value = values_part.strip().strip('"\'')
                            return [column_name, [value]]
                    else:
                        raise ValueError(f"f_add_column requires both column name AND values. Got: {args_str}")
                else:
                    # Only column name provided
                    column_name = args_str.strip('"\'[]{}')
                    raise ValueError(f"f_add_column requires both column name AND values for each row. Only got column name: {column_name}")
        
        elif operation == "f_select_row":
            # Expect a list of integers
            import re
            numbers = re.findall(r'\d+', args_str)
            if numbers:
                return [int(n) for n in numbers]
            else:
                return [1, 2, 3]  # fallback
        
        elif operation == "f_select_column":
            # Expect a list of strings or a single string
            import json
            try:
                parsed = json.loads(args_str)
                if isinstance(parsed, list):
                    return parsed
                else:
                    return [str(parsed)]
            except json.JSONDecodeError:
                # Manual parsing
                import re
                if '[' in args_str:
                    columns = re.findall(r'["\']([^"\']+)["\']', args_str)
                    return columns if columns else ["Column1"]
                else:
                    column = args_str.strip('"\'[]{}')
                    return [column] if column else ["Column1"]
        
        elif operation == "f_group_by":
            # Expect a single column name
            args_str = args_str.strip('"\'[]{}')
            return args_str if args_str else "Column1"
        
        elif operation == "f_sort_by":
            # Expect [column, ascending] or just column
            import json
            try:
                parsed = json.loads(args_str)
                if isinstance(parsed, list) and len(parsed) >= 2:
                    return [parsed[0], parsed[1]]
                elif isinstance(parsed, list) and len(parsed) == 1:
                    return [parsed[0], True]
                else:
                    return [str(parsed), True]
            except json.JSONDecodeError:
                # Manual parsing
                import re
                column_match = re.search(r'["\']?(\w+)["\']?', args_str)
                if column_match:
                    column = column_match.group(1)
                    ascending = not any(word in args_str.lower() for word in ['desc', 'descending', 'false'])
                    return [column, ascending]
                else:
                    return ["Column1", True]
        
        else:
            # Generic cleanup
            return args_str.strip('"\'[]{}')
    
    except Exception as e:
        # If parsing error, raise exception with details
        raise ValueError(f"Failed to parse arguments for {operation}. Args string: {args_str}. Error: {e}")



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
    
    # Check for f_add_column with existing columns
    if operation == "f_add_column" and table:
        current_columns = list(table[0].keys())
        # We'll validate after getting the response from LLM
    
    # Always use LLM - no simplified version
    prompt = create_generate_args_prompt(table, question, operation)
    response = llm_function(prompt)
    args = parse_args_response(response, operation)
    
    return args


# Function for compatibility with existing code
def get_operation_args(table: List[Dict], question: str, operation: str) -> Union[str, List, int]:
    """
    Convenience function to get operation arguments using LLM.
    """
    from request.request import ask_llm
    return generate_args(table, question, operation, use_llm=True, llm_function=ask_llm)