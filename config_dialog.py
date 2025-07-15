# config_dialog.py
import os
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QComboBox, QLineEdit, QPushButton, QFileDialog, 
                            QMessageBox, QGroupBox, QSpacerItem, QSizePolicy)





class ConfiguracionDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración")
        self.setGeometry(150, 150, 500, 350)
        self.setMinimumSize(480, 320)
        self.config = config
        self.parent = parent
        self.setup_ui()
        self.cargar_configuracion_actual()
        self.aplicar_estilos()

    def setup_ui(self):
        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Sección de Tema
        tema_group = QGroupBox("Apariencia")
        tema_group.setFont(QFont("Arial", 10, QFont.Bold))
        tema_layout = QVBoxLayout()
        
        tema_row = QHBoxLayout()
        tema_label = QLabel("Tema de la aplicación:")
        tema_label.setFont(QFont("Arial", 9))
        self.tema_selector = QComboBox(self)
        self.tema_selector.addItems(["Oscuro", "Encendido"])
        self.tema_selector.setFont(QFont("Arial", 9))
        self.tema_selector.setMinimumHeight(30)
        
        tema_row.addWidget(tema_label)
        tema_row.addStretch()
        tema_row.addWidget(self.tema_selector)
        
        tema_layout.addLayout(tema_row)
        tema_group.setLayout(tema_layout)
        main_layout.addWidget(tema_group)

        # Sección de Chrome
        chrome_group = QGroupBox("Configuración del Navegador")
        chrome_group.setFont(QFont("Arial", 10, QFont.Bold))
        chrome_layout = QVBoxLayout()
        chrome_layout.setSpacing(15)
        
        # Etiqueta descriptiva
        chrome_desc_label = QLabel("Especifica la ubicación de Google Chrome en tu sistema:")
        chrome_desc_label.setFont(QFont("Arial", 9))
        chrome_desc_label.setWordWrap(True)
        chrome_layout.addWidget(chrome_desc_label)
        
        # Campo de ruta
        ruta_layout = QVBoxLayout()
        ruta_label = QLabel("Ruta del ejecutable:")
        ruta_label.setFont(QFont("Arial", 9))
        
        self.chrome_ruta_input = QLineEdit(self)
        self.chrome_ruta_input.setFont(QFont("Arial", 9))
        self.chrome_ruta_input.setMinimumHeight(32)
        self.chrome_ruta_input.setPlaceholderText("Selecciona o detecta la ruta de Chrome...")
        
        ruta_layout.addWidget(ruta_label)
        ruta_layout.addWidget(self.chrome_ruta_input)
        chrome_layout.addLayout(ruta_layout)
        
        # Botones de Chrome
        chrome_buttons_layout = QHBoxLayout()
        chrome_buttons_layout.setSpacing(10)
        
        detect_chrome_btn = QPushButton("Detectar Automáticamente", self)
        detect_chrome_btn.setFont(QFont("Arial", 9))
        detect_chrome_btn.setMinimumHeight(35)
        detect_chrome_btn.clicked.connect(self.detectar_chrome_automaticamente)
        
        select_chrome_btn = QPushButton("Buscar Manualmente", self)
        select_chrome_btn.setFont(QFont("Arial", 9))
        select_chrome_btn.setMinimumHeight(35)
        select_chrome_btn.clicked.connect(self.seleccionar_ruta_chrome)
        
        chrome_buttons_layout.addWidget(detect_chrome_btn)
        chrome_buttons_layout.addWidget(select_chrome_btn)
        
        chrome_layout.addLayout(chrome_buttons_layout)
        chrome_group.setLayout(chrome_layout)
        main_layout.addWidget(chrome_group)

        # Espaciador flexible
        spacer = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        main_layout.addItem(spacer)

        # Botones de acción
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        
        # Espaciador para empujar botones a la derecha
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("Cancelar", self)
        cancel_btn.setFont(QFont("Arial", 9))
        cancel_btn.setMinimumSize(100, 35)
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Guardar", self)
        save_btn.setFont(QFont("Arial", 9, QFont.Bold))
        save_btn.setMinimumSize(100, 35)
        save_btn.setDefault(True)
        save_btn.clicked.connect(self.guardar)
        
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(save_btn)
        
        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)

    def aplicar_estilos(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                color: #333333;
                background-color: #f5f5f5;
            }
            
            QLabel {
                color: #333333;
                background-color: transparent;
            }
            
            QComboBox {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
                color: #333333;
                min-width: 120px;
            }
            
            QComboBox:hover {
                border-color: #999999;
            }
            
            QComboBox:focus {
                border-color: #0078d4;
            }
            
            QLineEdit {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 8px;
                background-color: white;
                color: #333333;
            }
            
            QLineEdit:hover {
                border-color: #999999;
            }
            
            QLineEdit:focus {
                border-color: #0078d4;
            }
            
            QPushButton {
                background-color: #e1e1e1;
                border: 1px solid #adadad;
                border-radius: 4px;
                padding: 8px 16px;
                color: #333333;
                font-weight: normal;
            }
            
            QPushButton:hover {
                background-color: #d4d4d4;
                border-color: #999999;
            }
            
            QPushButton:pressed {
                background-color: #c4c4c4;
            }
            
            QPushButton[default="true"] {
                background-color: #0078d4;
                border-color: #005a9e;
                color: white;
                font-weight: bold;
            }
            
            QPushButton[default="true"]:hover {
                background-color: #106ebe;
            }
            
            QPushButton[default="true"]:pressed {
                background-color: #005a9e;
            }
        """)

    def detectar_chrome_automaticamente(self):
        chrome_path = None
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
                chrome_path = path
                break

        if chrome_path:
            self.chrome_ruta_input.setText(chrome_path)
            QMessageBox.information(self, "Chrome Detectado", 
                                  f"Se ha detectado Chrome en:\n{chrome_path}", 
                                  QMessageBox.Ok)
        else:
            QMessageBox.warning(self, "Chrome No Encontrado", 
                              "No se pudo detectar Chrome automáticamente. Por favor, seleccione la ruta manualmente.", 
                              QMessageBox.Ok)

    def seleccionar_ruta_chrome(self):
        file_filter = "Chrome Executable ("
        if os.name == 'nt':
            file_filter += "chrome.exe"
        elif sys.platform == 'darwin':
            file_filter += "Google Chrome"
        else:
            file_filter += "chrome google-chrome"
        file_filter += ")"

        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter(file_filter)
        
        if file_dialog.exec_():
            selected_file = file_dialog.selectedFiles()[0]
            self.chrome_ruta_input.setText(selected_file)

    def cargar_configuracion_actual(self):
        self.tema_selector.setCurrentText(self.config.get("tema", "Oscuro"))
        self.chrome_ruta_input.setText(self.config.get("chrome_ruta", ""))

    def guardar(self):
        try:
            chrome_ruta = self.chrome_ruta_input.text().strip()
            
            if not chrome_ruta:
                QMessageBox.warning(self, "Error", 
                                  "Por favor, especifica la ruta de Chrome.", 
                                  QMessageBox.Ok)
                return
                
            if not os.path.isfile(chrome_ruta):
                QMessageBox.warning(self, "Error", 
                                  "La ruta especificada para Chrome no existe.", 
                                  QMessageBox.Ok)
                return

            self.config['tema'] = self.tema_selector.currentText()
            self.config['chrome_ruta'] = chrome_ruta
            
            if self.parent:
                self.parent.tema = self.config['tema']
                self.parent.aplicar_tema()
                self.parent.guardar_configuracion()
            
            QMessageBox.information(self, "Configuración Guardada", 
                                  "La configuración se ha guardado correctamente.", 
                                  QMessageBox.Ok)
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                               f"Error al guardar la configuración: {str(e)}", 
                               QMessageBox.Ok)

    def get_config(self):
        return self.config