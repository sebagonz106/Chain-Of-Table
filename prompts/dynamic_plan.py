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


def create_dynamic_plan_prompt(table: List[Dict], question: str, chain: List[Union[str, tuple]], max_steps: int = 5, excluded_ops: List[str] = []) -> str:
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
    current_steps = len(chain)
    print(chain_str)
    print("-> Remaining operations: " + str(max_steps - current_steps))
    
    # Get candidate operations

    candidates = get_available_operations()
    candidates_str = ", ".join([x for x in candidates if x not in excluded_ops])
    print(candidates_str)
    
    # Extract current column names
    if table:
        current_columns = list(table[0].keys())
        columns_str = ", ".join(current_columns)
    else:
        columns_str = "None"
    
    prompt = f"""You are an expert in tabular reasoning. Your task is to select the next atomic operations needed to solve a question about a table. In total, only {max_steps} operations can be used. 

CURRENT TABLE:
{table_str}

CURRENT COLUMNS: {columns_str}

QUESTION:
{question}

OPERATION HISTORY:
{chain_str}

CANDIDATE OPERATIONS:
{candidates_str}

IMPORTANT: 
    - The CURRENT COLUMNS above show what columns exist RIGHT NOW in the table. If a column is already listed in CURRENT COLUMNS, do NOT use f_add_column for it again!
    - Only used the operations given in CANDIDATE OPERATIONS

CRITICAL RULE: Before using f_group_by, f_sort_by, or f_select_column with a column name, CHECK if that column exists in CURRENT COLUMNS. If it doesn't exist, you MUST use f_add_column first to create it!

REASONING EXAMPLES (whith max amount of steps being 5):

Example 1:
Table: Rank | Cyclist
       1    | Alej. (ESP)
       2    | Davide (ITA)
       3    | Paolo (ITA)
       4    | Haimar  | ESP
Question: Which country had the most cyclists in the top 3?
History: [B]
Analysis: I need to answer which country had the most cyclists in the top 3. Looking at the current table, I see cyclist names with country codes in parentheses, but no dedicated Country column. The question requires me to: 1) Extract country information, 2) Focus on top 3 ranks, 3) Count by country.
→ FIRST: Since there's no Country column in CURRENT COLUMNS, I must use f_add_column to create it by extracting countries from cyclist names.
→ THEN: I can select the top 3 rows and group by the new country column to get counts.
OPERATIONS: f_add_column, f_select_row, f_group_by, [E]

Example 2:
Table: Rank | Cyclist | Country
       1    | Alej.   | ESP
       2    | Davide  | ITA
       3    | Paolo   | ITA
       4    | Haimar  | ESP
Question: Which country had the most cyclists in the top 3?
History: [B], f_add_column(['Country', ['ESP', 'ITA', 'ITA', 'ESP']])
Analysis: Perfect! The Country column now exists in the table (I can see ESP, ITA, ITA, ESP values). The question asks about the "top 3" cyclists, so I need to limit my analysis to just ranks 1-3, then count how many cyclists each country has in that subset.
→ FIRST: I need to use f_select_row to get only the top 3 rows (ranks 1-3).
→ THEN: I can group by the existing Country column to count cyclists per country.
OPERATIONS: f_select_row, f_group_by, [E]

Example 3:
Table: Rank | Cyclist | Country
       1    | Alej.   | ESP
       2    | Davide  | ITA
       3    | Paolo   | ITA
Question: Which country had the most cyclists in the top 3?
History: [B], f_add_column(['Country', ['ESP', 'ITA', 'ITA', 'ESP']]), f_select_row([1,2,3])
→ Analysis: I now have the top 3 cyclists with their countries. To answer which country had the most, I need to group them by country to get the count for each country.
→ FIRST: Group by country to count how many cyclists per country.
→ THEN: Answer.
OPERATIONS: f_group_by, [E]

Example 4:
Table: Country | Count
       ITA     | 2
       ESP     | 1
Question: Which country had the most cyclists in the top 3?
History: [B], f_add_column(['Country', ['ESP', 'ITA', 'ITA', 'ESP']]), f_select_row([1,2,3]), f_group_by(['Country'])
→ Analysis: Perfect! The table now shows the count of cyclists per country in the top 3. ITA has 2 cyclists and ESP has 1. I can directly answer the question: Italy (ITA) had the most cyclists in the top 3.
OPERATIONS: [E]

Example 5:
Table: Rank | Cyclist | Country
       1    | Alej.   | ESP
       2    | Davide  | ITA
       3    | Paolo   | ITA
       4    | Haimar  | ESP
       5    | Javier  | ESP
       6    | Franco  | ITA
       7    | Juan    | ESP
Question: What country has the most cyclists in the top 3?
History: [B], f_add_column(['Country', ['ESP', 'ITA', 'ITA', 'ESP', 'ESP', 'ITA', 'ESP']])
→ Analysis: The table has the Country column already created. Now I need to focus on the top 3 ranks (rows 1-3) and then count by country to determine which country has the most cyclists.
→ FIRST: Select the top 3 rows to limit the analysis to the top 3 cyclists.
→ THEN: Group by country to count cyclists per country.
OPERATIONS: f_select_row, f_group_by, [E]

Example 6 (WRONG - Don't do this):
Table: Rank | Item | Category
       1    | A    | X
       2    | B    | Y
Question: Which category had the most items?
History: [B], f_add_column(['Category', ['X', 'Y']])
→ Analysis: The question asks about categories, and I can see the table already has a Category column with values X and Y. I need to count how many items belong to each category.
→ WRONG: f_add_column (Category already exists!)
→ CORRECT: f_group_by (to count by existing Category column)
OPERATIONS: f_group_by, [E]

INSTRUCTIONS:
1. Look at the CURRENT COLUMNS to see what data is already available.
2. Check the OPERATION HISTORY to see what has already been done.
3. If you need a column that doesn't exist in CURRENT COLUMNS, use f_add_column to create it.
4. CRITICAL: If a column already exists in CURRENT COLUMNS, do NOT use f_add_column for that same column again.
5. NEVER suggest f_add_column if the column name already appears in CURRENT COLUMNS.
6. Select the most appropriate operations from CANDIDATE OPERATIONS to advance toward the answer.
7. If you can already answer the question with the current table, select [E].
8. Respond ONLY with the operations name separated by comma, DO NOT INCLUDE the arguments in your response.
9. You MUST NOT INCLUDE previous operations in your response, only the operations needed from now on to arrive to an answer.
10. You have ONLY {max_steps-current_steps} operations remaining. If there are no operations remaining, you must return [E].

What are the next most appropriate operations?
OPERATIONS:"""

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
    print("-> Response: " + response)
    # Look for lines containing "OPERATIONS:"
    lines = response.split('\n')
    for line in lines:
        if 'OPERATIONS:' in line:
            operations = line.split('OPERATIONS:')[-1].strip()
            print(operations)
            return operations.split(',')[0].strip()
    
    # If expected format not found, use last line
    response = response.split('\n')[-1].split(',')[0].strip()
    return response.split('(')[0].strip()


def dynamic_plan(table: List[Dict], question: str, chain: List[Union[str, tuple]], 
                max_steps: int = 5, excluded_ops: List[str] = [], llm_function=ask_llm) -> str:
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
    prompt = create_dynamic_plan_prompt(table, question, chain, max_steps, excluded_ops)
    response = llm_function(prompt)
    return parse_operation_response(response)