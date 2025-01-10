import google.generativeai as genai
from PIL import Image


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
    response = model.generate_content(prompt, image=image)
    print(response)
   
   
enviarIA("", "/uploads/573134916425_1274025340569878.jpeg")