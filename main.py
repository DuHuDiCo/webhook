from time import sleep
from fastapi import FastAPI, File, UploadFile, HTTPException,Request
from fastapi.responses import PlainTextResponse,JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import requests
import json
import redisConection, geminiConecctionImage, geminiConexionText
from fastapi import FastAPI, HTTPException
from hvac import Client
from decouple import config

# Configuración de Vault
VAULT_ADDR = config("VAULT_ADDR")
VAULT_TOKEN = config("VAULT_TOKEN")


app = FastAPI()


# Conexión con Vault
vault_client = Client(url=VAULT_ADDR, token=VAULT_TOKEN)



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



def iniciarSession():
    url = f"http://192.168.1.171:9000/api/v1/generate-token"
    
    
    body = {
        "username": secret.get("username"),
        "password": secret.get("password")
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(url,  headers=headers, data=json.dumps(body))
    
    response = response.json()
    return  response["token"]






secret = vault_client.secrets.kv.read_secret_version(path=f"boot", mount_point="kv")["data"]["data"]
expected_token = secret.get("expected_token")
print(expected_token)

token_backend = iniciarSession()




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
        new_client = False
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
                        message_id = message.get('id')
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
                                
                                media_object = {"media_id": media_id}
                                print(media_object)
                                
                                redisConection.guardar_datos_en_redis(phone_number_id, "media_id", media_object)
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
                               
                               
                                
                                if not new_client:
                               
                               

                                    datosIA = geminiConecctionImage.enviarIA("imagen", filename)
                                    
                                    
                                    print(validarResultadosIA(datosIA))
                                    
                                    if  validarResultadosIA(datosIA):
                                        
                                        datosRedis = redisConection.obtener_datos_de_redis(phone_number_id)
                                        new_client = True
                                        if not datosRedis["cedula"]:
                                            
                                            enviarMensaje("Hola, gracias por contactarte con nosotros. Este es el bot de comprobantes de pago para ElectroHogar. Acabas de ingresar el comprobante de pago, por favor Ingresa tu numero de documento (sin espacios, guiones, puntos, comas.)", sender_number, phone_number_id, message_id)
                                            return
                                
                                    else:
                                    
                                        compro = {"comprobante": datosIA}
                                        
                                        
                                        datosValid = redisConection.obtener_datos_de_redis(phone_number_id) 
                                    
                                        if not datosValid is None:
                                            if datosValid["numero_recibo"] == datosIA["numero_recibo"]:
                                                enviarMensaje("Ya existe un pago con ese numero de recibo. Por favor ingresa un pago valido.", sender_number, phone_number_id,message_id)
                                                return
                                        
                                        
                                        redisConection.guardar_datos_en_redis(phone_number_id, "comprobante", compro)
                                        
                                        
                                
                                        enviarMensaje("Gracias por enviar tu comprobante de pago. Por favor ingresa el nombre del banco donde realizaste el pago o la transferencia.", sender_number, phone_number_id,message_id)

                                enviarMensaje("Pago agregado correctamente. El tiempo de aplicacion del pago varia entre 3 a 5 dias habiles. Tu asesor de cartera te contactara y te enviara el recibo del pago realizado. CHAT FINALIZADO 😊", sender_number, phone_number_id, message_id)    
                                    
                            else:
                                enviarMensaje("Error al enviar el archivo. Por favor intenta de nuevo.", sender_number, phone_number_id, message_id)
                                print(f"Error al obtener la URL del archivo: {media_response.status_code}")
                        
                        
                        elif "text" in message:

                            if sender_number and message_body:
                                
                                message= {"text": message_body}
                                print(message)
                                print(phone_number_id)
                                
                      
                                ##VALIDAR NUMERO DOCUMENTO
                                if  validarNumeroDocumento(message_body) :
                                    
                                    client = buscarCliente(message_body)
                                    
                                    redisConection.guardar_datos_en_redis(phone_number_id, "text", message)
                                    
                                    
                                    datos = redisConection.obtener_datos_de_redis(phone_number_id)
                                    
                                    
                                    if  client is None:
                                        new_client = True
                                        
                                    if not datos["url"] is None:
                                        enviarMensaje("Pago agregado correctamente. El tiempo de aplicacion del pago varia entre 3 a 5 dias habiles. Tu asesor de cartera te contactara y te enviara el recibo del pago realizado. CHAT FINALIZADO 😊", sender_number, phone_number_id, message_id)
                                        if  new_client:
                                
                                            phone_number_redirect = secret.get("consignaNumber")
                                            datos = redisConection.obtener_datos_de_redis(phone_number_id)
                                            cdula = datos["cedula"]
                                            enviarMensajeFile(f"Este pago fue redirigido debido a un error o  nuevo cliente. \n Numero de Documento: {cdula}", 
                                                            phone_number_redirect, phone_number_id,datos["url"], datos["media_id"])
                                            print("MENSAJE A CAROLINA ENVIADO")
                                            return     
                                        return    
                                    enviarMensaje("Gracias por ingresar tu numero de documento. Por favor envianos el comprobante de pago para verificarlo.", sender_number, phone_number_id ,message_id)
                                    return
                                    

                                
                                if validarBanco( message_body) :
                                    print("Banco valido")
                                    redisConection.guardar_datos_en_redis(phone_number_id, "banco", message_body)
                                    enviarMensaje("Pago agregado correctamente. El tiempo de aplicacion del pago varia entre 3 a 5 dias habiles. Tu asesor de cartera te contactara y te enviara el recibo del pago realizado. CHAT FINALIZADO 😊", sender_number, phone_number_id, message_id)
                                    datos = redisConection.obtener_datos_de_redis(phone_number_id)
                                    
                                    
                                    # if  new_client:
                                    #     phone_number_id_redirect = secret.get("consingaPhoneId")
                                    #     phone_number_redirect = secret.get("consignaNumber")
                                    #     enviarMensajeFile("Este pago fue redirigido debido a un error o  nuevo cliente. Por favor ingresa el numero de documento del cliente.", phone_number_redirect, phone_number_id_redirect,datos["url"], media_id)
                                    #     print("MENSAJE A CAROLINA ENVIADO")
                                    #     return
                                    
                                    if not new_client:
                                        enviarDatos(datos)
                                        
                                    return  
                                
                                
                                enviarMensaje("Hola, gracias por contactarte con nosotros. Este es el bot de comprobantes de pago para ElectroHogar. Por favor Ingresa tu numero de documento (sin espacios, guiones, puntos, comas.)", sender_number, phone_number_id, message_id)
                            
                                print(f"Mensaje recibido de {sender_number}: {message_body}")
                                return    
                               
                
                
                                    
                        if  new_client:
                            
                            phone_number_redirect = secret.get("consignaNumber")
                            datos = redisConection.obtener_datos_de_redis(phone_number_id)
                            cdula = datos["cedula"]
                            enviarMensajeFile(f"Este pago fue redirigido debido a un error o  nuevo cliente. \n Numero de Documento: {cdula}", 
                                              phone_number_redirect, phone_number_id,datos["url"], datos["media_id"])
                            print("MENSAJE A CAROLINA ENVIADO")
                            return          

                                
                        
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
    # Descargar el archivo desde la URLiniciarSession()
    file_response = requests.get(image_url, headers=headers)
    
    if file_response.status_code != 200:
        print(f"Error al descargar la imagen: {file_response.status_code}")
        
    secret.get("username")
        
    path = "uploads/"
    filename = path+nombre_archivo
    # Guardar la imagen en el servidor
    with open(filename, "wb") as f:
        f.write(file_response.content)
    print("Imagen descargada y guardada")
    
    
def validarResultadosIA(content):
  
    # Verificar si hay campos nulos en el diccionario
    return any(value is None or value == "" for value in content.values())
  
      
def enviarMensaje(mensaje, number, phone_number_id, message_id):
    # Preparar el mensaje de respuesta
    

    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        
        "type": "text",
        "text": {
            "body": mensaje
        }
    }
    
    if  message_id != None:
        
        context ={
            "message_id": message_id
        }
        data["context"] = context
        
    print(data)
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
        


