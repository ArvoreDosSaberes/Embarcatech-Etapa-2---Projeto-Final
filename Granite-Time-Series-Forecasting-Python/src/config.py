"""
Configuracao - Configuration Module
Centraliza todas as configuracoes do sistema de previsao de series temporais

Este modulo define constantes e parametros configuraveis para:
- Modelo de previsao (Granite TTM-R2)
- Geracao de dados sinteticos
- Deteccao de anomalias
- Servidor web e API
"""

import os
import logging
from dotenv import load_dotenv

# Carregar variaveis de ambiente
load_dotenv()


logger = logging.getLogger(__name__)


class Config:
    """
    Classe de configuracao centralizada do sistema
    
    Todas as configuracoes podem ser sobrescritas via variaveis de ambiente
    para facilitar deployment em diferentes ambientes (dev, staging, prod)
    """
    
    # ========== Configuracoes do Servidor ==========
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    SECRET_KEY = os.getenv('SECRET_KEY', 'granite-timeseries-secret-key-2024')
    
    # ========== Configuracoes do Modelo Granite ==========
    MODEL_NAME = os.getenv('MODEL_NAME', 'ibm-granite/granite-timeseries-ttm-r2')
    FORECAST_HORIZON = int(os.getenv('FORECAST_HORIZON', 10))  # Pontos a frente para prever
    CONTEXT_LENGTH = int(os.getenv('CONTEXT_LENGTH', 512))  # Janela de contexto historico
    
    # ========== Configuracoes de Geracao de Dados ==========
    DATA_GENERATION_INTERVAL = float(os.getenv('DATA_GENERATION_INTERVAL', 2.0))  # Segundos
    BASE_VALUE = float(os.getenv('BASE_VALUE', 100.0))  # Valor base da serie temporal
    NOISE_LEVEL = float(os.getenv('NOISE_LEVEL', 5.0))  # Nivel de ruido aleatorio
    TREND_ENABLED = os.getenv('TREND_ENABLED', 'True').lower() == 'true'
    SEASONALITY_ENABLED = os.getenv('SEASONALITY_ENABLED', 'True').lower() == 'true'
    MIN_TEMPERATURE = float(os.getenv('MIN_TEMPERATURE', 0.0))  # Limite inferior da serie (°C)
    MAX_TEMPERATURE = float(os.getenv('MAX_TEMPERATURE', 100.0))  # Limite superior da serie (°C)
    
    # ========== Configuracoes de Deteccao de Anomalias ==========
    ANOMALY_THRESHOLD_MULTIPLIER = float(os.getenv('ANOMALY_THRESHOLD_MULTIPLIER', 3.0))  # Multiplo do desvio padrao
    ANOMALY_WINDOW_SIZE = int(os.getenv('ANOMALY_WINDOW_SIZE', 50))  # Janela para calcular estatisticas
    ROLLING_MEAN_WINDOW_SECONDS = int(os.getenv('ROLLING_MEAN_WINDOW_SECONDS', 30))  # Janela temporal para media movel
    
    # ========== Configuracoes de Armazenamento ==========
    MAX_HISTORY_SIZE = int(os.getenv('MAX_HISTORY_SIZE', 1000))  # Maximo de pontos em memoria
    
    # ========== Configuracoes de Performance ==========
    USE_GPU = os.getenv('USE_GPU', 'True').lower() == 'true'
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', 1))
    
    @classmethod
    def to_dict(cls):
        """
        Converte configuracoes para dicionario
        
        Returns:
            dict: Todas as configuracoes publicas
        """
        return {
            key: value for key, value in cls.__dict__.items()
            if not key.startswith('_') and not callable(value)
        }
    
    @classmethod
    def validate(cls):
        """
        Valida configuracoes criticas
        
        Raises:
            ValueError: Se alguma configuracao estiver invalida
        """
        if cls.FORECAST_HORIZON <= 0:
            raise ValueError("FORECAST_HORIZON must be positive")

        if cls.FORECAST_HORIZON != 10:
            logger.warning(
                "⚠️  [Config] FORECAST_HORIZON=%s inválido; ajustando automaticamente para 10 passos",
                cls.FORECAST_HORIZON
            )
            cls.FORECAST_HORIZON = 10
        
        if cls.CONTEXT_LENGTH < cls.FORECAST_HORIZON:
            raise ValueError("CONTEXT_LENGTH should be >= FORECAST_HORIZON")
        
        if cls.MAX_HISTORY_SIZE < cls.FORECAST_HORIZON:
            logger.warning(
                "⚠️  [Config] MAX_HISTORY_SIZE=%s inferior ao FORECAST_HORIZON=%s; ampliando histórico para suportar previsões",
                cls.MAX_HISTORY_SIZE,
                cls.FORECAST_HORIZON
            )
            cls.MAX_HISTORY_SIZE = cls.FORECAST_HORIZON

        if cls.MAX_HISTORY_SIZE < cls.CONTEXT_LENGTH:
            logger.warning(
                "⚠️  [Config] MAX_HISTORY_SIZE=%s inferior ao CONTEXT_LENGTH=%s; ajustando histórico para permitir %s amostras",
                cls.MAX_HISTORY_SIZE,
                cls.CONTEXT_LENGTH,
                cls.CONTEXT_LENGTH
            )
            cls.MAX_HISTORY_SIZE = cls.CONTEXT_LENGTH

        if cls.DATA_GENERATION_INTERVAL <= 0:
            raise ValueError("DATA_GENERATION_INTERVAL must be positive")

        if cls.ANOMALY_THRESHOLD_MULTIPLIER <= 0:
            raise ValueError("ANOMALY_THRESHOLD_MULTIPLIER must be positive")

        if cls.ROLLING_MEAN_WINDOW_SECONDS <= 0:
            raise ValueError("ROLLING_MEAN_WINDOW_SECONDS must be positive")

        if cls.MIN_TEMPERATURE >= cls.MAX_TEMPERATURE:
            raise ValueError("MIN_TEMPERATURE must be lower than MAX_TEMPERATURE")


# Validar configuracoes ao importar
Config.validate()
