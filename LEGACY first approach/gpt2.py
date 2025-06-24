from transformers import GPT2LMHeadModel, GPT2Tokenizer
import torch # pip install torch transformers accelerate bitsandbytes

def generar_respuesta_gpt2(
    prompt: str,
    modelo: str = "gpt2",  # Opciones: "gpt2", "gpt2-medium", "gpt2-large", "gpt2-xl"
    max_longitud: int = 100,
    temperatura: float = 0.7,
    usar_gpu: bool = False,
    seed: int = None
) -> str:
    """
    Genera una respuesta a partir de un prompt usando GPT-2.

    Args:
        prompt (str): Texto de entrada para el modelo.
        modelo (str): Versión de GPT-2 a usar.
        max_longitud (int): Máxima longitud de tokens en la respuesta.
        temperatura (float): Controla la creatividad (0.1-1.0).
        usar_gpu (bool): Si es True, usa CUDA (GPU).
        seed (int): Semilla para reproducibilidad.

    Returns:
        str: Respuesta generada por el modelo.
    """
    try:
        # Configurar semilla si se especifica
        if seed is not None:
            torch.manual_seed(seed)

        # Cargar modelo y tokenizador
        tokenizador = GPT2Tokenizer.from_pretrained(modelo)
        modelo = GPT2LMHeadModel.from_pretrained(modelo)

        # Mover a GPU si está disponible y se solicita
        dispositivo = "cuda" if usar_gpu and torch.cuda.is_available() else "cpu"
        modelo.to(dispositivo)

        # Tokenizar input y generar respuesta
        inputs = tokenizador(prompt, return_tensors="pt").to(dispositivo)
        
        with torch.no_grad():
            outputs = modelo.generate(
                **inputs,
                max_length=max_longitud,
                temperature=temperatura,
                do_sample=True,
                pad_token_id=tokenizador.eos_token_id
            )

        # Decodificar y limpiar la respuesta
        respuesta = tokenizador.decode(outputs[0], skip_special_tokens=True)
        
        # Eliminar el prompt de la respuesta si está presente
        if respuesta.startswith(prompt):
            respuesta = respuesta[len(prompt):].strip()

        return respuesta

    except Exception as e:
        return f"Error al generar la respuesta: {str(e)}"

# Ejemplo de uso
if __name__ == "__main__":
    prompt_ejemplo = "Explica la teoría de la relatividad de Einstein en términos simples:"
    
    respuesta = generar_respuesta_gpt2(
        prompt=prompt_ejemplo,
        modelo="gpt2-medium",  # Modelo más potente que el base
        max_longitud=150,
        temperatura=0.6,
        usar_gpu=True,  # Usará GPU si está disponible
        seed=42  # Para resultados reproducibles
    )
    
    print(f"Prompt: {prompt_ejemplo}\nRespuesta: {respuesta}")