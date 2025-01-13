import google.generativeai as genai


genai.configure(api_key="AIzaSyATWEAxTXNCLxJ2hjy8Dcoi_Ovsy7ALmkQ")
instruction = """Recibirás palabras o textos como entrada. Tu tarea es verificar si la entrada coincide exactamente con el nombre de algún banco que opera en Colombia. Si hay coincidencia, responde únicamente con ese nombre exacto del banco. Si no hay coincidencia, no respondas nada (respuesta vacía).

Reglas:
1. Solo responde con el nombre exacto del banco si hay coincidencia.
2. Devuelve un false si no hay coincidencia o un true si hay coincidencia.
3. No incluyas explicaciones ni texto adicional.
4. La comparación debe ignorar mayúsculas y minúsculas.
5. Considera tanto nombres comunes como nombres oficiales de los bancos.

Ejemplos de entradas válidas serían:
- Bancolombia
- Banco de Bogotá
- Davivienda
- Banco Popular
- BBVA Colombia
- Scotiabank Colpatria
- Banco de Occidente
- Banco Caja Social
- Banco Agrario de Colombia."""
model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=instruction)



def validarBanco(prompt):
    responseIa = model.generate_content(prompt)
    response = bool(responseIa.text.strip())
    
    print(response)
    return response;