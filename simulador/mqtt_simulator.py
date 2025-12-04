#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulador de Telemetria MQTT para Racks Inteligentes.

Este módulo gera leituras aleatórias de status, temperatura e umidade para
racks distintos, inserindo anomalias de forma esporádica para validação de
comportamento em cenário de teste.

Funcionalidades:
    - Geração de telemetria realista (temperatura, umidade, porta)
    - Simulação de anomalias térmicas e de umidade
    - Coordenadas GPS fixas de locais em Fortaleza-CE
    - Resposta a comandos MQTT (porta, ventilação)
    - Persistência de IDs de racks em SQLite
    - Suporte a múltiplos racks simultâneos

Arquitetura:
    - RackState: Estrutura de dados do estado de um rack
    - TelemetryPublisher: Publicador MQTT
    - RackSimulator: Simulador de um rack individual
    - run_simulation: Orquestrador da simulação

Tópicos MQTT publicados:
    - {base}/{rack_id}/environment/door: Estado da porta (0=fechada, 1=aberta)
    - {base}/{rack_id}/environment/temperature: Temperatura em °C
    - {base}/{rack_id}/environment/humidity: Umidade em %
    - {base}/{rack_id}/gps: Coordenadas GPS (JSON)
    - {base}/{rack_id}/tilt: Estado de inclinação
    - {base}/{rack_id}/ack/*: Confirmações de comandos

Tópicos MQTT assinados (comandos):
    - {base}/{rack_id}/command/door: Comando de porta
    - {base}/{rack_id}/command/ventilation: Comando de ventilação

Autor:
    EmbarcaTech TIC-27 - Rack Inteligente

Data:
    2025

Exemplo de uso::

    python mqtt_simulator.py --racks 5 --reset

Variáveis de ambiente:
    - MQTT_SERVER: Endereço do broker MQTT
    - MQTT_PORT: Porta do broker (padrão: 1883)
    - MQTT_USERNAME: Usuário MQTT (opcional)
    - MQTT_PASSWORD: Senha MQTT (opcional)
    - MQTT_BASE_TOPIC: Tópico base (padrão: "racks")
"""
from __future__ import annotations

import argparse
import asyncio
import math
import os
import random
import sqlite3
import string
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, Optional, Tuple

import paho.mqtt.client as mqtt
from dotenv import load_dotenv


def log_message(sector: str, rack_id: str, message: str, emoji: str) -> None:
    """Exibe mensagens padronizadas no console conforme regras de depuração.

    Args:
        sector: Identificador do setor responsável pela mensagem.
        rack_id: Rack associado ao evento.
        message: Texto informativo a ser exibido.
        emoji: Emoticon que realça o tipo de evento.
    """
    print(f"[{sector}/{rack_id}] {message} {emoji}")


# Coordenadas fixas de locais em Fortaleza-CE, Brasil
# Cada rack será associado a uma coordenada fixa (racks não se movem)
# a tupla representa (latitude, longitude)
FORTALEZA_COORDINATES: list[Tuple[float, float]] = [
    (-3.7319, -38.5267),   # Centro
    (-3.7403, -38.4993),   # Aldeota
    (-3.7648, -38.4712),   # Iguatemi Shopping
    (-3.7271, -38.4909),   # Mucuripe
    (-3.7191, -38.5089),   # Praia de Iracema
    (-3.7456, -38.5302),   # Fátima
    (-3.7589, -38.4834),   # Papicu
    (-3.7744, -38.5566),   # Benfica
    (-3.7505, -38.5124),   # Dionísio Torres
    (-3.7380, -38.5189),   # Meireles
    (-3.7612, -38.4563),   # Cocó
    (-3.7283, -38.5434),   # Jacarecanga
    (-3.7834, -38.5912),   # Messejana
    (-3.7422, -38.4621),   # Edson Queiroz
    (-3.7956, -38.5234),   # Maraponga
    (-3.9012, -38.3876),   # Aquiraz - Vereda Tropical
]


@dataclass
class RackState:
    """Representa o estado corrente de um rack monitorado."""

    rack_id: str
    status: int = field(default_factory=lambda: random.choice([0, 1]))
    temperature: float = field(default_factory=lambda: round(random.uniform(22.0, 30.0), 2))
    humidity: float = field(default_factory=lambda: round(random.uniform(40.0, 60.0), 2))
    latitude: float = 0.0
    longitude: float = 0.0
    publishes: int = 0
    anomalies: int = 0
    next_door_open_at: float = 0.0
    door_open_until: Optional[float] = None
    ventilation_status: int = 0
    temperature_anomaly: Optional[Dict[str, float]] = None
    humidity_anomaly: Optional[Dict[str, float]] = None


class TelemetryPublisher:
    """Serviço de publicação MQTT responsável pelo envio das leituras."""

    def __init__(self, client: mqtt.Client, base_topic: str) -> None:
        self._client = client
        self._base_topic = base_topic.rstrip("/")

    def publish(self, topic: str, payload: str) -> None:
        """Envia a leitura para o broker MQTT.

        Args:
            topic: Topico completo.
            payload: Conteudo textual a ser compartilhado.
        """
        result = self._client.publish(topic, payload, qos=0, retain=False)
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            log_message(
                "simulator",
                topic.split("/")[1],
                f"Falha ao publicar em {topic} | código={result.rc}",
                "⚠️",
            )


class RackSimulator:
    """Serviço de domínio que gera e publica telemetria de um rack."""

    def __init__(
        self,
        state: RackState,
        publisher: TelemetryPublisher,
        anomaly_probability: float = 0.07,
    ) -> None:
        self._state = state
        self._publisher = publisher
        self._anomaly_probability = anomaly_probability
        self._random = random.Random()
        self._pending_events: Deque[Tuple[str, str, bool, str]] = deque()
        self._command_queue: Deque[Tuple[str, str]] = deque()
        self._door_interval_range: Tuple[float, float] = (14 * 60, 16 * 60)
        self._door_open_duration_range: Tuple[float, float] = (45, 150)
        self._external_temperature = 18.0

        now = time.monotonic()
        if self._state.status not in {0, 1}:
            self._state.status = 0
        if self._state.ventilation_status not in {0, 1}:
            self._state.ventilation_status = 0
        self._state.next_door_open_at = now + self._random.uniform(*self._door_interval_range)
        self._state.door_open_until = None

    def _log_envelope(self, progress: float) -> float:
        progress = max(0.0, min(1.0, progress))
        if progress <= 0.0 or progress >= 1.0:
            return 0.0
        if progress <= 0.5:
            scaled = progress / 0.5
        else:
            scaled = (1.0 - progress) / 0.5
        scaled = max(0.0, min(1.0, scaled))
        return math.log1p(9.0 * scaled) / math.log1p(9.0)

    def _compute_normal_temperature(self) -> float:
        if self._state.status == 1:
            target = self._external_temperature + 2.0
            candidate = self._random.normalvariate(target, 1.0)
            candidate = min(max(candidate, self._external_temperature - 1.0), self._external_temperature + 6.0)
        elif self._state.ventilation_status == 1:
            candidate = self._random.normalvariate(25.0, 1.0)
            candidate = min(max(candidate, 20.0), 32.0)
        else:
            candidate = self._random.normalvariate(27.0, 2.0)
            candidate = min(max(candidate, 18.0), 40.0)
        return candidate

    def _compute_normal_humidity(self) -> float:
        if self._state.status == 1:
            candidate = self._random.normalvariate(47.0, 4.0)
            candidate = min(max(candidate, 35.0), 65.0)
        elif self._state.ventilation_status == 1:
            candidate = self._random.normalvariate(46.0, 3.0)
            candidate = min(max(candidate, 35.0), 60.0)
        else:
            candidate = self._random.normalvariate(50.0, 7.0)
            candidate = min(max(candidate, 30.0), 70.0)
        return candidate

    async def run(self) -> None:
        """Executa o ciclo assíncrono de geração de telemetria."""
        while True:
            if self._process_pending_command():
                await asyncio.sleep(self._random.uniform(0.1, 0.3))
                continue

            self._process_door_schedule()

            if self._pending_events:
                attribute, value, anomaly, reason = self._pending_events.popleft()
                self._publish_event(attribute, value, anomaly, reason)
                await asyncio.sleep(self._random.uniform(0.2, 0.6))
                continue

            attribute = self._random.choice(["temperature", "humidity", "status"])
            value, anomaly = self._generate_value(attribute)
            if value is None:
                await asyncio.sleep(self._random.uniform(0.4, 0.8))
                continue
            reason = "Atualização periódica" if not anomaly else "Anomalia logarítmica"
            self._publish_event(attribute, value, anomaly, reason)
            await asyncio.sleep(self._random.uniform(0.6, 3.2))

    def enqueue_command(self, command: str, payload: str) -> None:
        """Enfileira comandos vindos do broker MQTT."""
        self._command_queue.append((command, payload))

    def _process_pending_command(self) -> bool:
        if not self._command_queue:
            return False
        command, payload = self._command_queue.popleft()
        self._handle_command(command, payload)
        return True

    def _handle_command(self, command: str, payload: str) -> None:
        if command == "door":
            self._handle_door_command(payload)
        elif command == "ventilation":
            self._handle_ventilation_command(payload)

    def _handle_door_command(self, payload: str) -> None:
        try:
            target = int(payload)
        except ValueError:
            log_message("simulator", self._state.rack_id, f"Payload inválido para porta: {payload}", "⚠️")
            return

        target = 1 if target == 1 else 0
        if target == self._state.status:
            log_message("simulator", self._state.rack_id, "Comando de porta redundante ignorado", "ℹ️")
            return

        current_time = time.monotonic()
        if target == 1:
            self._state.status = 1
            duration = self._random.uniform(*self._door_open_duration_range)
            self._state.door_open_until = current_time + duration
            self._state.next_door_open_at = current_time + self._random.uniform(*self._door_interval_range)
            self._queue_event("status", "1", False, f"Comando porta (abrir) | duração={duration:.1f}s")
        else:
            self._state.status = 0
            self._state.door_open_until = None
            self._state.next_door_open_at = current_time + self._random.uniform(*self._door_interval_range)
            self._queue_event("status", "0", False, "Comando porta (fechar)")

    def _handle_ventilation_command(self, payload: str) -> None:
        try:
            target = int(payload)
        except ValueError:
            log_message("simulator", self._state.rack_id, f"Payload inválido para ventilação: {payload}", "⚠️")
            return

        target = 1 if target == 1 else 0
        if target == self._state.ventilation_status:
            log_message("simulator", self._state.rack_id, "Comando de ventilação redundante ignorado", "ℹ️")
            return

        self._state.ventilation_status = target
        status_text = "ligada" if target else "desligada"
        emoji = "💨" if target else "🛑"
        log_message("simulator", self._state.rack_id, f"Ventilação {status_text} via comando", emoji)
        self._queue_event(
            "temperature",
            f"{self._state.temperature:.2f}",
            False,
            "Ajuste térmico via ventilação",
        )

    def _process_door_schedule(self) -> None:
        """Verifica agenda de abertura/fechamento e enfileira eventos necessários."""
        now = time.monotonic()

        if self._state.status == 0 and now >= self._state.next_door_open_at:
            self._open_door(now)
            return

        if self._state.status == 1 and self._state.door_open_until and now >= self._state.door_open_until:
            self._close_door(now)

    def _open_door(self, current_time: float) -> None:
        """Agenda abertura programada do rack."""
        self._state.status = 1
        duration = self._random.uniform(*self._door_open_duration_range)
        self._state.door_open_until = current_time + duration
        self._queue_event(
            "status",
            "1",
            False,
            f"Abertura programada | duração={duration:.1f}s",
        )

    def _close_door(self, current_time: float) -> None:
        """Agenda fechamento do rack após período de abertura."""
        self._state.status = 0
        self._state.door_open_until = None
        self._state.next_door_open_at = current_time + self._random.uniform(*self._door_interval_range)
        self._queue_event("status", "0", False, "Fechamento automático")

    def _queue_event(self, attribute: str, value: str, anomaly: bool, reason: str) -> None:
        """Insere evento na fila de publicações."""
        self._pending_events.append((attribute, value, anomaly, reason))

    def _publish_event(self, attribute: str, value: str, anomaly: bool, reason: str) -> None:
        """Publica evento e realiza log padronizado."""
        topic = self._compose_topic(attribute)
        self._publisher.publish(topic, value)
        self._state.publishes += 1
        emoji = "🚨" if anomaly else "✅"
        status = "ANOMALIA" if anomaly else "OK"
        log_message(
            "simulator",
            self._state.rack_id,
            (
                f"{reason} -> {attribute}={value} | eventos={self._state.publishes} "
                f"| anomalias={self._state.anomalies} | status={status}"
            ),
            emoji,
        )

    def _generate_value(self, attribute: str) -> Tuple[str, bool]:
        """Calcula o próximo valor a ser publicado.

        Args:
            attribute: Identificador do parâmetro.

        Returns:
            Tuple com o valor formatado e indicador de anomalia.
        """
        if attribute == "status":
            return self._next_status()
        if attribute == "temperature":
            return self._next_temperature()
        return self._next_humidity()

    def _next_status(self) -> Tuple[str, bool]:
        """Retorna o estado atual da porta.
        
        A porta só pode estar fechada (0) ou aberta (1).
        Não há valores de anomalia para este atributo.
        
        Returns:
            Tuple com o valor formatado ('0' ou '1') e False (sem anomalia).
        """
        return str(self._state.status), False

    def _next_temperature(self) -> Tuple[str, bool]:
        now = time.monotonic()
        anomaly_state = self._state.temperature_anomaly

        if anomaly_state:
            progress = (now - anomaly_state["start"]) / anomaly_state["duration"]
            if progress >= 1.0:
                self._state.temperature_anomaly = None
                candidate = self._compute_normal_temperature()
                anomaly = False
            else:
                intensity = self._log_envelope(progress)
                candidate = anomaly_state["baseline"] + (anomaly_state["target"] - anomaly_state["baseline"]) * intensity
                candidate += self._random.uniform(-0.2, 0.2)
                anomaly = True
        else:
            safe_mode = self._state.status == 1 or self._state.ventilation_status == 1
            if not safe_mode and self._random.random() < self._anomaly_probability:
                baseline = self._state.temperature
                if baseline is None:
                    baseline = self._compute_normal_temperature()
                duration = self._random.uniform(18.0, 22.0)
                target = self._random.choice([
                    self._random.uniform(-5.0, 5.0),
                    self._random.uniform(60.0, 90.0),
                ])
                self._state.temperature_anomaly = {
                    "start": now,
                    "duration": duration,
                    "baseline": baseline,
                    "target": target,
                }
                log_message(
                    "simulator",
                    self._state.rack_id,
                    f"Início anomalia térmica | alvo={target:.2f}°C | duração={duration:.1f}s",
                    "🔥",
                )
                intensity = self._log_envelope(0.02)
                candidate = baseline + (target - baseline) * intensity
                anomaly = True
            else:
                candidate = self._compute_normal_temperature()
                anomaly = False

        candidate = max(-10.0, min(candidate, 120.0))
        self._state.temperature = round(candidate, 2)
        return f"{self._state.temperature:.2f}", anomaly

    def _next_humidity(self) -> Tuple[str, bool]:
        now = time.monotonic()
        anomaly_state = self._state.humidity_anomaly

        if anomaly_state:
            progress = (now - anomaly_state["start"]) / anomaly_state["duration"]
            if progress >= 1.0:
                self._state.humidity_anomaly = None
                candidate = self._compute_normal_humidity()
                anomaly = False
            else:
                intensity = self._log_envelope(progress)
                candidate = anomaly_state["baseline"] + (anomaly_state["target"] - anomaly_state["baseline"]) * intensity
                candidate += self._random.uniform(-0.5, 0.5)
                anomaly = True
        else:
            safe_mode = self._state.status == 1 or self._state.ventilation_status == 1
            if not safe_mode and self._random.random() < self._anomaly_probability:
                baseline = self._state.humidity
                if baseline is None:
                    baseline = self._compute_normal_humidity()
                duration = self._random.uniform(18.0, 22.0)
                target = self._random.choice([
                    self._random.uniform(0.0, 20.0),
                    self._random.uniform(85.0, 100.0),
                ])
                self._state.humidity_anomaly = {
                    "start": now,
                    "duration": duration,
                    "baseline": baseline,
                    "target": target,
                }
                log_message(
                    "simulator",
                    self._state.rack_id,
                    f"Início anomalia de umidade | alvo={target:.2f}% | duração={duration:.1f}s",
                    "💦",
                )
                intensity = self._log_envelope(0.02)
                candidate = baseline + (target - baseline) * intensity
                anomaly = True
            else:
                candidate = self._compute_normal_humidity()
                anomaly = False

        candidate = max(0.0, min(candidate, 100.0))
        self._state.humidity = round(candidate, 2)
        return f"{self._state.humidity:.2f}", anomaly

    def _compose_topic(self, attribute: str) -> str:
        return f"{self._publisher._base_topic}/{self._state.rack_id}/{self._topic_segment(attribute)}"

    def _topic_segment(self, attribute: str) -> str:
        """Retorna o segmento do tópico MQTT para o atributo especificado.
        
        Args:
            attribute: Nome do atributo (status, temperature, humidity, location)
            
        Returns:
            Segmento do tópico MQTT
        """
        if attribute == "status":
            return "status"
        if attribute == "location":
            return "location"
        return f"environment/{attribute}"
    
    def publish_location(self) -> None:
        """Publica as coordenadas do rack (latitude, longitude) no broker MQTT.
        
        As coordenadas são fixas por rack, representando a localização física
        do equipamento em Fortaleza-CE, Brasil.
        """
        import json
        location_data = json.dumps({
            "latitude": self._state.latitude,
            "longitude": self._state.longitude
        })
        topic = self._compose_topic("location")
        self._publisher.publish(topic, location_data)
        log_message(
            "simulator",
            self._state.rack_id,
            f"Localização publicada: lat={self._state.latitude:.6f}, lon={self._state.longitude:.6f}",
            "📍",
        )


def load_mqtt_client() -> mqtt.Client:
    """Configura e retorna o cliente MQTT baseado em variáveis de ambiente."""
    # Load environment variables from workspace root (.env located at project root)
    workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    load_dotenv(os.path.join(workspace_root, ".env"))

    host = os.getenv("MQTT_SERVER")
    port = int(os.getenv("MQTT_PORT", "1883"))
    username = os.getenv("MQTT_USERNAME")
    password = os.getenv("MQTT_PASSWORD")
    keepalive = int(os.getenv("MQTT_KEEPALIVE", "60"))

    if not host:
        raise RuntimeError("MQTT_SERVER não definido no arquivo .env")

    client = mqtt.Client(client_id=f"rack-simulator-{os.getpid()}")
    if username:
        client.username_pw_set(username, password or None)

    client.connect(host, port, keepalive)
    client.loop_start()

    log_message("simulator", "global", f"Conectado ao broker MQTT {host}:{port}", "🛰️")
    return client


def generate_rack_ids(amount: int = 10, reset: bool = False) -> list[str]:
    """Gera identificadores únicos para os racks simulados com persistência.

    Os identificadores são armazenados em uma base SQLite local, garantindo que
    execuções subsequentes reutilizem os mesmos racks. Quando ``reset`` é
    verdadeiro, a base é esvaziada e um novo conjunto de racks é criado.
    """

    db_path = os.path.join(os.path.dirname(__file__), "racks.db")
    conn = sqlite3.connect(db_path)

    try:
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS racks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rack_code TEXT NOT NULL UNIQUE
                )
                """
            )

            if reset:
                conn.execute("DELETE FROM racks")

            cursor = conn.execute("SELECT rack_code FROM racks ORDER BY id")
            existing_codes = [row[0] for row in cursor.fetchall()]

            identifiers: set[str] = set(existing_codes)
            alphabet = string.ascii_uppercase + string.digits
            while len(identifiers) < amount:
                suffix = "".join(random.choices(alphabet, k=4))
                identifiers.add(suffix)

            new_codes = [code for code in identifiers if code not in existing_codes]
            if new_codes:
                conn.executemany(
                    "INSERT OR IGNORE INTO racks (rack_code) VALUES (?)",
                    [(code,) for code in new_codes],
                )

        return sorted(identifiers)
    finally:
        conn.close()


async def run_simulation(reset: bool = False) -> None:
    """Inicializa recursos e executa a simulação de telemetria.

    Args:
        reset: Quando verdadeiro, recria o conjunto de racks persistidos.
    """
    client = load_mqtt_client()
    base_topic = os.getenv("MQTT_BASE_TOPIC", "racks/").rstrip("/")
    publisher = TelemetryPublisher(client, base_topic)
    rack_ids = generate_rack_ids(amount=10, reset=reset)
    
    # Atribui coordenadas fixas de Fortaleza-CE para cada rack
    rack_states = []
    for idx, rack_id in enumerate(rack_ids):
        coord_idx = idx % len(FORTALEZA_COORDINATES)
        lat, lon = FORTALEZA_COORDINATES[coord_idx]
        state = RackState(
            rack_id=rack_id,
            latitude=lat,
            longitude=lon,
        )
        rack_states.append(state)
        log_message(
            "simulator",
            rack_id,
            f"Coordenadas atribuídas: lat={lat:.6f}, lon={lon:.6f}",
            "📍",
        )
    
    simulators = [RackSimulator(state, publisher) for state in rack_states]
    
    # Publica localização inicial de cada rack
    for sim in simulators:
        sim.publish_location()
    simulator_map: Dict[str, RackSimulator] = {state.rack_id: sim for state, sim in zip(rack_states, simulators)}

    loop = asyncio.get_running_loop()
    setup_command_subscriptions(client, simulator_map, loop, base_topic)

    tasks = [asyncio.create_task(sim.run(), name=f"sim-{state.rack_id}") for sim, state in zip(simulators, rack_states)]

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        raise
    except Exception as exc:  # pragma: no cover
        log_message("simulator", "global", f"Erro inesperado: {exc}", "🔥")
    finally:
        for task in tasks:
            task.cancel()
        client.loop_stop()
        client.disconnect()
        log_message("simulator", "global", "Cliente MQTT desconectado", "👋")


def setup_command_subscriptions(
    client: mqtt.Client,
    simulators: Dict[str, RackSimulator],
    loop: asyncio.AbstractEventLoop,
    base_topic: str,
) -> None:
    """Configura assinaturas para comandos de porta e ventilação."""
    base = base_topic.rstrip("/")
    topics = [
        (f"{base}/+/command/door", 0),
        (f"{base}/+/command/ventilation", 0),
    ]
    for topic, qos in topics:
        client.subscribe(topic, qos)
        log_message("simulator", "global", f"Assinatura registrada para {topic}", "📡")

    def on_message(_client: mqtt.Client, _userdata, message: mqtt.MQTTMessage) -> None:
        prefix = f"{base}/"
        topic = message.topic
        if not topic.startswith(prefix):
            return

        remainder = topic[len(prefix):]
        parts = remainder.split("/")
        # Espera: <rack_id>/command/<tipo>
        if len(parts) < 3 or parts[1] != "command":
            return

        rack_id = parts[0]
        command = parts[2]
        simulator = simulators.get(rack_id)
        if not simulator:
            log_message("simulator", rack_id, "Comando recebido para rack não monitorado", "⚠️")
            return

        try:
            payload = message.payload.decode().strip()
        except UnicodeDecodeError:
            log_message("simulator", rack_id, "Payload inválido recebido (encoding)", "⚠️")
            return

        loop.call_soon_threadsafe(simulator.enqueue_command, command, payload)

    client.on_message = on_message


def main() -> None:
    """Ponto de entrada para execução direta do módulo."""

    parser = argparse.ArgumentParser(description="MQTT rack telemetry simulator")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Recria o conjunto de racks persistidos na base SQLite.",
    )
    args = parser.parse_args()

    try:
        asyncio.run(run_simulation(reset=args.reset))
    except KeyboardInterrupt:
        log_message("simulator", "global", "Simulação interrompida pelo usuário", "🛑")


if __name__ == "__main__":
    main()
