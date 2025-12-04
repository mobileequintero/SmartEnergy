import os
import json
from openai import OpenAI

# Obtener API Key desde variable de ambiente
api_key = os.getenv("OPENAI_API_KEY")

def lambda_handler(event, context):
    """
    AWS Lambda Handler
    """
    # Obtener la pregunta del evento
    pregunta = event.get("pregunta", "Hola, ¿cómo estás?")
    
    # Inicializar cliente de OpenAI
    client = OpenAI(api_key=api_key)
    
    # Llamar a OpenAI
    respuesta = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": pregunta}]
    )
    
    # Obtener la respuesta
    resultado = respuesta.choices[0].message.content
    
    # Retornar respuesta en formato JSON
    return {
        "statusCode": 200,
        "body": json.dumps({
            "pregunta": pregunta,
            "respuesta": resultado
        })
    }


# Para pruebas locales
if __name__ == "__main__":
    # Evento de prueba
    event = {"question": "¿Cuál es la capital de Francia?"}
    resultado = lambda_handler(event, None)
    print(resultado)