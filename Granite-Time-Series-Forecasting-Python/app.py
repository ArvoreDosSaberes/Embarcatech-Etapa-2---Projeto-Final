"""
Granite Time Series Forecasting - Main Application
Sistema de previsao de series temporais em tempo real usando IBM Granite TTM-R2

Este modulo implementa o servidor Flask principal que coordena:
- Geracao continua de dados temporais
- Previsao usando modelo Granite TTM-R2
- Deteccao de anomalias em tempo real
- Interface web com graficos dinamicos
"""

import os
import logging
from flask import Flask, render_template, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import threading
import time

from src.services.dataGenerator import DataGenerator
from src.services.forecastService import ForecastService
from src.services.anomalyDetector import AnomalyDetector
from src.config import Config

# Configuracao de logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configurar nivel de log para SocketIO para debug
logging.getLogger('socketio').setLevel(logging.INFO)
logging.getLogger('engineio').setLevel(logging.INFO)

# Inicializacao da aplicacao Flask
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Configurar SocketIO com timeouts maiores e ping/pong
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    async_mode='threading',
    ping_timeout=120,  # Timeout de ping aumentado para 120s
    ping_interval=25,  # Intervalo de ping a cada 25s
    max_http_buffer_size=10 * 1024 * 1024,  # Buffer de 10MB para mensagens grandes
    logger=True,  # Habilitar logs do SocketIO
    engineio_logger=True  # Habilitar logs do Engine.IO
)

# Inicializacao dos servicos
logger.info("🔧 [Initialization] Initializing services...")
data_generator = DataGenerator(
    interval_seconds=Config.DATA_GENERATION_INTERVAL,
    base_value=Config.BASE_VALUE,
    noise_level=Config.NOISE_LEVEL
)
forecast_service = ForecastService(
    model_name=Config.MODEL_NAME,
    forecast_horizon=Config.FORECAST_HORIZON,
    context_length=Config.CONTEXT_LENGTH
)
anomaly_detector = AnomalyDetector(
    threshold_multiplier=Config.ANOMALY_THRESHOLD_MULTIPLIER,
    window_size=Config.ANOMALY_WINDOW_SIZE,
    rolling_window_seconds=Config.ROLLING_MEAN_WINDOW_SECONDS
)

# Estado global da aplicacao
app_state = {
    'running': False,
    'data_history': [],
    'forecast_history': [],
    'anomaly_count': 0,
    'total_predictions': 0,
    'total_samples': 0,
    'rolling_mean_history': []
}


