import redis, json

# Configuración de Redis
r = redis.Redis(host='192.168.1.241', port=6379, decode_responses=True)

def guardar_datos_en_redis(telefono,message_type,content):
    clave = f"session:{telefono}"
    
    session_data = r.hgetall(clave)
    
    print(session_data)
    
    if not session_data:
        session_data = {
            "cedula": "",
            "numero_de_recibo": "aaaa",
            "fecha_pago": "aaaa",
            "valor": "02",
            "banco": "aaa",
            "url": "aaa"
        }
    
    
    if message_type == "text":
        session_data["cedula"] = content["text"]
        
    if message_type == "image":
        session_data["url"] = content["url"]
    
    if message_type == "comprobante":
        session_data["numero_de_recibo"] = content["comprobante"]["numero_de_recibo"]
        session_data["fecha_pago"] = content["comprobante"]["fecha_pago"]
        session_data["valor"] = content["comprobante"]["valor"]
        session_data["banco"] = content["comprobante"]["banco"]
        
    
    # if not validate_comprobante(session_data["comprobante"]):
    #     return None;
    
    
    print(session_data)
    
   # Guardar cada campo en Redis
    for campo, valor in session_data.items():
        r.hset(clave, campo, valor)
    
    r.expire(clave, 3600)  # Expira en 1 hora
    
    
    return session_data


# Recuperar y deserializar los datos de Redis:
def obtener_datos_de_redis(telefono):
    clave = f"session:{telefono}"
    
    # Obtener los datos de Redis (están en bytes)
    session_data = r.hgetall(clave)
    
    if session_data:
       
        return session_data
    else:
        return None

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
