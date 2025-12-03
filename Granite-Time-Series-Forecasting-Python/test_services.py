"""
🧪 Test Script - Granite Time Series Forecasting Services

Script de teste para validar os serviços principais do sistema:
- Data Generator
- Anomaly Detector
- Forecast Service (simulado)

Execute com: python test_services.py
"""

import sys
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

def test_data_generator():
    """Testa o gerador de dados sintéticos"""
    logger.info("=" * 60)
    logger.info("🧪 Testando Data Generator")
    logger.info("=" * 60)
    
    try:
        from src.services.dataGenerator import DataGenerator
        
        # Criar gerador
        generator = DataGenerator(
            interval_seconds=1.0,
            base_value=100.0,
            noise_level=5.0
        )
        
        # Gerar alguns pontos
        logger.info("📊 Gerando 10 pontos de dados...")
        for i in range(10):
            point = generator.generate_point()
            logger.info(
                f"  Ponto {i+1}: valor={point['value']:.2f}, "
                f"timestamp={point['timestamp']}, "
                f"anomalia_injetada={point['is_injected_anomaly']}"
            )
        
        logger.info("✅ Data Generator: PASSOU")
        return True
        
    except Exception as e:
        logger.error(f"❌ Data Generator: FALHOU - {str(e)}")
        return False


def test_anomaly_detector():
    """Testa o detector de anomalias"""
    logger.info("\n" + "=" * 60)
    logger.info("🧪 Testando Anomaly Detector")
    logger.info("=" * 60)
    
    try:
        from src.services.anomalyDetector import AnomalyDetector
        from src.services.dataGenerator import DataGenerator
        
        # Criar detector e gerador
        detector = AnomalyDetector(threshold_multiplier=3.0)
        generator = DataGenerator(base_value=100.0, noise_level=2.0)
        
        # Gerar histórico normal
        logger.info("📊 Gerando histórico de dados normais...")
        history = []
        for _ in range(50):
            point = generator.generate_point()
            history.append(point)
        
        # Testar valor normal
        normal_value = 100.0
        is_anomaly, info = detector.detect(normal_value, history)
        logger.info(f"  Valor normal (100.0): anomalia={is_anomaly}, z-score={info['zscore']:.2f}")
        
        # Testar valor anômalo
        anomalous_value = 150.0
        is_anomaly, info = detector.detect(anomalous_value, history)
        logger.info(
            f"  Valor anômalo (150.0): anomalia={is_anomaly}, "
            f"z-score={info['zscore']:.2f}, "
            f"severidade={info.get('severity', 'N/A')}"
        )
        
        # Verificar estatísticas
        stats = detector.get_statistics()
        logger.info(f"  Estatísticas: {stats}")
        
        logger.info("✅ Anomaly Detector: PASSOU")
        return True
        
    except Exception as e:
        logger.error(f"❌ Anomaly Detector: FALHOU - {str(e)}")
        return False


def test_config():
    """Testa o módulo de configuração"""
    logger.info("\n" + "=" * 60)
    logger.info("🧪 Testando Configuration")
    logger.info("=" * 60)
    
    try:
        from src.config import Config
        
        logger.info("📋 Configurações carregadas:")
        logger.info(f"  PORT: {Config.PORT}")
        logger.info(f"  MODEL_NAME: {Config.MODEL_NAME}")
        logger.info(f"  FORECAST_HORIZON: {Config.FORECAST_HORIZON}")
        logger.info(f"  CONTEXT_LENGTH: {Config.CONTEXT_LENGTH}")
        logger.info(f"  DATA_GENERATION_INTERVAL: {Config.DATA_GENERATION_INTERVAL}s")
        logger.info(f"  ANOMALY_THRESHOLD_MULTIPLIER: {Config.ANOMALY_THRESHOLD_MULTIPLIER}σ")
        
        # Validar configurações
        Config.validate()
        logger.info("✅ Configuration: PASSOU")
        return True
        
    except Exception as e:
        logger.error(f"❌ Configuration: FALHOU - {str(e)}")
        return False


def test_forecast_service_import():
    """Testa importação do serviço de previsão (sem carregar modelo)"""
    logger.info("\n" + "=" * 60)
    logger.info("🧪 Testando Forecast Service (import)")
    logger.info("=" * 60)
    
    try:
        from src.services.forecastService import ForecastService
        
        # Criar serviço (sem carregar modelo)
        service = ForecastService(
            model_name="ibm-granite/granite-timeseries-ttm-r2",
            forecast_horizon=96,
            context_length=512
        )
        
        logger.info(f"  Modelo configurado: {service.model_name}")
        logger.info(f"  Dispositivo: {service.device}")
        logger.info(f"  Modelo carregado: {service.is_model_loaded()}")
        
        # Obter informações
        info = service.get_model_info()
        logger.info(f"  Info: {info}")
        
        logger.info("✅ Forecast Service: PASSOU (import)")
        logger.info("ℹ️  Nota: Modelo não foi carregado (requer tsfm_public instalado)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Forecast Service: FALHOU - {str(e)}")
        return False


def main():
    """Executa todos os testes"""
    logger.info("\n")
    logger.info("🚀 " + "=" * 58)
    logger.info("🚀 Granite Time Series Forecasting - Test Suite")
    logger.info("🚀 " + "=" * 58)
    logger.info(f"🕐 Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("\n")
    
    results = {
        'Config': test_config(),
        'Data Generator': test_data_generator(),
        'Anomaly Detector': test_anomaly_detector(),
        'Forecast Service': test_forecast_service_import()
    }
    
    # Resumo
    logger.info("\n" + "=" * 60)
    logger.info("📊 RESUMO DOS TESTES")
    logger.info("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        logger.info(f"  {test_name}: {status}")
    
    logger.info("-" * 60)
    logger.info(f"  Total: {passed}/{total} testes passaram")
    logger.info("=" * 60)
    
    if passed == total:
        logger.info("🎉 Todos os testes passaram!")
        return 0
    else:
        logger.warning(f"⚠️  {total - passed} teste(s) falharam")
        return 1


if __name__ == '__main__':
    sys.exit(main())