def background_processing():
    """
    Thread de processamento em background que executa:
    1. Geracao de novos pontos de dados
    2. Previsao usando modelo Granite
    3. Deteccao de anomalias
    4. Emissao de eventos via WebSocket
    
    Complexidade: O(1) por iteracao
    """
    logger.info("🎯 [Background] Starting background processing thread")
    iteration_count = 0
    
    while app_state['running']:
        try:
            iteration_count += 1
            logger.debug(f"🔄 [Background] Iteration {iteration_count} started")
            
            # 1. Gerar novo ponto de dados
            new_point = data_generator.generate_point()
            app_state['data_history'].append(new_point)
            app_state['total_samples'] += 1
            
            # Manter apenas os ultimos N pontos
            max_history = Config.MAX_HISTORY_SIZE
            if len(app_state['data_history']) > max_history:
                app_state['data_history'] = app_state['data_history'][-max_history:]
            
            logger.info(f"📊 [Data] Generated point: value={new_point['value']:.2f}, timestamp={new_point['timestamp']}")
            
            # 2. Fazer previsao se houver dados suficientes
            forecast_data = None
            if len(app_state['data_history']) >= Config.CONTEXT_LENGTH:
                logger.info(f"🔮 [Forecast] Starting prediction (iteration {iteration_count})...")
                forecast_data = forecast_service.predict(app_state['data_history'])
                
                if forecast_data:
                    app_state['forecast_history'].append(forecast_data)
                    app_state['total_predictions'] += 1
                    logger.info(f"🔮 [Forecast] Prediction made: {len(forecast_data['predictions'])} points ahead")
                else:
                    logger.warning(f"⚠️  [Forecast] Prediction returned None (iteration {iteration_count})")
            else:
                logger.debug(f"🔮 [Forecast] Skipping prediction: {len(app_state['data_history'])} < {Config.CONTEXT_LENGTH} points")
            
            # 3. Detectar anomalias
            is_anomaly, anomaly_info = anomaly_detector.detect(
                new_point['value'],
                app_state['data_history']
            )

            rolling_mean_value = anomaly_info.get('mean', new_point['value']) if anomaly_info else new_point['value']
            app_state['rolling_mean_history'].append({
                'timestamp': new_point['timestamp'],
                'value': rolling_mean_value
            })
            if len(app_state['rolling_mean_history']) > max_history:
                app_state['rolling_mean_history'] = app_state['rolling_mean_history'][-max_history:]

            if is_anomaly:
                app_state['anomaly_count'] += 1
                logger.warning(f"⚠️  [Anomaly] Detected! Deviation: {anomaly_info['deviation']:.2f}σ")
            
            # 4. Emitir dados via WebSocket
            try:
                emit_data = {
                    'point': new_point,
                    'forecast': forecast_data,
                    'anomaly': {
                        'is_anomaly': is_anomaly,
                        'info': anomaly_info
                    },
                    'rolling_mean': {
                        'timestamp': new_point['timestamp'],
                        'value': rolling_mean_value
                    },
                    'stats': {
                        'total_points': app_state['total_samples'],
                        'anomaly_count': app_state['anomaly_count'],
                        'total_predictions': app_state['total_predictions']
                    }
                }
                
                # Log do tamanho dos dados antes de emitir
                import json
                data_size = len(json.dumps(emit_data, default=str))
                logger.info(f"📡 [WebSocket] Emitting data: {data_size} bytes (iteration {iteration_count})")
                
                if forecast_data:
                    logger.debug(f"📡 [WebSocket] Including forecast with {len(forecast_data['predictions'])} predictions")
                
                socketio.emit('new_data', emit_data)
                logger.debug(f"✅ [WebSocket] Data emitted successfully (iteration {iteration_count})")
                
            except Exception as emit_error:
                logger.error(f"❌ [WebSocket] Emit error (iteration {iteration_count}): {str(emit_error)}")
                logger.error(f"❌ [WebSocket] Exception type: {type(emit_error).__name__}")
                logger.error(f"❌ [WebSocket] Stack trace:", exc_info=True)
                # Continuar mesmo com erro de emissão
            
            # Aguardar intervalo configurado
            logger.debug(f"⏸️  [Background] Sleeping for {Config.DATA_GENERATION_INTERVAL}s")
            time.sleep(Config.DATA_GENERATION_INTERVAL)
            
        except Exception as e:
            logger.error(f"❌ [Error] Background processing error (iteration {iteration_count}): {str(e)}")
            logger.error(f"❌ [Error] Exception type: {type(e).__name__}")
            logger.error(f"❌ [Error] Stack trace:", exc_info=True)
            time.sleep(1)  # Evitar loop infinito em caso de erro


@app.route('/')
def index():
    """
    Rota principal que renderiza a interface web
    
    Returns:
        HTML template com interface de visualizacao
    """
    return render_template('index.html')


