"""
Atomic operations for Chain-of-Table (CoT)
Each operation transforms a table T into a new table T'
"""

import copy
from typing import List, Dict, Any, Union


def f_add_column(table: List[Dict], column_name: str, values: List[Any] = None, 
                 default_value: Any = "") -> List[Dict]:
    """
    Adds a new column to the table.
    
    Args:
        table: List of dictionaries representing the table
        column_name: Name of the new column
        values: List of values for the new column (optional)
        default_value: Default value if no values are provided
    
    Returns:
        New table with the added column
    """
    if not table:
        return table
    
    new_table = copy.deepcopy(table)
    
    if values is None:
        # If no values provided, use default value
        for row in new_table:
            row[column_name] = default_value
    else:
        # Assign provided values
        for i, row in enumerate(new_table):
            if i < len(values):
                row[column_name] = values[i]
            else:
                row[column_name] = default_value
    
    return new_table


def f_select_row(table: List[Dict], row_indices: Union[List[int], int]) -> List[Dict]:
    """
    Selects specific rows from the table by index.
    
    Args:
        table: List of dictionaries representing the table
        row_indices: Index or list of indices of rows to select (1-indexed)
    
    Returns:
        New table with only the selected rows
    """
    if not table:
        return table
    
    if isinstance(row_indices, int):
        row_indices = [row_indices]
    
    # Convert from 1-indexed to 0-indexed
    zero_based_indices = [i - 1 for i in row_indices if 0 < i <= len(table)]
    
    return [table[i] for i in zero_based_indices]


def f_select_column(table: List[Dict], column_names: Union[List[str], str]) -> List[Dict]:
    """
    Selects specific columns from the table.
    
    Args:
        table: List of dictionaries representing the table
        column_names: Name or list of names of columns to select
    
    Returns:
        New table with only the selected columns
    """
    if not table:
        return table
    
    if isinstance(column_names, str):
        column_names = [column_names]
    
    return [{col: row.get(col, "") for col in column_names} for row in table]


def f_group_by(table: List[Dict], column_name: str, count_column: str = "Count") -> List[Dict]:
    """
    Groups rows by a column and counts elements in each group.
    
    Args:
        table: List of dictionaries representing the table
        column_name: Name of the column to group by
        count_column: Name of the column that will contain the count
    
    Returns:
        New grouped table with counts
    """
    if not table:
        return table
    
    # Count occurrences of each value in the column
    groups = {}
    for row in table:
        value = row.get(column_name, "")
        groups[value] = groups.get(value, 0) + 1
    
    # Create new table with groups and counts
    result = []
    for value, count in groups.items():
        result.append({column_name: value, count_column: count})
    
    return result


def f_sort_by(table: List[Dict], column_name: str, ascending: bool = True) -> List[Dict]:
    """
    Sorts table rows by a specific column.
    
    Args:
        table: List of dictionaries representing the table
        column_name: Name of the column to sort by
        ascending: True for ascending order, False for descending
    
    Returns:
        New sorted table
    """
    if not table:
        return table
    
    def sort_key(row):
        value = row.get(column_name, "")
        # Try to convert to number if possible for numeric sorting
        try:
            return float(value)
        except (ValueError, TypeError):
            return str(value)
    
    return sorted(copy.deepcopy(table), key=sort_key, reverse=not ascending)


