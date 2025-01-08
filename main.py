from fastapi import FastAPI, File, UploadFile, HTTPException,Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import List, Optional
import requests
import json


app = FastAPI()
# Definir las clases de Pydantic que coinciden con la estructura de los datos
class Profile(BaseModel):
    name: str

class Contact(BaseModel):
    profile: Profile
    wa_id: str

class TextMessage(BaseModel):
    body: str

class Message(BaseModel):
    from_: str
    id: str
    timestamp: str
    type: str
    text: Optional[TextMessage] = None  # Solo si el tipo es texto

class Metadata(BaseModel):
    display_phone_number: str
    phone_number_id: str

class Value(BaseModel):
    messaging_product: str
    metadata: Metadata
    contacts: List[Contact]
    messages: List[Message]

class WebhookPayload(BaseModel):
    field: str
    value: Value


expected_token = "EAAXRz1H2U84BOzvhWOslZAnVryCduZCQb8XWmk5tZAcxuOJKOiEwtH83maCUz8MMMZAnuDe4Y0y3kkdDoAycjl5SLWRVO5EvYKroSSDdziC0BbtSTDBt81FlQLGvWT6eMm0xGJZBAXHZAIKnBrOuvwnr4km0ekOuzTOOJxVlJZBICv6ygut1tRHz3rlnmvsQgBDKRjzn0ZCMzpsdqKlCVjy0ePko7IW2won7gOt4PditCAZDZD"



@app.post("/webhook")
async def webhook(file: UploadFile = File(...)):
    try:
        print({"filename": file.filename, "content_type": file.content_type})
        return {"message": "Archivo procesado correctamente"}
    except Exception as e:
        return HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    
    
@app.get("/webhook/verify")
async def verify_webhook(request: Request):
    # Aquí validas el `hub_verify_token` con el valor esperado
    
    
     # Obtener los parámetros de la URL
    params = request.query_params

    hub_mode = params.get('hub.mode')
    hub_challenge = params.get('hub.challenge')
    hub_verify_token = params.get('hub.verify_token')
    
    print(hub_mode)
    print(hub_challenge)
    print(hub_verify_token)
    
    print(hub_verify_token == expected_token)
    print(hub_mode == "subscribe")
    
    
    
    if hub_verify_token == expected_token:
        if hub_mode == "subscribe":
            return PlainTextResponse(content=hub_challenge)
    else:
        return PlainTextResponse(content="Unauthorized", status_code=401)
    
@app.post("/webhook/verify")
async def webhook(request: Request):
    # Extraemos el cuerpo de la solicitud en formato JSON
    payload = await request.json()

    # Extraemos el número de teléfono del remitente y el mensaje
    sender_number = payload['entry'][0]['changes'][0]['value']['messages'][0]['from']
    number_id = payload['entry'][0]['changes'][0]['value']['metadata']['phone_number_id']
    message_text = payload['entry'][0]['changes'][0]['value']['messages'][0]['text']['body']
    
    # Imprimir para depuración
    print(f"Mensaje recibido de {sender_number}: {message_text}")

    # Definir el mensaje que se va a enviar como respuesta
    response_message = "Mensaje recibido"
    
    # Preparar el cuerpo de la solicitud para enviar el mensaje
    data = {
        "messaging_product": "whatsapp",
        "to": sender_number,
        "type": "text",
        "text": {"body": response_message}
    }
    print(data)
    print("NUMBER_ID: "+number_id)

    # Enviar la respuesta al remitente usando la API de WhatsApp Business
    url = f"https://graph.facebook.com/v21.0/{number_id}/messages"
    headers = {
        "Authorization": f"Bearer {expected_token}",
        "Content-Type": "application/json"
    }

    # Realizar la solicitud POST para enviar el mensaje
    response = requests.post(url, headers=headers, data=json.dumps(data))

    # Verificamos si se envió correctamente
    if response.status_code == 200:
        print({"status": "Message sent"})
        return {"status": "EVENT_RECEIVED"}
    else:
        print({"status": "Message no sent"})
        return {"status": "Failed to send message", "error": response.json()}
