# session_manager.py
import os
import re
import sys
import json
import time
import shutil
import socket
import subprocess
import threading
from pathlib import Path
from datetime import datetime
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLineEdit, QTreeWidget, QTreeWidgetItem,
    QMessageBox, QHBoxLayout, QLabel, QDialog, QFileDialog, QComboBox
)

from config_dialog import ConfiguracionDialog

# Metadata de versión
VERSION = '2.0.0'





class SizeCalculatorThread(QThread):
    size_calculated = pyqtSignal(str, int)
    
    def __init__(self, session_name, session_path):
        super().__init__()
        self.session_name = session_name
        self.session_path = session_path
        self.should_stop = False
        
    def run(self):
        try:
            if os.path.exists(self.session_path) and not self.should_stop:
                total_size = 0
                for root, dirs, files in os.walk(self.session_path):
                    if self.should_stop:
                        break
                    for file in files:
                        if self.should_stop:
                            break
                        try:
                            file_path = os.path.join(root, file)
                            total_size += os.path.getsize(file_path)
                        except (OSError, IOError):
                            continue
                        # Pequeña pausa para no saturar el sistema
                        time.sleep(0.001)
                
                if not self.should_stop:
                    self.size_calculated.emit(self.session_name, total_size)
        except Exception:
            if not self.should_stop:
                self.size_calculated.emit(self.session_name, 0)
    
    def stop(self):
        self.should_stop = True





class ChromeSessionManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Session Manager (v{VERSION}) - Google Chrome")
        self.setGeometry(100, 100, 1080, 720)
        icon_r = os.path.join('Storage', 'Settings', 'icons', 'favicon.png')
        self.setWindowIcon(QIcon(icon_r))

        self.config = self.cargar_configuracion()
        self.sort_orders = {
            'name': Qt.AscendingOrder,
            'date': Qt.AscendingOrder,
            'size': Qt.DescendingOrder
        }

        # Cache para tamaños de sesiones
        self.session_sizes = {}
        self.size_threads = {}
        self.calculating_sizes = set()

        self.setup_ui()
        self.sesiones = self.cargar_sesiones_existentes()
        self.mostrar_sesiones()
        self.actualizar_espacio()
        self.sessions_tree.sortItems(0, Qt.AscendingOrder)
        self.sessions_tree.header().setSortIndicator(0, Qt.AscendingOrder)
        self.tema = self.config.get("tema", "Oscuro")
        self.aplicar_tema()

        # Timer para actualizar tamaños periódicamente
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.calculate_pending_sizes)
        self.update_timer.start(500)  # Cada 500ms

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # SECCIÓN 1: ENCABEZADO
        header_container = QWidget()
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        header_label = QLabel("Administrador de Sesiones Paralelas", self)
        header_label.setFont(QFont("Arial", 18, QFont.Bold))
        header_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(header_label)
        
        subtitle_label = QLabel("Gestiona múltiples sesiones de Chrome de forma independiente", self)
        subtitle_label.setFont(QFont("Arial", 10))
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        header_layout.addWidget(subtitle_label)
        
        header_container.setLayout(header_layout)
        main_layout.addWidget(header_container)

        # SECCIÓN 2: CREACIÓN DE SESIÓN
        creation_container = QWidget()
        creation_container.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        creation_layout = QVBoxLayout()
        creation_layout.setSpacing(10)
        
        creation_title = QLabel("¿Desea crear una nueva sesión?")
        creation_title.setFont(QFont("Arial", 12, QFont.Bold))
        creation_title.setStyleSheet("color: #333; margin-bottom: 5px;")
        creation_layout.addWidget(creation_title)
        
        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)
        
        self.session_name_input = QLineEdit(self)
        self.session_name_input.setPlaceholderText("Ingresa el nombre de la nueva sesión...")
        self.session_name_input.setFont(QFont("Arial", 11))
        self.session_name_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
                color: #333;
            }
            QLineEdit:focus {
                border-color: #007bff;
            }
        """)
        input_layout.addWidget(self.session_name_input, 3)
        
        create_session_btn = QPushButton("Crear Sesión", self)
        create_session_btn.setFont(QFont("Arial", 11, QFont.Bold))
        create_session_btn.setStyleSheet("""
            QPushButton {
                padding: 12px 20px;
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        create_session_btn.clicked.connect(self.crear_sesion)
        input_layout.addWidget(create_session_btn, 1)
        
        creation_layout.addLayout(input_layout)
        creation_container.setLayout(creation_layout)
        main_layout.addWidget(creation_container)

        # SECCIÓN 3: LISTA DE SESIONES
        sessions_container = QWidget()
        sessions_layout = QVBoxLayout()
        sessions_layout.setSpacing(10)
        
        sessions_header_layout = QHBoxLayout()
        sessions_title = QLabel("Sesiones Existentes")
        sessions_title.setFont(QFont("Arial", 12, QFont.Bold))
        sessions_title.setStyleSheet("color: #333;")
        sessions_header_layout.addWidget(sessions_title)
        
        sessions_header_layout.addStretch()
        
        self.update_btn = QPushButton("Actualizar Lista", self)
        self.update_btn.setFont(QFont("Arial", 10))
        self.update_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.update_btn.clicked.connect(self.actualizar_todo)
        sessions_header_layout.addWidget(self.update_btn)
        
        sessions_layout.addLayout(sessions_header_layout)
        
        self.sessions_tree = QTreeWidget(self)
        self.sessions_tree.setFont(QFont("Arial", 10))
        self.sessions_tree.setHeaderLabels(["Nombre de Sesión", "Fecha de Creación", "Almacenamiento"])
        self.sessions_tree.setStyleSheet("""
            QTreeWidget {
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: white;
                alternate-background-color: #f8f9fa;
            }
            QTreeWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QTreeWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
            QTreeWidget::item:hover {
                background-color: #e9ecef;
            }
            QHeaderView::section {
                background-color: #f1f3f4;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #dee2e6;
                font-weight: bold;
                color: #333;
            }
        """)
        
        header = self.sessions_tree.header()
        header.setSectionsClickable(True)
        header.sectionClicked.connect(self.on_header_click)
        header.setSortIndicatorShown(True)
        self.sessions_tree.itemSelectionChanged.connect(self.actualizar_botones)
        sessions_layout.addWidget(self.sessions_tree)
        
        sessions_container.setLayout(sessions_layout)
        main_layout.addWidget(sessions_container)

        # SECCIÓN 4: INFORMACIÓN DE ESPACIO
        self.space_info_label = QLabel(self)
        self.space_info_label.setFont(QFont("Arial", 10))
        self.space_info_label.setStyleSheet("""
            QLabel {
                background-color: #e9ecef;
                padding: 10px;
                border-radius: 6px;
                color: #495057;
            }
        """)
        self.space_info_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.space_info_label)

        # SECCIÓN 5: ACCIONES DE SESIÓN
        actions_container = QWidget()
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(10)
        
        actions_title = QLabel("Acciones de Sesión")
        actions_title.setFont(QFont("Arial", 12, QFont.Bold))
        actions_title.setStyleSheet("color: #333;")
        actions_layout.addWidget(actions_title)
        
        session_actions_layout = QHBoxLayout()
        session_actions_layout.setSpacing(10)
        
        self.run_session_btn = QPushButton("Ejecutar Sesión", self)
        self.run_session_btn.setFont(QFont("Arial", 11, QFont.Bold))
        self.run_session_btn.setStyleSheet("""
            QPushButton {
                padding: 12px 20px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.run_session_btn.clicked.connect(self.ejecutar_sesion)
        self.run_session_btn.setEnabled(False)
        session_actions_layout.addWidget(self.run_session_btn)
        
        self.view_sessions_folder_btn = QPushButton("Abrir Carpeta", self)
        self.view_sessions_folder_btn.setFont(QFont("Arial", 11))
        self.view_sessions_folder_btn.setStyleSheet("""
            QPushButton {
                padding: 12px 20px;
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.view_sessions_folder_btn.clicked.connect(self.abrir_carpeta_sesiones)
        self.view_sessions_folder_btn.setEnabled(False)
        session_actions_layout.addWidget(self.view_sessions_folder_btn)
        
        self.delete_session_btn = QPushButton("Eliminar Sesión", self)
        self.delete_session_btn.setFont(QFont("Arial", 11, QFont.Bold))
        self.delete_session_btn.setStyleSheet("""
            QPushButton {
                padding: 12px 20px;
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.delete_session_btn.clicked.connect(self.borrar_sesion)
        self.delete_session_btn.setEnabled(False)
        session_actions_layout.addWidget(self.delete_session_btn)
        
        actions_layout.addLayout(session_actions_layout)
        actions_container.setLayout(actions_layout)
        main_layout.addWidget(actions_container)

        # SECCIÓN 6: CONFIGURACIÓN Y SALIDA
        bottom_container = QWidget()
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)
        
        config_btn = QPushButton("Configuración", self)
        config_btn.setFont(QFont("Arial", 11))
        config_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #ffc107;
                color: #212529;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
        """)
        config_btn.clicked.connect(self.abrir_configuracion)
        bottom_layout.addWidget(config_btn)
        
        bottom_layout.addStretch()
        
        exit_btn = QPushButton("Salir", self)
        exit_btn.setFont(QFont("Arial", 11))
        exit_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        exit_btn.clicked.connect(self.close)
        bottom_layout.addWidget(exit_btn)
        
        bottom_container.setLayout(bottom_layout)
        main_layout.addWidget(bottom_container)

        self.setLayout(main_layout)

    def aplicar_tema(self):
        if self.tema == "Oscuro":
            self.setStyleSheet("""
                QWidget {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QLabel {
                    color: #ffffff;
                }
            """)
            
            # Actualizar estilos para tema oscuro
            self.sessions_tree.setStyleSheet("""
                QTreeWidget {
                    background-color: #3c3c3c;
                    border: 1px solid #555;
                    border-radius: 8px;
                    color: #ffffff;
                    alternate-background-color: #444444;
                }
                QTreeWidget::item {
                    padding: 8px;
                    border-bottom: 1px solid #555;
                }
                QTreeWidget::item:selected {
                    background-color: #0078d4;
                    color: white;
                }
                QTreeWidget::item:hover {
                    background-color: #484848;
                }
                QHeaderView::section {
                    background-color: #404040;
                    padding: 10px;
                    border: none;
                    border-bottom: 2px solid #555;
                    font-weight: bold;
                    color: #ffffff;
                }
            """)
            
            self.session_name_input.setStyleSheet("""
                QLineEdit {
                    padding: 12px;
                    border: 2px solid #555;
                    border-radius: 8px;
                    background-color: #3c3c3c;
                    color: #ffffff;
                }
                QLineEdit:focus {
                    border-color: #0078d4;
                }
            """)
            
            self.space_info_label.setStyleSheet("""
                QLabel {
                    background-color: #404040;
                    padding: 10px;
                    border-radius: 6px;
                    color: #ffffff;
                }
            """)
            
            # Actualizar contenedor de creación para tema oscuro
            creation_containers = self.findChildren(QWidget)
            for container in creation_containers:
                if container.styleSheet() and "background-color: #f8f9fa" in container.styleSheet():
                    container.setStyleSheet("""
                        QWidget {
                            background-color: #404040;
                            border-radius: 10px;
                            padding: 15px;
                        }
                    """)
            
            # Actualizar títulos para tema oscuro
            titles = self.findChildren(QLabel)
            for title in titles:
                if title.styleSheet() and "color: #333" in title.styleSheet():
                    title.setStyleSheet(title.styleSheet().replace("color: #333", "color: #ffffff"))
        else:
            # Tema claro (por defecto)
            self.setStyleSheet("""
                QWidget {
                    background-color: #ffffff;
                    color: #333333;
                }
            """)
            
            # Restaurar estilos originales para tema claro
            self.sessions_tree.setStyleSheet("""
                QTreeWidget {
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    background-color: white;
                    alternate-background-color: #f8f9fa;
                }
                QTreeWidget::item {
                    padding: 8px;
                    border-bottom: 1px solid #eee;
                }
                QTreeWidget::item:selected {
                    background-color: #007bff;
                    color: white;
                }
                QTreeWidget::item:hover {
                    background-color: #e9ecef;
                }
                QHeaderView::section {
                    background-color: #f1f3f4;
                    padding: 10px;
                    border: none;
                    border-bottom: 2px solid #dee2e6;
                    font-weight: bold;
                    color: #333;
                }
            """)
            
            self.session_name_input.setStyleSheet("""
                QLineEdit {
                    padding: 12px;
                    border: 2px solid #e0e0e0;
                    border-radius: 8px;
                    background-color: white;
                    color: #333;
                }
                QLineEdit:focus {
                    border-color: #007bff;
                }
            """)
            
            self.space_info_label.setStyleSheet("""
                QLabel {
                    background-color: #e9ecef;
                    padding: 10px;
                    border-radius: 6px;
                    color: #495057;
                }
            """)

    def on_header_click(self, logical_index):
        if logical_index == 0:
            current_order = self.sort_orders['name']
            self.sessions_tree.sortItems(0, current_order)
            self.sort_orders['name'] = Qt.AscendingOrder if current_order == Qt.DescendingOrder else Qt.DescendingOrder
        elif logical_index == 1:
            current_order = self.sort_orders['date']
            self.sort_sessions_by_date(current_order)
            self.sort_orders['date'] = Qt.AscendingOrder if current_order == Qt.DescendingOrder else Qt.DescendingOrder
        elif logical_index == 2:
            current_order = self.sort_orders['size']
            self.sort_sessions_by_size(current_order)
            self.sort_orders['size'] = Qt.AscendingOrder if current_order == Qt.DescendingOrder else Qt.DescendingOrder
        self.actualizar_botones()

    def sort_sessions_by_date(self, order):
        items = []
        for index in range(self.sessions_tree.topLevelItemCount()):
            item = self.sessions_tree.topLevelItem(index)
            items.append({
                'name': item.text(0),
                'date': item.text(1),
                'size': item.text(2)
            })
        items.sort(key=lambda x: datetime.strptime(x['date'], "%Y-%m-%d %H:%M:%S"), reverse=order == Qt.DescendingOrder)
        self.sessions_tree.clear()
        for item_data in items:
            new_item = QTreeWidgetItem([item_data['name'], item_data['date'], item_data['size']])
            self.sessions_tree.addTopLevelItem(new_item)

    def sort_sessions_by_size(self, order):
        items = []
        for index in range(self.sessions_tree.topLevelItemCount()):
            item = self.sessions_tree.topLevelItem(index)
            size_text = item.text(2)
            match = re.search(r'(\d+(\.\d+)?)\s*(B|KB|MB|GB|TB)', size_text)
            if match:
                size_value = float(match.group(1))
                size_unit = match.group(3)
                size_in_bytes = self.convert_to_bytes(size_value, size_unit)
            else:
                size_in_bytes = 0
            items.append({
                'name': item.text(0),
                'date': item.text(1),
                'size': item.text(2),
                'size_in_bytes': size_in_bytes
            })
        items.sort(key=lambda x: x['size_in_bytes'], reverse=order == Qt.DescendingOrder)
        self.sessions_tree.clear()
        for item_data in items:
            new_item = QTreeWidgetItem([item_data['name'], item_data['date'], item_data['size']])
            self.sessions_tree.addTopLevelItem(new_item)

    def convert_to_bytes(self, size_value, size_unit):
        unit_multipliers = {'B': 1, 'KB': 1024, 'MB': 1024 ** 2, 'GB': 1024 ** 3, 'TB': 1024 ** 4}
        return size_value * unit_multipliers[size_unit.upper()]

    def cargar_configuracion(self):
        config_path = os.path.join('Storage', 'Settings', 'constants.json')
        if not os.path.exists(config_path):
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            chrome_path = self.detectar_ruta_chrome()
            default_config = {
                "chrome_ruta": chrome_path,
                "tema": "Oscuro"
            }
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=4)
            return default_config
        else:
            with open(config_path, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    default_config = {
                        "chrome_ruta": self.detectar_ruta_chrome(),
                        "tema": "Oscuro"
                    }
                    with open(config_path, 'w') as f:
                        json.dump(default_config, f, indent=4)
                    return default_config

    def guardar_configuracion(self):
        config_path = os.path.join('Storage', 'Settings', 'constants.json')
        self.config['tema'] = self.tema
        with open(config_path, 'w') as f:
            json.dump(self.config, f, indent=4)

    def detectar_ruta_chrome(self):
        if os.name == 'nt':
            possible_paths = [
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome', 'Application', 'chrome.exe'),
                os.path.join(os.environ.get('PROGRAMFILES', ''), 'Google', 'Chrome', 'Application', 'chrome.exe'),
                os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), 'Google', 'Chrome', 'Application', 'chrome.exe')
            ]
        elif sys.platform == 'darwin':
            possible_paths = [
                '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                os.path.expanduser('~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
            ]
        else:
            possible_paths = [
                '/usr/bin/google-chrome',
                '/usr/bin/google-chrome-stable',
                '/usr/bin/chrome',
                '/snap/bin/google-chrome'
            ]
        for path in possible_paths:
            if os.path.isfile(path):
                return path
        if os.name == 'nt':
            return os.path.join(os.environ.get('PROGRAMFILES', ''), 'Google', 'Chrome', 'Application', 'chrome.exe')
        elif sys.platform == 'darwin':
            return '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        else:
            return '/usr/bin/google-chrome'

    def cargar_sesiones_existentes(self):
        storage_path = os.path.join('Storage', 'Settings', 'sessions.json')
        if not os.path.exists(storage_path):
            os.makedirs(os.path.dirname(storage_path), exist_ok=True)
            with open(storage_path, 'w') as f:
                json.dump({}, f, indent=4)
        with open(storage_path, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}

    def guardar_sesiones(self):
        storage_path = os.path.join('Storage', 'Settings', 'sessions.json')
        try:
            os.makedirs(os.path.dirname(storage_path), exist_ok=True)
            with open(storage_path, 'w', encoding='utf-8') as f:
                json.dump(self.sesiones, f, indent=4, ensure_ascii=False)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar las sesiones: {str(e)}", QMessageBox.Ok)

    def mostrar_sesiones(self):
        self.sessions_tree.clear()
        for nombre_sesion, fecha_hora in self.sesiones.items():
            size_text = "Estimando..."
            
            if nombre_sesion in self.session_sizes:
                size_bytes = self.session_sizes[nombre_sesion]
                total_space = self.calcular_espacio_ocupado_cache()
                porcentaje_uso = (size_bytes / total_space) * 100 if total_space > 0 else 0
                size_text = f"{self.format_size(size_bytes)} ({porcentaje_uso:.1f}% del espacio total ocupado)"
            
            item = QTreeWidgetItem([nombre_sesion, fecha_hora, size_text])
            self.sessions_tree.addTopLevelItem(item)
            
            # Iniciar cálculo asíncrono si no está en cache
            if nombre_sesion not in self.session_sizes and nombre_sesion not in self.calculating_sizes:
                self.start_size_calculation(nombre_sesion)
        
        self.actualizar_botones()
        for column in range(self.sessions_tree.columnCount()):
            self.sessions_tree.resizeColumnToContents(column)
            current_width = self.sessions_tree.columnWidth(column)
            self.sessions_tree.setColumnWidth(column, current_width + 20)
        self.actualizar_espacio()
        self.view_sessions_folder_btn.setVisible(len(self.sesiones) > 0)
    
    def start_size_calculation(self, session_name):
        if session_name in self.calculating_sizes:
            return
            
        self.calculating_sizes.add(session_name)
        session_path = os.path.join('Storage', 'Sessions', session_name)
        
        # Detener thread anterior si existe
        if session_name in self.size_threads:
            self.size_threads[session_name].stop()
            self.size_threads[session_name].wait()
        
        thread = SizeCalculatorThread(session_name, session_path)
        thread.size_calculated.connect(self.on_size_calculated)
        thread.finished.connect(lambda: self.calculating_sizes.discard(session_name))
        self.size_threads[session_name] = thread
        thread.start()
    
    def on_size_calculated(self, session_name, size_bytes):
        self.session_sizes[session_name] = size_bytes
        self.update_session_display(session_name)
    
    def update_session_display(self, session_name):
        for i in range(self.sessions_tree.topLevelItemCount()):
            item = self.sessions_tree.topLevelItem(i)
            if item.text(0) == session_name:
                size_bytes = self.session_sizes.get(session_name, 0)
                total_space = self.calcular_espacio_ocupado_cache()
                porcentaje_uso = (size_bytes / total_space) * 100 if total_space > 0 else 0
                size_text = f"{self.format_size(size_bytes)} ({porcentaje_uso:.1f}% del espacio total ocupado)"
                item.setText(2, size_text)
                break
    
    def calculate_pending_sizes(self):
        # Actualizar espacio total periódicamente
        self.actualizar_espacio()
        
        # Limpiar threads terminados
        finished_threads = [name for name, thread in self.size_threads.items() if thread.isFinished()]
        for name in finished_threads:
            del self.size_threads[name]
    
    def calcular_espacio_ocupado_cache(self):
        return sum(self.session_sizes.values())
    
    def calcular_tamano_sesion(self, nombre_sesion):
        # Usar cache si está disponible
        if nombre_sesion in self.session_sizes:
            return self.session_sizes[nombre_sesion]
        
        # Cálculo rápido solo para archivos principales
        storage_r = Path('Storage') / 'Sessions' / nombre_sesion
        try:
            if storage_r.exists():
                total_size = 0
                # Solo contar archivos de nivel superior para estimación rápida
                for item in storage_r.iterdir():
                    if item.is_file():
                        total_size += item.stat().st_size
                return total_size
            return 0
        except Exception:
            return 0

    def calcular_espacio_ocupado_directorio(self, directory):
        try:
            directory_path = Path(directory)
            return sum(f.stat().st_size for f in directory_path.rglob('*') if f.is_file())
        except Exception:
            return 0

    def calcular_espacio_ocupado(self):
        storage_dir = os.path.join('Storage', 'Sessions')
        if not os.path.exists(storage_dir):
            return 0
        return self.calcular_espacio_ocupado_directorio(storage_dir)

    def obtener_espacio_libre(self):
        if os.name == 'nt':
            import ctypes
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(os.path.abspath('.')), None, None, ctypes.pointer(free_bytes))
            return free_bytes.value
        elif os.name == 'posix':
            if hasattr(os, 'statvfs'):
                disk_info = os.statvfs('/')
                return disk_info.f_frsize * disk_info.f_bavail
            else:
                st = os.statvfs(os.path.abspath('.'))
                return st.f_bavail * st.f_frsize

    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"

    def actualizar_espacio(self):
        espacio_ocupado = self.calcular_espacio_ocupado()
        espacio_libre = self.obtener_espacio_libre()
        self.space_info_label.setText(f"Espacio total ocupado: {self.format_size(espacio_ocupado)}  -  Espacio libre: {self.format_size(espacio_libre)}")

    def actualizar_botones(self):
        selected_item = self.sessions_tree.currentItem()
        has_sessions = len(self.sesiones) > 0
        
        if selected_item:
            self.run_session_btn.setEnabled(True)
            self.delete_session_btn.setEnabled(True)
        else:
            self.run_session_btn.setEnabled(False)
            self.delete_session_btn.setEnabled(False)
        
        self.view_sessions_folder_btn.setEnabled(has_sessions)

    def crear_sesion(self):
        nombre_instancia = self.session_name_input.text().strip()
        chrome_ruta = self.config['chrome_ruta']
        if not nombre_instancia:
            QMessageBox.warning(self, "Error", "Debe ingresar un nombre para la sesión.", QMessageBox.Ok)
            return
        if nombre_instancia in self.sesiones:
            QMessageBox.warning(self, "Error", "La sesión ya existe.", QMessageBox.Ok)
            return
        fecha_hora_creacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.sesiones[nombre_instancia] = fecha_hora_creacion
        self.guardar_sesiones()
        self.crear_instancia_chrome(nombre_instancia, chrome_ruta)
        self.mostrar_sesiones()
        self.session_name_input.clear()
        self.view_sessions_folder_btn.setVisible(True)

    def ejecutar_sesion(self):
        selected_item = self.sessions_tree.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Seleccionar Sesión", "Debe seleccionar una sesión antes de ejecutar.", QMessageBox.Ok)
            return
        nombre_sesion = selected_item.text(0)
        chrome_ruta = self.config['chrome_ruta']
        self.crear_instancia_chrome(nombre_sesion, chrome_ruta)

    def borrar_sesion(self):
        selected_item = self.sessions_tree.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Seleccionar Sesión", "Debe seleccionar una sesión antes de borrar.", QMessageBox.Ok)
            return
        nombre_sesion = selected_item.text(0)
        confirm = QMessageBox.question(self, "Confirmar Borrado", f"¿Está seguro de que desea borrar la sesión '{nombre_sesion}' permanentemente?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            storage_r = os.path.join('Storage', 'Sessions', nombre_sesion)
            try:
                if os.path.exists(storage_r):
                    shutil.rmtree(storage_r, ignore_errors=True)
                if nombre_sesion in self.sesiones:
                    del self.sesiones[nombre_sesion]
                    self.guardar_sesiones()
                self.mostrar_sesiones()
                self.view_sessions_folder_btn.setVisible(len(self.sesiones) > 0)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar la sesión: {str(e)}", QMessageBox.Ok)

    def crear_instancia_chrome(self, nombre_instancia, chrome_ruta):
        def find_available_port():
            for port in range(49152, 65536):
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    result = s.connect_ex(('127.0.0.1', port))
                    if result != 0:
                        return port
            return None

        if not os.path.isfile(chrome_ruta):
            chrome_ruta = self.detectar_ruta_chrome()
            if not chrome_ruta:
                QMessageBox.critical(self, "Error", "No se pudo encontrar Google Chrome instalado en el sistema.", QMessageBox.Ok)
                return

        port = find_available_port()
        if port is None:
            QMessageBox.critical(self, "Error", "No se pudo encontrar un puerto disponible.", QMessageBox.Ok)
            return

        storage_r = os.path.join('Storage', 'Sessions', nombre_instancia)
        if not os.path.exists(storage_r):
            os.makedirs(storage_r)

        # Crear archivos de inicialización para evitar errores de Chrome
        self.inicializar_sesion_chrome(storage_r)

        url = "https://www.google.com/"

        try:
            chrome_args = [
                chrome_ruta,
                f"--remote-debugging-port={port}",
                f"--user-data-dir={os.path.abspath(storage_r)}",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-default-apps",
                "--disable-extensions-file-access-check",
                "--disable-extensions-http-throttling",
                "--disable-background-mode",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-features=TranslateUI",
                "--disable-ipc-flooding-protection",
                url
            ]
            
            if os.name == 'nt':
                subprocess.Popen(chrome_args, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            else:
                subprocess.Popen(chrome_args, start_new_session=True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al iniciar Chrome: {str(e)}", QMessageBox.Ok)
    
    def inicializar_sesion_chrome(self, storage_path):
        """Inicializa archivos básicos para evitar errores de Chrome"""
        try:
            # Crear directorio Default si no existe
            default_dir = os.path.join(storage_path, 'Default')
            os.makedirs(default_dir, exist_ok=True)
            
            # Crear archivo de preferencias básico
            preferences = {
                "profile": {
                    "default_content_setting_values": {
                        "notifications": 2
                    },
                    "default_content_settings": {
                        "popups": 0
                    }
                },
                "first_run_tabs": ["https://www.google.com/"]
            }
            
            prefs_path = os.path.join(default_dir, 'Preferences')
            with open(prefs_path, 'w') as f:
                json.dump(preferences, f)
            
            # Crear archivo First Run
            first_run_path = os.path.join(storage_path, 'First Run')
            with open(first_run_path, 'w') as f:
                f.write('')
                
        except Exception:
            pass  # Si hay error, Chrome se encargará de crear los archivos

    def abrir_configuracion(self):
        config_dialog = ConfiguracionDialog(self.config, self)
        config_dialog.exec_()
        self.config = config_dialog.get_config()
        self.guardar_configuracion()

    def abrir_carpeta_sesiones(self):
        folder_path = os.path.abspath(os.path.join('Storage', 'Sessions'))
        if os.path.exists(folder_path):
            if os.name == 'nt':
                os.startfile(folder_path)
            elif sys.platform == 'darwin':
                subprocess.call(['open', folder_path])
            else:
                subprocess.call(['xdg-open', folder_path])
        else:
            QMessageBox.warning(self, "Error", "La carpeta de sesiones no existe.", QMessageBox.Ok)

    def actualizar_todo(self):
        self.sesiones = self.cargar_sesiones_existentes()
        self.mostrar_sesiones()
        self.actualizar_espacio()
    
    def closeEvent(self, event):
        for thread in self.size_threads.values():
            thread.stop()
        for thread in self.size_threads.values():
            thread.wait()
        event.accept()
