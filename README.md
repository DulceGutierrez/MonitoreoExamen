# Sistema de Monitoreo de Atención en Exámenes en Línea Mediante Visión por Computadora

## Descripción

Este proyecto implementa una herramienta de monitoreo en tiempo real de la atención de los estudiantes durante exámenes en línea. Utilizando técnicas de visión por computadora, el sistema detecta el rostro del estudiante, calcula su nivel de atención mediante giros de cabeza y cambios de ventana, y genera estadísticas detalladas sobre su comportamiento durante el examen.  
La aplicación fue desarrollada en Python utilizando OpenCV para la detección de rostros, PyNput para monitoreo de eventos globales (como cambios de ventana), y Tkinter para la interfaz gráfica.

## Requisitos

- **Python 3.6+**
- **Librerías:**
  - `opencv-python`
  - `numpy`
  - `Pillow`
  - `pynput`
  - `tkinter`

## Instalación

1. Clona el repositorio:

```bash
git clone https://github.com/DulceGutierrez/MonitoreoExamen.git

## Uso

Para ejecutar el sistema de monitoreo, solo corre el siguiente comando en la terminal:

```bash
python Monitoreo.py