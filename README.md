# 🧠 Chain-of-Table (CoT) - Complete Implementation

A complete, robust implementation of the **Chain-of-Table** algorithm for step-by-step tabular reasoning with Large Language Models (LLMs). This implementation includes advanced validation, loop prevention, and intelligent prompt engineering for reliable table operations.

## 🎯 What is Chain-of-Table?

Chain-of-Table (CoT) is a tabular reasoning strategy that allows LLMs to solve complex questions about tables. Instead of directly generating an answer, CoT guides the model to progressively transform the table through a chain of atomic operations until reaching a final table from which the answer is obtained.

### 🛡️ Robustness Features

This implementation includes several key improvements for production use:

- **Loop Prevention**: Prevents infinite loops by detecting repeated operations
- **Smart Validation**: Validates column existence before operations like `f_group_by`, `f_sort_by`, `f_select_column`
- **Intelligent Prompting**: Uses step-by-step reasoning examples with explicit "Analysis", "FIRST", and "THEN" logic
- **Operation Exclusion**: Automatically excludes problematic operations and retries with reduced sets
- **Answer Detection**: Stops the chain when the answer is available (e.g., after grouping/counting)

## 🏗️ System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   DynamicPlan   │───▶│  GenerateArgs    │───▶│   Execution     │
│ (Select         │    │ (Generate        │    │ (Apply          │
│  operation)     │    │  arguments)      │    │  operation)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         ▲                                               │
         │              ┌──────────────────┐             ▼
