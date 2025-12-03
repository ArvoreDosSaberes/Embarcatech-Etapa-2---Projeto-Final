"""
Forecast Service
Servico de previsao de series temporais usando IBM Granite TTM-R2

Este modulo tenta usar o modelo IBM Granite TTM-R2 (Tiny Time Mixer).
Se o modelo nao estiver disponivel, faz fallback para Exponential Smoothing.

Para instalar o Granite TTM-R2:
    bash install_granite.sh
"""

import logging
import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import warnings

logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')

# Tentar importar Granite TTM-R2
GRANITE_AVAILABLE = False
try:
    from tsfm_public import TimeSeriesForecastingPipeline, TinyTimeMixerForPrediction
    import torch
    GRANITE_AVAILABLE = True
    logger.info("✅ [ForecastService] IBM Granite TTM-R2 disponivel")
except ImportError:
    logger.warning("⚠️  [ForecastService] IBM Granite TTM-R2 nao disponivel - usando modelo alternativo")
    logger.info("💡 [ForecastService] Execute: bash install_granite.sh")


class ForecastService:
    """
    Servico de previsao de series temporais
    
    Tenta usar IBM Granite TTM-R2 se disponivel.
    Caso contrario, usa Holt-Winters (Triple Exponential Smoothing).
    """
    
    def __init__(
        self,
        model_name: str = "ibm-granite/granite-timeseries-ttm-r2",
        forecast_horizon: int = 96,
        context_length: int = 512
    ):
        self.model_name = model_name
        self.forecast_horizon = forecast_horizon
        self.context_length = context_length
        self.use_granite = GRANITE_AVAILABLE
        self.granite_model = None
        self.granite_pipeline = None
        
        if GRANITE_AVAILABLE:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"🔮 [ForecastService] Using IBM Granite TTM-R2 on {self.device}")
        else:
            self.device = "cpu"
            logger.info(f"🔮 [ForecastService] Using Exponential Smoothing (fallback)")
        
        self._model_loaded = False
        logger.info(f"📊 [ForecastService] Forecast horizon={forecast_horizon}, context={context_length}")
    
    def _prepare_series(self, data_history: List[Dict]) -> pd.Series:
        """
        Prepara serie temporal para o modelo
        
        Args:
            data_history: Historico de dados
            
        Returns:
            pd.Series: Serie temporal indexada por timestamp
        """
        recent_data = data_history[-self.context_length:]
        
        timestamps = [pd.to_datetime(point['timestamp']) for point in recent_data]
        values = [point['value'] for point in recent_data]
        
        series = pd.Series(values, index=timestamps)
        series = series.sort_index()
        
        logger.debug(f"📋 [ForecastService] Prepared series: {len(series)} points")
        return series
    
    def _coerce_scalar_float(self, value: Any) -> Optional[float]:
        """
        Converte um valor potencialmente aninhado em um float escalar.

        Args:
            value: Valor de entrada (escalar, lista ou array) com previsao.

        Returns:
            float | None: Valor convertido ou None se nao for possivel extrair.
        """
        array_value = np.asarray(value)

        if array_value.size == 0:
            return None

        scalar_candidate = array_value.reshape(-1)[0]

        try:
            return float(scalar_candidate)
        except (TypeError, ValueError):
            return None

    def _sanitize_predictions(self, raw_predictions: Any, limit: Optional[int] = None) -> np.ndarray:
        """
        Normaliza previsoes para um array 1D de floats.

        Args:
            raw_predictions: Valores retornados pelo modelo Granite.
            limit: Quantidade maxima de valores a retornar.

        Returns:
            np.ndarray: Array 1D com valores float64.
        """
        sanitized_values: List[float] = []
        stack: List[Any] = [raw_predictions]

        while stack and (limit is None or len(sanitized_values) < limit):
            current = stack.pop()

            if isinstance(current, np.ndarray):
                # Converter para lista preservando ordem
                stack.extend(reversed(current.tolist()))
                continue

            if isinstance(current, (list, tuple)):
                stack.extend(reversed(list(current)))
                continue

            scalar_value = self._coerce_scalar_float(current)

            if scalar_value is None or not np.isfinite(scalar_value):
                logger.debug("🧹 [ForecastService/Granite] Ignoring non-numeric prediction value during sanitization")
                continue

            sanitized_values.append(scalar_value)

        if not sanitized_values:
            return np.array([], dtype=np.float64)

        if limit is not None:
            sanitized_values = sanitized_values[:limit]

        sanitized = np.array(sanitized_values, dtype=np.float64)
        logger.debug(
            f"🧹 [ForecastService/Granite] Sanitized predictions: {len(sanitized)} points"
        )
        return sanitized

    def _simple_forecast(self, series: pd.Series, steps: int) -> np.ndarray:
        """
        Realiza previsao simples usando media movel exponencial
        
        Este metodo e usado como fallback quando statsmodels nao esta disponivel
        ou quando ha poucos dados.
        
        Args:
            series: Serie temporal
            steps: Numero de passos a prever
            
        Returns:
            np.ndarray: Valores previstos
        """
        # Calcular componentes basicos
        recent_values = series.values[-50:]  # Ultimos 50 pontos
        
        # Tendencia simples (regressao linear)
        x = np.arange(len(recent_values))
        if len(recent_values) > 1:
            trend_coef = np.polyfit(x, recent_values, 1)
            trend = np.poly1d(trend_coef)
        else:
            trend = lambda x: recent_values[-1]
        
        # Sazonalidade simples (media dos ultimos ciclos)
        period = 50
        if len(recent_values) >= period:
            seasonal = recent_values[-period:]
        else:
            seasonal = np.zeros(period)
        
        # Gerar previsoes
        predictions = []
        last_value = series.values[-1]
        
        for i in range(steps):
            # Tendencia
            trend_value = trend(len(recent_values) + i)
            
            # Sazonalidade
            seasonal_idx = i % len(seasonal)
            seasonal_value = seasonal[seasonal_idx] - np.mean(recent_values)
            
            # Combinacao com suavizacao
            pred = trend_value + seasonal_value * 0.3
            
            # Adicionar pequeno ruido para variacao
            noise = np.random.normal(0, np.std(recent_values) * 0.1)
            pred += noise
            
            predictions.append(pred)
        
        return np.array(predictions)
    
    def _load_granite_model(self):
        """Carrega o modelo IBM Granite TTM-R2 (lazy loading)"""
        if self._model_loaded or not GRANITE_AVAILABLE:
            return
        
        try:
            logger.info(f"⏳ [ForecastService] Loading Granite TTM-R2...")
            
            self.granite_model = TinyTimeMixerForPrediction.from_pretrained(
                self.model_name,
                num_input_channels=1,
            )
            
            self.granite_pipeline = TimeSeriesForecastingPipeline(
                self.granite_model,
                timestamp_column="timestamp",
                id_columns=[],
                target_columns=["value"],
                explode_forecasts=False,
                freq="S",
                device=self.device,
            )
            
            self._model_loaded = True
            logger.info(f"✅ [ForecastService] Granite TTM-R2 loaded on {self.device}")
            
        except Exception as e:
            logger.error(f"❌ [ForecastService] Error loading Granite: {str(e)}")
            self.use_granite = False
            logger.info("📊 [ForecastService] Falling back to Exponential Smoothing")
    
    def _granite_forecast(self, data_history: List[Dict], steps: int) -> Optional[np.ndarray]:
        """
        Realiza previsao usando IBM Granite TTM-R2
        
        Args:
            data_history: Historico de dados
            steps: Numero de passos a prever
            
        Returns:
            np.ndarray: Valores previstos ou None se erro
        """
        import time
        start_time = time.time()
        
        try:
            self._load_granite_model()
            
            if not self._model_loaded:
                logger.warning("⚠️  [ForecastService/Granite] Model not loaded")
                return None
            
            # Preparar DataFrame
            recent_data = data_history[-self.context_length:]
            logger.info(f"📊 [ForecastService/Granite] Preparing data: {len(recent_data)} points")
            
            df = pd.DataFrame([
                {
                    'timestamp': pd.to_datetime(point['timestamp']),
                    'value': point['value']
                }
                for point in recent_data
            ])
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            logger.info(f"📋 [ForecastService/Granite] DataFrame shape: {df.shape}")
            logger.debug(f"📋 [ForecastService/Granite] DataFrame head:\n{df.head()}")
            logger.debug(f"📋 [ForecastService/Granite] DataFrame tail:\n{df.tail()}")
            
            # Fazer previsao
            logger.info(f"🔮 [ForecastService/Granite] Starting prediction with {steps} steps...")
            prediction_start = time.time()
            
            forecast_df = self.granite_pipeline(df)
            
            prediction_time = time.time() - prediction_start
            logger.info(f"⏱️  [ForecastService/Granite] Prediction completed in {prediction_time:.3f}s")
            
            # Log detalhado da resposta do Granite
            logger.info(f"📊 [ForecastService/Granite] Response shape: {forecast_df.shape}")
            logger.info(f"📊 [ForecastService/Granite] Response columns: {list(forecast_df.columns)}")
            logger.info(f"📊 [ForecastService/Granite] Response dtypes:\n{forecast_df.dtypes}")
            logger.debug(f"📊 [ForecastService/Granite] Response head:\n{forecast_df.head()}")
            logger.debug(f"📊 [ForecastService/Granite] Response tail:\n{forecast_df.tail()}")
            logger.debug(f"📊 [ForecastService/Granite] Response describe:\n{forecast_df.describe()}")
            
            # Extrair valores
            if 'value' in forecast_df.columns:
                predictions = forecast_df['value'].values[:steps]
                logger.info(f"✅ [ForecastService/Granite] Extracted {len(predictions)} predictions from 'value' column")
            else:
                predictions = forecast_df.iloc[:, 0].values[:steps]
                logger.info(f"✅ [ForecastService/Granite] Extracted {len(predictions)} predictions from first column")

            predictions = self._sanitize_predictions(predictions, limit=steps)

            if predictions.size == 0:
                logger.warning("⚠️  [ForecastService/Granite] No numeric predictions available after sanitization")
                return None

            # Log estatísticas das predições
            logger.info(f"📈 [ForecastService/Granite] Predictions stats: min={np.min(predictions):.2f}, max={np.max(predictions):.2f}, mean={np.mean(predictions):.2f}, std={np.std(predictions):.2f}")
            logger.debug(f"📈 [ForecastService/Granite] First 10 predictions: {predictions[:10]}")
            
            total_time = time.time() - start_time
            logger.info(f"✅ [ForecastService/Granite] Total forecast time: {total_time:.3f}s")
            
            return predictions
            
        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"❌ [ForecastService/Granite] Forecast error after {total_time:.3f}s: {str(e)}")
            logger.error(f"❌ [ForecastService/Granite] Exception type: {type(e).__name__}")
            logger.error(f"❌ [ForecastService/Granite] Exception details:", exc_info=True)
            return None
    
    def _exponential_smoothing_forecast(self, series: pd.Series, steps: int) -> np.ndarray:
        """
        Realiza previsao usando Exponential Smoothing (statsmodels)
        
        Args:
            series: Serie temporal
            steps: Numero de passos a prever
            
        Returns:
            np.ndarray: Valores previstos
        """
        try:
            from statsmodels.tsa.holtwinters import ExponentialSmoothing
            
            # Configurar modelo com tendencia e sazonalidade
            model = ExponentialSmoothing(
                series.values,
                trend='add',
                seasonal='add',
                seasonal_periods=min(50, len(series) // 2)
            )
            
            # Treinar modelo
            fitted_model = model.fit(optimized=True, use_brute=False)
            
            # Fazer previsao
            forecast = fitted_model.forecast(steps=steps)
            
            logger.debug(f"✅ [ForecastService] Exponential Smoothing forecast completed")
            return forecast
            
        except Exception as e:
            logger.warning(f"⚠️  [ForecastService] Exponential Smoothing failed: {str(e)}")
            logger.info("📊 [ForecastService] Falling back to simple forecast")
            return self._simple_forecast(series, steps)
    
    def predict(self, data_history: List[Dict]) -> Optional[Dict]:
        """
        Realiza previsao de valores futuros
        
        Tenta usar Granite TTM-R2 primeiro. Se nao disponivel ou falhar,
        usa Exponential Smoothing como fallback.
        
        Args:
            data_history: Historico de dados (minimo 10 pontos)
            
        Returns:
            dict: Previsoes com timestamps e valores, ou None se erro
        """
        import time
        predict_start = time.time()
        
        if len(data_history) < 10:
            logger.warning(
                f"⚠️  [ForecastService] Insufficient data: {len(data_history)} < 10"
            )
            return None
        
        try:
            steps = min(self.forecast_horizon, 96)
            logger.info(f"🎯 [ForecastService] Starting prediction: {len(data_history)} data points, {steps} forecast steps")
            
            # Tentar usar Granite TTM-R2 primeiro
            forecast_values = None
            model_used = "unknown"
            
            if self.use_granite and len(data_history) >= self.context_length:
                logger.info("🔮 [ForecastService] Usando IBM Granite TTM-R2 para previsao")
                granite_start = time.time()
                forecast_values = self._granite_forecast(data_history, steps)
                granite_time = time.time() - granite_start
                
                if forecast_values is not None:
                    model_used = "IBM Granite TTM-R2"
                    logger.info(f"✅ [ForecastService] Granite prediction successful in {granite_time:.3f}s")
                else:
                    logger.warning(f"⚠️  [ForecastService] Granite prediction failed after {granite_time:.3f}s")
            
            # Fallback para Exponential Smoothing
            if forecast_values is None:
                if self.use_granite:
                    logger.warning("⚠️  [ForecastService] Granite falhou, usando Exponential Smoothing")
                else:
                    logger.info("📊 [ForecastService] Usando Exponential Smoothing (Granite nao disponivel)")
                
                fallback_start = time.time()
                series = self._prepare_series(data_history)
                forecast_values = self._exponential_smoothing_forecast(series, steps)
                model_used = "Exponential Smoothing (Holt-Winters)"
                fallback_time = time.time() - fallback_start
                logger.info(f"✅ [ForecastService] Fallback prediction completed in {fallback_time:.3f}s")
            
            # Calcular intervalo de tempo
            last_timestamp = pd.to_datetime(data_history[-1]['timestamp'])
            if len(data_history) >= 2:
                t1 = pd.to_datetime(data_history[-1]['timestamp'])
                t2 = pd.to_datetime(data_history[-2]['timestamp'])
                interval = (t1 - t2).total_seconds()
            else:
                interval = 1.0
            
            # Gerar timestamps futuros e montar resultado
            predictions = []
            for i, value in enumerate(forecast_values):
                future_timestamp = last_timestamp + timedelta(seconds=interval * (i + 1))
                
                # Extrair valor escalar se for lista ou array
                if isinstance(value, (list, np.ndarray)):
                    scalar_value = float(value[0]) if len(value) > 0 else 0.0
                else:
                    scalar_value = float(value)
                
                predictions.append({
                    'timestamp': future_timestamp.isoformat(),
                    'value': scalar_value,
                    'horizon_step': i + 1
                })
            
            result = {
                'predictions': predictions,
                'forecast_timestamp': datetime.now().isoformat(),
                'context_size': len(data_history),
                'model': model_used,
                'model_type': 'granite' if 'Granite' in model_used else 'statistical'
            }
            
            total_predict_time = time.time() - predict_start
            logger.info(f"✅ [ForecastService] Previsao concluida: {len(predictions)} pontos usando {model_used} em {total_predict_time:.3f}s")
            logger.debug(f"📦 [ForecastService] Result size: {len(str(result))} bytes")
            
            return result
            
        except Exception as e:
            total_predict_time = time.time() - predict_start
            logger.error(f"❌ [ForecastService] Prediction error after {total_predict_time:.3f}s: {str(e)}")
            logger.error(f"❌ [ForecastService] Exception type: {type(e).__name__}")
            logger.error(f"❌ [ForecastService] Stack trace:", exc_info=True)
            return None
    
    def is_model_loaded(self) -> bool:
        """Verifica se o modelo esta carregado"""
        return self._model_loaded
    
    def get_model_info(self) -> Dict:
        """
        Retorna informacoes detalhadas sobre o modelo
        
        Returns:
            dict: Informacoes do modelo incluindo tipo e status
        """
        model_type = "IBM Granite TTM-R2" if self.use_granite and self._model_loaded else "Exponential Smoothing"
        
        info = {
            'model_name': self.model_name,
            'model_type': model_type,
            'using_granite': self.use_granite and self._model_loaded,
            'granite_available': GRANITE_AVAILABLE,
            'forecast_horizon': self.forecast_horizon,
            'context_length': self.context_length,
            'device': self.device,
            'loaded': self._model_loaded,
            'gpu_available': torch.cuda.is_available() if GRANITE_AVAILABLE else False
        }
        
        # Log do status atual
        if info['using_granite']:
            logger.info(f"ℹ️  [ForecastService] Status: Usando IBM Granite TTM-R2 em {self.device}")
        else:
            logger.info(f"ℹ️  [ForecastService] Status: Usando Exponential Smoothing (fallback)")
        
        return info
