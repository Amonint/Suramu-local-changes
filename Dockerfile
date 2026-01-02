# Imagen base ligera de Python
FROM python:3.11-slim

# Evitar creación de __pycache__ y buffer de stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# Crear directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para build (si alguna lib de Python lo requiere)
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Exponer el puerto usado por la app
EXPOSE 8080

# Comando de arranque con gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:${PORT}", "main:app"]
