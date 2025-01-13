from fastapi import FastAPI, File, UploadFile, HTTPException,Request
from fastapi.responses import PlainTextResponse,JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import requests
import json
import redisConection, geminiConecctionImage, geminiConexionText


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


expected_token = "EAAXRz1H2U84BO5VU70F9PJXdsUSa3fuL22zL1lM1PUEcayE30wzNEyyjSNEP0yqR5Y4NTyKs7h4SgusUXXRYQTBqlfhUKvKyznSLNkDSxi3wjnDROgHOKjUbYFsx0TKDUwtxh2kBZBuZBbCZCBv5lLiMc4n48Ua3r6gpSUoAQXuEtl9MOSWgHsMWkuG6uLsQ8oKPBBtF1vsuvFcmEEf9bYPxnL4jIsyUdHrVXFwLwZDZD"



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
                        # if not message_body:
                        #     message_body = message.get('image', {})
                        phone_number_id = value.get('metadata', {}).get('phone_number_id')
                        
                        
                        if "image" in message:
                             # Si el mensaje contiene una imagen
                            print(message_body)
                            image_info =  message.get('image', {})
                            media_id = image_info.get("id")
                            extention = image_info.get("mime_type").split("/")[1]
                            filename = f"{sender_number}_{media_id}.{extention}"
                            print("IMAGE ID: "+media_id)
                            
                             # Obtener la URL para descargar el archivo de medios
                            download_url = f"https://graph.facebook.com/v21.0/{media_id}?phone_number_id={phone_number_id}"
                            headers = {
                                "Authorization": f"Bearer {expected_token}",
                            }
                            print(headers)
                            
                            # Solicitar los detalles del archivo de medios
                            media_response = requests.get(download_url, headers=headers)
                            
                            print("REQUEST:")
                            print(media_response)
                            
                            
                            if media_response.status_code == 200:
                                media_data = media_response.json()
                                file_url = media_data["url"]
                                image_url = {"url": file_url}
                                print(file_url)
                                redisConection.guardar_datos_en_redis(phone_number_id, "image", image_url)
                                guardarImagen(file_url, headers, filename)
                                print("Imagen recibida y guardada en Redis")
                                
                                
                                
                                # Descargar el archivo desde la URL
                                file_response = requests.get(file_url, headers=headers)
                                
                                if file_response.status_code != 200:
                                    print(f"Error al descargar la imagen: {file_response.status_code}")
                                    
                               
                                    
                                path = "uploads/"
                                filename = path+filename
                                # Guardar la imagen en el servidor
                                with open(filename, "wb") as f:
                                    f.write(file_response.content)
                                print("Imagen descargada y guardada")
                                
                               

                                datosIA = geminiConecctionImage.enviarIA("imagen", filename)
                                                           
                                
                                compro = {"comprobante": datosIA}
                                redisConection.guardar_datos_en_redis(phone_number_id, "comprobante", compro)
                                enviarMensaje("Gracias por enviar tu comprobante de pago. Por favor ingresa el nombre del banco donde realizaste el pago o la transferencia.", sender_number, phone_number_id)

                                
                                
                                
                                

                                
                                    
                            else:
                                print(f"Error al obtener la URL del archivo: {media_response.status_code}")
                        
                        
                        elif "text" in message:

                            if sender_number and message_body:
                                
                                message= {"text": message_body}
                                print(message)
                                print(phone_number_id)
                                
                                
                                ##VALIDAR NUMERO DOCUMENTO
                                if  validarNumeroDocumento(message_body) :
                                    print("Numero documento  valido")
                                    redisConection.guardar_datos_en_redis(phone_number_id, "text", message)
                                    enviarMensaje("Gracias por ingresar tu numero de documento. Por favor envianos el comprobante de pago para verificarlo.", sender_number, phone_number_id)
                                    return
                                    
                                if geminiConexionText.validarBanco(message_body):
                                    print("Banco valido")
                                    redisConection.guardar_datos_en_redis(phone_number_id, "banco", message)
                                    return
                                    
                                    
                                enviarMensaje("Hola, gracias por contactarte con nosotros. Este es el bot de comprobantes de pago para ElectroHogar. Por favor Ingresa tu numero de documento (sin espacios, guiones, puntos, comas.)", sender_number, phone_number_id)
                                
                                
                                
                                
                                
                                print(f"Mensaje recibido de {sender_number}: {message_body}")

                                
                        
                        # # Enviar el mensaje a Meta
                        # enviarMensaje(response_message, sender_number)

        # Responder a Meta que el evento fue recibido correctamente
        return JSONResponse(content={"status": "EVENT_RECEIVED"}, status_code=200)

    except KeyError as e:
        print(f"KeyError: {e}")
        raise HTTPException(status_code=400, detail=f"Missing key: {e}")
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


def guardarImagen(image_url, headers, nombre_archivo):
    # Descargar el archivo desde la URL
    file_response = requests.get(image_url, headers=headers)
    
    if file_response.status_code != 200:
        print(f"Error al descargar la imagen: {file_response.status_code}")
        
    
        
    path = "uploads/"
    filename = path+nombre_archivo
    # Guardar la imagen en el servidor
    with open(filename, "wb") as f:
        f.write(file_response.content)
    print("Imagen descargada y guardada")
    
    
def validarResultadosIA(content):
  
    # Validar cuáles son nulos
    campos_nulos = {key: value for key, value in content.items() if value is None or value == ""}
    return campos_nulos
  
      
def enviarMensaje(mensaje, number, phone_number_id):
    # Preparar el mensaje de respuesta
    

    data = {
        "messaging_product": "whatsapp",
        "to": number,
        "type": "text",
        "text": {
            "body": mensaje
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
        response = redisConection.obtener_datos_de_redis(phone_number_id)
        
        print(response)
        print("Mensaje enviado exitosamente.")
    else:
        print(f"Error al enviar el mensaje: {response.text}")  
        
        
def validarNumeroDocumento(numero_documento):
    if len(numero_documento) >= 6 and len(numero_documento) <= 10 and numero_documento.isdigit():
        return True
    else:
        return False