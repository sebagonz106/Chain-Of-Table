"""
Table input/output utilities for Chain-of-Table
Functions for loading, saving, displaying and validating tables
"""

import json
import csv
import os
from typing import List, Dict, Any, Optional, Union
from datetime import datetime


def load_table(path: str, encoding: str = 'utf-8') -> List[Dict[str, Any]]:
    """
    Load a table from a JSON or CSV file.
    
    Args:
        path: File path
        encoding: File encoding
    
    Returns:
        List of dictionaries representing the table
    
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If format is invalid
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    
    file_ext = os.path.splitext(path)[1].lower()
    
    try:
        if file_ext == '.json':
            with open(path, 'r', encoding=encoding) as f:
                data = json.load(f)
                if isinstance(data, list) and all(isinstance(row, dict) for row in data):
                    return data
                else:
                    raise ValueError("JSON file must contain a list of dictionaries")
        
        elif file_ext == '.csv':
            table = []
            with open(path, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Try to convert numbers
                    converted_row = {}
                    for key, value in row.items():
                        try:
                            # Try to convert to int first, then float
                            if '.' in value:
                                converted_row[key] = float(value)
                            else:
                                converted_row[key] = int(value)
                        except (ValueError, TypeError):
                            converted_row[key] = value
                    table.append(converted_row)
            return table
        
        else:
            raise ValueError(f"Unsupported file format: {file_ext}. Use .json or .csv")
    
    except Exception as e:
        raise ValueError(f"Error loading file {path}: {str(e)}")


def save_table(table: List[Dict[str, Any]], path: str, encoding: str = 'utf-8') -> None:
    """
    Save a table to a JSON or CSV file.
    
    Args:
        table: List of dictionaries representing the table
        path: Path where to save the file
        encoding: File encoding
    
    Raises:
        ValueError: If table is empty or has invalid format
    """
    if not table:
        raise ValueError("Table is empty")
    
    if not all(isinstance(row, dict) for row in table):
        raise ValueError("Table must be a list of dictionaries")
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    file_ext = os.path.splitext(path)[1].lower()
    
    try:
        if file_ext == '.json':
            with open(path, 'w', encoding=encoding) as f:
                json.dump(table, f, indent=2, ensure_ascii=False)
        
        elif file_ext == '.csv':
            if not table:
                return
            
            fieldnames = list(table[0].keys())
            with open(path, 'w', newline='', encoding=encoding) as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(table)
        
        else:
            raise ValueError(f"Unsupported file format: {file_ext}. Use .json or .csv")
    
    except Exception as e:
        raise ValueError(f"Error saving file {path}: {str(e)}")


def print_table(table: List[Dict[str, Any]], max_rows: Optional[int] = None, 
                max_col_width: int = 20) -> None:
    """
    Print a table in readable format.
    
    Args:
        table: List of dictionaries representing the table
        max_rows: Maximum number of rows to show (None for all)
        max_col_width: Maximum column width
    """
    if not table:
        print("📋 Empty table")
        return
    
    headers = list(table[0].keys())
    
    # Truncate content if too long
    def truncate(text: str, width: int) -> str:
        text = str(text)
        return text[:width-3] + "..." if len(text) > width else text
    
    # Calculate column widths
    col_widths = {}
    for header in headers:
        max_width = len(header)
        for row in table[:max_rows] if max_rows else table:
            content_width = len(str(row.get(header, "")))
            max_width = max(max_width, min(content_width, max_col_width))
        col_widths[header] = max_width
    
    # Print headers
    header_line = " | ".join(header.ljust(col_widths[header]) for header in headers)
    print(header_line)
    print("-" * len(header_line))
    
    # Print rows
    rows_to_show = table[:max_rows] if max_rows else table
    for row in rows_to_show:
        row_line = " | ".join(
            truncate(str(row.get(header, "")), max_col_width).ljust(col_widths[header]) 
            for header in headers
        )
        print(row_line)
    
    # Show additional information
    if max_rows and len(table) > max_rows:
        print(f"... and {len(table) - max_rows} more rows")
    
    print(f"\n📊 Total: {len(table)} rows, {len(headers)} columns")


def save_chain_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Save Chain-of-Table results to a structured file.
    
    Args:
        results: Dictionary with reasoning results
        output_path: Path where to save the results
    """
    # Create directory if it doesn't exist
    output_dir = os.path.dirname(output_path)
    if output_dir:  # Only create if there's a directory
        os.makedirs(output_dir, exist_ok=True)
    
    # Prepare data for serialization
    serializable_results = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "version": "1.0",
            "algorithm": "Chain-of-Table"
        },
        "answer": results.get("answer", ""),
        "steps": results.get("steps", 0),
        "chain": [],
        "tables": results.get("tables", []),
        "final_table": results.get("final_table", [])
    }
    
    # Convert operation chain to serializable format
    for step in results.get("chain", []):
        if isinstance(step, str):
            serializable_results["chain"].append(step)
        elif isinstance(step, tuple) and len(step) == 2:
            operation, args = step
            serializable_results["chain"].append({
                "operation": operation,
                "arguments": args
            })
        else:
            serializable_results["chain"].append(str(step))
    
    # Save file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump([serializable_results], f, indent=2, ensure_ascii=False)
        print(f"✅ Results saved to: {output_path}")
    except Exception as e:
        raise ValueError(f"Error saving file {output_path}: {str(e)}")


