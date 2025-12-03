#!/usr/bin/env python3
"""
Test WebSocket Stability
Script para testar a estabilidade da conexão WebSocket durante predições
"""

import socketio
import time
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Estatísticas
stats = {
    'connected': False,
    'messages_received': 0,
    'forecasts_received': 0,
    'anomalies_detected': 0,
    'disconnections': 0,
    'errors': 0,
    'start_time': None,
    'last_message_time': None,
    'max_message_size': 0,
    'total_bytes': 0
}

# Criar cliente SocketIO
sio = socketio.Client(
    logger=True,
    engineio_logger=True,
    reconnection=True,
    reconnection_attempts=5,
    reconnection_delay=1,
    reconnection_delay_max=5
)


@sio.event
def connect():
    """Handler de conexão"""
    logger.info("🔌 Conectado ao servidor!")
    stats['connected'] = True
    stats['start_time'] = datetime.now()


@sio.event
def connected(data):
    """Handler de confirmação de conexão"""
    logger.info(f"✅ Confirmação recebida: {data}")
    logger.info(f"📍 Client ID: {data.get('client_id', 'unknown')}")


@sio.event
def disconnect():
    """Handler de desconexão"""
    logger.warning("🔌 Desconectado do servidor!")
    stats['connected'] = False
    stats['disconnections'] += 1
    
    # Calcular tempo de conexão
    if stats['start_time']:
        duration = (datetime.now() - stats['start_time']).total_seconds()
        logger.info(f"⏱️  Tempo de conexão: {duration:.2f}s")


@sio.event
def new_data(data):
    """Handler de novos dados"""
    try:
        stats['messages_received'] += 1
        stats['last_message_time'] = datetime.now()
        
        # Calcular tamanho da mensagem
        import json
        message_size = len(json.dumps(data))
        stats['total_bytes'] += message_size
        
        if message_size > stats['max_message_size']:
            stats['max_message_size'] = message_size
        
        # Verificar se há forecast
        if data.get('forecast'):
            stats['forecasts_received'] += 1
            forecast = data['forecast']
            num_predictions = len(forecast.get('predictions', []))
            model_used = forecast.get('model', 'unknown')
            
            logger.info(
                f"🔮 Forecast recebido: {num_predictions} predições, "
                f"modelo={model_used}, tamanho={message_size} bytes"
            )
        
        # Verificar anomalia
        if data.get('anomaly', {}).get('is_anomaly'):
            stats['anomalies_detected'] += 1
            anomaly_info = data['anomaly']['info']
            logger.warning(
                f"⚠️  Anomalia detectada! Desvio: {anomaly_info.get('deviation', 0):.2f}σ"
            )
        
        # Log periódico de estatísticas (a cada 10 mensagens)
        if stats['messages_received'] % 10 == 0:
            logger.info(
                f"📊 Stats: {stats['messages_received']} mensagens, "
                f"{stats['forecasts_received']} forecasts, "
                f"{stats['anomalies_detected']} anomalias, "
                f"max_size={stats['max_message_size']} bytes"
            )
    
    except Exception as e:
        stats['errors'] += 1
        logger.error(f"❌ Erro processando mensagem: {str(e)}", exc_info=True)


@sio.event
def status_changed(data):
    """Handler de mudança de status"""
    logger.info(f"📊 Status mudou: {data}")


@sio.event
def data_reset(data):
    """Handler de reset de dados"""
    logger.info("🔄 Dados resetados no servidor")


def print_final_stats():
    """Imprime estatísticas finais"""
    logger.info("=" * 80)
    logger.info("📊 ESTATÍSTICAS FINAIS")
    logger.info("=" * 80)
    logger.info(f"Mensagens recebidas: {stats['messages_received']}")
    logger.info(f"Forecasts recebidos: {stats['forecasts_received']}")
    logger.info(f"Anomalias detectadas: {stats['anomalies_detected']}")
    logger.info(f"Desconexões: {stats['disconnections']}")
    logger.info(f"Erros: {stats['errors']}")
    logger.info(f"Tamanho máximo de mensagem: {stats['max_message_size']} bytes")
    logger.info(f"Total de dados recebidos: {stats['total_bytes'] / 1024:.2f} KB")
    
    if stats['start_time']:
        duration = (datetime.now() - stats['start_time']).total_seconds()
        logger.info(f"Tempo total: {duration:.2f}s")
        
        if duration > 0:
            msg_per_sec = stats['messages_received'] / duration
            logger.info(f"Taxa de mensagens: {msg_per_sec:.2f} msg/s")
    
    logger.info("=" * 80)


def main():
    """Função principal"""
    server_url = 'http://localhost:5000'
    test_duration = 300  # 5 minutos
    
    logger.info("=" * 80)
    logger.info("🧪 TESTE DE ESTABILIDADE DO WEBSOCKET")
    logger.info("=" * 80)
    logger.info(f"Servidor: {server_url}")
    logger.info(f"Duração do teste: {test_duration}s")
    logger.info("=" * 80)
    
    try:
        # Conectar ao servidor
        logger.info("🔌 Conectando ao servidor...")
        sio.connect(server_url)
        
        # Aguardar um pouco
        time.sleep(2)
        
        # Iniciar processamento
        logger.info("▶️  Iniciando processamento...")
        sio.emit('start_processing')
        
        # Aguardar duração do teste
        logger.info(f"⏳ Aguardando {test_duration}s...")
        start = time.time()
        
        while time.time() - start < test_duration:
            if not stats['connected']:
                logger.error("❌ Conexão perdida! Tentando reconectar...")
                time.sleep(5)
            
            # Verificar se está recebendo mensagens
            if stats['last_message_time']:
                silence = (datetime.now() - stats['last_message_time']).total_seconds()
                if silence > 30:
                    logger.warning(f"⚠️  Sem mensagens há {silence:.0f}s")
            
            time.sleep(10)
        
        # Parar processamento
        logger.info("⏸️  Parando processamento...")
        sio.emit('stop_processing')
        time.sleep(2)
        
        # Desconectar
        logger.info("🔌 Desconectando...")
        sio.disconnect()
        
    except KeyboardInterrupt:
        logger.info("\n⚠️  Teste interrompido pelo usuário")
        try:
            sio.emit('stop_processing')
            sio.disconnect()
        except:
            pass
    
    except Exception as e:
        logger.error(f"❌ Erro durante o teste: {str(e)}", exc_info=True)
    
    finally:
        print_final_stats()


if __name__ == '__main__':
    main()
