from google import genai
from google.genai import types
from schemas import AlarmeClimaSchema

def analisar_mensagem_lembrete(texto_usuario: str) -> AlarmeClimaSchema:
    client = genai.Client()
    
    prompt = f"""
    Você é um assistente meteorológico encarregado de configurar alarmes climáticos.
    Extraia as informações necessárias da seguinte mensagem do usuário.
    
    Mensagem do usuário: "{texto_usuario}"
    """
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=AlarmeClimaSchema,
            temperature=0.1,
        ),
    )
    
    return response.parsed