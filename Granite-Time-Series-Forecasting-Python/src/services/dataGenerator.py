"""
Data Generator Service
Gera series temporais sinteticas com caracteristicas realistas
"""

import random
import math
import time
from datetime import datetime, timedelta
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

from src.config import Config


class DataGenerator:
    """Gerador de series temporais sinteticas para simulacao em tempo real"""
    
    def __init__(
        self,
        interval_seconds: float = 1.0,
        base_value: float = 100.0,
        noise_level: float = 5.0,
        trend_coefficient: float = 0.01,
        seasonality_amplitude: float = 10.0,
        seasonality_period: int = 50
    ):
        self.interval_seconds = interval_seconds
        self.base_value = base_value
        self.noise_level = noise_level
        self.trend_coefficient = trend_coefficient
        self.seasonality_amplitude = seasonality_amplitude
        self.seasonality_period = seasonality_period
        
        self.counter = 0
        self.start_time = datetime.now()
        self.anomaly_probability = 0.05
        self.min_value = Config.MIN_TEMPERATURE
        self.max_value = Config.MAX_TEMPERATURE
        
        logger.info(f"📊 [DataGenerator] Initialized with base_value={base_value}, noise={noise_level}")
    
    def _calculate_trend(self, t: int) -> float:
        """Calcula componente de tendencia linear"""
        return self.trend_coefficient * t
    
    def _calculate_seasonality(self, t: int) -> float:
        """Calcula componente de sazonalidade (padrao ciclico)"""
        phase = (2 * math.pi * t) / self.seasonality_period
        return self.seasonality_amplitude * math.sin(phase)
    
    def _calculate_noise(self) -> float:
        """Gera ruido aleatorio gaussiano"""
        return random.gauss(0, self.noise_level)
    
    def _should_inject_anomaly(self) -> bool:
        """Decide se deve injetar uma anomalia neste ponto"""
        return random.random() < self.anomaly_probability
    
    def _generate_anomaly(self, normal_value: float) -> float:
        """Gera um valor anomalo baseado no valor normal"""
        anomaly_magnitude = random.uniform(3, 6) * self.noise_level
        direction = random.choice([-1, 1])
        anomaly_value = normal_value + (direction * anomaly_magnitude)
        logger.warning(f"⚠️  [DataGenerator] Injecting anomaly: {anomaly_value:.2f} (normal: {normal_value:.2f})")
        return anomaly_value
    
    def generate_point(self) -> Dict:
        """
        Gera um novo ponto de dados da serie temporal
        
        Returns:
            dict: Ponto de dados com timestamp, valor e metadados
        """
        current_time = self.start_time + timedelta(seconds=self.counter * self.interval_seconds)
        
        trend = self._calculate_trend(self.counter)
        seasonality = self._calculate_seasonality(self.counter)
        noise = self._calculate_noise()
        
        normal_value = self.base_value + trend + seasonality + noise
        
        is_injected_anomaly = self._should_inject_anomaly()
        final_value = self._generate_anomaly(normal_value) if is_injected_anomaly else normal_value
        final_value = max(self.min_value, min(self.max_value, final_value))
        
        data_point = {
            'timestamp': current_time.isoformat(),
            'value': final_value,
            'index': self.counter,
            'components': {
                'base': self.base_value,
                'trend': trend,
                'seasonality': seasonality,
                'noise': noise
            },
            'is_injected_anomaly': is_injected_anomaly
        }
        
        self.counter += 1
        return data_point
    
    def generate_batch(self, size: int) -> List[Dict]:
        """Gera um lote de pontos de dados"""
        return [self.generate_point() for _ in range(size)]
    
    def reset(self):
        """Reseta o gerador para estado inicial"""
        self.counter = 0
        self.start_time = datetime.now()
        logger.info("🔄 [DataGenerator] Reset to initial state")
