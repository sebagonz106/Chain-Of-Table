from prompts.dynamic_plan import dynamic_plan
from prompts.generate_args import generate_args
from prompts.query import query
from utils.table_ops import apply_operation
from utils.table_io import load_table, print_table

def chain_of_table_reasoning(table_path, question):
    T = load_table(table_path)
    chain = [('[B]', None)]
    print("Pregunta:", question)
    print("Tabla inicial:")
    print_table(T)

    while True:
        f = dynamic_plan(T, question, chain)
        if f == '[E]':
            break
        args = generate_args(T, question, f)
        T = apply_operation(T, f, args)
        chain.append((f, args))
        print(f"Se aplica operación: {f} con argumentos: {args}")
        print_table(T)

    answer = query(T, question)
    print("Respuesta final:", answer)