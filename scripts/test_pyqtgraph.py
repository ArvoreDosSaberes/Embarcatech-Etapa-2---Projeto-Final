#!/usr/bin/env python3
"""
Script de teste para diagnosticar problemas de renderização do pyqtgraph.
Cria um grafo simples com nós e linhas para verificar funcionamento.
"""
import sys
import math
import numpy as np

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
import pyqtgraph as pg

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Teste PyQtGraph - Grafo")
        self.resize(800, 600)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Cria PlotWidget
        self.plot = pg.PlotWidget(title="Teste de Grafo")
        self.plot.showGrid(x=True, y=True)
        layout.addWidget(self.plot)
        
        # Dados de teste: 5 nós em círculo
        n = 5
        radius = 10.0
        xData = []
        yData = []
        for i in range(n):
            angle = (2.0 * math.pi * i) / n
            xData.append(math.cos(angle) * radius)
            yData.append(math.sin(angle) * radius)
        
        print(f"Posições dos nós:")
        for i in range(n):
            print(f"  Nó {i}: ({xData[i]:.2f}, {yData[i]:.2f})")
        
        # Arestas: 0->1, 1->2, 2->3, 3->4, 4->0
        edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0), (0, 2), (1, 3)]
        
        # Desenha linhas
        linePen = pg.mkPen(color=(150, 150, 150, 200), width=2)
        for src, dst in edges:
            x1, y1 = xData[src], yData[src]
            x2, y2 = xData[dst], yData[dst]
            self.plot.plot([x1, x2], [y1, y2], pen=linePen)
            print(f"  Linha: ({x1:.2f}, {y1:.2f}) -> ({x2:.2f}, {y2:.2f})")
        
        # Desenha nós usando ScatterPlotItem
        scatter = pg.ScatterPlotItem()
        self.plot.addItem(scatter)
        
        scatter.setData(
            x=xData,
            y=yData,
            size=20,
            pen=pg.mkPen(color=(255, 255, 255), width=2),
            brush=pg.mkBrush(100, 150, 255, 200),
            symbol='o',
        )
        
        # Ajusta range
        self.plot.setXRange(-15, 15)
        self.plot.setYRange(-15, 15)
        
        print("\nGrafo criado com sucesso!")
        print("Você deve ver 5 nós em círculo conectados por linhas.")

def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
