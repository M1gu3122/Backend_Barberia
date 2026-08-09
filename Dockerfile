FROM python:3.12.10-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia los archivos de dependencias
COPY requirements.txt .

# Instala dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo el código
COPY . .

# Expose el puerto
EXPOSE 8000

# Comando para ejecutar
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