@app.route('/api/status')
def get_status():
    """
    Endpoint REST para obter status atual do sistema
    
    Returns:
        JSON com estatisticas e estado do sistema
    """
    model_info = forecast_service.get_model_info()
    
    status = {
        'running': app_state['running'],
        'data_points': len(app_state['data_history']),
        'anomaly_count': app_state['anomaly_count'],
        'total_predictions': app_state['total_predictions'],
        'model_info': model_info,
        'config': {
            'forecast_horizon': Config.FORECAST_HORIZON,
            'context_length': Config.CONTEXT_LENGTH,
            'generation_interval': Config.DATA_GENERATION_INTERVAL
        }
    }
    
    logger.info(
        f"📊 [API] Status solicitado - Modelo: {model_info['model_type']}, "
        f"Granite: {'Sim' if model_info['using_granite'] else 'Nao'}"
    )
    
    return jsonify(status)


@app.route('/api/history')
def get_history():
    """
    Endpoint REST para obter historico de dados
    
    Returns:
        JSON com historico completo de dados e previsoes
    """
    return jsonify({
        'data': app_state['data_history'][-100:],  # Ultimos 100 pontos
        'forecasts': app_state['forecast_history'][-10:],  # Ultimas 10 previsoes
        'rolling_mean': app_state['rolling_mean_history'][-100:]
    })


@socketio.on('connect')
def handle_connect():
    """
    Handler de conexao WebSocket
    Envia estado inicial ao cliente conectado
    """
    from flask import request
    client_id = request.sid if hasattr(request, 'sid') else 'unknown'
    logger.info(f"🔌 [WebSocket] Client connected: {client_id} (thread: {threading.current_thread().name})")
    
    try:
        emit('connected', {
            'message': 'Connected to Granite Time Series Forecasting',
            'status': app_state['running'],
            'client_id': client_id
        })
        logger.info(f"✅ [WebSocket] Connection confirmation sent to {client_id}")
    except Exception as e:
        logger.error(f"❌ [WebSocket] Error sending connection confirmation: {str(e)}", exc_info=True)


@socketio.on('disconnect')
def handle_disconnect():
    """
    Handler de desconexao WebSocket
    """
    from flask import request
    client_id = request.sid if hasattr(request, 'sid') else 'unknown'
    logger.info(f"🔌 [WebSocket] Client disconnected: {client_id}")
    logger.info(f"📊 [WebSocket] Stats at disconnect - Total predictions: {app_state['total_predictions']}, Anomalies: {app_state['anomaly_count']}")


@socketio.on('start_processing')
def handle_start():
    """
    Handler para iniciar processamento em tempo real
    """
    if not app_state['running']:
        app_state['running'] = True
        thread = threading.Thread(target=background_processing, daemon=True)
        thread.start()
        logger.info("▶️  [Control] Processing started")
        emit('status_changed', {'running': True}, broadcast=True)


@socketio.on('stop_processing')
def handle_stop():
    """
    Handler para parar processamento em tempo real
    """
    app_state['running'] = False
    logger.info("⏸️  [Control] Processing stopped")
    emit('status_changed', {'running': False}, broadcast=True)


@socketio.on('reset_data')
def handle_reset():
    """
    Handler para resetar todos os dados
    """
    app_state['data_history'].clear()
    app_state['forecast_history'].clear()
    app_state['anomaly_count'] = 0
    app_state['total_predictions'] = 0
    app_state['rolling_mean_history'].clear()
    logger.info("🔄 [Control] Data reset")
    emit('data_reset', {}, broadcast=True)


if __name__ == '__main__':
    logger.info("=" * 80)
    logger.info("🚀 Granite Time Series Forecasting System")
    logger.info("=" * 80)
    logger.info(f"📍 Server starting on http://localhost:{Config.PORT}")
    logger.info(f"🤖 Model: {Config.MODEL_NAME}")
    logger.info(f"⏱️  Generation interval: {Config.DATA_GENERATION_INTERVAL}s")
    logger.info(f"🔮 Forecast horizon: {Config.FORECAST_HORIZON} points")
    logger.info("=" * 80)
    
    socketio.run(
        app,
        host='0.0.0.0',
        port=Config.PORT,
        debug=Config.DEBUG,
        allow_unsafe_werkzeug=True
    )
