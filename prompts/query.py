"""
Prompt for Query: Generate final answer from transformed table
"""

from typing import List, Dict, Any
import sys
import os

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.table_ops import format_table_as_pipe


def create_query_prompt(table: List[Dict], question: str) -> str:
    """
    Create the prompt for the LLM to generate the final answer.
    
    Args:
        table: Final transformed table
        question: Original question to answer
    
    Returns:
        String with formatted prompt
    """
    
    table_str = format_table_as_pipe(table)
    
    prompt = f"""You are an expert in data analysis. Your task is to answer a question based on the final table that results from a chain of transformations.

FINAL TABLE:
{table_str}

ORIGINAL QUESTION:
{question}

ANSWER EXAMPLES:

Example 1:
Table: Country | Count
       ITA     | 3
       ESP     | 2
       FRA     | 1
Question: Which country had the most cyclists in the top 6?
→ Looking at the table, ITA has the highest count (3)
ANSWER: Italy

Example 2:
Table: Name | Age
       Alice | 25
       Bob   | 30
       Carol | 28
Question: Who is the oldest person?
→ Bob has the highest age (30)
ANSWER: Bob

Example 3:
Table: City | Count
       Madrid | 5
       Barcelona | 3
Question: How many people are from Madrid?
→ Madrid has a count of 5
ANSWER: 5

Example 4:
Table: Product | Sales
       Laptop  | 1500
       Phone   | 2000
       Tablet  | 800
Question: What is the total sales?
→ Sum: 1500 + 2000 + 800 = 4300
ANSWER: 4300

Example 5:
Table: Team | Wins
       Red  | 12
       Blue | 8
       Green| 10
Question: Which team has more wins than 10?
→ Only Red has more than 10 wins (12)
ANSWER: Red

INSTRUCTIONS:
1. Carefully analyze the final table.
2. Answer the original question based only on the table data.
3. If the question seeks the highest/lowest value, identify the corresponding row.
4. If the question seeks a count or sum, perform the necessary calculation.
5. If the question seeks multiple elements, list all that meet the condition.
6. Answer concisely and directly.
7. If you cannot answer with available data, indicate "Cannot be determined".

Based on the final table, what is the answer to the question?
ANSWER:"""

    return prompt


def parse_query_response(response: str) -> str:
    """
    Parse LLM response to extract the final answer.
    
    Args:
        response: Complete LLM response
    
    Returns:
        Extracted final answer
    """
    # Clean the response
    response = response.strip()
    
    # Look for lines containing "ANSWER:"
    lines = response.split('\n')
    for line in lines:
        if 'ANSWER:' in line:
            answer = line.split('ANSWER:')[-1].strip()
            return answer
    
    # If expected format not found, use last line
    return response.split('\n')[-1].strip()


def analyze_table_for_answer(table: List[Dict], question: str) -> Dict[str, Any]:
    """
    Analyze table to get useful information for answering the question.
    
    Args:
        table: Final table
        question: Question to answer
    
    Returns:
        Dictionary with analyzed information
    """
    if not table:
        return {"error": "Empty table"}
    
    columns = list(table[0].keys())
    analysis = {
        "num_rows": len(table),
        "columns": columns,
        "numeric_columns": [],
        "text_columns": [],
        "has_count": 'Count' in columns,
        "max_values": {},
        "min_values": {},
        "totals": {}
    }
    
    # Analyze column types and calculate statistics
    for col in columns:
        values = [row.get(col, 0) for row in table]
        
        # Try to identify numeric columns
        numeric_values = []
        for val in values:
            try:
                numeric_values.append(float(val))
            except (ValueError, TypeError):
                pass
        
        if len(numeric_values) == len(values):
            analysis["numeric_columns"].append(col)
            analysis["max_values"][col] = max(numeric_values)
            analysis["min_values"][col] = min(numeric_values)
            analysis["totals"][col] = sum(numeric_values)
        else:
            analysis["text_columns"].append(col)
    
    return analysis


def query(table: List[Dict], question: str, use_llm: bool = True, llm_function=None) -> str:
    """
    Main function to generate the final answer using LLM.
    
    Args:
        table: Final transformed table
        question: Original question to answer
        use_llm: Whether to use real LLM (always True now)
        llm_function: LLM function to generate responses
    
    Returns:
        Answer to the question
    """
    if not llm_function:
        raise ValueError("LLM function is required. No fallback methods available.")
    
    # Always use LLM - no simplified version
    prompt = create_query_prompt(table, question)
    response = llm_function(prompt)
    return parse_query_response(response)


# Function for compatibility with existing code
def get_final_answer(table: List[Dict], question: str) -> str:
    """
    Convenience function to get the final answer using LLM.
    """
    from request.request import ask_llm
    return query(table, question, use_llm=True, llm_function=ask_llm)