┌─────────────────┐     │   Validation     │    ┌─────────────────┐
│     Query       │◀────│  - Loop Check    │◀───│ Table Transform │
│ (Final          │     │  - Column Check  │    │ (T → T')        │
│  answer)        │     │  - Answer Check  │    │                 │
└─────────────────┘     └──────────────────┘    └─────────────────┘
```

### Key Components:
- **DynamicPlan**: Selects the next operation using intelligent prompting with step-by-step reasoning
- **GenerateArgs**: Generates arguments for the selected operation
- **Validation**: Prevents loops, validates columns, and detects when answers are available
- **Execution**: Applies atomic operations to transform the table
- **Query**: Generates the final answer from the transformed table

## 📁 Project Structure

```
Chain-Of-Table/
├── main.py                 # Main orchestrator
├── sample_table.json       # Sample table
├── utils/
│   ├── table_ops.py        # Atomic operations
│   └── table_io.py         # Table input/output
├── prompts/
│   ├── dynamic_plan.py     # Operation selection with step-by-step reasoning
│   ├── generate_args.py    # Argument generation with validation
│   └── query.py            # Final answer generation
├── reasoner.py             # Main reasoning orchestrator with validation
├── test_operations.py      # Operation tests
├── test_prompts.py         # Prompt tests
├── demo_operations.py      # Operation demo
├── full_demo.py           # Complete demo
└── README.md              # This file
```

## 🤖 Intelligent Prompt Engineering

### Step-by-Step Reasoning Structure

The system uses a sophisticated prompt structure that guides LLMs through explicit reasoning:

1. **Analysis**: General analysis of the table and question
2. **FIRST**: Explicit first step with reasoning  
3. **THEN**: Follow-up steps with clear logic

#### Example Prompt Structure:
```
Analysis: The table contains cyclists with embedded country information. To answer 
"What country has the most cyclists?", I need to extract countries, group by country, 
and count.

FIRST: Use f_add_column to extract country information from the cyclist names.
THEN: Use f_group_by to group by country and count cyclists per country.
```

### Critical Rules

The prompts include explicit rules to prevent common errors:

- **Column Existence Check**: Before using `f_group_by`, `f_sort_by`, or `f_select_column`, check if the column exists
- **Add Columns First**: If a column doesn't exist, use `f_add_column` first
- **No Repetition**: Don't repeat the same operation with identical arguments
- **Answer Detection**: Stop when the answer is clearly available in the table

## 🛡️ Validation & Error Prevention

### Loop Prevention
- Tracks all executed operations with their arguments
- Prevents repeating identical operations
- Automatically excludes problematic operations and retries

### Column Validation
- Checks column existence before operations that require specific columns
- Suggests `f_add_column` when needed columns are missing
- Validates column names in arguments

### Smart Stopping
- Detects when the answer is available (e.g., after grouping operations)
- Prevents unnecessary additional operations
- Maintains operation chain integrity

### Enhanced Args Validation
- **Post-Generation Validation**: Validates all generated arguments against current table state
- **Column Existence Checks**: Ensures operations only reference existing columns
- **Duplicate Column Prevention**: Prevents creating columns that already exist
- **Row Index Validation**: Validates row indices are within valid range (1-based indexing)
- **Smart Error Messages**: Provides clear error messages and helpful suggestions
- **Automatic Recovery**: Excludes operations with invalid arguments and retries with different operations

## 🔧 Implemented Atomic Operations

### 1. `f_add_column(table, column_name, values=None, default_value="")`
Add a new column to the table.
```python
# Example: Add countries extracted from names
f_add_column(table, "Country", ["ESP", "ITA", "ESP"])
```

### 2. `f_select_row(table, row_indices)`
Select specific rows (1-based indexing).
```python
# Example: Select top 3
f_select_row(table, [1, 2, 3])
```

### 3. `f_select_column(table, column_names)`
Select specific columns.
```python
# Example: Only cyclist and country
f_select_column(table, ["Cyclist", "Country"])
```

### 4. `f_group_by(table, column_name, count_column="Count")`
Group rows and count elements.
```python
# Example: Group by country
f_group_by(table, "Country")
```

### 5. `f_sort_by(table, column_name, ascending=True)`
Sort rows by a column.
```python
# Example: Sort by count descending
f_sort_by(table, "Count", ascending=False)
```

## 🚀 System Usage

### Basic Execution (Demo)
```bash
python main.py
```

### Execution with Parameters
```bash
python main.py --question "What country has the most cyclists?" --output results.json
```

### Available Parameters
- `--table`: Path to JSON table file (default: `sample_table.json`)
- `--question`: Question to answer
- `--output`: Output file for results (JSON format)
- `--max-steps`: Maximum number of steps (default: 10)
- `--quiet`: Quiet mode

## 📊 Execution Example

**Input:**
```json
[
  {"Rank": 1, "Cyclist": "Alejandro (ESP)"},
  {"Rank": 2, "Cyclist": "Davide (ITA)"},
  {"Rank": 3, "Cyclist": "Paolo (ITA)"},
  {"Rank": 4, "Cyclist": "Haimar (ESP)"}
]
```

**Question:** "What country has the most cyclists in the top 3?"

**Operation Chain:**
1. `f_add_column("Country")` → Extract countries from names
2. `f_select_row([1, 2, 3])` → Select top 3
3. `f_group_by("Country")` → Group by country
4. `f_sort_by("Count", False)` → Sort by count descending

**Answer:** "Italy" (2 cyclists vs 1 from Spain in top 3)

## 🧪 Tests and Demos

### Atomic Operations Tests
```bash
python test_operations.py
```

### Prompt Tests
```bash
python test_prompts.py
```

### Individual Operations Demo
```bash
python demo_operations.py
```

### Complete Demo
```bash
python full_demo.py
```

## 🎨 Main Features

### ✅ **Robust Operations**
- Error and edge case handling
- Input validation with column existence checks
- 1-based indexing (as in original paper)
- Loop prevention and operation tracking

### ✅ **Intelligent Prompts**
- Step-by-step reasoning with Analysis → FIRST → THEN structure
- Explicit rules to prevent common LLM errors
- Critical column existence validation in prompts
- Fallback logic without LLM for testing

### ✅ **Advanced Validation**
- **Loop Prevention**: Tracks executed operations to prevent infinite loops
- **Column Validation**: Ensures columns exist before operations that require them
- **Answer Detection**: Automatically stops when answer is available
- **Operation Exclusion**: Excludes problematic operations and retries intelligently

### ✅ **Output Format**
- PIPE format visualization
- JSON export with complete operation chain
- Complete transformation history
- Step-by-step execution tracking

### ✅ **Production Ready**
- Works reliably with real LLMs
- Handles edge cases and malformed inputs
- Command line interface with extensive options
- Silent and verbose modes
- Comprehensive error handling

## 🔄 Algorithm Flow

```python
def chain_of_table_flow(table, question):
    chain = ['[B]']  # Start
    executed_operations = set()  # Track operations to prevent loops
    excluded_ops = set()  # Track problematic operations
    
    while True:
        # 1. Check if answer is available
        if answer_available_in_table(table, question):
            break
            
        # 2. Select operation (excluding problematic ones)
        operation = dynamic_plan(table, question, chain, excluded_ops)
        
        if operation == '[E]':  # End
            break
            
        # 3. Generate arguments with validation
        args = generate_args(table, question, operation)
        
        # 4. Validate operation (prevent loops, check columns)
        operation_key = (operation, str(args))
        if operation_key in executed_operations:
            excluded_ops.add(operation)
            continue  # Retry with excluded operation
            
        # 5. Validate column existence for certain operations
        if operation in ['f_group_by', 'f_sort_by', 'f_select_column']:
            if not column_exists(table, args):
                excluded_ops.add(operation)
                continue  # Retry, hopefully with f_add_column
        
        # 6. Apply operation
        table = apply_operation(table, operation, args)
        chain.append((operation, args))
        executed_operations.add(operation_key)
    
    # 7. Generate final answer
    answer = query(table, question)
    return answer
```

### New Validation Features:
- **Loop Detection**: Tracks executed operations to prevent infinite loops
- **Column Validation**: Ensures columns exist before operations that require them  
- **Answer Detection**: Stops when the answer is clearly available
- **Operation Exclusion**: Excludes problematic operations and retries
- **Smart Retry Logic**: Automatically adjusts strategy when operations fail

## 📈 Example Results

The system generates a JSON file with:
- **answer**: Final answer
- **chain**: Complete operation chain
- **tables**: Intermediate tables at each step
- **final_table**: Final transformed table
- **steps**: Number of executed steps

## 🎯 Approach Advantages

1. **Transparency**: Each step is visible and explainable
2. **Reliability**: Advanced validation prevents common LLM errors and infinite loops
3. **Flexibility**: Works with different types of questions and table structures
4. **Robustness**: Handles errors, edge cases, and malformed LLM outputs
5. **Scalability**: Easy to add new operations and validation rules
6. **Evaluation**: Allows step-by-step metrics and debugging
7. **Production Ready**: Includes comprehensive error handling and retry logic

## 🔧 Robustness Testing

The system has been tested for common failure modes:

### Prevented Issues:
- ✅ **Infinite Loops**: System detects and prevents repeated operations
- ✅ **Missing Columns**: Validates column existence before operations
- ✅ **Malformed Arguments**: Robust argument parsing and validation
- ✅ **Endless Chains**: Automatically stops when answer is available
- ✅ **Operation Conflicts**: Excludes problematic operations and retries

### Test Cases:
```bash
# Test loop prevention
python main.py --question "Test question that might cause loops"

# Test column validation  
python main.py --question "Question requiring non-existent columns"

# Test answer detection
python main.py --question "Simple question with clear answer"
```

## 🔧 Customization

### Add New Operation
1. Implement function in `utils/table_ops.py`
2. Add to `get_available_operations()`
3. Update `apply_operation()`
4. Add logic in prompts if necessary

### Integrate Real LLM
```python
# In prompts, change use_llm=True
reasoner = ChainOfTableReasoner()
results = reasoner.reason(table, question, use_llm=True, llm_function=your_llm)
```

## 📚 References

- Original paper: "Chain-of-Table: Evolving Tables in the Reasoning Chain for Table Understanding"
- Implementation based on CoT algorithm for tabular reasoning

## 🏆 Project Status

✅ **Completed:**
- Complete atomic operations with robust error handling
- Advanced prompts with step-by-step reasoning structure
- Comprehensive validation system (loop prevention, column validation, answer detection)
- Complete reasoning system with operation exclusion and retry logic
- Command line interface with extensive options
- Extensive tests and demos
- Production-ready robustness features

### 🚀 **Recent Improvements:**
- **Intelligent Prompting**: Refactored all prompt examples to use Analysis → FIRST → THEN structure
- **Loop Prevention**: Added detection and prevention of repeated operations  
- **Column Validation**: Added checks for column existence before operations
- **Answer Detection**: System stops automatically when answer is available
- **Operation Exclusion**: Problematic operations are excluded and system retries intelligently
- **Critical Rules**: Added explicit rules in prompts to prevent common LLM errors
- **Enhanced Args Validation**: Added comprehensive argument validation after generation to prevent operations on non-existent columns, duplicate columns, and invalid row indices

### ⚠️ **Validation Features:**
- **Column Existence**: Validates that operations like `f_group_by`, `f_sort_by`, `f_select_column` only use existing columns
- **Duplicate Prevention**: Prevents `f_add_column` from creating columns that already exist
- **Row Range Validation**: Ensures `f_select_row` only uses valid row indices (1-based)
- **Smart Error Messages**: Provides helpful suggestions when validation fails
- **Graceful Retry**: Automatically excludes operations with invalid arguments and retries

🎯 **Ready for production use** in tabular reasoning projects with real LLMs!