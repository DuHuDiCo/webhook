# Imagen base
FROM python:3.10

# Crear directorio de trabajo
WORKDIR /app

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY . .

# Crear carpeta para subir archivos
RUN mkdir /app/uploads

# Exponer el puerto de la aplicación
EXPOSE 3000

# Comando de inicio
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]
