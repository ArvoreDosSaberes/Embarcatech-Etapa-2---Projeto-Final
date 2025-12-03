"""
Rack Control Service

Módulo responsável pelo controle de racks via MQTT.
Contém a classe Rack que representa um rack físico e o serviço
RackControlService que envia comandos para o firmware via MQTT.

Autor: Dashboard Rack Inteligente - EmbarcaTech
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from enum import IntEnum


class DoorStatus(IntEnum):
    """Status da porta do rack."""
    CLOSED = 0
    OPEN = 1


class VentilationStatus(IntEnum):
    """Status da ventilação do rack."""
    OFF = 0
    ON = 1


class BuzzerStatus(IntEnum):
    """Status do buzzer/alarme do rack."""
    OFF = 0
    DOOR_OPEN = 1
    BREAK_IN = 2
    OVERHEAT = 3


@dataclass
class Rack:
    """
    Representa um rack físico no sistema.
    
    Attributes:
        rackId: Identificador único do rack
        temperature: Temperatura atual em °C
        humidity: Umidade relativa em %
        doorStatus: Status da porta (aberta/fechada)
        ventilationStatus: Status da ventilação (ligada/desligada)
        buzzerStatus: Status do alarme sonoro
        latitude: Coordenada de latitude do rack
        longitude: Coordenada de longitude do rack
    """
    rackId: str
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    doorStatus: DoorStatus = DoorStatus.CLOSED
    ventilationStatus: VentilationStatus = VentilationStatus.OFF
    buzzerStatus: BuzzerStatus = BuzzerStatus.OFF
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    def isDoorOpen(self) -> bool:
        """Verifica se a porta está aberta."""
        return self.doorStatus == DoorStatus.OPEN
    
    def isVentilationOn(self) -> bool:
        """Verifica se a ventilação está ligada."""
        return self.ventilationStatus == VentilationStatus.ON
    
    def isBuzzerActive(self) -> bool:
        """Verifica se o buzzer está ativo (qualquer estado exceto OFF)."""
        return self.buzzerStatus != BuzzerStatus.OFF


class RackControlService:
    """
    Serviço de controle de racks via MQTT.
    
    Envia comandos para os racks através do broker MQTT,
    permitindo que o firmware dos dispositivos execute as ações.
    
    Attributes:
        mqttClient: Cliente MQTT para publicação de comandos
        baseTopic: Tópico base para comandos MQTT
    """
    
    def __init__(self, mqttClient, baseTopic: Optional[str] = None):
        """
        Inicializa o serviço de controle.
        
        Args:
            mqttClient: Instância do cliente MQTT (paho.mqtt.client.Client)
            baseTopic: Tópico base MQTT (default: valor de MQTT_BASE_TOPIC no .env ou 'racks')
        """
        self.mqttClient = mqttClient
        self.baseTopic = baseTopic or os.getenv("MQTT_BASE_TOPIC", "racks").rstrip("/")
    
    def _publishCommand(self, rack: Rack, commandType: str, value: int) -> bool:
        """
        Publica um comando MQTT para o rack especificado.
        
        Args:
            rack: Instância do rack alvo
            commandType: Tipo de comando (door, ventilation, buzzer)
            value: Valor do comando
            
        Returns:
            bool: True se publicado com sucesso, False caso contrário
        """
        if self.mqttClient is None:
            print(f"[RackControlService/Error] ❌ MQTT client not initialized")
            return False
        
        topic = f"{self.baseTopic}/{rack.rackId}/command/{commandType}"
        try:
            result = self.mqttClient.publish(topic, str(value))
            if result.rc == 0:
                print(f"[RackControlService/Command] 📤 Sent {commandType}={value} to rack {rack.rackId}")
                return True
            else:
                print(f"[RackControlService/Error] ❌ Failed to publish: rc={result.rc}")
                return False
        except Exception as e:
            print(f"[RackControlService/Error] ❌ Exception publishing command: {e}")
            return False
    
    def openDoor(self, rack: Rack) -> bool:
        """
        Abre a porta do rack.
        
        Args:
            rack: Instância do rack
            
        Returns:
            bool: True se comando enviado com sucesso
        """
        success = self._publishCommand(rack, "door", DoorStatus.OPEN)
        if success:
            rack.doorStatus = DoorStatus.OPEN
        return success
    
    def closeDoor(self, rack: Rack) -> bool:
        """
        Fecha a porta do rack.
        
        Args:
            rack: Instância do rack
            
        Returns:
            bool: True se comando enviado com sucesso
        """
        success = self._publishCommand(rack, "door", DoorStatus.CLOSED)
        if success:
            rack.doorStatus = DoorStatus.CLOSED
        return success
    
    def toggleDoor(self, rack: Rack) -> bool:
        """
        Alterna o estado da porta (abre se fechada, fecha se aberta).
        
        Args:
            rack: Instância do rack
            
        Returns:
            bool: True se comando enviado com sucesso
        """
        if rack.isDoorOpen():
            return self.closeDoor(rack)
        else:
            return self.openDoor(rack)
    
    def turnOnVentilation(self, rack: Rack) -> bool:
        """
        Liga a ventilação do rack.
        
        Args:
            rack: Instância do rack
            
        Returns:
            bool: True se comando enviado com sucesso
        """
        success = self._publishCommand(rack, "ventilation", VentilationStatus.ON)
        if success:
            rack.ventilationStatus = VentilationStatus.ON
        return success
    
    def turnOffVentilation(self, rack: Rack) -> bool:
        """
        Desliga a ventilação do rack.
        
        Args:
            rack: Instância do rack
            
        Returns:
            bool: True se comando enviado com sucesso
        """
        success = self._publishCommand(rack, "ventilation", VentilationStatus.OFF)
        if success:
            rack.ventilationStatus = VentilationStatus.OFF
        return success
    
    def toggleVentilation(self, rack: Rack) -> bool:
        """
        Alterna o estado da ventilação (liga se desligada, desliga se ligada).
        
        Args:
            rack: Instância do rack
            
        Returns:
            bool: True se comando enviado com sucesso
        """
        if rack.isVentilationOn():
            return self.turnOffVentilation(rack)
        else:
            return self.turnOnVentilation(rack)
    
    def activateCriticalTemperatureAlert(self, rack: Rack) -> bool:
        """
        Ativa o alerta de temperatura crítica (superaquecimento).
        
        Args:
            rack: Instância do rack
            
        Returns:
            bool: True se comando enviado com sucesso
        """
        success = self._publishCommand(rack, "buzzer", BuzzerStatus.OVERHEAT)
        if success:
            rack.buzzerStatus = BuzzerStatus.OVERHEAT
        return success
    
    def deactivateCriticalTemperatureAlert(self, rack: Rack) -> bool:
        """
        Desativa o alerta de temperatura crítica.
        
        Args:
            rack: Instância do rack
            
        Returns:
            bool: True se comando enviado com sucesso
        """
        success = self._publishCommand(rack, "buzzer", BuzzerStatus.OFF)
        if success:
            rack.buzzerStatus = BuzzerStatus.OFF
        return success
    
    def activateDoorOpenAlert(self, rack: Rack) -> bool:
        """
        Ativa o alerta de porta aberta.
        
        Args:
            rack: Instância do rack
            
        Returns:
            bool: True se comando enviado com sucesso
        """
        success = self._publishCommand(rack, "buzzer", BuzzerStatus.DOOR_OPEN)
        if success:
            rack.buzzerStatus = BuzzerStatus.DOOR_OPEN
        return success
    
    def activateBreakInAlert(self, rack: Rack) -> bool:
        """
        Ativa o alerta de arrombamento.
        
        Args:
            rack: Instância do rack
            
        Returns:
            bool: True se comando enviado com sucesso
        """
        success = self._publishCommand(rack, "buzzer", BuzzerStatus.BREAK_IN)
        if success:
            rack.buzzerStatus = BuzzerStatus.BREAK_IN
        return success
    
    def silenceBuzzer(self, rack: Rack) -> bool:
        """
        Silencia o buzzer do rack.
        
        Args:
            rack: Instância do rack
            
        Returns:
            bool: True se comando enviado com sucesso
        """
        return self.deactivateCriticalTemperatureAlert(rack)
    
    # Métodos com nomes em português para compatibilidade
    def abrirPorta(self, rack: Rack) -> bool:
        """Alias para openDoor()."""
        return self.openDoor(rack)
    
    def fecharPorta(self, rack: Rack) -> bool:
        """Alias para closeDoor()."""
        return self.closeDoor(rack)
    
    def acionarVentilador(self, rack: Rack) -> bool:
        """Alias para turnOnVentilation()."""
        return self.turnOnVentilation(rack)
    
    def desligarVentilador(self, rack: Rack) -> bool:
        """Alias para turnOffVentilation()."""
        return self.turnOffVentilation(rack)
    
    def gerarAlertaTemperaturaCritica(self, rack: Rack) -> bool:
        """Alias para activateCriticalTemperatureAlert()."""
        return self.activateCriticalTemperatureAlert(rack)
    
    def desativarAlertaTemperaturaCritica(self, rack: Rack) -> bool:
        """Alias para deactivateCriticalTemperatureAlert()."""
        return self.deactivateCriticalTemperatureAlert(rack)
