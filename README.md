# Google Chrome Session Manager
**Session Manager** es una aplicación de escritorio para gestionar múltiples sesiones paralelas de Google Chrome. Permite crear, ejecutar y eliminar sesiones independientes, cada una con su propio perfil y configuración, todo desde una interfaz gráfica intuitiva. También muestra el uso de almacenamiento y permite ver la carpeta donde se guardan las sesiones.

## Requisitos
- **Python** 3.10 o superior (Se usó Python 3.10.13)

## Instalación
1. **Clonar el repositorio:**

   ```bash
   git clone https://github.com/rodolfocasan/chrome-session-manager.git
   cd chrome-session-manager
   ```

2. **Instalar las dependencias necesarias:**

   ```bash
   python3 -m pip install --upgrade pip && pip3 cache purge && pip3 install -q DOCs/requirements.txt
   ```

## Configuración

1. **Ruta a Google Chrome:**
   
   La aplicación necesita conocer la ruta del ejecutable de Google Chrome en tu sistema. Puedes configurarla desde la interfaz gráfica accediendo al menú **Configuración**.

## Ejecución

Para ejecutar la aplicación, asegúrate de que el entorno virtual está activado y usa el siguiente comando:

```bash
python3 main.py
```

## Estructura de Archivos

- **`main.py`**: Código principal de la aplicación.
- **`Storage/Settings/constants.json`**: Archivo de configuración principal del programa.
- **`Storage/Settings/sessions.json`**: Archivo que guarda la información de las sesiones creadas.
- **`Storage/Sessions/`**: Carpeta que contiene los datos de cada sesión.

## Funcionalidades

- Crear nuevas sesiones de Chrome con un nombre personalizado.
- Ejecutar sesiones paralelas con perfiles independientes.
- Eliminar sesiones existentes y liberar espacio.
- Ver información sobre el uso de almacenamiento y espacio libre en disco.
- Configurar la ruta del ejecutable de Chrome desde la interfaz gráfica.

## Compilación

Para generar un archivo ejecutable de la aplicación, puedes usar `pyinstaller`. Sigue estos pasos:

1. **Instalar PyInstaller:**

   ```bash
   python3 -m pip install pyinstaller
   ```

2. **Ejecutar el comando de compilación**  
   Utiliza el siguiente comando para compilar el proyecto:

   - En **Windows**:
     ```bash
     pyinstaller --onefile --windowed --name "chrome_session_manager" --icon=Storage\Settings\icons\favicon.ico main.py
     ```

   - En **macOS / Linux**:
     ```bash
     pyinstaller --onefile --windowed --name "chrome_session_manager" --icon=Storage/Settings/icons/favicon.ico main.py
     ```

   El archivo ejecutable se generará en la carpeta `dist` dentro del directorio del proyecto.

Goodbye world!