def load_multiple_tables(directory: str, pattern: str = "*.json") -> Dict[str, List[Dict]]:
    """
    Load multiple tables from a directory.
    
    Args:
        directory: Directory to search for files
        pattern: File pattern to load
    
    Returns:
        Dictionary with filename -> table
    """
    import glob
    
    tables = {}
    pattern_path = os.path.join(directory, pattern)
    
    for file_path in glob.glob(pattern_path):
        filename = os.path.basename(file_path)
        name = os.path.splitext(filename)[0]
        try:
            tables[name] = load_table(file_path)
            print(f"✅ Loaded table: {filename}")
        except Exception as e:
            print(f"❌ Error loading {filename}: {e}")
    
    return tables


def validate_table_format(table: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate table format and provide statistics.
    
    Args:
        table: List of dictionaries representing the table
    
    Returns:
        Dictionary with validation information
    """
    validation_result = {
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "stats": {}
    }
    
    # Check if it's a list
    if not isinstance(table, list):
        validation_result["is_valid"] = False
        validation_result["errors"].append("Table must be a list")
        return validation_result
    
    # Check empty table
    if not table:
        validation_result["warnings"].append("Table is empty")
        validation_result["stats"] = {"rows": 0, "columns": 0}
        return validation_result
    
    # Check that all elements are dictionaries
    non_dict_rows = [i for i, row in enumerate(table) if not isinstance(row, dict)]
    if non_dict_rows:
        validation_result["is_valid"] = False
        validation_result["errors"].append(f"Invalid rows (not dictionaries): {non_dict_rows}")
    
    # Check column consistency
    if table:
        first_keys = set(table[0].keys())
        validation_result["stats"]["columns"] = len(first_keys)
        validation_result["stats"]["column_names"] = list(first_keys)
        
        inconsistent_rows = []
        for i, row in enumerate(table[1:], 1):
            if set(row.keys()) != first_keys:
                inconsistent_rows.append(i)
        
        if inconsistent_rows:
            validation_result["warnings"].append(f"Rows with inconsistent columns: {inconsistent_rows}")
    
    validation_result["stats"]["rows"] = len(table)
    
    # Data type statistics
    if table:
        type_stats = {}
        for col in first_keys:
            types = [type(row.get(col)).__name__ for row in table]
            type_counts = {t: types.count(t) for t in set(types)}
            type_stats[col] = type_counts
        
        validation_result["stats"]["column_types"] = type_stats
    
    return validation_result


def create_sample_table(table_type: str = "cyclists") -> List[Dict[str, Any]]:
    """
    Create a sample table for testing.
    
    Args:
        table_type: Type of table to create ("cyclists", "students", "sales")
    
    Returns:
        List of dictionaries representing the sample table
    """
    if table_type == "cyclists":
        return [
            {"Rank": 1, "Cyclist": "Alejandro (ESP)", "Time": "2:45:30"},
            {"Rank": 2, "Cyclist": "Davide (ITA)", "Time": "2:45:45"},
            {"Rank": 3, "Cyclist": "Paolo (ITA)", "Time": "2:46:10"},
            {"Rank": 4, "Cyclist": "Haimar (ESP)", "Time": "2:46:25"},
            {"Rank": 5, "Cyclist": "Javier (ESP)", "Time": "2:46:40"}
        ]
    
    elif table_type == "students":
        return [
            {"Name": "Alice", "Age": 20, "Major": "Computer Science", "GPA": 3.8},
            {"Name": "Bob", "Age": 21, "Major": "Mathematics", "GPA": 3.6},
            {"Name": "Charlie", "Age": 19, "Major": "Physics", "GPA": 3.9},
            {"Name": "Diana", "Age": 22, "Major": "Computer Science", "GPA": 3.7}
        ]
    
    elif table_type == "sales":
        return [
            {"Product": "Laptop", "Category": "Electronics", "Price": 1200, "Units": 15},
            {"Product": "Phone", "Category": "Electronics", "Price": 800, "Units": 25},
            {"Product": "Desk", "Category": "Furniture", "Price": 300, "Units": 8},
            {"Product": "Chair", "Category": "Furniture", "Price": 150, "Units": 12}
        ]
    
    else:
        raise ValueError(f"Unsupported table type: {table_type}")


# Convenience function maintained for compatibility
def print_table_simple(T: List[Dict[str, Any]]) -> None:
    """Simple version of print_table for compatibility with existing code"""
    print_table(T, max_rows=None, max_col_width=30)