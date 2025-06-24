# 🧠 Chain-of-Table (CoT) - Complete Implementation

A complete implementation of the **Chain-of-Table** algorithm for step-by-step tabular reasoning with Large Language Models (LLMs).

## 🎯 What is Chain-of-Table?

Chain-of-Table (CoT) is a tabular reasoning strategy that allows LLMs to solve complex questions about tables. Instead of directly generating an answer, CoT guides the model to progressively transform the table through a chain of atomic operations until reaching a final table from which the answer is obtained.

## 🏗️ System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   DynamicPlan   │───▶│  GenerateArgs    │───▶│   Execution     │
│ (Select         │    │ (Generate        │    │ (Apply          │
│  operation)     │    │  arguments)      │    │  operation)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         ▲                                               │
         │                                               ▼
┌─────────────────┐                            ┌─────────────────┐
│     Query       │◀───────────────────────────│ Table Transform │
│ (Final          │                            │ (T → T')        │
│  answer)        │                            │                 │
└─────────────────┘                            └─────────────────┘
```

## 📁 Project Structure

```
Chain-Of-Table/
├── main.py                 # Main orchestrator
├── sample_table.json       # Sample table
├── utils/
│   ├── table_ops.py        # Atomic operations
│   └── table_io.py         # Table input/output
├── prompts/
│   ├── dynamic_plan.py     # Operation selection
│   ├── generate_args.py    # Argument generation
│   └── query.py            # Final answer
├── test_operations.py      # Operation tests
├── test_prompts.py         # Prompt tests
├── demo_operations.py      # Operation demo
├── full_demo.py           # Complete demo
└── README.md              # This file
```

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
- Input validation
- 1-based indexing (as in original paper)

### ✅ **Intelligent Prompts**
- Integrated few-shot examples
- Fallback logic without LLM
- Automatic country and data extraction

### ✅ **Output Format**
- PIPE format visualization
- JSON export
- Complete transformation history

### ✅ **Flexibility**
- Works with and without LLM
- Command line arguments
- Silent and verbose modes

## 🔄 Algorithm Flow

```python
def chain_of_table_flow(table, question):
    chain = ['[B]']  # Start
    
    while True:
        # 1. Select operation
        operation = dynamic_plan(table, question, chain)
        
        if operation == '[E]':  # End
            break
            
        # 2. Generate arguments
        args = generate_args(table, question, operation)
        
        # 3. Apply operation
        table = apply_operation(table, operation, args)
        chain.append((operation, args))
    
    # 4. Generate final answer
    answer = query(table, question)
    return answer
```

## 📈 Example Results

The system generates a JSON file with:
- **answer**: Final answer
- **chain**: Complete operation chain
- **tables**: Intermediate tables at each step
- **final_table**: Final transformed table
- **steps**: Number of executed steps

## 🎯 Approach Advantages

1. **Transparency**: Each step is visible and explainable
2. **Flexibility**: Works with different types of questions
3. **Robustness**: Handles errors and edge cases
4. **Scalability**: Easy to add new operations
5. **Evaluation**: Allows step-by-step metrics

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
- Complete atomic operations
- Prompts with few-shot examples
- Complete reasoning system
- Command line interface
- Extensive tests and demos

🚀 **Ready to use** in tabular reasoning projects!