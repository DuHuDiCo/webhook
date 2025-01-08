from fastapi import FastAPI, File, UploadFile, HTTPException,Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import List, Optional
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
    expected_token = "EAAXRz1H2U84BOzvhWOslZAnVryCduZCQb8XWmk5tZAcxuOJKOiEwtH83maCUz8MMMZAnuDe4Y0y3kkdDoAycjl5SLWRVO5EvYKroSSDdziC0BbtSTDBt81FlQLGvWT6eMm0xGJZBAXHZAIKnBrOuvwnr4km0ekOuzTOOJxVlJZBICv6ygut1tRHz3rlnmvsQgBDKRjzn0ZCMzpsdqKlCVjy0ePko7IW2won7gOt4PditCAZDZD"
    
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
async def webhook(payload: WebhookPayload):
    
    print(payload)
    return {"message": "datos recibidos correctamente"}