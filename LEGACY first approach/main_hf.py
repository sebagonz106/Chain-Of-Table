import os
import re
import pandas as pd
import requests
import sqlite3
from gpt2 import generar_respuesta_gpt2 as gpt2

HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    raise ValueError("No se ha configurado la variable de entorno HF_TOKEN. Por favor, añade tu token de Hugging Face.")
    
API_URL = "https://api-inference.huggingface.co/models/philschmid/bart-large-cnn-samsum" #https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

def load_data(source: str, sql_query: str = None):
    if source.endswith(".csv"):
        return pd.read_csv(source)
    elif source.endswith(".html"):
        tables = pd.read_html(source)
        return tables[0]
    elif source.endswith(".db") or source.endswith(".sqlite"):
        if not sql_query:
            raise ValueError("Se requiere una consulta SQL para cargar datos desde la base de datos.")
        conn = sqlite3.connect(source)
        df = pd.read_sql_query(sql_query, conn)
        conn.close()
        return df
    else:
        raise ValueError(f"Tipo de archivo no compatible: {source}")

def aplicar_prompts(df: pd.DataFrame, prompt_template: str, columnas=None):
    if columnas:
        df = df[columnas]
    resultados = []
    for _, fila in df.iterrows():
        prompt = prompt_template.format(**fila.to_dict())
        respuesta = send_prompt(prompt)
        resultados.append(respuesta)
    return resultados

def send_prompt_through_api(prompt: str) -> str:
    payload = {
        "inputs": prompt,
        "options": {"wait_for_model": True}
    }
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    if response.ok:
        res = response.json()
        if isinstance(res, list):
            return res[0]["generated_text"]
        elif isinstance(res, dict) and "generated_text" in res:
            return res["generated_text"]
        else:
            return str(res)
    return f"Error {response.status_code}: {response.text}"

def send_prompt(prompt: str) -> str:
    return gpt2(prompt)

def get_content(name: str, folder: str = "prompts", type: str = ".txt") -> str:
    with open(folder + "/"+ name + type, encoding="utf-8") as f:
        content = f.read()
    return content

def format_str(text: str, values: dict) -> str:
    try:
        return text.format(**values)
    except KeyError as e:
        raise KeyError(f"La variable {e} no está definida en el diccionario proporcionado.")
    
def get_plan (text: str) -> list[str]:
    # Patrón para identificar secuencias como "1-", "2-", etc.
    pattern = re.compile(r'(?<!\S)\d+-(?=\s|$)')
    matches = list(pattern.finditer(text))
    
    if not matches:
        return []
    
    plan = []
    for i, match in enumerate(matches):
        start_idx = match.end()   # Inicio de la oración (después del "-")
        if i < len(matches) - 1:
            end_idx = matches[i+1].start()  # Fin de la oración (antes del siguiente número)
        else:
            end_idx = len(text)  # Última oración: hasta el final del texto
        
        # Extraer y limpiar espacios alrededor de la oración
        oracion = text[start_idx:end_idx].strip()
        plan.append(oracion)
    
    return plan

def main(data: str):
    prompt = format_str(get_content("base"), {"query": get_content("query")})
    first_response = send_prompt(prompt)

    prompt = format_str(get_content("plan"), {"question": first_response})
    plan_response = send_prompt(prompt) #si devuelve el prompt: [len(prompt)+1:]
    
    plan = get_plan(plan_response)

    if not plan:
        print("No se pudo generar un plan a partir de la respuesta.")
        return "No se pudo completar la tarea."

    info = [None] * len(plan) #almacenar el feedback
    
    prompt = format_str(get_content("first_step"), {"task" : plan[0], "data": data})
    info[0] = send_prompt(prompt) #si devuelve el prompt: [len(prompt)+1:]
    print(f"Paso 1: {info[0]}")

    for i in range(1, len(plan)):
        prompt = format_str(get_content("step_struct"), {"task": plan[i], "info": info[0:i-1], "data": data})
        info[i] = send_prompt(prompt)
        print(f"Paso {i+1}: {info[i]}")
    
    return info[-1]

# source = "datos/ejemplo.csv"
# sql_query = None

# df = load_data(source, sql_query)

data = get_content("ejemplo", "datos", ".csv")
print(main(data))


# respuestas = aplicar_prompts(df, prompt_template)
# for i, r in enumerate(respuestas):
#     print(f"[{i}] {r}\n")

