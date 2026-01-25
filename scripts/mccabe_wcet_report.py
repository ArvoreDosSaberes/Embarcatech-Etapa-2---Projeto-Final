#!/usr/bin/env python3
"""mccabe_wcet_report.py

Autor: Carlos Delfino / EmbarcaTech TIC-27 (script recriado com suporte a GUI)
Data: 2025-12-18 (revisado 2025-12-23)

Objetivo
- Analisar arquivos ELF para extrair complexidade ciclomática (McCabe) e estimativa de WCET.
- Quando --serial é informado, coletar métricas de RTOS emitidas via serial pelo firmware.
- Agregar estatísticas (mínimo, máximo, média) e gerar relatório em Markdown.
- Exibir as métricas em tempo real via interface Qt com grafo de chamadas interativo.

Modos de operação:
1. Modo OFFLINE (sem --serial): Analisa apenas o arquivo ELF
   - Complexidade ciclomática McCabe
   - Estimativa de WCET baseada em ciclos de instrução
   - Grafo de chamadas de funções
   - Não requer conexão serial

2. Modo ONLINE (com --serial): Coleta dados do firmware em tempo real
   - Métricas de heap, stack e CPU
   - WCET medido via probes
   - Trace de escalonamento de tasks

Dependências (ver requirements.txt na raiz)
- PySide6
- pyserial
- pyqtgraph
- networkx (opcional, para layout de grafos)

Execução (exemplos)
# Modo offline (apenas análise de ELF):
python scripts/mccabe_wcet_report.py --out-md docs.temp/analise.md --elf firmware/build/rack_inteligente.elf --mcu-code rp2040 --gui

# Modo online (com serial):
python scripts/mccabe_wcet_report.py --out-md docs.temp/analise.md --serial --port /dev/ttyACM0 --elf firmware/build/rack_inteligente.elf --mcu-code rp2040 --gui

Observações importantes
- No modo online, o script depende do firmware emitir linhas no formato KV (key=value):
  - [MonitorKV] heap_free, heap_min, stack_total, stack_free, stack_used, stack_usage_pct
  - [HwKV] clk_*_hz, rtos_tick_hz, etc.
  - [WcetKV] ts_us, name, dur_us, task, isr
  - [TraceKV] ts_us, ev=switch_in|switch_out, task, reason, wait_ticks
- As estatísticas de CPU por tarefa são obtidas do bloco "Run Time Stats (CPU)" quando habilitado.

Saída graciosa
- Ctrl+C e sinais de término fecham a porta serial e gravam o Markdown de saída.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as _dt
import json
import logging
import math
import numpy as np
import os
import re
import signal
import subprocess
import sys
import threading
import time
from collections import defaultdict, deque
from typing import Any, Deque, Dict, List, Optional, Set, Tuple

# Serial é opcional (apenas para modo online)
try:
    import serial  # type: ignore
    _HAS_SERIAL = True
except ImportError:
    serial = None  # type: ignore
    _HAS_SERIAL = False

# Qt / gráficos - opcional para modo CLI offline
_HAS_QT = False
QtCore: Any = None
QtWidgets: Any = None
QtGui: Any = None
pg: Any = None

try:
    from PySide6 import QtCore, QtWidgets, QtGui  # type: ignore
    import pyqtgraph as pg  # type: ignore
    _HAS_QT = True
except ImportError:
    # Cria classes stub para permitir definição das classes Qt
    class _QtCoreStub:
        class QObject:
            pass
        class QThread:
            pass
        class Signal:
            def __init__(self, *args: Any) -> None:
                pass
        class Slot:
            def __init__(self, *args: Any) -> None:
                pass
            def __call__(self, fn: Any) -> Any:
                return fn
        class Qt:
            class PenStyle:
                DashLine = 0
            class MatchFlag:
                MatchExactly = 0
            class ConnectionType:
                QueuedConnection = 0
            class ItemDataRole:
                DisplayRole = 0
        class QTimer:
            pass

    class _QtWidgetsStub:
        class QMainWindow:
            pass
        class QWidget:
            pass
        class QApplication:
            pass
        class QTabWidget:
            pass
        class QVBoxLayout:
            pass
        class QHBoxLayout:
            pass
        class QLabel:
            pass
        class QListWidget:
            pass
        class QTableWidget:
            pass
        class QLineEdit:
            pass
        class QCheckBox:
            pass
        class QSpinBox:
            pass
        class QTableWidgetItem:
            pass
        class QAbstractItemView:
            class EditTrigger:
                NoEditTriggers = 0
            class SelectionBehavior:
                SelectRows = 0
        class QHeaderView:
            class ResizeMode:
                Stretch = 0
                ResizeToContents = 0

    class _PgStub:
        class PlotWidget:
            pass
        class GraphItem:
            pass
        class TextItem:
            pass
        class BarGraphItem:
            pass
        class InfiniteLine:
            pass
        class ViewBox:
            YAxis = 0
        @staticmethod
        def setConfigOptions(**kwargs: Any) -> None:
            pass
        @staticmethod
        def mkPen(*args: Any, **kwargs: Any) -> Any:
            return None
        @staticmethod
        def mkBrush(*args: Any, **kwargs: Any) -> Any:
            return None

    QtCore = _QtCoreStub()  # type: ignore
    QtWidgets = _QtWidgetsStub()  # type: ignore
    QtGui = None  # type: ignore
    pg = _PgStub()  # type: ignore

# networkx é opcional para layout de grafos
try:
    import networkx as nx
    _HAS_NETWORKX = True
except ImportError:
    nx = None  # type: ignore
    _HAS_NETWORKX = False


_KV_RE = re.compile(r"(?P<key>[a-zA-Z0-9_]+)=(?P<value>[^\s]+)")
_PREFIX_RE = re.compile(r"^\[(?P<prefix>[A-Za-z0-9_]+)\]\s*(?P<body>.*)$")
_PLAIN_PREFIX_RE = re.compile(r"^(?P<prefix>[A-Za-z0-9_]+)\s*(?P<body>.*)$")
_LOG_LEVEL_PREFIX_RE = re.compile(r"^\[[A-Z]{3,5}\s*\]\s*(?P<rest>.*)$")
_ANSI_ESCAPE_RE = re.compile(r"(?:\x1b)?\[[0-9;]*m")
_KNOWN_PREFIXES = {"MonitorKV", "HwKV", "WcetKV", "TraceKV", "WCET", "TRACE"}

_LOGGER = logging.getLogger("wcet_report")


_TRACE_REASON_LABEL_BY_CODE: Dict[int, str] = {
    0: "desconhecido",
    1: "preempção",
    2: "delay",
    3: "queue_recv",
    4: "queue_send",
    5: "notify",
    6: "eventgroup",
}


def _formatTraceReason(reasonCode: Optional[int], waitTicks: Optional[int]) -> str:
    label = _TRACE_REASON_LABEL_BY_CODE.get(int(reasonCode or 0), str(reasonCode))
    if waitTicks is not None and waitTicks > 0:
        return f"{label} (wait={waitTicks} ticks)"
    return label


@dataclasses.dataclass(frozen=True)
class CliArgs:
    outMd: str
    serialEnabled: bool
    port: Optional[str]
    baud: int
    elfPath: Optional[str]
    mcuCode: Optional[str]
    projectDir: Optional[str]
    board: Optional[str]
    gui: bool
    logFile: Optional[str]
    serialLogPath: Optional[str]
    appLogPath: Optional[str]
    logLevel: str
    debugSerial: bool
    debugOutLog: Optional[str]


@dataclasses.dataclass
class RunningStats:
    """Estatística incremental para min/max/média."""

    count: int = 0
    mean: float = 0.0
    m2: float = 0.0
    minValue: Optional[float] = None
    maxValue: Optional[float] = None

    def update(self, value: float) -> None:
        if not math.isfinite(value):
            return
        self.count += 1
        if self.minValue is None or value < self.minValue:
            self.minValue = value
        if self.maxValue is None or value > self.maxValue:
            self.maxValue = value
        delta = value - self.mean
        self.mean += delta / float(self.count)
        delta2 = value - self.mean
        self.m2 += delta * delta2

    def variance(self) -> Optional[float]:
        if self.count < 2:
            return None
        return self.m2 / float(self.count - 1)

    def stddev(self) -> Optional[float]:
        var = self.variance()
        if var is None:
            return None
        if var < 0.0:
            return 0.0
        return float(var ** 0.5)


@dataclasses.dataclass
class TimeSeries:
    """Série temporal com janela fixa (memória limitada)."""

    maxLen: int
    points: Deque[Tuple[float, float]] = dataclasses.field(default_factory=deque)
    _startTs: Optional[float] = None
    _version: int = dataclasses.field(default=0, init=False, repr=False)
    _cacheVersion: int = dataclasses.field(default=-1, init=False, repr=False)
    _cacheX: Optional[np.ndarray] = dataclasses.field(default=None, init=False, repr=False)
    _cacheY: Optional[np.ndarray] = dataclasses.field(default=None, init=False, repr=False)

    def append(self, ts: float, value: float) -> None:
        if not math.isfinite(ts) or not math.isfinite(value):
            return
        if self._startTs is None:
            self._startTs = ts
        relTs = ts - self._startTs
        self.points.append((relTs, value))
        while len(self.points) > self.maxLen:
            self.points.popleft()
        self._version += 1

    def toArrays(self) -> Tuple[List[float], List[float]]:
        xs: List[float] = []
        ys: List[float] = []
        for x, y in self.points:
            xs.append(x)
            ys.append(y)
        return xs, ys

    def toNumpyArrays(self) -> Tuple[np.ndarray, np.ndarray]:
        if (
            self._cacheVersion == self._version
            and self._cacheX is not None
            and self._cacheY is not None
        ):
            return self._cacheX, self._cacheY

        n = len(self.points)
        if n <= 0:
            xs = np.asarray([], dtype=float)
            ys = np.asarray([], dtype=float)
            self._cacheX = xs
            self._cacheY = ys
            self._cacheVersion = self._version
            return xs, ys

        xs = np.empty(n, dtype=float)
        ys = np.empty(n, dtype=float)
        for i, (x, y) in enumerate(self.points):
            xs[i] = x
            ys[i] = y

        self._cacheX = xs
        self._cacheY = ys
        self._cacheVersion = self._version
        return xs, ys

    def clear(self) -> None:
        self.points.clear()
        self._startTs = None
        self._version += 1
        self._cacheVersion = -1
        self._cacheX = None
        self._cacheY = None


@dataclasses.dataclass
class TaskMetrics:
    """Métricas agregadas por task."""

    stackTotalStats: RunningStats = dataclasses.field(default_factory=RunningStats)
    stackFreeStats: RunningStats = dataclasses.field(default_factory=RunningStats)
    stackUsedStats: RunningStats = dataclasses.field(default_factory=RunningStats)
    stackUsagePctStats: RunningStats = dataclasses.field(default_factory=RunningStats)

    cpuPctStats: RunningStats = dataclasses.field(default_factory=RunningStats)

    stackUsedSeries: TimeSeries = dataclasses.field(default_factory=lambda: TimeSeries(maxLen=600))
    cpuPctSeries: TimeSeries = dataclasses.field(default_factory=lambda: TimeSeries(maxLen=600))


@dataclasses.dataclass
class WcetKey:
    name: str
    task: str
    isr: int


@dataclasses.dataclass
class WcetMetrics:
    """Métricas de WCET coletadas em tempo real via serial."""
    durUsStats: RunningStats = dataclasses.field(default_factory=RunningStats)
    durUsSeries: TimeSeries = dataclasses.field(default_factory=lambda: TimeSeries(maxLen=1200))
    durUsSamples: Deque[float] = dataclasses.field(default_factory=lambda: deque(maxlen=5000))
    lastTsUs: Optional[int] = None

    def quantiles(self, ps: List[float]) -> Dict[float, Optional[float]]:
        if not self.durUsSamples:
            return {p: None for p in ps}
        try:
            arr = np.fromiter(self.durUsSamples, dtype=float, count=len(self.durUsSamples))
        except Exception:
            return {p: None for p in ps}

        out: Dict[float, Optional[float]] = {}
        try:
            qs = np.percentile(arr, ps)
            for p, q in zip(ps, qs):
                out[p] = float(q)
        except Exception:
            for p in ps:
                out[p] = None
        return out


@dataclasses.dataclass
class FunctionInfo:
    """Informações de uma função extraídas do ELF (análise offline)."""
    name: str
    address: int = 0
    size: int = 0
    instructionCount: int = 0
    decisionCount: int = 0  # Número de branches condicionais
    mccabe: int = 1  # Complexidade ciclomática (1 + decisionCount)
    estimatedCycles: int = 0  # Estimativa de ciclos (para WCET)
    estimatedTimeUs: float = 0.0  # Tempo estimado em microsegundos
    callees: List[str] = dataclasses.field(default_factory=list)  # Funções chamadas
    callers: List[str] = dataclasses.field(default_factory=list)  # Funções que chamam esta
    stackUsage: Optional[int] = None  # Uso de stack (se disponível via -fstack-usage)
    isTask: bool = False  # Se é uma task do RTOS
    taskName: Optional[str] = None


@dataclasses.dataclass
class CallGraphData:
    """Dados do grafo de chamadas extraído do ELF."""
    functions: Dict[str, FunctionInfo] = dataclasses.field(default_factory=dict)
    edges: List[Tuple[str, str]] = dataclasses.field(default_factory=list)
    maxDepth: int = 0
    rootFunctions: List[str] = dataclasses.field(default_factory=list)  # Funções sem callers
    taskFunctions: List[str] = dataclasses.field(default_factory=list)  # Tasks identificadas
    mcuClockHz: int = 125_000_000  # Clock do MCU para cálculo de tempo


# Tabela de ciclos por instrução (ARM Cortex-M0+/M33, simplificada)
# Valores médios/piores casos para estimativa de WCET
_ARM_INSTRUCTION_CYCLES: Dict[str, int] = {
    # Aritméticas simples (1 ciclo)
    "add": 1, "adds": 1, "adc": 1, "adcs": 1, "sub": 1, "subs": 1,
    "sbc": 1, "sbcs": 1, "rsb": 1, "rsbs": 1, "mul": 1, "muls": 1,
    "and": 1, "ands": 1, "orr": 1, "orrs": 1, "eor": 1, "eors": 1,
    "bic": 1, "bics": 1, "mvn": 1, "mvns": 1, "neg": 1, "negs": 1,
    "mov": 1, "movs": 1, "movw": 1, "movt": 1,
    # Shifts (1 ciclo)
    "lsl": 1, "lsls": 1, "lsr": 1, "lsrs": 1, "asr": 1, "asrs": 1,
    "ror": 1, "rors": 1, "rrx": 1,
    # Comparações (1 ciclo)
    "cmp": 1, "cmn": 1, "tst": 1, "teq": 1,
    # Load/Store (2 ciclos em média, pior caso com wait states)
    "ldr": 2, "ldrb": 2, "ldrh": 2, "ldrsb": 2, "ldrsh": 2,
    "str": 2, "strb": 2, "strh": 2,
    "ldm": 4, "stm": 4, "push": 3, "pop": 3,
    # Branches (2-4 ciclos, pior caso para pipeline flush)
    "b": 3, "bl": 4, "blx": 4, "bx": 3,
    "beq": 3, "bne": 3, "bcs": 3, "bcc": 3, "bhs": 3, "blo": 3,
    "bmi": 3, "bpl": 3, "bvs": 3, "bvc": 3, "bhi": 3, "bls": 3,
    "bge": 3, "blt": 3, "bgt": 3, "ble": 3,
    "cbz": 3, "cbnz": 3,
    # Divisão (em MCUs com suporte, 2-12 ciclos)
    "sdiv": 8, "udiv": 8,
    # NOP
    "nop": 1,
    # Default para instruções desconhecidas
    "_default": 2,
}

# Padrões de nomes de tasks FreeRTOS comuns
_TASK_NAME_PATTERNS = [
    re.compile(r"^.*[Tt]ask.*$"),
    re.compile(r"^vTask.*$"),
    re.compile(r"^xTask.*$"),
    re.compile(r"^prv.*Task$"),
    re.compile(r"^.*_task$"),
    re.compile(r"^.*TaskEntry$"),
]


@dataclasses.dataclass
class SystemMetrics:
    heapFreeStats: RunningStats = dataclasses.field(default_factory=RunningStats)
    heapMinStats: RunningStats = dataclasses.field(default_factory=RunningStats)

    heapFreeSeries: TimeSeries = dataclasses.field(default_factory=lambda: TimeSeries(maxLen=600))
    heapMinSeries: TimeSeries = dataclasses.field(default_factory=lambda: TimeSeries(maxLen=600))


@dataclasses.dataclass
class SchedulingState:
    """Mantém timeline simplificada (switch_in/out) por task."""

    # segmentos recentes (start_ts, end_ts) em segundos (epoch)
    segments: Deque[Tuple[float, float]] = dataclasses.field(default_factory=lambda: deque(maxlen=2000))


@dataclasses.dataclass
class TraceGlobalState:
    """Estado global do escalonamento.

    O trace do FreeRTOS representa uma linha do tempo única (uma task executando
    por vez). Então, ao invés de armazenar currentStart por task (que falha
    quando os logs chegam com perdas), mantemos a task atual e seu início.
    """

    currentTask: Optional[str] = None
    currentStartRelSec: Optional[float] = None
    startTargetSec: Optional[float] = None
    startHostSec: Optional[float] = None
    lastRelSec: Optional[float] = None
    timeBase: Optional[str] = None

    pendingSwitchOutTask: Optional[str] = None
    pendingSwitchOutReason: Optional[int] = None
    pendingSwitchOutWaitTicks: Optional[int] = None
    pendingSwitchOutRelSec: Optional[float] = None


@dataclasses.dataclass
class TraceEdgeInfo:
    count: int = 0
    lastReason: Optional[int] = None
    lastWaitTicks: Optional[int] = None
    lastRelSec: Optional[float] = None


class MetricsStore:
    """Armazena dados em memória e fornece agregações rápidas."""

    def __init__(self) -> None:
        self.system = SystemMetrics()
        self.tasks: Dict[str, TaskMetrics] = defaultdict(TaskMetrics)
        self.scheduling: Dict[str, SchedulingState] = defaultdict(SchedulingState)
        self.hwKv: Dict[str, str] = {}
        self.trace = TraceGlobalState()
        self.traceEdges: Dict[Tuple[str, str], TraceEdgeInfo] = defaultdict(TraceEdgeInfo)
        self.wcet: Dict[WcetKey, WcetMetrics] = defaultdict(WcetMetrics)
        self.rxTotalLines: int = 0
        self.rxCountsByPrefix: Dict[str, int] = defaultdict(int)
        # Dados de análise offline do ELF
        self.callGraph: Optional[CallGraphData] = None
        self.offlineAnalysisComplete: bool = False

    def listTasks(self) -> List[str]:
        names = list(self.tasks.keys())
        names.sort()
        return names

    def listWcetKeys(self) -> List[WcetKey]:
        keys = list(self.wcet.keys())
        keys.sort(key=lambda k: (k.name, k.task, k.isr))
        return keys


class FirmwareLineParser:
    """Parser das linhas da serial conforme os prefixes já emitidos pelo firmware."""

    def parseLine(self, line: str) -> Tuple[Optional[str], Dict[str, str]]:
        txt = _ANSI_ESCAPE_RE.sub("", line).strip()

        # Alguns ambientes/loggers prefixam timestamp/ruído antes do KV.
        # Heurística: corta a partir do primeiro '[' para tentar alinhar com "[MonitorKV] ...".
        lb = txt.find("[")
        if lb > 0:
            txt = txt[lb:]

        # Normaliza prefixos de logger do firmware (ex.: "[INFO ] [TraceKV] ...")
        lm = _LOG_LEVEL_PREFIX_RE.match(txt)
        if lm:
            txt = lm.group("rest").lstrip()

        lb2 = txt.find("[")
        if lb2 > 0:
            txt = txt[lb2:]

        m = _PREFIX_RE.match(txt)
        if not m:
            # Fallback: permite linhas sem colchetes, ex.: "MonitorKV key=val"
            pm = _PLAIN_PREFIX_RE.match(txt)
            if not pm:
                return None, {}
            prefix = pm.group("prefix")
            if prefix not in _KNOWN_PREFIXES:
                return None, {}
            body = pm.group("body")
        else:
            prefix = m.group("prefix")
            body = m.group("body")

        kv: Dict[str, str] = {}
        for km in _KV_RE.finditer(body):
            kv[km.group("key")] = km.group("value")

        # Special handling for WCET prefix
        if prefix == "WCET" and not kv:
            m = re.search(r'Task:\s*(\w+),\s*WCET:\s*(\d+)\s*us', body.strip())
            if m:
                kv = {'name': 'wcet', 'task': m.group(1), 'dur_us': m.group(2), 'isr': '0'}

        if prefix.upper() == "TRACE" and not kv:
            m = re.search(r"Task\s+switched:\s*(?P<frm>.+?)\s*->\s*(?P<to>.+)$", body.strip())
            if m:
                kv = {"from": m.group("frm").strip(), "to": m.group("to").strip()}
                prefix = "TRACE"

        return prefix, kv

    def normalizeLine(self, line: str) -> str:
        """Remove prefixos de log (ex.: [INFO ]) para facilitar debug/replay."""

        txt = _ANSI_ESCAPE_RE.sub("", line).strip()

        lb = txt.find("[")
        if lb > 0:
            txt = txt[lb:]
        lm = _LOG_LEVEL_PREFIX_RE.match(txt)
        if lm:
            txt = lm.group("rest").lstrip()

        lb2 = txt.find("[")
        if lb2 > 0:
            txt = txt[lb2:]

        return txt


_CPU_HEADER_RE = re.compile(r"=+\s*Run Time Stats \(CPU\)\s*=+", re.IGNORECASE)
_CPU_END_RE = re.compile(r"=+\s*End Run Time Stats\s*=+", re.IGNORECASE)


class CpuStatsBlockParser:
    """Parser do bloco de vTaskGetRunTimeStats.

    Exemplo típico de linhas (FreeRTOS):
    TaskName\t\tRunTimeCounter\t\tPercentage
    Idle\t\t12345\t\t50%

    O firmware imprime cada linha com LOG_INFO("%s", line).
    """

    def __init__(self) -> None:
        self._inBlock = False

    def feed(self, line: str) -> Optional[List[Tuple[str, float]]]:
        txt = _ANSI_ESCAPE_RE.sub("", line).strip()
        lb = txt.find("[")
        if lb > 0:
            txt = txt[lb:]
        lm = _LOG_LEVEL_PREFIX_RE.match(txt)
        if lm:
            txt = lm.group("rest").lstrip()
        lb2 = txt.find("[")
        if lb2 > 0:
            txt = txt[lb2:]
        if _CPU_HEADER_RE.search(txt):
            self._inBlock = True
            _LOGGER.debug("CPU stats block start")
            return None
        if _CPU_END_RE.search(txt):
            self._inBlock = False
            _LOGGER.debug("CPU stats block end")
            return None
        if not self._inBlock:
            return None

        # Ignora cabeçalho
        if txt.lower().startswith("task"):
            return None

        # Tenta extrair "<name> ... <pct>%"
        parts = re.split(r"\s+", txt)
        if len(parts) < 2:
            return None

        # Percentual normalmente é o último campo e pode vir como "12%" ou "<1%"
        last = parts[-1]
        if not last.endswith("%"):
            return None

        try:
            rawPct = last.rstrip("%")
            if rawPct.startswith("<"):
                # Ex.: "<1%" -> aproxima para metade do limite
                pct = float(rawPct.lstrip("<")) * 0.5
            else:
                pct = float(rawPct)
        except ValueError:
            return None

        taskName = parts[0]
        return [(taskName, pct)]


class Aggregator:
    """Aplica eventos parseados no MetricsStore."""

    def __init__(self, store: MetricsStore) -> None:
        self._store = store

    def applyMonitorKv(self, kv: Dict[str, str], now: float) -> None:
        # heap
        if "heap_free" in kv:
            try:
                v = float(kv["heap_free"])
            except (TypeError, ValueError):
                v = None
            if v is not None:
                self._store.system.heapFreeStats.update(v)
                self._store.system.heapFreeSeries.append(now, v)
        if "heap_min" in kv:
            try:
                v = float(kv["heap_min"])
            except (TypeError, ValueError):
                v = None
            if v is not None:
                self._store.system.heapMinStats.update(v)
                self._store.system.heapMinSeries.append(now, v)

        # stack per task
        task = kv.get("task")
        if task:
            tm = self._store.tasks[task]

            if "stack_total" in kv:
                try:
                    tm.stackTotalStats.update(float(kv["stack_total"]))
                except (TypeError, ValueError):
                    pass
            if "stack_free" in kv:
                try:
                    tm.stackFreeStats.update(float(kv["stack_free"]))
                except (TypeError, ValueError):
                    pass
            if "stack_used" in kv:
                try:
                    used = float(kv["stack_used"])
                except (TypeError, ValueError):
                    used = None
                if used is not None:
                    tm.stackUsedStats.update(used)
                    tm.stackUsedSeries.append(now, used)
            if "stack_usage_pct" in kv:
                try:
                    tm.stackUsagePctStats.update(float(kv["stack_usage_pct"]))
                except (TypeError, ValueError):
                    pass

    def applyHwKv(self, kv: Dict[str, str]) -> None:
        # Armazena último snapshot
        for k, v in kv.items():
            self._store.hwKv[k] = v

    def applyWcetKv(self, kv: Dict[str, str]) -> None:
        name = kv.get("name")
        task = kv.get("task")
        durUs = kv.get("dur_us")
        tsUs = kv.get("ts_us")
        isrStr = kv.get("isr")
        if not name or not task or not durUs:
            return
        try:
            dur = float(durUs)
        except ValueError:
            return
        if (not math.isfinite(dur)) or dur < 0.0:
            return
        try:
            isr = int(isrStr) if isrStr is not None else 0
        except ValueError:
            isr = 0

        key = WcetKey(name=name, task=task, isr=isr)
        wm = self._store.wcet[key]
        wm.durUsStats.update(dur)
        wm.durUsSamples.append(dur)

        nowEpoch = time.time()
        wm.durUsSeries.append(nowEpoch, dur)
        if tsUs is not None:
            try:
                wm.lastTsUs = int(tsUs)
            except ValueError:
                pass

    def applyTraceKv(self, kv: Dict[str, str]) -> None:
        ev = kv.get("ev")
        task = kv.get("task")
        tsUs = kv.get("ts_us")
        if not ev or not task or not tsUs:
            return

        if self._store.trace.timeBase == "host":
            self._store.trace.currentTask = None
            self._store.trace.currentStartRelSec = None
            self._store.trace.startTargetSec = None
            self._store.trace.startHostSec = None
            self._store.trace.lastRelSec = None
            self._store.trace.pendingSwitchOutTask = None
            self._store.trace.pendingSwitchOutReason = None
            self._store.trace.pendingSwitchOutWaitTicks = None
            self._store.trace.pendingSwitchOutRelSec = None
            self._store.scheduling.clear()
            self._store.traceEdges.clear()
            self._store.trace.timeBase = None

        if self._store.trace.timeBase is None:
            self._store.trace.timeBase = "target"

        try:
            ts = float(tsUs) / 1_000_000.0
        except ValueError:
            return

        reasonCode: Optional[int] = None
        waitTicks: Optional[int] = None
        if "reason" in kv:
            try:
                reasonCode = int(kv["reason"], 10)
            except (TypeError, ValueError):
                reasonCode = None
        if "wait_ticks" in kv:
            try:
                waitTicks = int(kv["wait_ticks"], 10)
            except (TypeError, ValueError):
                waitTicks = None

        # Tempo relativo do alvo (ts_us) para padronizar eixo X em segundos.
        if self._store.trace.startTargetSec is None:
            self._store.trace.startTargetSec = ts
        relTs = ts - (self._store.trace.startTargetSec or 0.0)
        if relTs < 0.0:
            # Proteção contra wrap/ruído.
            return
        self._store.trace.lastRelSec = relTs

        # Modelo global: fecha segmento da task atual no switch_out
        if ev == "switch_in":
            prev = self._store.trace.pendingSwitchOutTask
            if prev is not None:
                edge = self._store.traceEdges[(prev, task)]
                edge.count += 1
                edge.lastReason = self._store.trace.pendingSwitchOutReason
                edge.lastWaitTicks = self._store.trace.pendingSwitchOutWaitTicks
                edge.lastRelSec = relTs

                self._store.trace.pendingSwitchOutTask = None
                self._store.trace.pendingSwitchOutReason = None
                self._store.trace.pendingSwitchOutWaitTicks = None
                self._store.trace.pendingSwitchOutRelSec = None

            self._store.trace.currentTask = task
            self._store.trace.currentStartRelSec = relTs
            # garante que task exista na lista
            _ = self._store.tasks[task]
            return

        if ev == "switch_out":
            # Alguns logs podem vir incompletos; se não sabemos o start, ignoramos.
            if self._store.trace.currentTask != task:
                return
            start = self._store.trace.currentStartRelSec
            if start is None:
                return
            if relTs <= start:
                return
            self._store.scheduling[task].segments.append((start, relTs))

            self._store.trace.pendingSwitchOutTask = task
            self._store.trace.pendingSwitchOutReason = reasonCode
            self._store.trace.pendingSwitchOutWaitTicks = waitTicks
            self._store.trace.pendingSwitchOutRelSec = relTs

            self._store.trace.currentTask = None
            self._store.trace.currentStartRelSec = None

    def applyTraceTextSwitch(self, kv: Dict[str, str], nowEpoch: float) -> None:
        if self._store.trace.timeBase == "target":
            return

        if self._store.trace.timeBase is None:
            self._store.trace.timeBase = "host"

        fromTask = kv.get("from")
        toTask = kv.get("to")
        if not fromTask or not toTask:
            return

        if self._store.trace.startHostSec is None:
            self._store.trace.startHostSec = nowEpoch
        relTs = nowEpoch - (self._store.trace.startHostSec or 0.0)
        if relTs < 0.0:
            return
        self._store.trace.lastRelSec = relTs

        if self._store.trace.currentTask == fromTask:
            start = self._store.trace.currentStartRelSec
            if start is not None and relTs > start:
                self._store.scheduling[fromTask].segments.append((start, relTs))

        edge = self._store.traceEdges[(fromTask, toTask)]
        edge.count += 1
        edge.lastReason = None
        edge.lastWaitTicks = None
        edge.lastRelSec = relTs

        _ = self._store.tasks[fromTask]
        _ = self._store.tasks[toTask]
        self._store.trace.currentTask = toTask
        self._store.trace.currentStartRelSec = relTs

    def updateCpuFromTrace(self, nowRelSec: float, windowSeconds: float = 5.0) -> None:
        """Estima CPU% por task somando tempo 'rodando' no trace numa janela.

        Isso funciona mesmo sem vTaskGetRunTimeStats.
        """

        if windowSeconds <= 0.1:
            return

        windowStart = nowRelSec - windowSeconds
        totals: Dict[str, float] = {}
        totalTime = 0.0

        for taskName, sched in self._store.scheduling.items():
            t = 0.0
            for start, end in reversed(sched.segments):
                if end <= windowStart:
                    break
                s = max(start, windowStart)
                e = min(end, nowRelSec)
                if e > s:
                    t += (e - s)
            if t > 0.0:
                totals[taskName] = t
                totalTime += t

        if totalTime <= 0.0:
            return

        for taskName, t in totals.items():
            pct = (t * 100.0) / totalTime
            # Série temporal de CPU continua usando clock do host (epoch) para o plot geral.
            self.applyCpuPct(taskName, pct, time.time())

    def applyCpuPct(self, task: str, pct: float, now: float) -> None:
        if not math.isfinite(pct):
            return
        if pct < 0.0:
            pct = 0.0
        elif pct > 100.0:
            pct = 100.0
        tm = self._store.tasks[task]
        tm.cpuPctStats.update(pct)
        tm.cpuPctSeries.append(now, pct)


# Classes Qt - usam stubs quando Qt não está disponível
# A verificação em main() impede uso real sem Qt
class SerialWorker(QtCore.QObject):
    """Worker para leitura serial em thread separada (Qt)."""

    lineReceived = QtCore.Signal(str)
    statusChanged = QtCore.Signal(str)

    def __init__(self, port: str, baud: int) -> None:
        super().__init__()
        self._port = port
        self._baud = baud
        self._stopEvent = threading.Event()
        self._ser: Optional[serial.Serial] = None

    @QtCore.Slot()
    def run(self) -> None:
        # Retry para o caso do dispositivo ainda não ter aparecido no /dev
        attempt = 0
        while not self._stopEvent.is_set():
            attempt += 1
            try:
                self._ser = serial.Serial(self._port, self._baud, timeout=0.2)
                self.statusChanged.emit(f"Serial aberta: {self._port} @ {self._baud}")
                _LOGGER.info("serial opened port=%s baud=%s", self._port, self._baud)
                break
            except Exception as exc:
                self.statusChanged.emit(
                    f"Falha ao abrir serial (tentativa {attempt}): {exc}"
                )
                _LOGGER.warning("serial open failed attempt=%s err=%s", attempt, exc)
                time.sleep(1.0)

        if self._ser is None:
            self.statusChanged.emit("Serial não disponível (encerrando worker)")
            return

        buf = bytearray()
        while not self._stopEvent.is_set():
            try:
                chunk = self._ser.read(256)
                if chunk:
                    buf.extend(chunk)
                    while b"\n" in buf:
                        raw, _, rest = buf.partition(b"\n")
                        buf = bytearray(rest)
                        line = raw.decode(errors="replace").rstrip("\r")
                        if line:
                            self.lineReceived.emit(line)
            except Exception as exc:
                self.statusChanged.emit(f"Erro leitura serial: {exc}")
                _LOGGER.exception("serial read error: %s", exc)
                break

        try:
            if self._ser is not None:
                self._ser.close()
        except Exception:
            pass
        self.statusChanged.emit("Serial encerrada")

    def stop(self) -> None:
        self._stopEvent.set()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, store: MetricsStore, args: CliArgs) -> None:
        super().__init__()
        self._store = store
        self._args = args
        self._tasksDirty = False
        self._wcetDirty = False

        self._lastHwKvSnapshot: Optional[Tuple[Tuple[str, str], ...]] = None
        self._traceNodeLabels: Dict[str, pg.TextItem] = {}
        self._traceEdgeLabels: Dict[Tuple[str, str], pg.TextItem] = {}

        self.setWindowTitle("RTOS WCET/Stack/Heap Analyzer")
        self.resize(1280, 720)

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)

        layout = QtWidgets.QHBoxLayout(central)

        # Left: tabs
        leftTabs = QtWidgets.QTabWidget()
        leftTabs.setMinimumWidth(320)
        layout.addWidget(leftTabs)

        tasksTab = QtWidgets.QWidget()
        tasksTabLayout = QtWidgets.QVBoxLayout(tasksTab)
        self._taskList = QtWidgets.QListWidget()
        tasksTabLayout.addWidget(self._taskList)
        leftTabs.addTab(tasksTab, "Tasks")

        wcetTab = QtWidgets.QWidget()
        wcetTabLayout = QtWidgets.QVBoxLayout(wcetTab)
        self._wcetList = QtWidgets.QListWidget()
        wcetTabLayout.addWidget(self._wcetList)
        leftTabs.addTab(wcetTab, "Probes")

        # Right: status + tabs de plots (evita que o WCET fique fora da área visível)
        right = QtWidgets.QWidget()
        rightLayout = QtWidgets.QVBoxLayout(right)
        layout.addWidget(right, 1)

        self._status = QtWidgets.QLabel("Pronto")
        rightLayout.addWidget(self._status)

        pg.setConfigOptions(antialias=True)

        rightTabs = QtWidgets.QTabWidget()
        rightLayout.addWidget(rightTabs, 1)

        heapTab = QtWidgets.QWidget()
        heapTabLayout = QtWidgets.QVBoxLayout(heapTab)
        rightTabs.addTab(heapTab, "Heap")

        taskTab = QtWidgets.QWidget()
        taskTabLayout = QtWidgets.QVBoxLayout(taskTab)
        rightTabs.addTab(taskTab, "Task")

        schedTab = QtWidgets.QWidget()
        schedTabLayout = QtWidgets.QVBoxLayout(schedTab)
        rightTabs.addTab(schedTab, "Escalonamento")

        wcetPlotTab = QtWidgets.QWidget()
        wcetPlotTabLayout = QtWidgets.QVBoxLayout(wcetPlotTab)
        rightTabs.addTab(wcetPlotTab, "WCET Plot")

        hwTab = QtWidgets.QWidget()
        hwTabLayout = QtWidgets.QVBoxLayout(hwTab)
        rightTabs.addTab(hwTab, "HwKV")

        traceGraphTab = QtWidgets.QWidget()
        traceGraphTabLayout = QtWidgets.QVBoxLayout(traceGraphTab)
        rightTabs.addTab(traceGraphTab, "Trace Graph")

        # Nova aba: Callgraph (grafo de chamadas de funções)
        callgraphTab = QtWidgets.QWidget()
        callgraphTabLayout = QtWidgets.QVBoxLayout(callgraphTab)
        rightTabs.addTab(callgraphTab, "Callgraph")

        # Controles do callgraph
        callgraphControls = QtWidgets.QHBoxLayout()
        callgraphTabLayout.addLayout(callgraphControls)

        self._callgraphFilterEdit = QtWidgets.QLineEdit()
        self._callgraphFilterEdit.setPlaceholderText("Filtrar funções (regex)...")
        self._callgraphFilterEdit.textChanged.connect(self._onCallgraphFilterChanged)
        callgraphControls.addWidget(QtWidgets.QLabel("Filtro:"))
        callgraphControls.addWidget(self._callgraphFilterEdit)

        self._callgraphTasksOnlyCheck = QtWidgets.QCheckBox("Apenas Tasks")
        self._callgraphTasksOnlyCheck.stateChanged.connect(self._onCallgraphFilterChanged)
        callgraphControls.addWidget(self._callgraphTasksOnlyCheck)

        self._callgraphDepthSpin = QtWidgets.QSpinBox()
        self._callgraphDepthSpin.setRange(1, 10)
        self._callgraphDepthSpin.setValue(3)
        self._callgraphDepthSpin.valueChanged.connect(self._onCallgraphFilterChanged)
        callgraphControls.addWidget(QtWidgets.QLabel("Profundidade:"))
        callgraphControls.addWidget(self._callgraphDepthSpin)

        callgraphControls.addStretch()

        # Plot do callgraph
        self._callgraphPlot = pg.PlotWidget(title="Grafo de Chamadas (análise offline do ELF)")
        self._callgraphPlot.showGrid(x=True, y=True, alpha=0.3)
        self._callgraphPlot.setAspectLocked(True)
        callgraphTabLayout.addWidget(self._callgraphPlot, 1)

        # Itens do grafo serão criados dinamicamente em _refreshCallgraph
        self._callgraphScatter: Optional[pg.ScatterPlotItem] = None
        self._callgraphNodeLabels: Dict[str, pg.TextItem] = {}
        self._callgraphLines: List[Any] = []
        self._callgraphArrows: List[Any] = []
        self._callgraphTooltip: Optional[pg.TextItem] = None
        self._callgraphNodePositions: Dict[str, Tuple[float, float]] = {}
        self._callgraphLastFilter: str = ""
        self._callgraphDirty: bool = True

        # Tabela de funções (McCabe/WCET offline)
        mcCabeTab = QtWidgets.QWidget()
        mcCabeTabLayout = QtWidgets.QVBoxLayout(mcCabeTab)
        rightTabs.addTab(mcCabeTab, "McCabe/WCET")

        self._mcCabeTable = QtWidgets.QTableWidget()
        self._mcCabeTable.setColumnCount(6)
        self._mcCabeTable.setHorizontalHeaderLabels([
            "Função", "McCabe", "Decisões", "Instruções", "Ciclos Est.", "WCET Est. (μs)"
        ])
        self._mcCabeTable.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self._mcCabeTable.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self._mcCabeTable.setSortingEnabled(True)
        try:
            header = self._mcCabeTable.horizontalHeader()
            header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
            for i in range(1, 6):
                header.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        except Exception:
            pass
        mcCabeTabLayout.addWidget(self._mcCabeTable, 1)

        # Resumo do McCabe
        self._mcCabeSummaryLabel = QtWidgets.QLabel("Aguardando análise do ELF...")
        mcCabeTabLayout.addWidget(self._mcCabeSummaryLabel)

        self._heapPlot = pg.PlotWidget(title="Heap (sistema)")
        self._heapPlot.setLabel("bottom", "Time", units="s")
        self._heapPlot.addLegend()
        self._heapPlot.showGrid(x=True, y=True)
        self._heapFreeCurve = self._heapPlot.plot(
            pen=pg.mkPen(color=(0, 180, 0), width=2),
            symbol="o",
            symbolSize=4,
            symbolBrush=pg.mkBrush(0, 180, 0),
            name="heap_free",
        )
        self._heapMinCurve = self._heapPlot.plot(
            pen=pg.mkPen(color=(220, 120, 0), width=2),
            symbol="o",
            symbolSize=4,
            symbolBrush=pg.mkBrush(220, 120, 0),
            name="heap_min",
        )

        self._heapMinLine = pg.InfiniteLine(angle=0, pen=pg.mkPen(color=(220, 120, 0), style=QtCore.Qt.PenStyle.DashLine))
        self._heapMeanLine = pg.InfiniteLine(angle=0, pen=pg.mkPen(color=(0, 180, 0), style=QtCore.Qt.PenStyle.DashLine))
        self._heapMaxLine = pg.InfiniteLine(angle=0, pen=pg.mkPen(color=(0, 120, 0), style=QtCore.Qt.PenStyle.DashLine))
        self._heapPlot.addItem(self._heapMinLine)
        self._heapPlot.addItem(self._heapMeanLine)
        self._heapPlot.addItem(self._heapMaxLine)
        heapTabLayout.addWidget(self._heapPlot, 1)

        self._stackPlot = pg.PlotWidget(title="Stack (task selecionada) - stack_used")
        self._stackPlot.setLabel("bottom", "Time", units="s")
        self._stackPlot.addLegend()
        self._stackPlot.showGrid(x=True, y=True)
        self._stackUsedCurve = self._stackPlot.plot(
            pen=pg.mkPen(color=(0, 120, 255), width=2),
            symbol="o",
            symbolSize=4,
            symbolBrush=pg.mkBrush(0, 120, 255),
            name="stack_used",
        )
        self._stackMinLine = pg.InfiniteLine(angle=0, pen=pg.mkPen(color=(0, 120, 255), style=QtCore.Qt.PenStyle.DashLine))
        self._stackMeanLine = pg.InfiniteLine(angle=0, pen=pg.mkPen(color=(0, 90, 200), style=QtCore.Qt.PenStyle.DashLine))
        self._stackMaxLine = pg.InfiniteLine(angle=0, pen=pg.mkPen(color=(0, 60, 160), style=QtCore.Qt.PenStyle.DashLine))
        self._stackPlot.addItem(self._stackMinLine)
        self._stackPlot.addItem(self._stackMeanLine)
        self._stackPlot.addItem(self._stackMaxLine)
        taskTabLayout.addWidget(self._stackPlot, 1)

        self._cpuPlot = pg.PlotWidget(title="CPU (task selecionada) - %")
        self._cpuPlot.setLabel("bottom", "Time", units="s")
        self._cpuPlot.addLegend()
        self._cpuPlot.showGrid(x=True, y=True)
        self._cpuCurve = self._cpuPlot.plot(
            pen=pg.mkPen(color=(180, 0, 180), width=2),
            symbol="o",
            symbolSize=4,
            symbolBrush=pg.mkBrush(180, 0, 180),
            name="cpu_pct",
        )
        self._cpuPlot.setYRange(0, 100)
        self._cpuMinLine = pg.InfiniteLine(angle=0, pen=pg.mkPen(color=(180, 0, 180), style=QtCore.Qt.PenStyle.DashLine))
        self._cpuMeanLine = pg.InfiniteLine(angle=0, pen=pg.mkPen(color=(140, 0, 140), style=QtCore.Qt.PenStyle.DashLine))
        self._cpuMaxLine = pg.InfiniteLine(angle=0, pen=pg.mkPen(color=(100, 0, 100), style=QtCore.Qt.PenStyle.DashLine))
        self._cpuPlot.addItem(self._cpuMinLine)
        self._cpuPlot.addItem(self._cpuMeanLine)
        self._cpuPlot.addItem(self._cpuMaxLine)
        taskTabLayout.addWidget(self._cpuPlot, 1)

        self._schedPlot = pg.PlotWidget(title="Escalonamento (task selecionada)")
        self._schedPlot.setLabel("bottom", "Time", units="s")
        self._schedPlot.showGrid(x=True, y=True)
        self._schedPlot.setYRange(0, 1)
        self._schedPlot.hideAxis("left")
        self._schedItem = pg.BarGraphItem(x=[], height=[], width=[], y=[], brush=pg.mkBrush(50, 180, 255, 120), pen=pg.mkPen(None))
        self._schedPlot.addItem(self._schedItem)
        schedTabLayout.addWidget(self._schedPlot, 1)

        self._wcetPlot = pg.PlotWidget(title="WCET (probe selecionada) - dur_us")
        self._wcetPlot.setLabel("bottom", "Time", units="s")
        self._wcetPlot.addLegend()
        self._wcetPlot.showGrid(x=True, y=True)
        self._wcetCurve = self._wcetPlot.plot(
            pen=pg.mkPen(color=(255, 80, 80), width=2),
            symbol="o",
            symbolSize=4,
            symbolBrush=pg.mkBrush(255, 80, 80),
            name="dur_us",
        )
        self._wcetMinLine = pg.InfiniteLine(angle=0, pen=pg.mkPen(color=(255, 80, 80), style=QtCore.Qt.PenStyle.DashLine))
        self._wcetMeanLine = pg.InfiniteLine(angle=0, pen=pg.mkPen(color=(200, 60, 60), style=QtCore.Qt.PenStyle.DashLine))
        self._wcetMaxLine = pg.InfiniteLine(angle=0, pen=pg.mkPen(color=(160, 40, 40), style=QtCore.Qt.PenStyle.DashLine))
        self._wcetPlot.addItem(self._wcetMinLine)
        self._wcetPlot.addItem(self._wcetMeanLine)
        self._wcetPlot.addItem(self._wcetMaxLine)
        wcetPlotTabLayout.addWidget(self._wcetPlot, 1)

        self._hwTable = QtWidgets.QTableWidget()
        self._hwTable.setColumnCount(2)
        self._hwTable.setHorizontalHeaderLabels(["Key", "Value"])
        self._hwTable.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self._hwTable.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        try:
            header = self._hwTable.horizontalHeader()
            header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        except Exception:
            pass
        hwTabLayout.addWidget(self._hwTable, 1)

        self._traceGraphPlot = pg.PlotWidget(title="Transições de tasks (trace)")
        self._traceGraphPlot.showGrid(x=False, y=False)
        self._traceGraphPlot.hideAxis("left")
        self._traceGraphPlot.hideAxis("bottom")
        self._traceGraphPlot.setAspectLocked(True)
        traceGraphTabLayout.addWidget(self._traceGraphPlot, 1)

        self._traceGraphItem = pg.GraphItem()
        self._traceGraphPlot.addItem(self._traceGraphItem)

        self._taskList.currentTextChanged.connect(self._onTaskChanged)
        self._wcetList.currentTextChanged.connect(self._onWcetChanged)

        self._refreshTimer = QtCore.QTimer(self)
        self._refreshTimer.timeout.connect(self._refreshPlots)
        self._refreshTimer.start(500)

    @QtCore.Slot(str)
    def setStatus(self, text: str) -> None:
        self._status.setText(text)

    def _onTaskChanged(self, taskName: str) -> None:
        self._refreshPlots()

    def _onWcetChanged(self, wcetKeyText: str) -> None:
        self._refreshPlots()

    def _refreshPlots(self) -> None:
        now = time.time()

        # heap
        hx, hy = self._store.system.heapFreeSeries.toNumpyArrays()
        mx, my = self._store.system.heapMinSeries.toNumpyArrays()
        self._heapFreeCurve.setData(x=hx, y=hy)
        self._heapMinCurve.setData(x=mx, y=my)
        self._heapPlot.enableAutoRange(axis=pg.ViewBox.YAxis, enable=True)

        # overlays (heap_free stats)
        hf = self._store.system.heapFreeStats
        if hf.minValue is not None:
            self._heapMinLine.setValue(hf.minValue)
        if hf.maxValue is not None:
            self._heapMaxLine.setValue(hf.maxValue)
        if hf.count > 0:
            self._heapMeanLine.setValue(hf.mean)
        if len(hx) > 0:
            self._setXWindow(self._heapPlot, hx, window=120.0, minSpan=2.0)

        # selected task
        task = self._taskList.currentItem().text() if self._taskList.currentItem() else None
        if task and task in self._store.tasks:
            tm = self._store.tasks[task]
            sx, sy = tm.stackUsedSeries.toNumpyArrays()
            cx, cy = tm.cpuPctSeries.toNumpyArrays()
            self._stackUsedCurve.setData(x=sx, y=sy)
            self._cpuCurve.setData(x=cx, y=cy)
            self._stackPlot.enableAutoRange(axis=pg.ViewBox.YAxis, enable=True)

            if tm.stackUsedStats.minValue is not None:
                self._stackMinLine.setValue(tm.stackUsedStats.minValue)
            if tm.stackUsedStats.maxValue is not None:
                self._stackMaxLine.setValue(tm.stackUsedStats.maxValue)
            if tm.stackUsedStats.count > 0:
                self._stackMeanLine.setValue(tm.stackUsedStats.mean)

            if tm.cpuPctStats.minValue is not None:
                self._cpuMinLine.setValue(tm.cpuPctStats.minValue)
            if tm.cpuPctStats.maxValue is not None:
                self._cpuMaxLine.setValue(tm.cpuPctStats.maxValue)
            if tm.cpuPctStats.count > 0:
                self._cpuMeanLine.setValue(tm.cpuPctStats.mean)

            if len(sx) > 0:
                self._setXWindow(self._stackPlot, sx, window=120.0, minSpan=2.0)
            if len(cx) > 0:
                self._setXWindow(self._cpuPlot, cx, window=120.0, minSpan=2.0)

            # scheduling timeline (últimos 10s)
            segments = self._store.scheduling[task].segments
            nowRel = self._store.trace.lastRelSec
            if nowRel is None:
                self._schedItem.setOpts(x=[], height=[], width=[], y=[])
                self._schedPlot.setXRange(0.0, 1.0)
            else:
                windowStart = max(0.0, nowRel - 10.0)
                xs: List[float] = []
                widths: List[float] = []
                # Itera do mais recente para o mais antigo e para cedo quando sair da janela.
                # Isso evita travar quando houver muitos segmentos no deque.
                for start, end in reversed(segments):
                    if end < windowStart:
                        break
                    s = max(start, windowStart)
                    e = end
                    if e <= s:
                        continue
                    width = max(0.0001, e - s)
                    xs.append(s + width / 2.0)
                    widths.append(width)
                    if len(xs) >= 2000:
                        break
                xs.reverse()
                widths.reverse()
                if xs:
                    n = len(xs)
                    self._schedItem.setOpts(
                        x=xs,
                        height=[1.0] * n,
                        width=widths,
                        y=[0.0] * n,
                    )
                else:
                    self._schedItem.setOpts(x=[], height=[], width=[], y=[])

                right = max(windowStart + 0.1, nowRel)
                self._schedPlot.setXRange(windowStart, right)
        else:
            self._stackUsedCurve.setData(x=[], y=[])
            self._cpuCurve.setData(x=[], y=[])
            self._schedItem.setOpts(x=[], height=[], width=[], y=[])

        wcetSel = self._wcetList.currentItem().text() if self._wcetList.currentItem() else None
        if wcetSel:
            # text format: name|task|isr
            parts = wcetSel.split("|")
            if len(parts) == 3:
                name, taskName, isrStr = parts
                try:
                    isr = int(isrStr)
                except ValueError:
                    isr = 0
                key = WcetKey(name=name, task=taskName, isr=isr)
                if key in self._store.wcet:
                    wm = self._store.wcet[key]
                    wx, wy = wm.durUsSeries.toNumpyArrays()
                    self._wcetCurve.setData(x=wx, y=wy)
                    self._wcetPlot.enableAutoRange(axis=pg.ViewBox.YAxis, enable=True)
                    if wm.durUsStats.minValue is not None:
                        self._wcetMinLine.setValue(wm.durUsStats.minValue)
                    if wm.durUsStats.maxValue is not None:
                        self._wcetMaxLine.setValue(wm.durUsStats.maxValue)
                    if wm.durUsStats.count > 0:
                        self._wcetMeanLine.setValue(wm.durUsStats.mean)
                    if len(wx) > 0:
                        self._setXWindow(self._wcetPlot, wx, window=120.0, minSpan=2.0)
                else:
                    self._wcetCurve.setData(x=[], y=[])
        else:
            self._wcetCurve.setData(x=[], y=[])

        self._refreshHwKvTable()
        self._refreshTraceGraph()

        if self._tasksDirty:
            self.refreshTaskList()
            self._tasksDirty = False
        if self._wcetDirty:
            self.refreshWcetList()
            self._wcetDirty = False

    def _setXWindow(self, plot: pg.PlotWidget, xs: List[float], window: float, minSpan: float) -> None:
        if len(xs) <= 0:
            return
        right = float(xs[-1])
        left = float(max(right - window, float(xs[0]), 0.0))
        if right - left < minSpan:
            right = left + float(minSpan)
        plot.setXRange(left, right)

    def refreshTaskList(self) -> None:
        current = self._taskList.currentItem().text() if self._taskList.currentItem() else None
        self._taskList.blockSignals(True)

        existing: set[str] = set()
        for i in range(self._taskList.count()):
            existing.add(self._taskList.item(i).text())

        # Só adiciona novos itens (não limpa a lista a cada linha recebida).
        for name in self._store.listTasks():
            if name not in existing:
                self._taskList.addItem(name)

        self._taskList.blockSignals(False)

        if current:
            items = self._taskList.findItems(current, QtCore.Qt.MatchFlag.MatchExactly)
            if items:
                self._taskList.setCurrentItem(items[0])
        else:
            if self._taskList.count() > 0:
                self._taskList.setCurrentRow(0)

    def refreshWcetList(self) -> None:
        current = self._wcetList.currentItem().text() if self._wcetList.currentItem() else None
        self._wcetList.blockSignals(True)

        existing: set[str] = set()
        for i in range(self._wcetList.count()):
            existing.add(self._wcetList.item(i).text())

        for key in self._store.listWcetKeys():
            txt = f"{key.name}|{key.task}|{key.isr}"
            if txt not in existing:
                self._wcetList.addItem(txt)

        self._wcetList.blockSignals(False)

        if current:
            items = self._wcetList.findItems(current, QtCore.Qt.MatchFlag.MatchExactly)
            if items:
                self._wcetList.setCurrentItem(items[0])
        else:
            if self._wcetList.count() > 0:
                self._wcetList.setCurrentRow(0)

    def _refreshHwKvTable(self) -> None:
        if not hasattr(self, "_hwTable"):
            return

        items = tuple((k, self._store.hwKv.get(k, "")) for k in sorted(self._store.hwKv.keys()))
        if items == (self._lastHwKvSnapshot or ()):
            return

        self._lastHwKvSnapshot = items
        self._hwTable.setRowCount(len(items))
        for row, (k, v) in enumerate(items):
            self._hwTable.setItem(row, 0, QtWidgets.QTableWidgetItem(str(k)))
            self._hwTable.setItem(row, 1, QtWidgets.QTableWidgetItem(str(v)))

    def _taskRunDurationBetweenPreemptionsSec(self, taskName: str) -> Optional[float]:
        nowRel = self._store.trace.lastRelSec
        if taskName == self._store.trace.currentTask:
            start = self._store.trace.currentStartRelSec
            if start is not None and nowRel is not None and nowRel >= start:
                return float(nowRel - start)

        segs = self._store.scheduling[taskName].segments
        if not segs:
            return None

        start, end = segs[-1]
        if end <= start:
            return None
        return float(end - start)

    def _formatTaskNodeLabel(self, taskName: str) -> str:
        dur = self._taskRunDurationBetweenPreemptionsSec(taskName)
        if dur is None:
            durTxt = "-"
        elif dur < 1.0:
            durTxt = f"{dur * 1000.0:.2f} ms"
        else:
            durTxt = f"{dur:.3f} s"
        return f"{taskName}\n{durTxt}"

    def _refreshTraceGraph(self, windowSeconds: float = 10.0) -> None:
        if not hasattr(self, "_traceGraphPlot"):
            return

        tasks = self._store.listTasks()
        if not tasks:
            # Não chama setData quando não há dados - apenas limpa os itens visuais
            for it in list(self._traceNodeLabels.values()):
                try:
                    self._traceGraphPlot.removeItem(it)
                except Exception:
                    pass
            for it in list(self._traceEdgeLabels.values()):
                try:
                    self._traceGraphPlot.removeItem(it)
                except Exception:
                    pass
            self._traceNodeLabels.clear()
            self._traceEdgeLabels.clear()
            return

        n = len(tasks)
        radius = max(1.0, float(n) * 0.9)
        pos = np.empty((n, 2), dtype=float)
        for i, name in enumerate(tasks):
            a = (2.0 * math.pi * float(i)) / float(n)
            pos[i, 0] = math.cos(a) * radius
            pos[i, 1] = math.sin(a) * radius

        idxByName: Dict[str, int] = {name: i for i, name in enumerate(tasks)}

        nowRel = self._store.trace.lastRelSec
        edgeKeys: List[Tuple[str, str]] = []
        adjs: List[Tuple[int, int]] = []
        for (src, dst), info in self._store.traceEdges.items():
            if src not in idxByName or dst not in idxByName:
                continue
            if (
                nowRel is not None
                and windowSeconds > 0.0
                and info.lastRelSec is not None
                and (nowRel - info.lastRelSec) > windowSeconds
            ):
                continue
            edgeKeys.append((src, dst))
            adjs.append((idxByName[src], idxByName[dst]))

        # Garante shape correto (M, 2) para o array de adjacências
        if adjs:
            adj = np.array(adjs, dtype=int).reshape(-1, 2)
        else:
            adj = None  # None evita IndexError no pyqtgraph

        brushes: List[object] = []
        for name in tasks:
            if name == self._store.trace.currentTask:
                brushes.append(pg.mkBrush(80, 160, 255, 220))
            else:
                brushes.append(pg.mkBrush(220, 220, 220, 180))

        # Cores mais claras para modo escuro
        # Monta kwargs para setData - adj é opcional
        graphKwargs = {
            "pos": pos,
            "size": [34] * n,
            "symbol": "o",
            "pxMode": True,
            "brush": brushes,
            "pen": pg.mkPen(150, 150, 150, 220),
            "symbolPen": pg.mkPen(200, 200, 200, 200),
        }
        if adj is not None:
            graphKwargs["adj"] = adj
        
        try:
            self._traceGraphItem.setData(**graphKwargs)
        except Exception as exc:
            _LOGGER.debug("Erro ao configurar traceGraph: %s", exc)

        pad = radius * 0.6
        self._traceGraphPlot.setXRange(-radius - pad, radius + pad)
        self._traceGraphPlot.setYRange(-radius - pad, radius + pad)

        for name in tasks:
            i = idxByName[name]
            x = float(pos[i, 0])
            y = float(pos[i, 1])
            label = self._traceNodeLabels.get(name)
            if label is None:
                # Cor clara para visibilidade em modo escuro
                label = pg.TextItem(anchor=(0.5, 0.5), color=(220, 220, 220))
                self._traceNodeLabels[name] = label
                self._traceGraphPlot.addItem(label)
            label.setPos(x, y)
            label.setText(self._formatTaskNodeLabel(name))

        for name in list(self._traceNodeLabels.keys()):
            if name not in idxByName:
                it = self._traceNodeLabels.pop(name)
                try:
                    self._traceGraphPlot.removeItem(it)
                except Exception:
                    pass

        activeEdgeSet = set(edgeKeys)
        for (src, dst) in edgeKeys:
            info = self._store.traceEdges.get((src, dst))
            if info is None:
                continue
            si = idxByName[src]
            di = idxByName[dst]
            mx = (float(pos[si, 0]) + float(pos[di, 0])) / 2.0
            my = (float(pos[si, 1]) + float(pos[di, 1])) / 2.0

            label = self._traceEdgeLabels.get((src, dst))
            if label is None:
                label = pg.TextItem(anchor=(0.5, 0.5), color=(120, 0, 0))
                self._traceEdgeLabels[(src, dst)] = label
                self._traceGraphPlot.addItem(label)
            label.setPos(mx, my)
            reasonTxt = _formatTraceReason(info.lastReason, info.lastWaitTicks)
            if info.count > 1:
                label.setText(f"{reasonTxt} x{info.count}")
            else:
                label.setText(reasonTxt)

        for key in list(self._traceEdgeLabels.keys()):
            if key not in activeEdgeSet:
                it = self._traceEdgeLabels.pop(key)
                try:
                    self._traceGraphPlot.removeItem(it)
                except Exception:
                    pass

    @QtCore.Slot()
    def _onCallgraphFilterChanged(self) -> None:
        """Chamado quando o filtro do callgraph muda."""
        self._callgraphDirty = True
        self._refreshCallgraph()

    def _refreshCallgraph(self) -> None:
        """Atualiza o grafo de chamadas baseado nos dados offline do ELF."""
        if not hasattr(self, "_callgraphPlot"):
            return

        # Limpa o plot completamente
        self._callgraphPlot.clear()
        self._callgraphLines.clear()
        self._callgraphNodeLabels.clear()
        self._callgraphScatter = None

        callGraph = self._store.callGraph
        if callGraph is None or not callGraph.functions:
            return

        # Aplica filtros
        filterText = self._callgraphFilterEdit.text().strip()
        tasksOnly = self._callgraphTasksOnlyCheck.isChecked()

        filteredFuncs: List[str] = []
        filterRe = None
        if filterText:
            try:
                filterRe = re.compile(filterText, re.IGNORECASE)
            except re.error:
                filterRe = None

        for name, info in callGraph.functions.items():
            if tasksOnly and not info.isTask:
                continue
            if filterRe and not filterRe.search(name):
                continue
            filteredFuncs.append(name)

        # Limita quantidade para performance
        if len(filteredFuncs) > 80:
            filteredFuncs.sort(key=lambda n: (
                not callGraph.functions[n].isTask,
                -callGraph.functions[n].mccabe,
            ))
            filteredFuncs = filteredFuncs[:80]

        if not filteredFuncs:
            return

        n = len(filteredFuncs)
        idxByName: Dict[str, int] = {name: i for i, name in enumerate(filteredFuncs)}

        # Filtra arestas
        adjs: List[Tuple[int, int]] = []
        for caller, callee in callGraph.edges:
            if caller in idxByName and callee in idxByName:
                adjs.append((idxByName[caller], idxByName[callee]))

        # Layout circular como base - mais confiável para distribuição
        radius = max(100.0, float(n) * 5.0)
        self._nodePositions = np.empty((n, 2), dtype=float)
        
        for i in range(n):
            angle = (2.0 * math.pi * float(i)) / float(n)
            self._nodePositions[i, 0] = math.cos(angle) * radius
            self._nodePositions[i, 1] = math.sin(angle) * radius
        
        # Aplica força leve para ajustar posições baseado em conexões
        if len(adjs) > 0:
            temp_pos = self._calculateForceDirectedLayout(
                filteredFuncs, adjs,
                iterations=50,  # Menos iterações para manter forma circular
                k=2.0,
                cooling=0.95
            )
            # Mistura 70% circular + 30% force-directed
            self._nodePositions = 0.7 * self._nodePositions + 0.3 * temp_pos

        # Armazena dados para redesenho interativo
        self._graphNodes = filteredFuncs
        self._graphEdges = adjs
        self._graphIdxByName = idxByName
        
        # Cores por tipo
        self._nodeBrushes: List[object] = []
        for name in filteredFuncs:
            info = callGraph.functions.get(name)
            if info and info.isTask:
                self._nodeBrushes.append(pg.mkBrush(80, 160, 255, 220))
            elif info and info.mccabe > 10:
                self._nodeBrushes.append(pg.mkBrush(255, 100, 100, 200))
            elif info and info.mccabe > 5:
                self._nodeBrushes.append(pg.mkBrush(255, 180, 100, 200))
            else:
                self._nodeBrushes.append(pg.mkBrush(150, 150, 150, 180))

        # Desenha o grafo
        self._drawCallgraph()
        
        # Define range explícito baseado no raio
        range_size = radius * 1.2
        self._callgraphPlot.setXRange(-range_size, range_size, padding=0)
        self._callgraphPlot.setYRange(-range_size, range_size, padding=0)
        print(f"[DEBUG] Layout: {n} nós, raio={radius:.1f}, range=±{range_size:.1f}")

    def _drawCallgraph(self) -> None:
        """Desenha/redesenha o grafo com as posições atuais."""
        if not hasattr(self, "_nodePositions") or self._nodePositions is None:
            return
        if not hasattr(self, "_graphEdges"):
            return
        
        pos = self._nodePositions
        n = len(pos)
        edges = self._graphEdges
        
        # Limpa itens anteriores
        self._callgraphPlot.clear()
        
        # Desenha edges primeiro (ficam atrás dos nós)
        # Cor branca sólida para máxima visibilidade em modo escuro
        linePen = pg.mkPen(color=(255, 255, 255, 255), width=2)
        edgeCount = 0
        maxEdges = min(len(edges), 200)
        for srcIdx, dstIdx in edges[:maxEdges]:
            if srcIdx < n and dstIdx < n:
                x1, y1 = float(pos[srcIdx, 0]), float(pos[srcIdx, 1])
                x2, y2 = float(pos[dstIdx, 0]), float(pos[dstIdx, 1])
                lineItem = self._callgraphPlot.plot([x1, x2], [y1, y2], pen=linePen)
                edgeCount += 1
        
        # Desenha nós por cima das edges
        xData = pos[:, 0].tolist()
        yData = pos[:, 1].tolist()
        
        # Prepara dados para tooltips
        nodeData = []
        callGraph = self._store.callGraph
        for name in self._graphNodes:
            info = callGraph.functions.get(name)
            if info:
                nodeData.append({
                    'name': name,
                    'mccabe': info.mccabe,
                    'wcet': info.estimatedTimeUs,
                    'instructions': info.instructionCount,
                    'stack': info.stackUsage if info.stackUsage else 0
                })
            else:
                nodeData.append({'name': name})
        
        self._callgraphScatter = pg.ScatterPlotItem(
            x=xData,
            y=yData,
            size=20,
            pen=pg.mkPen(color=(255, 255, 255), width=2),
            brush=self._nodeBrushes,
            symbol='o',
            data=nodeData,
            hoverable=True,
            hoverSize=25
        )
        self._callgraphPlot.addItem(self._callgraphScatter)
        
        # Adiciona labels com nomes das funções
        for i, name in enumerate(self._graphNodes):
            if i < n:
                info = callGraph.functions.get(name)
                if info:
                    # Mostra apenas nome abreviado para não poluir
                    shortName = name.split('::')[-1][:15]
                    label = pg.TextItem(
                        text=f"{shortName}\n{info.mccabe}/{info.estimatedTimeUs:.0f}μs",
                        anchor=(0.5, 0.5),
                        color=(255, 255, 255, 200)
                    )
                    label.setPos(pos[i, 0], pos[i, 1])
                    self._callgraphPlot.addItem(label)
        
        # Conecta eventos
        self._callgraphScatter.sigClicked.connect(self._onNodeClicked)
        self._callgraphScatter.sigHovered.connect(self._onNodeHovered)
        
    def _onNodeClicked(self, plot, points) -> None:
        """Callback quando um nó é clicado."""
        if len(points) == 0:
            return
        point = points[0]
        idx = point.index()
        if idx is not None and idx < len(self._graphNodes):
            name = self._graphNodes[idx]
            print(f"[DEBUG] Nó clicado: {name} (idx={idx})")
    
    def _onNodeHovered(self, plot, points, ev=None) -> None:
        """Callback quando o mouse passa sobre um nó."""
        callGraph = self._store.callGraph
        if callGraph is None:
            return
        
        # Remove tooltip anterior
        if self._callgraphTooltip is not None:
            try:
                self._callgraphPlot.removeItem(self._callgraphTooltip)
            except Exception:
                pass
            self._callgraphTooltip = None
        
        if len(points) == 0:
            return
        
        # Pega dados do nó
        point = points[0]
        nodeData = point.data()
        if nodeData is None or not isinstance(nodeData, dict):
            return
        
        name = nodeData.get('name')
        if not name:
            return
        
        # Cria texto do tooltip
        info = callGraph.functions.get(name)
        if info:
            tooltipText = f"{name}\n"
            tooltipText += f"McCabe: {info.mccabe}\n"
            tooltipText += f"WCET: {info.estimatedTimeUs:.1f}μs\n"
            tooltipText += f"Instructions: {info.instructionCount}\n"
            if info.stackUsage:
                tooltipText += f"Stack: {info.stackUsage} bytes"
        else:
            tooltipText = name
        
        # Posiciona tooltip
        pos = point.pos()
        self._callgraphTooltip = pg.TextItem(
            text=tooltipText,
            anchor=(0, 1),
            color=(255, 255, 200),
            fill=pg.mkBrush(40, 40, 40, 220),
            border=pg.mkPen(150, 150, 150, 200),
        )
        self._callgraphTooltip.setPos(pos.x() + 0.5, pos.y() + 0.5)
        self._callgraphPlot.addItem(self._callgraphTooltip)

    def _updateCallgraphArrows(
        self,
        pos: np.ndarray,
        adjs: List[Tuple[int, int]],
        names: List[str],
        idxByName: Dict[str, int]
    ) -> None:
        """Atualiza as setas que indicam a direção das arestas do grafo."""
        # Remove setas antigas
        for arrow in self._callgraphArrows:
            try:
                self._callgraphPlot.removeItem(arrow)
            except Exception:
                pass
        self._callgraphArrows.clear()

        if len(pos) == 0 or not adjs:
            return

        # Limita número de setas para performance
        maxArrows = min(len(adjs), 150)

        for i, (srcIdx, dstIdx) in enumerate(adjs[:maxArrows]):
            if srcIdx >= len(pos) or dstIdx >= len(pos):
                continue

            x1, y1 = float(pos[srcIdx, 0]), float(pos[srcIdx, 1])
            x2, y2 = float(pos[dstIdx, 0]), float(pos[dstIdx, 1])

            # Calcula direção e ponto da seta (próximo ao destino)
            dx, dy = x2 - x1, y2 - y1
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < 0.1:
                continue

            # Posiciona a seta a 70% do caminho (antes do nó destino)
            ratio = 0.7
            ax = x1 + dx * ratio
            ay = y1 + dy * ratio

            # Ângulo da seta
            angle = math.degrees(math.atan2(dy, dx))

            try:
                # Cor clara para setas visíveis em modo escuro
                arrow = pg.ArrowItem(
                    pos=(ax, ay),
                    angle=180 - angle,  # Inverte para apontar na direção correta
                    tipAngle=25,
                    headLen=10,
                    tailLen=0,
                    tailWidth=0,
                    pen=pg.mkPen(color=(180, 180, 180, 220), width=1),
                    brush=pg.mkBrush(180, 180, 180, 220),
                )
                self._callgraphPlot.addItem(arrow)
                self._callgraphArrows.append(arrow)
            except Exception:
                pass  # ArrowItem pode não estar disponível em algumas versões

    def _onCallgraphNodeHovered(self, plot, points, ev) -> None:
        """Callback quando o mouse passa sobre um nó do callgraph."""
        callGraph = self._store.callGraph
        if callGraph is None:
            return
        
        # Remove tooltip anterior
        if self._callgraphTooltip is not None:
            try:
                self._callgraphPlot.removeItem(self._callgraphTooltip)
            except Exception:
                pass
            self._callgraphTooltip = None
        
        if len(points) == 0:
            return
        
        # Pega o primeiro ponto sob o mouse
        point = points[0]
        funcName = point.data()
        if funcName is None:
            return
        
        # Obtém informações da função
        funcInfo = callGraph.functions.get(funcName)
        if funcInfo is None:
            return
        
        # Cria tooltip com informações da função
        tooltipText = self._buildFunctionTooltip(funcInfo)
        if not tooltipText:
            return
        
        # Posiciona tooltip próximo ao nó
        pos = point.pos()
        self._callgraphTooltip = pg.TextItem(
            text=tooltipText,
            anchor=(0, 1),
            color=(255, 255, 200),
            fill=pg.mkBrush(40, 40, 40, 220),
            border=pg.mkPen(150, 150, 150, 200),
        )
        self._callgraphTooltip.setPos(pos.x() + 0.5, pos.y() + 0.5)
        self._callgraphPlot.addItem(self._callgraphTooltip)

    def _calculateCircularLayout(self, names: List[str]) -> np.ndarray:
        """Layout circular simples."""
        n = len(names)
        if n == 0:
            return np.empty((0, 2), dtype=float)
        radius = max(5.0, float(n) * 0.8)
        pos = np.empty((n, 2), dtype=float)
        for i in range(n):
            a = (2.0 * math.pi * float(i)) / float(n)
            pos[i, 0] = math.cos(a) * radius
            pos[i, 1] = math.sin(a) * radius
        return pos

    def _calculateForceDirectedLayout(
        self,
        names: List[str],
        edges: List[Tuple[int, int]],
        iterations: int = 100,
        k: float = 1.0,
        cooling: float = 0.95,
    ) -> np.ndarray:
        """
        Algoritmo Force-Directed (Fruchterman-Reingold) para layout de grafo.
        
        Args:
            names: Lista de nomes dos nós
            edges: Lista de tuplas (src_idx, dst_idx) representando arestas
            iterations: Número de iterações do algoritmo
            k: Distância ideal entre nós (fator de escala)
            cooling: Fator de resfriamento para convergência
        
        Returns:
            Array numpy (N, 2) com posições dos nós
        """
        n = len(names)
        if n == 0:
            return np.empty((0, 2), dtype=float)
        if n == 1:
            return np.array([[0.0, 0.0]], dtype=float)
        
        # Inicialização: distribui nós em grid para melhor espalhamento inicial
        np.random.seed(42)
        gridSize = int(math.ceil(math.sqrt(n)))
        spacing = 50.0  # Espaçamento maior entre nós
        pos = np.empty((n, 2), dtype=float)
        
        for i in range(n):
            row = i // gridSize
            col = i % gridSize
            # Adiciona aleatoriedade para quebrar simetria
            pos[i, 0] = (col - gridSize/2) * spacing + np.random.uniform(-5, 5)
            pos[i, 1] = (row - gridSize/2) * spacing + np.random.uniform(-5, 5)
        
        # Área do layout - maior para melhor distribuição
        area = float(n) * 100.0  # Aumentado de 10 para 100
        k_opt = k * math.sqrt(area / n)  # Distância ideal
        
        # Temperatura inicial (controla movimento máximo)
        temp = math.sqrt(area) * 0.5
        
        # Constrói matriz de adjacência para acesso rápido
        adjSet = set()
        for src, dst in edges:
            adjSet.add((src, dst))
            adjSet.add((dst, src))  # Considera como não-direcionado para layout
        
        for iteration in range(iterations):
            # Calcula forças de repulsão (todos os pares)
            displacement = np.zeros((n, 2), dtype=float)
            
            for i in range(n):
                for j in range(i + 1, n):
                    dx = pos[i, 0] - pos[j, 0]
                    dy = pos[i, 1] - pos[j, 1]
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist < 0.01:
                        dist = 0.01
                        dx = np.random.uniform(-0.1, 0.1)
                        dy = np.random.uniform(-0.1, 0.1)
                    
                    # Força de repulsão: k^2 / d
                    repForce = (k_opt * k_opt) / dist
                    fx = (dx / dist) * repForce
                    fy = (dy / dist) * repForce
                    
                    displacement[i, 0] += fx
                    displacement[i, 1] += fy
                    displacement[j, 0] -= fx
                    displacement[j, 1] -= fy
            
            # Calcula forças de atração (apenas arestas conectadas)
            for src, dst in edges:
                if src >= n or dst >= n:
                    continue
                dx = pos[src, 0] - pos[dst, 0]
                dy = pos[src, 1] - pos[dst, 1]
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < 0.01:
                    continue
                
                # Força de atração: d^2 / k
                attForce = (dist * dist) / k_opt
                fx = (dx / dist) * attForce
                fy = (dy / dist) * attForce
                
                displacement[src, 0] -= fx
                displacement[src, 1] -= fy
                displacement[dst, 0] += fx
                displacement[dst, 1] += fy
            
            # Aplica deslocamento limitado pela temperatura
            for i in range(n):
                dispLen = math.sqrt(
                    displacement[i, 0] ** 2 + displacement[i, 1] ** 2
                )
                if dispLen > 0.01:
                    scale = min(dispLen, temp) / dispLen
                    pos[i, 0] += displacement[i, 0] * scale
                    pos[i, 1] += displacement[i, 1] * scale
            
            # Resfriamento
            temp *= cooling
        
        # Centraliza o layout
        centerX = np.mean(pos[:, 0])
        centerY = np.mean(pos[:, 1])
        pos[:, 0] -= centerX
        pos[:, 1] -= centerY
        
        # Escala para visualização adequada - MAIOR escala para melhor distribuição
        maxDist = np.max(np.sqrt(pos[:, 0] ** 2 + pos[:, 1] ** 2))
        if maxDist > 0.1:
            # Aumenta drasticamente o fator de escala para espalhar os nós
            scaleFactor = max(50.0, float(n) * 2.0) / maxDist
            pos *= scaleFactor
        
        return pos

    def _calculateNetworkxLayout(self, names: List[str], callGraph: CallGraphData) -> np.ndarray:
        """Layout usando networkx para melhor visualização."""
        # Constrói lista de arestas como índices
        idxByName = {name: i for i, name in enumerate(names)}
        edges: List[Tuple[int, int]] = []
        for caller, callee in callGraph.edges:
            if caller in idxByName and callee in idxByName:
                edges.append((idxByName[caller], idxByName[callee]))
        
        # Usa algoritmo force-directed próprio (mais confiável)
        if len(names) <= 150:
            return self._calculateForceDirectedLayout(
                names, edges,
                iterations=80 if len(names) < 50 else 50,
                k=1.2,
                cooling=0.92
            )
        
        # Para grafos muito grandes, usa networkx se disponível
        if _HAS_NETWORKX:
            G = nx.DiGraph()
            for name in names:
                G.add_node(name)
            for caller, callee in callGraph.edges:
                if caller in idxByName and callee in idxByName:
                    G.add_edge(caller, callee)
            
            try:
                layout = nx.kamada_kawai_layout(G)
                pos = np.empty((len(names), 2), dtype=float)
                for i, name in enumerate(names):
                    if name in layout:
                        pos[i, 0] = layout[name][0] * 15.0
                        pos[i, 1] = layout[name][1] * 15.0
                    else:
                        pos[i, 0] = 0.0
                        pos[i, 1] = 0.0
                return pos
            except Exception:
                pass
        
        # Fallback: layout circular
        return self._calculateCircularLayout(names)

    def _formatCallgraphNodeLabel(self, name: str, callGraph: CallGraphData) -> str:
        """Formata label do nó com informações relevantes."""
        info = callGraph.functions.get(name)
        if info is None:
            return name

        # Nome abreviado se muito longo
        displayName = name if len(name) <= 20 else name[:17] + "..."

        lines = [displayName]
        lines.append(f"M:{info.mccabe} T:{info.estimatedTimeUs:.1f}μs")
        if info.isTask:
            lines.append("[TASK]")
        return "\n".join(lines)

    def refreshMcCabeTable(self) -> None:
        """Atualiza a tabela de McCabe/WCET offline."""
        if not hasattr(self, "_mcCabeTable"):
            return

        callGraph = self._store.callGraph
        if callGraph is None or not callGraph.functions:
            self._mcCabeTable.setRowCount(0)
            self._mcCabeSummaryLabel.setText("Nenhum dado de análise offline disponível.")
            return

        # Ordena por complexidade
        funcs = sorted(
            callGraph.functions.values(),
            key=lambda f: (f.mccabe, f.instructionCount),
            reverse=True
        )

        self._mcCabeTable.setSortingEnabled(False)
        self._mcCabeTable.setRowCount(len(funcs))

        for row, info in enumerate(funcs):
            self._mcCabeTable.setItem(row, 0, QtWidgets.QTableWidgetItem(info.name))

            mccabeItem = QtWidgets.QTableWidgetItem()
            mccabeItem.setData(QtCore.Qt.ItemDataRole.DisplayRole, info.mccabe)
            self._mcCabeTable.setItem(row, 1, mccabeItem)

            decItem = QtWidgets.QTableWidgetItem()
            decItem.setData(QtCore.Qt.ItemDataRole.DisplayRole, info.decisionCount)
            self._mcCabeTable.setItem(row, 2, decItem)

            insItem = QtWidgets.QTableWidgetItem()
            insItem.setData(QtCore.Qt.ItemDataRole.DisplayRole, info.instructionCount)
            self._mcCabeTable.setItem(row, 3, insItem)

            cyclesItem = QtWidgets.QTableWidgetItem()
            cyclesItem.setData(QtCore.Qt.ItemDataRole.DisplayRole, info.estimatedCycles)
            self._mcCabeTable.setItem(row, 4, cyclesItem)

            wcetItem = QtWidgets.QTableWidgetItem()
            wcetItem.setData(QtCore.Qt.ItemDataRole.DisplayRole, round(info.estimatedTimeUs, 2))
            self._mcCabeTable.setItem(row, 5, wcetItem)

            # Tooltip com informações extras
            tooltip = self._buildFunctionTooltip(info)
            for col in range(6):
                item = self._mcCabeTable.item(row, col)
                if item:
                    item.setToolTip(tooltip)

        self._mcCabeTable.setSortingEnabled(True)

        # Resumo
        totalFuncs = len(funcs)
        avgMccabe = sum(f.mccabe for f in funcs) / totalFuncs if totalFuncs > 0 else 0
        maxMccabe = max((f.mccabe for f in funcs), default=0)
        tasksCount = sum(1 for f in funcs if f.isTask)
        highComplexity = sum(1 for f in funcs if f.mccabe > 10)

        self._mcCabeSummaryLabel.setText(
            f"Funções: {totalFuncs} | Tasks: {tasksCount} | "
            f"McCabe médio: {avgMccabe:.1f} | McCabe máx: {maxMccabe} | "
            f"Alta complexidade (>10): {highComplexity}"
        )

    def _buildFunctionTooltip(self, info: FunctionInfo) -> str:
        """Constrói tooltip com informações detalhadas da função."""
        lines = [
            f"Função: {info.name}",
            f"Endereço: 0x{info.address:08X}",
            f"Complexidade McCabe: {info.mccabe}",
            f"Decisões (branches): {info.decisionCount}",
            f"Instruções: {info.instructionCount}",
            f"Ciclos estimados: {info.estimatedCycles}",
            f"WCET estimado: {info.estimatedTimeUs:.2f} μs",
        ]
        if info.isTask:
            lines.append("Tipo: TASK do RTOS")
        if info.stackUsage is not None:
            lines.append(f"Uso de stack: {info.stackUsage} bytes")
        if info.callees:
            lines.append(f"Chama: {', '.join(info.callees[:5])}" + ("..." if len(info.callees) > 5 else ""))
        if info.callers:
            lines.append(f"Chamada por: {', '.join(info.callers[:5])}" + ("..." if len(info.callers) > 5 else ""))
        return "\n".join(lines)

    def loadOfflineAnalysis(self, callGraph: CallGraphData) -> None:
        """Carrega dados da análise offline do ELF."""
        self._store.callGraph = callGraph
        self._store.offlineAnalysisComplete = True
        self._callgraphDirty = True
        self._refreshCallgraph()
        self.refreshMcCabeTable()
        self.setStatus(f"Análise offline carregada: {len(callGraph.functions)} funções")


def _parseArgs(argv: List[str]) -> CliArgs:
    p = argparse.ArgumentParser()
    p.add_argument("--out-md", dest="outMd", required=True)
    p.add_argument("--serial", dest="serialEnabled", action="store_true")
    p.add_argument("--port", dest="port", default=None)
    p.add_argument("--baud", dest="baud", type=int, default=115200)

    p.add_argument("--elf", dest="elfPath", default=None)
    p.add_argument("--mcu-code", dest="mcuCode", default=None)
    p.add_argument("--project-dir", dest="projectDir", default=None)
    p.add_argument("--board", dest="board", default=None)

    p.add_argument("--gui", dest="gui", action="store_true")
    p.add_argument("--log-file", dest="logFile", default=None)
    p.add_argument(
        "--log",
        dest="serialLogPath",
        default=None,
        help="(Opcional) Grava em arquivo as linhas recebidas da serial (linhas normalizadas).",
    )
    p.add_argument(
        "--app-log",
        dest="appLogPath",
        default=None,
        help="(Opcional) Grava em arquivo o log interno do script (logging).",
    )
    p.add_argument(
        "--log-level",
        dest="logLevel",
        default="INFO",
        help="Nível de log interno: DEBUG, INFO, WARNING, ERROR.",
    )
    p.add_argument(
        "--verbose",
        dest="verbose",
        action="store_true",
        help="Atalho para --log-level DEBUG.",
    )
    p.add_argument(
        "--debug-serial",
        dest="debugSerial",
        action="store_true",
        help="Modo diagnóstico: lê a serial e imprime linhas cruas/normalizadas e estatísticas de parsing.",
    )
    p.add_argument(
        "--debug-out-log",
        dest="debugOutLog",
        default=None,
        help="(Opcional) Arquivo para salvar as linhas normalizadas durante --debug-serial.",
    )

    ns = p.parse_args(argv)

    if (ns.serialEnabled or ns.debugSerial) and not ns.port:
        p.error("--serial/--debug-serial requer --port")

    logLevel = str(ns.logLevel).upper()
    if bool(getattr(ns, "verbose", False)):
        logLevel = "DEBUG"

    return CliArgs(
        outMd=ns.outMd,
        serialEnabled=bool(ns.serialEnabled),
        port=ns.port,
        baud=int(ns.baud),
        elfPath=ns.elfPath,
        mcuCode=ns.mcuCode,
        projectDir=ns.projectDir,
        board=ns.board,
        gui=bool(ns.gui),
        logFile=ns.logFile,
        serialLogPath=ns.serialLogPath,
        appLogPath=ns.appLogPath,
        logLevel=logLevel,
        debugSerial=bool(ns.debugSerial),
        debugOutLog=ns.debugOutLog,
    )


def _setupLogging(args: CliArgs) -> None:
    level = getattr(logging, (args.logLevel or "INFO").upper(), logging.INFO)

    handlers: List[logging.Handler] = []
    console = logging.StreamHandler(stream=sys.stderr)
    handlers.append(console)

    if args.appLogPath:
        _ensureOutDir(args.appLogPath)
        handlers.append(logging.FileHandler(args.appLogPath, mode="a", encoding="utf-8"))

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=handlers,
        force=True,
    )

    _LOGGER.debug("logging configured level=%s app_log=%s", logging.getLevelName(level), args.appLogPath)


def _runDebugSerial(args: CliArgs) -> int:
    parser = FirmwareLineParser()
    exitMgr = GracefulExit()
    exitMgr.install()

    if not args.port:
        print("--debug-serial requer --port", file=sys.stderr)
        return 2

    outF = None
    if args.debugOutLog:
        _ensureOutDir(args.debugOutLog)
        outF = open(args.debugOutLog, "w", encoding="utf-8")

    countsByPrefix: Dict[str, int] = defaultdict(int)
    lastPrint = time.time()

    ser: Optional[serial.Serial] = None
    attempt = 0
    while not exitMgr.stopRequested() and ser is None:
        attempt += 1
        try:
            ser = serial.Serial(args.port, args.baud, timeout=0.2)
        except Exception as exc:
            print(f"Falha ao abrir serial (tentativa {attempt}): {exc}", file=sys.stderr)
            time.sleep(1.0)

    if ser is None:
        if outF:
            outF.close()
        return 1

    try:
        while not exitMgr.stopRequested():
            raw = ser.readline()
            if not raw:
                # print periódico de resumo
                now = time.time()
                if now - lastPrint >= 2.0:
                    lastPrint = now
                    total = sum(countsByPrefix.values())
                    top = sorted(countsByPrefix.items(), key=lambda x: x[1], reverse=True)[:8]
                    print(f"[debug-serial] total_lines={total} top_prefixes={top}")
                continue

            line = raw.decode(errors="replace").rstrip("\r\n")
            if not line:
                continue

            norm = parser.normalizeLine(line)
            prefix, kv = parser.parseLine(line)

            if prefix is None:
                _LOGGER.debug("unparsed line=%r", norm)
                countsByPrefix["<unparsed>"] += 1
            else:
                countsByPrefix[prefix] += 1

            keys = sorted(kv.keys())
            print(f"[raw] {line}")
            if norm != line:
                print(f"[norm] {norm}")
            if prefix is None:
                print("[parse] prefix=None")
            else:
                print(f"[parse] prefix={prefix} keys={keys}")

            if outF is not None:
                outF.write(norm + "\n")
                outF.flush()

    finally:
        try:
            ser.close()
        except Exception:
            pass
        if outF:
            outF.close()

    return 0


def _ensureOutDir(path: str) -> None:
    outDir = os.path.dirname(os.path.abspath(path))
    if outDir and not os.path.isdir(outDir):
        os.makedirs(outDir, exist_ok=True)


def _tryReadMapSummary(elfPath: Optional[str]) -> Dict[str, str]:
    """Extrai resumo simples a partir do .map (se existir).

    Observação: isso não substitui WCET; serve como informação adicional no MD.
    """

    if not elfPath:
        return {}

    mapPath = None
    if elfPath.endswith(".elf"):
        candidate = elfPath + ".map"
        if os.path.isfile(candidate):
            mapPath = candidate
    if mapPath is None:
        # tenta em tmp/ ou build/ padrões comuns
        base = os.path.splitext(elfPath)[0]
        candidate = base + ".map"
        if os.path.isfile(candidate):
            mapPath = candidate

    if not mapPath:
        return {}

    summary: Dict[str, str] = {"map_path": mapPath}

    # Heurística leve: captura linhas "\.text"/"\.data"/"\.bss" com tamanhos hex.
    sectionRe = re.compile(r"^\.(text|data|bss)\s+0x[0-9a-fA-F]+\s+0x([0-9a-fA-F]+)")
    try:
        with open(mapPath, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                m = sectionRe.match(line.strip())
                if not m:
                    continue
                sec = m.group(1)
                sizeHex = m.group(2)
                size = int(sizeHex, 16)
                summary[f"section_{sec}_bytes"] = str(size)
    except Exception:
        return summary

    return summary


def _which(cmd: str) -> Optional[str]:
    for p in os.environ.get("PATH", "").split(os.pathsep):
        fp = os.path.join(p, cmd)
        if os.path.isfile(fp) and os.access(fp, os.X_OK):
            return fp
    return None


def _getMcuClockHz(mcuCode: Optional[str]) -> int:
    """
    Retorna a frequência do clock do MCU para cálculo de WCET.

    Args:
        mcuCode: Código do MCU (ex: 'rp2040', 'rp2350', 'esp32')

    Returns:
        Frequência em Hz
    """
    if not mcuCode:
        return 125_000_000  # Default: RP2040 @ 125MHz

    mcuCode = mcuCode.lower().strip()

    # Tabela de clocks por MCU
    clockTable: Dict[str, int] = {
        # Raspberry Pi Pico
        "rp2040": 125_000_000,
        "rp2350": 150_000_000,
        "pico": 125_000_000,
        "pico-w": 125_000_000,
        "pico2": 150_000_000,
        # ESP32
        "esp32": 240_000_000,
        "esp32-s2": 240_000_000,
        "esp32-s3": 240_000_000,
        "esp32-c3": 160_000_000,
        "esp32-c6": 160_000_000,
        # STM32 (valores comuns)
        "stm32f4": 168_000_000,
        "stm32f7": 216_000_000,
        "stm32h7": 480_000_000,
        "stm32l4": 80_000_000,
        # nRF
        "nrf52": 64_000_000,
        "nrf52840": 64_000_000,
    }

    # Busca exata
    if mcuCode in clockTable:
        return clockTable[mcuCode]

    # Busca parcial
    for key, hz in clockTable.items():
        if key in mcuCode or mcuCode in key:
            return hz

    return 125_000_000  # Default


def _isTaskFunction(name: str) -> bool:
    """Verifica se o nome da função parece ser uma task do RTOS."""
    for pattern in _TASK_NAME_PATTERNS:
        if pattern.match(name):
            return True
    return False


def _getInstructionCycles(mnemonic: str) -> int:
    """Retorna estimativa de ciclos para uma instrução ARM."""
    base = mnemonic.lower().split(".", 1)[0]
    # Remove sufixos condicionais (ex: addeq -> add)
    for suffix in ["eq", "ne", "cs", "cc", "hs", "lo", "mi", "pl", "vs", "vc", "hi", "ls", "ge", "lt", "gt", "le", "al"]:
        if base.endswith(suffix) and len(base) > len(suffix):
            base = base[:-len(suffix)]
            break
    return _ARM_INSTRUCTION_CYCLES.get(base, _ARM_INSTRUCTION_CYCLES["_default"])


def _analyzeElfComplete(
    elfPath: Optional[str],
    mcuClockHz: int = 125_000_000,
    maxLines: int = 300000,
    maxFunctions: int = 3000,
) -> Optional[CallGraphData]:
    """
    Analisa o ELF de forma completa, extraindo:
    - Complexidade ciclomática (McCabe) por função
    - Grafo de chamadas (callgraph)
    - Estimativa de WCET baseada em ciclos de instrução
    - Identificação de tasks

    Args:
        elfPath: Caminho para o arquivo ELF
        mcuClockHz: Frequência do clock do MCU (para cálculo de tempo)
        maxLines: Número máximo de linhas do objdump a processar
        maxFunctions: Número máximo de funções a processar

    Returns:
        CallGraphData com todas as informações extraídas, ou None se falhar
    """
    if not elfPath or not os.path.isfile(elfPath):
        _LOGGER.warning("ELF não encontrado: %s", elfPath)
        return None

    # Tenta encontrar o objdump apropriado
    objdump = _which("arm-none-eabi-objdump") or _which("objdump")
    if not objdump:
        _LOGGER.warning("objdump não encontrado no PATH")
        return None

    _LOGGER.info("Analisando ELF: %s (clock=%d Hz)", elfPath, mcuClockHz)

    try:
        res = subprocess.run(
            [objdump, "-d", "--demangle", elfPath],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        _LOGGER.error("objdump timeout")
        return None
    except Exception as exc:
        _LOGGER.error("Erro ao executar objdump: %s", exc)
        return None

    if res.returncode != 0:
        _LOGGER.warning("objdump retornou código %d", res.returncode)
        return None

    lines = res.stdout.splitlines()
    if len(lines) > maxLines:
        lines = lines[:maxLines]
        _LOGGER.warning("Truncando saída do objdump para %d linhas", maxLines)

    # Regex para identificar funções e instruções
    funcRe = re.compile(r"^([0-9a-fA-F]+)\s+<([^>]+)>:\s*$")
    # Formato ARM Thumb: "1000077c:       b5f0            push    {r4, r5, r6, r7, lr}"
    # Formato ARM 32-bit: "10000784:       f004 faea       bl      10004d5c <...>"
    insRe = re.compile(
        r"^\s*([0-9a-fA-F]+):\s+([0-9a-fA-F]+(?:\s+[0-9a-fA-F]+)*)\s+(?P<mn>[a-zA-Z][a-zA-Z0-9_.]*)"
    )
    # Regex para chamadas (bl, blx)
    callRe = re.compile(r"\bbl[x]?\s+([0-9a-fA-F]+)\s+<([^>]+)>")

    # Regex para branches condicionais (para McCabe)
    decisionRe = re.compile(
        r"^(?:"
        r"b(?:eq|ne|cs|cc|hs|lo|mi|pl|vs|vc|hi|ls|ge|lt|gt|le)"
        r"|cbz|cbnz"
        r"|beqz|bnez|bgez|bltz|bgtz|blez"
        r"|tbb|tbh"
        r"|it|ite|itt|ittt|itttt"
        r")$"
    )

    functions: Dict[str, FunctionInfo] = {}
    edges: List[Tuple[str, str]] = []
    edgesSet: Set[Tuple[str, str]] = set()

    currentFunc: Optional[str] = None
    currentAddr: int = 0
    funcsSeen = 0

    for ln in lines:
        # Verifica se é início de função
        fm = funcRe.match(ln.strip())
        if fm:
            addr = int(fm.group(1), 16)
            name = fm.group(2)
            currentFunc = name
            currentAddr = addr
            funcsSeen += 1

            if funcsSeen > maxFunctions:
                break

            if name not in functions:
                functions[name] = FunctionInfo(
                    name=name,
                    address=addr,
                    isTask=_isTaskFunction(name),
                )
            continue

        if currentFunc is None:
            continue

        # Verifica se é uma instrução
        im = insRe.match(ln)
        if not im:
            continue

        funcInfo = functions.get(currentFunc)
        if funcInfo is None:
            continue

        mnemonic = im.group("mn").lower().split(".", 1)[0]
        funcInfo.instructionCount += 1
        funcInfo.estimatedCycles += _getInstructionCycles(mnemonic)

        # Verifica se é branch condicional (para McCabe)
        if decisionRe.match(mnemonic):
            funcInfo.decisionCount += 1

        # Verifica se é chamada de função
        cm = callRe.search(ln)
        if cm:
            callee = cm.group(2)
            if callee not in funcInfo.callees:
                funcInfo.callees.append(callee)
            edgeKey = (currentFunc, callee)
            if edgeKey not in edgesSet:
                edges.append(edgeKey)
                edgesSet.add(edgeKey)

    # Calcula McCabe e tempo estimado para cada função
    cyclesPerUs = mcuClockHz / 1_000_000.0
    for funcInfo in functions.values():
        funcInfo.mccabe = 1 + funcInfo.decisionCount
        if cyclesPerUs > 0:
            funcInfo.estimatedTimeUs = funcInfo.estimatedCycles / cyclesPerUs

    # Preenche lista de callers
    for caller, callee in edges:
        if callee in functions:
            if caller not in functions[callee].callers:
                functions[callee].callers.append(caller)

    # Identifica funções raiz (sem callers) e tasks
    rootFunctions: List[str] = []
    taskFunctions: List[str] = []
    for name, info in functions.items():
        if not info.callers:
            rootFunctions.append(name)
        if info.isTask:
            taskFunctions.append(name)

    # Calcula profundidade máxima do callgraph
    maxDepth = _calculateCallgraphDepth(functions)

    _LOGGER.info(
        "Análise ELF completa: %d funções, %d arestas, profundidade=%d, %d tasks",
        len(functions), len(edges), maxDepth, len(taskFunctions)
    )

    return CallGraphData(
        functions=functions,
        edges=edges,
        maxDepth=maxDepth,
        rootFunctions=rootFunctions,
        taskFunctions=taskFunctions,
        mcuClockHz=mcuClockHz,
    )


def _calculateCallgraphDepth(functions: Dict[str, FunctionInfo]) -> int:
    """Calcula a profundidade máxima do callgraph."""
    visited: Dict[str, int] = {}
    inStack: Set[str] = set()

    def dfs(name: str) -> int:
        if name in visited:
            return visited[name]
        if name in inStack:
            return 0  # Ciclo detectado
        if name not in functions:
            return 0

        inStack.add(name)
        maxChildDepth = 0
        for callee in functions[name].callees:
            depth = dfs(callee)
            if depth > maxChildDepth:
                maxChildDepth = depth
        inStack.discard(name)

        visited[name] = maxChildDepth + 1
        return visited[name]

    maxDepth = 0
    for name in list(functions.keys())[:500]:
        depth = dfs(name)
        if depth > maxDepth:
            maxDepth = depth

    return maxDepth


def _tryCyclomaticComplexityFromElf(
    elfPath: Optional[str],
    maxLines: int = 250000,
    maxFunctions: int = 2000,
) -> List[Tuple[str, int, int, int]]:
    """
    Função de compatibilidade que retorna lista de tuplas (nome, mccabe, decisoes, instrucoes).
    Utiliza a análise completa internamente.
    """
    callGraph = _analyzeElfComplete(elfPath, maxLines=maxLines, maxFunctions=maxFunctions)
    if callGraph is None:
        return []

    out: List[Tuple[str, int, int, int]] = []
    for name, info in callGraph.functions.items():
        out.append((name, info.mccabe, info.decisionCount, info.instructionCount))

    out.sort(key=lambda r: (r[1], r[3], r[0]), reverse=True)
    return out


def _tryElfSymbols(elfPath: Optional[str]) -> List[Tuple[str, int]]:
    if not elfPath or not os.path.isfile(elfPath):
        return []

    nm = _which("arm-none-eabi-nm") or _which("nm")
    if not nm:
        return []

    try:
        res = subprocess.run(
            [nm, "--print-size", "--size-sort", "--demangle", elfPath],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except Exception:
        return []

    if res.returncode != 0:
        return []

    out: List[Tuple[str, int]] = []
    for line in res.stdout.splitlines():
        # formato comum: "00000010 00000024 T symbol"
        parts = line.strip().split(None, 3)
        if len(parts) < 4:
            continue
        sizeHex = parts[1]
        name = parts[3]
        try:
            size = int(sizeHex, 16)
        except ValueError:
            continue
        if size <= 0:
            continue
        out.append((name, size))
    # Já vem ordenado por size asc; queremos top
    out = out[-50:]
    out.reverse()
    return out


def _tryCallgraphDepth(elfPath: Optional[str], maxLines: int = 200000) -> Optional[Tuple[int, List[Tuple[str, str]]]]:
    if not elfPath or not os.path.isfile(elfPath):
        return None

    objdump = _which("arm-none-eabi-objdump") or _which("objdump")
    if not objdump:
        return None

    try:
        res = subprocess.run(
            [objdump, "-d", "--demangle", elfPath],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except Exception:
        return None

    if res.returncode != 0:
        return None

    lines = res.stdout.splitlines()
    if len(lines) > maxLines:
        lines = lines[:maxLines]

    funcRe = re.compile(r"^[0-9a-fA-F]+\s+<([^>]+)>:\s*$")
    callRe = re.compile(r"\bbl\s+([0-9a-fA-F]+)\s+<([^>]+)>")

    current: Optional[str] = None
    edges: List[Tuple[str, str]] = []
    adj: Dict[str, List[str]] = defaultdict(list)

    for ln in lines:
        fm = funcRe.match(ln.strip())
        if fm:
            current = fm.group(1)
            continue
        if current is None:
            continue
        cm = callRe.search(ln)
        if cm:
            callee = cm.group(2)
            adj[current].append(callee)
            edges.append((current, callee))
            if len(edges) >= 4000:
                break

    if not adj:
        return None

    visited: Dict[str, int] = {}
    inStack: Dict[str, bool] = {}

    def dfs(n: str) -> int:
        if n in visited:
            return visited[n]
        if inStack.get(n, False):
            return 0
        inStack[n] = True
        best = 0
        for c in adj.get(n, []):
            d = dfs(c)
            if d > best:
                best = d
        inStack[n] = False
        visited[n] = best + (1 if adj.get(n) else 0)
        return visited[n]

    maxDepth = 0
    for n in list(adj.keys())[:500]:
        d = dfs(n)
        if d > maxDepth:
            maxDepth = d

    return maxDepth, edges[:50]


def _cpuWindowFromTrace(store: MetricsStore, nowEpoch: float, windowSeconds: float) -> List[Tuple[str, float, float]]:
    nowRel = store.trace.lastRelSec
    if nowRel is None:
        return []
    windowStart = nowRel - windowSeconds
    totals: Dict[str, float] = {}
    totalTime = 0.0
    for taskName, sched in store.scheduling.items():
        t = 0.0
        for start, end in reversed(sched.segments):
            if end <= windowStart:
                break
            s = max(start, windowStart)
            e = min(end, nowRel)
            if e > s:
                t += (e - s)
        if t > 0.0:
            totals[taskName] = t
            totalTime += t
    if totalTime <= 0.0:
        return []
    rows: List[Tuple[str, float, float]] = []
    for taskName, t in totals.items():
        rows.append((taskName, (t * 100.0) / totalTime, t))
    rows.sort(key=lambda r: r[1], reverse=True)
    return rows


def _segmentsSummary(store: MetricsStore) -> List[Tuple[str, int, float, Optional[float], Optional[float]]]:
    rows: List[Tuple[str, int, float, Optional[float], Optional[float]]] = []
    for taskName in store.listTasks():
        segs = store.scheduling[taskName].segments if taskName in store.scheduling else []
        count = len(segs)
        if count <= 0:
            rows.append((taskName, 0, 0.0, None, None))
            continue
        total = 0.0
        maxSeg = 0.0
        for start, end in segs:
            d = end - start
            if d <= 0.0:
                continue
            total += d
            if d > maxSeg:
                maxSeg = d
        meanSeg = (total / float(count)) if count > 0 else None
        rows.append((taskName, count, total, meanSeg, maxSeg if maxSeg > 0.0 else None))
    rows.sort(key=lambda r: (r[2], r[1]), reverse=True)
    return rows


def _renderMarkdown(store: MetricsStore, args: CliArgs) -> str:
    now = _dt.datetime.now().astimezone()

    lines: List[str] = []
    lines.append(f"# Análise RTOS (WCET / Stack / Heap)\n")
    lines.append(f"Gerado em: `{now.isoformat()}`\n")

    lines.append("## Parâmetros\n")
    lines.append(f"- **board**: `{args.board}`\n")
    lines.append(f"- **mcuCode**: `{args.mcuCode}`\n")
    lines.append(f"- **projectDir**: `{args.projectDir}`\n")
    lines.append(f"- **elf**: `{args.elfPath}`\n")
    if args.serialEnabled:
        lines.append(f"- **serial**: `{args.port}` @ `{args.baud}`\n")

    if store.hwKv:
        lines.append("\n## Hardware / RTOS (último snapshot)\n")
        for k in sorted(store.hwKv.keys()):
            lines.append(f"- `{k}`: `{store.hwKv[k]}`\n")

    if store.rxTotalLines > 0:
        lines.append("\n## Log (resumo de parsing)\n")
        lines.append(f"- Linhas processadas: `{store.rxTotalLines}`\n")
        lines.append("\n| Prefixo | Linhas |\n")
        lines.append("|---|---:|\n")
        for k, v in sorted(store.rxCountsByPrefix.items(), key=lambda kv: kv[1], reverse=True)[:20]:
            lines.append(f"| `{k}` | `{v}` |\n")

    # Heap
    lines.append("\n## Heap\n")
    hf = store.system.heapFreeStats
    hm = store.system.heapMinStats
    lines.append("- **heap_free**\n")
    lines.append(f"  - count: `{hf.count}`\n")
    lines.append(f"  - min: `{hf.minValue}`\n")
    lines.append(f"  - max: `{hf.maxValue}`\n")
    lines.append(f"  - mean: `{hf.mean}`\n")
    lines.append("- **heap_min**\n")
    lines.append(f"  - count: `{hm.count}`\n")
    lines.append(f"  - min: `{hm.minValue}`\n")
    lines.append(f"  - max: `{hm.maxValue}`\n")
    lines.append(f"  - mean: `{hm.mean}`\n")

    # Tasks
    lines.append("\n## Tasks\n")
    for task in store.listTasks():
        tm = store.tasks[task]
        lines.append(f"### {task}\n")
        lines.append("- **stack_used (bytes)**\n")
        lines.append(f"  - min: `{tm.stackUsedStats.minValue}`\n")
        lines.append(f"  - max: `{tm.stackUsedStats.maxValue}`\n")
        lines.append(f"  - mean: `{tm.stackUsedStats.mean}`\n")
        lines.append("- **stack_free (bytes)**\n")
        lines.append(f"  - min: `{tm.stackFreeStats.minValue}`\n")
        lines.append(f"  - max: `{tm.stackFreeStats.maxValue}`\n")
        lines.append(f"  - mean: `{tm.stackFreeStats.mean}`\n")
        lines.append("- **stack_usage_pct (%)**\n")
        lines.append(f"  - min: `{tm.stackUsagePctStats.minValue}`\n")
        lines.append(f"  - max: `{tm.stackUsagePctStats.maxValue}`\n")
        lines.append(f"  - mean: `{tm.stackUsagePctStats.mean}`\n")
        lines.append("- **cpu_pct (%)**\n")
        lines.append(f"  - min: `{tm.cpuPctStats.minValue}`\n")
        lines.append(f"  - max: `{tm.cpuPctStats.maxValue}`\n")
        lines.append(f"  - mean: `{tm.cpuPctStats.mean}`\n")

    # Scheduling/CPU window
    lines.append("\n## Escalonamento / CPU (janela)\n")
    nowEpoch = time.time()
    windowSeconds = 5.0
    rows = _cpuWindowFromTrace(store, nowEpoch, windowSeconds)
    if rows:
        lines.append(f"Janela: `{windowSeconds}s` (estimativa via TraceKV)\n\n")
        lines.append("| Task | CPU% | RunTime(s) |\n")
        lines.append("|---|---:|---:|\n")
        for taskName, pct, runtime in rows[:20]:
            lines.append(f"| `{taskName}` | `{pct:.2f}` | `{runtime:.4f}` |\n")
    else:
        lines.append("Sem dados suficientes de TraceKV para estimar CPU por janela.\n")

    lines.append("\n### Segmentos de escalonamento (resumo)\n")
    lines.append("| Task | Segments | TotalRunTime(s) | MeanSegment(s) | MaxSegment(s) |\n")
    lines.append("|---|---:|---:|---:|---:|\n")
    for taskName, segCount, totalRun, meanSeg, maxSeg in _segmentsSummary(store)[:30]:
        ms = f"{meanSeg:.6f}" if meanSeg is not None else "None"
        mx = f"{maxSeg:.6f}" if maxSeg is not None else "None"
        lines.append(f"| `{taskName}` | `{segCount}` | `{totalRun:.6f}` | `{ms}` | `{mx}` |\n")

    # WCET
    if store.wcet:
        lines.append("\n## WCET (probes)\n")
        lines.append("| Probe | Task | ISR | Count | Min(us) | P95(us) | P99(us) | Mean(us) | Std(us) | Max(us) |\n")
        lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|\n")
        for key in store.listWcetKeys():
            wm = store.wcet[key]
            qs = wm.quantiles([95.0, 99.0])
            p95 = qs.get(95.0)
            p99 = qs.get(99.0)
            std = wm.durUsStats.stddev()
            p95s = f"{p95:.2f}" if p95 is not None else "None"
            p99s = f"{p99:.2f}" if p99 is not None else "None"
            stds = f"{std:.2f}" if std is not None else "None"
            lines.append(
                f"| `{key.name}` | `{key.task}` | `{key.isr}` | `{wm.durUsStats.count}` | `{wm.durUsStats.minValue}` | `{p95s}` | `{p99s}` | `{wm.durUsStats.mean}` | `{stds}` | `{wm.durUsStats.maxValue}` |\n"
            )

    # Map summary (extra)
    mapSummary = _tryReadMapSummary(args.elfPath)
    if mapSummary:
        lines.append("\n## ELF/MAP (resumo)\n")
        for k in sorted(mapSummary.keys()):
            lines.append(f"- `{k}`: `{mapSummary[k]}`\n")

    # Symbols / callgraph
    if args.elfPath:
        syms = _tryElfSymbols(args.elfPath)
        if syms:
            lines.append("\n## ELF (maiores símbolos por tamanho)\n")
            lines.append("| Símbolo | Bytes |\n")
            lines.append("|---|---:|\n")
            for name, size in syms[:30]:
                lines.append(f"| `{name}` | `{size}` |\n")

    # Análise offline do callgraph (usa dados já calculados se disponíveis)
    if store.callGraph and store.offlineAnalysisComplete:
        cg = store.callGraph
        lines.append("\n## Complexidade Ciclomática (McCabe) - análise offline\n")
        lines.append(
            "A complexidade é calculada a partir do assembly (contagem de branches condicionais por função).\n"
        )
        lines.append(f"\n- Clock do MCU: `{cg.mcuClockHz / 1_000_000:.0f} MHz`\n")
        lines.append(f"- Funções analisadas: `{len(cg.functions)}`\n")
        lines.append(f"- Tasks identificadas: `{len(cg.taskFunctions)}`\n")
        lines.append(f"- Profundidade máxima do callgraph: `{cg.maxDepth}`\n")

        # Tabela de funções (top 50 por complexidade)
        funcs = sorted(
            cg.functions.values(),
            key=lambda f: (f.mccabe, f.instructionCount),
            reverse=True
        )[:50]

        if funcs:
            avgMccabe = sum(f.mccabe for f in cg.functions.values()) / len(cg.functions)
            maxMccabe = max(f.mccabe for f in cg.functions.values())
            lines.append(f"- McCabe médio: `{avgMccabe:.2f}`\n")
            lines.append(f"- McCabe máximo: `{maxMccabe}`\n")

            lines.append("\n| Função | McCabe | Decisões | Instruções | Ciclos Est. | WCET Est. (μs) | Task |\n")
            lines.append("|---|---:|---:|---:|---:|---:|:---:|\n")
            for info in funcs:
                taskMark = "✓" if info.isTask else ""
                lines.append(
                    f"| `{info.name}` | `{info.mccabe}` | `{info.decisionCount}` | "
                    f"`{info.instructionCount}` | `{info.estimatedCycles}` | "
                    f"`{info.estimatedTimeUs:.2f}` | {taskMark} |\n"
                )

        # Tasks identificadas
        if cg.taskFunctions:
            lines.append("\n### Tasks Identificadas\n")
            for taskName in sorted(cg.taskFunctions):
                info = cg.functions.get(taskName)
                if info:
                    lines.append(
                        f"- **{taskName}**: McCabe=`{info.mccabe}`, "
                        f"WCET=`{info.estimatedTimeUs:.2f} μs`, "
                        f"Chama {len(info.callees)} funções\n"
                    )

        # Callgraph (amostra de arestas)
        if cg.edges:
            lines.append("\n### Callgraph (amostra de arestas)\n")
            for src, dst in cg.edges[:30]:
                lines.append(f"- `{src}` → `{dst}`\n")
            if len(cg.edges) > 30:
                lines.append(f"- ... e mais {len(cg.edges) - 30} arestas\n")

    elif args.elfPath:
        # Fallback: análise sob demanda se não houver dados pré-calculados
        cc = _tryCyclomaticComplexityFromElf(args.elfPath)
        if cc:
            lines.append("\n## Complexidade Ciclomática (McCabe) - offline via ELF\n")
            lines.append(
                "A complexidade é uma aproximação calculada a partir do assembly.\n"
            )
            lines.append("\n| Função | McCabe | Decisões | Instruções |\n")
            lines.append("|---|---:|---:|---:|\n")
            for fn, mccabe, decisions, insCount in cc[:30]:
                lines.append(
                    f"| `{fn}` | `{mccabe}` | `{decisions}` | `{insCount}` |\n"
                )

        cg = _tryCallgraphDepth(args.elfPath)
        if cg:
            depth, edges = cg
            lines.append("\n## Callgraph\n")
            lines.append(f"- Profundidade máxima estimada: `{depth}`\n")

    lines.append("\n## Notas\n")
    if args.serialEnabled:
        lines.append("- Este relatório inclui dados coletados via serial do firmware.\n")
    if store.offlineAnalysisComplete:
        lines.append("- Análise offline do ELF realizada com sucesso.\n")
        lines.append("- O WCET estimado é baseado em contagem de ciclos de instrução (pior caso).\n")
    else:
        lines.append("- Nenhuma análise offline do ELF foi realizada.\n")

    return "".join(lines)


class GracefulExit:
    def __init__(self) -> None:
        self._stop = threading.Event()

    def install(self) -> None:
        def handler(signum: int, frame) -> None:  # type: ignore[no-untyped-def]
            _ = frame
            self._stop.set()

        signal.signal(signal.SIGINT, handler)
        signal.signal(signal.SIGTERM, handler)

    def stopRequested(self) -> bool:
        return self._stop.is_set()

    def requestStop(self) -> None:
        self._stop.set()


def _runGui(args: CliArgs) -> int:
    store = MetricsStore()
    parser = FirmwareLineParser()
    cpuParser = CpuStatsBlockParser()
    agg = Aggregator(store)

    serialLogF = None
    if args.serialLogPath:
        _ensureOutDir(args.serialLogPath)
        serialLogF = open(args.serialLogPath, "a", encoding="utf-8")
        _LOGGER.info("serial capture enabled path=%s", args.serialLogPath)

    # Análise offline do ELF (sempre executada se ELF disponível)
    callGraph: Optional[CallGraphData] = None
    if args.elfPath and os.path.isfile(args.elfPath):
        mcuClockHz = _getMcuClockHz(args.mcuCode)
        _LOGGER.info("Iniciando análise offline do ELF: %s (clock=%d Hz)", args.elfPath, mcuClockHz)
        callGraph = _analyzeElfComplete(args.elfPath, mcuClockHz=mcuClockHz)
        if callGraph:
            store.callGraph = callGraph
            store.offlineAnalysisComplete = True
            _LOGGER.info(
                "Análise offline concluída: %d funções, %d arestas, %d tasks",
                len(callGraph.functions), len(callGraph.edges), len(callGraph.taskFunctions)
            )
        else:
            _LOGGER.warning("Falha na análise offline do ELF")

    # Filtra spam do Qt que pode ocorrer com QGraphicsView/pyqtgraph.
    # Mantém outros warnings/erros visíveis.
    def _qtMessageHandler(mode, context, message):  # type: ignore[no-untyped-def]
        _ = mode
        _ = context
        if isinstance(message, str) and "QGraphicsItem::itemTransform: null pointer passed" in message:
            return
        try:
            sys.stderr.write(str(message) + "\n")
        except Exception:
            pass

    try:
        QtCore.qInstallMessageHandler(_qtMessageHandler)
    except Exception:
        pass

    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow(store, args)

    # Carrega análise offline na GUI
    if callGraph:
        win.loadOfflineAnalysis(callGraph)

    win.show()

    # Serial thread
    serialThread: Optional[QtCore.QThread] = None
    serialWorker: Optional[SerialWorker] = None

    # Diagnóstico simples (GUI): contadores por prefixo e última linha parseada.
    diagCounts: Dict[str, int] = defaultdict(int)
    diagLastPrefix: Optional[str] = None
    diagLastUpdate = time.time()

    class _GuiDispatcher(QtCore.QObject):
        """Garante que callbacks da serial rodem na thread principal (Qt)."""

        @QtCore.Slot(str)
        def onLine(self, line: str) -> None:
            nonlocal diagLastPrefix, diagLastUpdate
            now = time.time()

            store.rxTotalLines += 1

            if serialLogF is not None:
                try:
                    serialLogF.write(parser.normalizeLine(line) + "\n")
                    serialLogF.flush()
                except Exception:
                    pass

            # CPU block parsing
            cpuRes = cpuParser.feed(line)
            if cpuRes:
                for taskName, pct in cpuRes:
                    agg.applyCpuPct(taskName, pct, now)

            prefix, kv = parser.parseLine(line)

            diagLastPrefix = prefix
            diagCounts[prefix or "<unparsed>"] += 1
            store.rxCountsByPrefix[prefix or "<unparsed>"] += 1
            if now - diagLastUpdate >= 1.0:
                diagLastUpdate = now
                win.setStatus(
                    f"rx={sum(diagCounts.values())} unparsed={diagCounts.get('<unparsed>', 0)} MonitorKV={diagCounts.get('MonitorKV', 0)} TraceKV={diagCounts.get('TraceKV', 0)} WcetKV={diagCounts.get('WcetKV', 0)} WCET={diagCounts.get('WCET', 0)} last={diagLastPrefix}"
                )

            if prefix == "MonitorKV":
                agg.applyMonitorKv(kv, now)
                win._tasksDirty = True
            elif prefix == "HwKV":
                agg.applyHwKv(kv)
            elif prefix == "TRACE":
                agg.applyTraceTextSwitch(kv, now)
                win._tasksDirty = True
            elif prefix == "TraceKV":
                agg.applyTraceKv(kv)
                if store.trace.lastRelSec is not None:
                    agg.updateCpuFromTrace(store.trace.lastRelSec, windowSeconds=5.0)
                win._tasksDirty = True
            elif prefix == "WcetKV":
                agg.applyWcetKv(kv)
                win._wcetDirty = True
            elif prefix == "WCET":
                agg.applyWcetKv(kv)
                win._wcetDirty = True

        @QtCore.Slot(str)
        def onStatus(self, text: str) -> None:
            _LOGGER.info("status: %s", text)
            win.setStatus(text)

    dispatcher = _GuiDispatcher()

    if args.serialEnabled and args.port:
        serialWorker = SerialWorker(args.port, args.baud)
        serialThread = QtCore.QThread()
        serialWorker.moveToThread(serialThread)
        serialThread.started.connect(serialWorker.run)
        serialWorker.lineReceived.connect(dispatcher.onLine, QtCore.Qt.ConnectionType.QueuedConnection)
        serialWorker.statusChanged.connect(dispatcher.onStatus, QtCore.Qt.ConnectionType.QueuedConnection)
        serialThread.start()

    # Log file replay (opcional)
    if args.logFile and os.path.isfile(args.logFile):
        try:
            with open(args.logFile, "r", encoding="utf-8", errors="replace") as f:
                for ln in f:
                    dispatcher.onLine(ln.rstrip("\n"))
        except Exception as exc:
            win.setStatus(f"Erro lendo log-file: {exc}")

    # Fechamento gracioso
    exitMgr = GracefulExit()
    exitMgr.install()

    def qtStop() -> None:
        exitMgr.requestStop()
        if serialWorker is not None:
            serialWorker.stop()
        if serialThread is not None:
            serialThread.quit()
            serialThread.wait(1500)
        try:
            if serialLogF is not None:
                serialLogF.close()
        except Exception:
            pass
        try:
            md = _renderMarkdown(store, args)
            _ensureOutDir(args.outMd)
            with open(args.outMd, "w", encoding="utf-8") as f:
                f.write(md)
        except Exception:
            pass

    app.aboutToQuit.connect(qtStop)

    rc = app.exec()
    return int(rc)


def _runCli(args: CliArgs) -> int:
    store = MetricsStore()
    parser = FirmwareLineParser()
    cpuParser = CpuStatsBlockParser()
    agg = Aggregator(store)

    serialLogF = None
    if args.serialLogPath:
        _ensureOutDir(args.serialLogPath)
        serialLogF = open(args.serialLogPath, "a", encoding="utf-8")

    # Análise offline do ELF (sempre executada se ELF disponível)
    if args.elfPath and os.path.isfile(args.elfPath):
        mcuClockHz = _getMcuClockHz(args.mcuCode)
        _LOGGER.info("Iniciando análise offline do ELF: %s", args.elfPath)
        callGraph = _analyzeElfComplete(args.elfPath, mcuClockHz=mcuClockHz)
        if callGraph:
            store.callGraph = callGraph
            store.offlineAnalysisComplete = True
            _LOGGER.info(
                "Análise offline concluída: %d funções, %d arestas",
                len(callGraph.functions), len(callGraph.edges)
            )
            print(f"Análise offline: {len(callGraph.functions)} funções, {len(callGraph.taskFunctions)} tasks")

    # Modo offline: se não há serial nem log-file, gera o relatório e sai
    if not args.serialEnabled and not args.logFile:
        _LOGGER.info("Modo offline: gerando relatório sem dados de serial")
        print("Modo offline: gerando relatório Markdown...")
        md = _renderMarkdown(store, args)
        _ensureOutDir(args.outMd)
        with open(args.outMd, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"Relatório gerado: {args.outMd}")
        return 0

    exitMgr = GracefulExit()
    exitMgr.install()

    def feedLine(line: str) -> None:
        now = time.time()

        store.rxTotalLines += 1

        if serialLogF is not None:
            try:
                serialLogF.write(parser.normalizeLine(line) + "\n")
            except Exception:
                pass

        cpuRes = cpuParser.feed(line)
        if cpuRes:
            for taskName, pct in cpuRes:
                agg.applyCpuPct(taskName, pct, now)

        prefix, kv = parser.parseLine(line)
        store.rxCountsByPrefix[prefix or "<unparsed>"] += 1
        if prefix == "MonitorKV":
            agg.applyMonitorKv(kv, now)
        elif prefix == "HwKV":
            agg.applyHwKv(kv)
        elif prefix == "TRACE":
            agg.applyTraceTextSwitch(kv, now)
        elif prefix == "TraceKV":
            agg.applyTraceKv(kv)
            if store.trace.lastRelSec is not None:
                agg.updateCpuFromTrace(store.trace.lastRelSec, windowSeconds=5.0)
        elif prefix == "WcetKV":
            agg.applyWcetKv(kv)
        elif prefix == "WCET":
            agg.applyWcetKv(kv)

    # Fonte 1: replay de arquivo de log
    if args.logFile and os.path.isfile(args.logFile):
        with open(args.logFile, "r", encoding="utf-8", errors="replace") as f:
            for ln in f:
                feedLine(ln.rstrip("\n"))

    # Fonte 2: serial ao vivo
    ser: Optional[serial.Serial] = None
    if args.serialEnabled and args.port:
        attempt = 0
        while not exitMgr.stopRequested() and ser is None:
            attempt += 1
            try:
                ser = serial.Serial(args.port, args.baud, timeout=0.2)
                _LOGGER.info("serial opened port=%s baud=%s", args.port, args.baud)
            except Exception as exc:
                print(f"Falha ao abrir serial (tentativa {attempt}): {exc}", file=sys.stderr)
                _LOGGER.warning("serial open failed attempt=%s err=%s", attempt, exc)
                time.sleep(1.0)

    try:
        while not exitMgr.stopRequested():
            if ser is None:
                # Sem serial: apenas aguarda Ctrl+C (pode ser útil em modo replay)
                time.sleep(0.1)
                continue
            raw = ser.readline()
            if not raw:
                continue
            line = raw.decode(errors="replace").rstrip("\r\n")
            if line:
                feedLine(line)
    finally:
        try:
            if ser is not None:
                ser.close()
        except Exception:
            pass

        try:
            if serialLogF is not None:
                serialLogF.close()
        except Exception:
            pass

        md = _renderMarkdown(store, args)
        _ensureOutDir(args.outMd)
        with open(args.outMd, "w", encoding="utf-8") as f:
            f.write(md)

    return 0


def main(argv: List[str]) -> int:
    args = _parseArgs(argv)
    _setupLogging(args)
    _LOGGER.info(
        "start gui=%s serial=%s port=%s baud=%s log_file=%s serial_log=%s elf=%s",
        args.gui,
        args.serialEnabled,
        args.port,
        args.baud,
        args.logFile,
        args.serialLogPath,
        args.elfPath,
    )

    # Verifica dependências para modos específicos
    if args.gui and not _HAS_QT:
        print("ERRO: --gui requer PySide6 e pyqtgraph. Instale com:", file=sys.stderr)
        print("  pip install PySide6 pyqtgraph", file=sys.stderr)
        return 1

    if args.serialEnabled and not _HAS_SERIAL:
        print("ERRO: --serial requer pyserial. Instale com:", file=sys.stderr)
        print("  pip install pyserial", file=sys.stderr)
        return 1

    if args.debugSerial:
        if not _HAS_SERIAL:
            print("ERRO: --debug-serial requer pyserial.", file=sys.stderr)
            return 1
        return _runDebugSerial(args)

    if args.gui:
        return _runGui(args)
    return _runCli(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
