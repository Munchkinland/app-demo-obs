# Usar una imagen base de Python
FROM python:3.9-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar los requisitos y el código de la aplicación al contenedor
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Exponer los puertos que usará la aplicación
EXPOSE 5000
EXPOSE 8000

# Comando para ejecutar la aplicación
CMD ["python", "app.py"]