def apply_operation(table: List[Dict], operation: str, args: Union[List, str, int]) -> List[Dict]:
    """
    Applies an atomic operation to the table.
    
    Args:
        table: List of dictionaries representing the table
        operation: Name of the operation to apply
        args: Arguments for the operation
    
    Returns:
        New transformed table
    """
    if operation == "f_add_column":
        if isinstance(args, str):
            return f_add_column(table, args)
        elif isinstance(args, list) and len(args) >= 1:
            column_name = args[0]
            values = args[1] if len(args) > 1 else None
            default_value = args[2] if len(args) > 2 else ""
            return f_add_column(table, column_name, values, default_value)
    
    elif operation == "f_select_row":
        return f_select_row(table, args)
    
    elif operation == "f_select_column":
        return f_select_column(table, args)
    
    elif operation == "f_group_by":
        if isinstance(args, str):
            return f_group_by(table, args)
        elif isinstance(args, list) and len(args) >= 1:
            column_name = args[0]
            count_column = args[1] if len(args) > 1 else "Count"
            return f_group_by(table, column_name, count_column)
    
    elif operation == "f_sort_by":
        if isinstance(args, str):
            return f_sort_by(table, args)
        elif isinstance(args, list) and len(args) >= 1:
            column_name = args[0]
            ascending = args[1] if len(args) > 1 else True
            return f_sort_by(table, column_name, ascending)
    
    # If operation is not recognized, return table unchanged
    return table


def get_available_operations() -> List[str]:
    """
    Returns the list of available atomic operations.
    
    Returns:
        List of operation names
    """
    return [
        "f_add_column",
        "f_select_row", 
        "f_select_column",
        "f_group_by",
        "f_sort_by"
    ]


def format_table_as_pipe(table: List[Dict]) -> str:
    """
    Converts a table to PIPE format for better visualization.
    
    Args:
        table: List of dictionaries representing the table
    
    Returns:
        String with table in PIPE format
    """
    if not table:
        return "Empty table"
    
    # Get all unique columns
    columns = list(table[0].keys()) if table else []
    
    # Create header
    header = " | ".join(columns)
    separator = "-" * len(header)
    
    # Create rows
    rows = []
    for row in table:
        row_values = [str(row.get(col, "")) for col in columns]
        rows.append(" | ".join(row_values))
    
    return "\n".join([header, separator] + rows)


def show_operations_summary():
    """
    Shows a summary of all available operations with examples.
    """
    print("🔧 AVAILABLE ATOMIC OPERATIONS IN CHAIN-OF-TABLE")
    print("=" * 60)
    
    operations = [
        {
            "name": "f_add_column",
            "description": "Adds a new column to the table",
            "args": "column_name, [values], [default_value]",
            "example": "f_add_column(table, 'Country', ['ESP', 'ITA', 'ESP'])"
        },
        {
            "name": "f_select_row", 
            "description": "Selects specific rows by index (1-indexed)",
            "args": "row_indices (int or List[int])",
            "example": "f_select_row(table, [1, 2, 3])"
        },
        {
            "name": "f_select_column",
            "description": "Selects specific columns",
            "args": "column_names (str or List[str])",
            "example": "f_select_column(table, ['Name', 'Country'])"
        },
        {
            "name": "f_group_by",
            "description": "Groups rows by a column and counts elements",
            "args": "column_name, [count_column]",
            "example": "f_group_by(table, 'Country')"
        },
        {
            "name": "f_sort_by",
            "description": "Sorts rows by a column",
            "args": "column_name, [ascending=True]",
            "example": "f_sort_by(table, 'Rank', ascending=False)"
        }
    ]
    
    for i, op in enumerate(operations, 1):
        print(f"{i}. {op['name']}")
        print(f"   📝 {op['description']}")
        print(f"   📋 Arguments: {op['args']}")
        print(f"   💡 Example: {op['example']}")
        print()
    
    print("🎯 Usage with apply_operation:")
    print("   apply_operation(table, 'f_select_row', [1, 2, 3])")
    print("   apply_operation(table, 'f_group_by', 'Country')")
    print()


def validate_table(table: List[Dict]) -> bool:
    """
    Validates that the table has the correct format.
    
    Args:
        table: List of dictionaries representing the table
    
    Returns:
        True if table is valid, False otherwise
    """
    if not isinstance(table, list):
        return False
    
    if not table:
        return True  # Empty table is valid
    
    # Check that all elements are dictionaries
    if not all(isinstance(row, dict) for row in table):
        return False
    
    # Check that all rows have the same columns
    if table:
        first_keys = set(table[0].keys())
        if not all(set(row.keys()) == first_keys for row in table):
            return False
    
    return True