import redis, json

# Configuración de Redis
r = redis.Redis(host='192.168.1.241', port=6379, decode_responses=True)

def guardar_datos_en_redis(telefono,message_type,content):
    clave = f"session:{telefono}"
    
    session_data = r.hgetall(clave)
    
    
    if not session_data:
        session_data = {
            "cedula": "",
            "comprobante": {
                    "numero_de_recibo": "",
                    "fecha_pago": "",
                    "valor": 0,
                    "banco": "",
                    "url": ""
            }
        }
    
    
    if message_type == "text":
        session_data["cedula"] = content["text"]
        
    if message_type == "image":
        session_data["comprobante"]["url"] = content["url"]
    
    if message_type == "comprobante":
        session_data["comprobante"]["numero_de_recibo"] = content["comprobante"]["numero_de_recibo"]
        session_data["comprobante"]["fecha_pago"] = content["comprobante"]["fecha_pago"]
        session_data["comprobante"]["valor"] = content["comprobante"]["valor"]
        session_data["comprobante"]["banco"] = content["comprobante"]["banco"]
        
    
    # if not validate_comprobante(session_data["comprobante"]):
    #     return None;
    
    r.hset(clave, json.dumps(session_data))
    r.expire(clave, 3600)  # Expira en 1 hora
    
    
    return session_data


def obtener_datos_de_redis(telefono):
    clave = f"session:{telefono}"
    return r.hgetall(clave)


def validate_comprobante(comprobante):
    # Validar que todas las claves tengan valores válidos
    for key, value in comprobante.items():
        if isinstance(value, str) and not value.strip():  # Verifica cadenas no vacías
            return False
        if isinstance(value, (int, float)) and value <= 0:  # Verifica números mayores a cero
            return False
        if value is None:  # Verifica que no sea None
            return False
    return True
