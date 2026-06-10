# Detector de Vulnerabilidades en Dependencias Python

Aplicación de escritorio desarrollada en Python para analizar archivos de dependencias, como `requirements.txt`, y detectar vulnerabilidades conocidas mediante consultas a la base de datos OSV.[web:255]

## Descripción

Este proyecto tiene como objetivo ofrecer una herramienta sencilla y accesible para revisar las librerías utilizadas en proyectos Python y comprobar si presentan problemas de seguridad conocidos.[cite:226][cite:258]

La aplicación permite cargar un archivo de dependencias, procesar los paquetes detectados, consultar la API de OSV y mostrar los resultados de forma clara a través de una interfaz gráfica de escritorio.[cite:223][web:255]

Además, incorpora almacenamiento local para conservar el historial de análisis realizados por el usuario, lo que facilita la consulta posterior de ejecuciones previas.[web:240]

## Funcionalidades principales

- Carga de archivos de dependencias, como `requirements.txt`.
- Análisis de paquetes y versiones detectadas.
- Consulta de vulnerabilidades conocidas mediante OSV.[cite:223]
- Visualización de resultados en una interfaz gráfica.
- Consulta de historial de análisis almacenado localmente.
- Gestión básica de errores durante el proceso de análisis.

## Tecnologías utilizadas

| Tecnología | Uso principal |
|---|---|
| Python | Lenguaje principal de la aplicación.[cite:227] |
| PySide6 | Desarrollo de la interfaz gráfica de escritorio.[web:257] |
| SQLite | Almacenamiento local del historial y resultados.[web:240] |
| HTTPX | Cliente HTTP para consultar la API de OSV.[web:255] |
| pytest | Pruebas del sistema. |
| PyInstaller | Empaquetado de la aplicación en ejecutable.[web:253] |

## Estructura general

```text
app/
├── ui/
├── presenters/
├── services/
├── persistence/
├── domain/
└── utils/
```

La aplicación se organiza de forma modular para separar la interfaz, la lógica de análisis, el acceso a datos y las utilidades auxiliares, lo que facilita su mantenimiento y evolución.

## Instalación

1. Clonar el repositorio.
2. Crear y activar un entorno virtual.
3. Instalar las dependencias del proyecto:

```bash
pip install -r requirements.txt
```

4. Ejecutar la aplicación:

```bash
python main.py
```

## Empaquetado

Para generar un ejecutable distribuible, puede emplearse PyInstaller, herramienta habitual para empaquetar aplicaciones Python en un formato autónomo.[web:253]

```bash
pyinstaller --onefile --windowed main.py
```

## Estado del proyecto

Proyecto académico en desarrollo como Trabajo de Fin de Grado, centrado en la detección de vulnerabilidades en dependencias Python de forma simple, rápida y accesible.[cite:226][cite:237]