def enviarMensajeFile(message, number, phone_number_id, url_file, media_id):
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "image",
        "image": {
            "id": media_id,
            "caption":  message 
        }
    }

    # Enviar la respuesta usando la API de WhatsApp Business
    url = f"https://graph.facebook.com/v21.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {expected_token}",
        "Content-Type": "application/json"
    }
    # files = {
    #     "file": open(url_file, "rb"),
    #     "type": (None, "image/jpeg")  # Cambia el tipo si usas PNG o GIF
    # }
    print(data)
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    print(response.json())
    return response


        
def validarNumeroDocumento(numero_documento):
    if len(numero_documento) >= 6 and len(numero_documento) <= 10 and numero_documento.isdigit():
        return True
    else:
        return False
    
    
def validarBanco( message_body):    
    bank = geminiConexionText.validarBanco(message_body)
    if bank == "true" or bank.lower() == message_body.lower():
        return True

    return False

def enviarDatos(data):
    url = f"http://192.168.1.171:8025/api/v1/inputData/validar"
    
    token = token_backend
    print("token iniciado "+ token)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    print(response)
    return


def buscarCliente(cedula):
    url = f"http://192.168.1.171:9000/api/v1/clientes/find/{cedula}"
    token = token_backend
    print("token iniciado "+ token)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    exist = False
    if response.status_code != 200:
        return None;
    
    response = response.json()
    exist = True    
    cliente = {"exist": exist, "cliente": response["nombres"]+ " " + response["apellidos"]}
    return cliente
    


def confirmacionDeLectura(phone_number_id, message_id):
    sleep(2)
    url = f"https://graph.facebook.com/v21.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {expected_token}",
        "Content-Type": "application/json"
    }
    
    body ={
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id
    }
    response = requests.put(url, headers=headers, data=json.dumps(body))