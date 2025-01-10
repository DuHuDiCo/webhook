import google.generativeai as genai
from PIL import Image
import json


genai.configure(api_key="AIzaSyATWEAxTXNCLxJ2hjy8Dcoi_Ovsy7ALmkQ")
instruction = """Eres un modelo especializado en procesar imágenes de recibos de pago. Voy a proporcionarte imágenes de recibos, y tu tarea será analizar la información contenida en estas imágenes y devolver exclusivamente un objeto JSON con los siguientes campos:



"numero_recibo": El número del recibo (o transacción).

"fecha_pago": La fecha del pago en formato YYYY-MM-DD.

"numero_aprobacion": El número de aprobación (si existe).

"valor": El monto pagado.

"banco": El nombre del banco.

Si no encuentras alguno de los campos solicitados en la imagen, usa el valor null en su lugar. No incluyas ningún otro texto ni comentarios en la respuesta, únicamente el JSON."""
model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=instruction)



def enviarIA(prompt, imagen):
    image = Image.open(imagen)
    responseIa = model.generate_content([prompt, image])
    response = responseIa.text.strip()
    print(response)
    
    # Eliminar los delimitadores de código
    if response.startswith("```json"):
        response = response[7:]  # Eliminar ```json del inicio
    if response.endswith("```"):
        response = response[:-3]  # Eliminar ``` del final
    
    try:
        json_response = json.loads(response)
        return json_response
    except json.JSONDecodeError as e:
        print("Error al decodificar JSON:", e)
        print("Respuesta recibida:", response)
        return None
    
   

