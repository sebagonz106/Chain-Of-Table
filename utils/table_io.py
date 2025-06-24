import json

def load_table(path):
    with open(path, 'r') as f:
        return json.load(f)

def print_table(T):
    if not T:
        print("Tabla vacía")
        return
    headers = T[0].keys()
    print(" | ".join(headers))
    for row in T:
        print(" | ".join(str(row[h]) for h in headers))