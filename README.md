# Detector de Vulnerabilidades en Dependencias Python

Aplicación de escritorio desarrollada en Python para analizar archivos de dependencias, como `requirements.txt`, y detectar vulnerabilidades conocidas mediante consultas a la base de datos OSV.

## Descripción

Este proyecto tiene como objetivo ofrecer una herramienta sencilla y accesible para revisar las librerías utilizadas en proyectos Python y comprobar si presentan problemas de seguridad conocidos.

La aplicación permite cargar un archivo de dependencias, procesar los paquetes detectados, consultar la API de OSV y mostrar los resultados de forma clara a través de una interfaz gráfica de escritorio.

Además, incorpora almacenamiento local para conservar el historial de análisis realizados por el usuario, lo que facilita la consulta posterior de ejecuciones previas.

## Funcionalidades principales

- Carga de archivos de dependencias, como `requirements.txt`.
- Análisis de paquetes y versiones detectadas.
- Consulta de vulnerabilidades conocidas mediante OSV.
- Visualización de resultados en una interfaz gráfica.
- Consulta de historial de análisis almacenado localmente.
- Gestión básica de errores durante el proceso de análisis.

## Tecnologías utilizadas

| Tecnología | Uso principal |
|---|---|
| Python | Lenguaje principal de la aplicación. |
| PySide6 | Desarrollo de la interfaz gráfica de escritorio. |
| SQLite | Almacenamiento local del historial y resultados. |
| HTTPX | Cliente HTTP para consultar la API de OSV. |
| pytest | Pruebas del sistema. |
| PyInstaller | Empaquetado de la aplicación en ejecutable. |

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

## Instalación para desarrollo

Los pasos siguientes son necesarios únicamente si se desea utilizar la aplicación o contribuir al desarrollo:

1. Clonar el repositorio.
2. Crear y activar un entorno virtual.
3. Instalar las dependencias del proyecto:

```bash
pip install -r requirements.txt
```

4. Ejecutar la aplicación en modo desarrollo:

```bash
python main.py
```

## Empaquetado

Si se desea generar de nuevo el ejecutable a partir del código fuente, puede utilizarse PyInstaller para empaquetar la aplicación:

```bash
pyinstaller safepy.spec
```

Este paso está orientado al desarrollo y distribución del proyecto, y no es necesario para el uso habitual de la aplicación por parte del usuario final.

## Estado del proyecto

Proyecto académico desarrollado como Trabajo de Fin de Grado, centrado en la detección de vulnerabilidades en dependencias Python de forma simple, rápida y accesible.