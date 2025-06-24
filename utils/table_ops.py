def apply_operation(T, f, args):
    # Aplica operaciones simuladas sobre la tabla (lista de dicts)
    if f == "f_select_column":
        return [{k: row[k] for k in args if k in row} for row in T]
    return T