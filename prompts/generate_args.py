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
3. For f_add_column, you MUST provide both the column name AND the actual values for each row in the table.
4. Output format by operation:
   - f_add_column: [column_name, [values_for_each_row]] (e.g., ["Country", ["ESP", "ITA", "FRA"]])
   - f_select_row: List of row numbers (e.g., [1, 2, 3])  
   - f_select_column: List of column names (e.g., ["Name", "Country"])
   - f_group_by: Just the column name (e.g., Country)
   - f_sort_by: [column_name, ascending] (e.g., ["Count", false])
5. For f_add_column: Extract/generate the exact value for each row in the current table.
6. IMPORTANT: Respond with ONLY the arguments for {operation}, no explanation, no examples for other operations.

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
    
    # Look for the specific operation in the response
    lines = response.split('\n')
    args_str = ""
    
    # Method 1: Look for "ARGUMENTS:" pattern
    for line in lines:
        if 'ARGUMENTS:' in line:
            args_str = line.split('ARGUMENTS:')[-1].strip()
            break
    
    # Method 2: Look for the specific operation pattern (e.g., "- f_add_column: ...")
    if not args_str:
        operation_pattern = f"- {operation}:"
        for line in lines:
            if operation_pattern in line:
                args_str = line.split(operation_pattern)[-1].strip()
                break
    
    # Method 3: Look for just the operation name followed by colon
    if not args_str:
        operation_pattern = f"{operation}:"
        for line in lines:
            if operation_pattern in line:
                args_str = line.split(operation_pattern)[-1].strip()
                break
    
    # Method 4: If the response is just the arguments (single line)
    if not args_str and len(lines) == 1:
        args_str = lines[0].strip()
    
    # Method 5: Look for the last line that looks like arguments
    if not args_str:
        for line in reversed(lines):
            line = line.strip()
            if line and (line.startswith('[') or line.startswith('"') or line.replace('"', '').replace("'", '').replace('[', '').replace(']', '').replace(',', '').replace(' ', '').isalnum()):
                args_str = line
                break
    
    if not args_str:
        raise ValueError(f"Could not extract arguments for {operation} from LLM response: {response}")
    
    # Parse according to operation type
    try:
        if operation == "f_add_column":
            # Expect [column_name, [values]] format
            import json
            import re
            
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
        raise ValueError(f"Failed to parse arguments for {operation}. Response: {response}. Error: {e}")



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