from flask import Flask, jsonify, request
import time
import random
import logging
import threading
import requests
from prometheus_client import start_http_server, Summary, Counter
import argparse

# Configurar logging
logging.basicConfig(level=logging.INFO)

# Métricas de Prometheus
REQUEST_TIME = Summary('request_processing_seconds', 'Tiempo dedicado a procesar la solicitud')
REQUEST_COUNT = Counter('request_count', 'Número total de solicitudes')
ERROR_COUNT = Counter('error_count', 'Número total de errores')

def create_app():
  app = Flask(__name__)

  # Función para simular carga de CPU
  def simulate_cpu_load(duration):
      end_time = time.time() + duration
      while time.time() < end_time:
          random.random() * random.random()

  # Endpoint para simular una carga pesada
  @REQUEST_TIME.time()
  @app.route('/heavy', methods=['GET'])
  def heavy_load():
      REQUEST_COUNT.inc()
      try:
          start = time.time()
          duration = float(request.args.get('duration', 5))
          simulate_cpu_load(duration)  # Simula una carga pesada en CPU
          processing_time = time.time() - start
          logging.info(f"Procesado heavy load en {processing_time} segundos")
          return jsonify({
              "status": "success",
              "message": "Heavy load simulated",
              "duration": processing_time
          }), 200
      except Exception as e:
          ERROR_COUNT.inc()
          logging.error(f"Error durante heavy load: {e}")
          return jsonify({"status": "error", "message": str(e)}), 500

  # Endpoint para simular una carga ligera
  @REQUEST_TIME.time()
  @app.route('/light', methods=['GET'])
  def light_load():
      REQUEST_COUNT.inc()
      try:
          duration = float(request.args.get('duration', 1))
          time.sleep(duration)  # Simula una carga ligera
          logging.info("Procesado light load")
          return jsonify({"status": "success", "message": "Light load simulated"}), 200
      except Exception as e:
          ERROR_COUNT.inc()
          logging.error(f"Error durante light load: {e}")
          return jsonify({"status": "error", "message": str(e)}), 500

  # Endpoint para simular errores
  @app.route('/fail', methods=['GET'])
  def fail():
      REQUEST_COUNT.inc()
      ERROR_COUNT.inc()
      logging.error("Fallo simulado")
      return jsonify({"status": "error", "message": "Simulated failure"}), 500

  return app

# Clase para generar cargas automáticamente
class LoadGenerator:
  def __init__(self, endpoint, interval, request_type='GET', params=None):
      self.endpoint = endpoint
      self.interval = interval
      self.request_type = request_type.upper()
      self.params = params or {}
      self.stop_event = threading.Event()
      self.thread = threading.Thread(target=self.run, daemon=True)

  def start(self):
      self.thread.start()
      logging.info(f"Generador de carga iniciado para {self.endpoint} cada {self.interval} segundos")

  def stop(self):
      self.stop_event.set()
      self.thread.join()
      logging.info(f"Generador de carga detenido para {self.endpoint}")

  def run(self):
      while not self.stop_event.is_set():
          try:
              url = f"http://localhost:5000{self.endpoint}"
              if self.request_type == 'GET':
                  requests.get(url, params=self.params)
              elif self.request_type == 'POST':
                  requests.post(url, data=self.params)
              else:
                  logging.error(f"Tipo de solicitud no soportada: {self.request_type}")
              time.sleep(self.interval)
          except Exception as e:
              logging.error(f"Error durante la generación automática de carga: {e}")

if __name__ == "__main__":
  # Analizar argumentos de línea de comandos
  parser = argparse.ArgumentParser(description='Simulador de Cargas con Flask')
  parser.add_argument('--port', type=int, default=5000, help='Puerto para la aplicación Flask')
  parser.add_argument('--prometheus_port', type=int, default=8000, help='Puerto para métricas de Prometheus')
  parser.add_argument('--auto_load', action='store_true', help='Habilitar generación automática de carga')
  args = parser.parse_args()

  # Iniciar el servidor de métricas en el puerto especificado
  start_http_server(args.prometheus_port)

  # Crear la aplicación Flask
  app = create_app()

  # Iniciar la generación automática de carga si está habilitada
  if args.auto_load:
      # Crear generadores de carga para diferentes endpoints
      heavy_load_generator = LoadGenerator(endpoint='/heavy', interval=10, params={'duration': 5})
      light_load_generator = LoadGenerator(endpoint='/light', interval=5, params={'duration': 1})
      failure_generator = LoadGenerator(endpoint='/fail', interval=15)

      # Iniciar los generadores de carga
      heavy_load_generator.start()
      light_load_generator.start()
      failure_generator.start()

  # Iniciar la aplicación Flask
  app.run(host="0.0.0.0", port=args.port)