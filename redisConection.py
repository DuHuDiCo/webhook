import redis, json

# Configuración de Redis
r = redis.Redis(host='192.168.1.241', port=6379, decode_responses=True)

def guardar_datos_en_redis(telefono, campo, valor):
    clave = f"session:{telefono}"
    dictionary = {campo: valor}
    json_data = json.dumps(dictionary)
    r.rpush(clave, json_data)
    r.expire(clave, 3600)  # Expira en 1 hora


def obtener_datos_de_redis(telefono):
    clave = f"session:{telefono}"
    return r.hgetall(clave)
