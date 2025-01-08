from fastapi import FastAPI, File, UploadFile, HTTPException,Request
from fastapi.responses import PlainTextResponse,JSONResponse
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


expected_token = "EAAXRz1H2U84BO49c7WZC9mqWZAF4w7vx8ZCN1LIjDnq2SM2pOXnDZBYEPeHmCZBuZBPaY2LQCSd0NKYcmVz7kBW7TZAiZAZBUylu9s0JZBZCZCOohZADnoC5btiRDuHrKqGwNnGHl3j9XtCPsWTdYL9ZCvLa1hVDceucAo4TsfcGGLE1vvWWQYBBzwUSsPao64KpESfy6Vgq0EF3DSXOpX4ADAkL2kMOJV8i9AAPYlpJNRl0oESGoZD"



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
    try:
        payload = await request.json()
        print("Payload recibido:", json.dumps(payload, indent=2))  # Para depuración

        # Verificar si 'entry' y 'changes' están en el payload
        entries = payload.get('entry', [])
        for entry in entries:
            changes = entry.get('changes', [])
            for change in changes:
                value = change.get('value', {})
                messages = value.get('messages', [])

                if messages:
                    for message in messages:
                        sender_number = message.get('from')
                        message_body = message.get('text', {}).get('body')
                        phone_number_id = value.get('metadata', {}).get('phone_number_id')

                        if sender_number and message_body:
                            print(f"Mensaje recibido de {sender_number}: {message_body}")

                            # Preparar el mensaje de respuesta
                            response_message = "Mensaje recibido con éxito"

                            data = {
                                "messaging_product": "whatsapp",
                                "to": sender_number,
                                "type": "text",
                                "text": {
                                    "body": response_message
                                }
                            }

                            # Enviar la respuesta usando la API de WhatsApp Business
                            url = f"https://graph.facebook.com/v21.0/{phone_number_id}/messages"
                            headers = {
                                "Authorization": f"Bearer {expected_token}",
                                "Content-Type": "application/json"
                            }

                            response = requests.post(url, headers=headers, data=json.dumps(data))

                            if response.status_code == 200:
                                print("Mensaje enviado exitosamente.")
                            else:
                                print(f"Error al enviar el mensaje: {response.text}")

        # Responder a Meta que el evento fue recibido correctamente
        return JSONResponse(content={"status": "EVENT_RECEIVED"}, status_code=200)

    except KeyError as e:
        print(f"KeyError: {e}")
        raise HTTPException(status_code=400, detail=f"Missing key: {e}")
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
