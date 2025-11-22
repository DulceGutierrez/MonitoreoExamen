import tkinter as tk
from tkinter import messagebox
import cv2
import time
from face_detection_module import FaceDetectionModule
from event_monitor import EventMonitor
from PIL import Image, ImageTk

class ProctoringApp:
    """
    Aplicación principal que integra la interfaz, la visión por computadora y el monitoreo de eventos.
    """
    def __init__(self, window, window_title="Monitoreo de Examen"):
        self.window = window
        self.window.title(window_title)

        #Módulos y Estados
        self.face_detector = FaceDetectionModule()
        self.event_monitor = EventMonitor()
        self.cap = cv2.VideoCapture(0)  # Inicializa la cámara 
        self.is_exam_running = False
        self.exam_start_time = None
        self.total_attention_frames = 0
        self.total_frames = 0
        self.frame_delay = 15  # Milisegundos de retraso (aprox. 66 FPS si no hay procesamiento)

        #Configuración de la Interfaz (Tkinter)
        self.setup_ui()

        #Iniciar bucle de actualización de video
        self.update_video_stream()

        #Configurar protocolo de cierre para detener hilos
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_ui(self):
        #Contenedor principal para el video
        self.video_label = tk.Label(self.window)
        self.video_label.pack(padx=10, pady=10)

        #Botón de control
        self.btn_toggle = tk.Button(self.window, text="Iniciar Examen", 
                                    width=50, command=self.toggle_exam_state)
        self.btn_toggle.pack(anchor=tk.CENTER, expand=True, pady=10)

        #Marco para las estadísticas
        self.stats_frame = tk.LabelFrame(self.window, text="Estadísticas de Examen")
        self.stats_frame.pack(padx=10, pady=5, fill="x")
        
        self.stats_labels = {}
        labels = [
            "Total Duración:", "Tiempo Atención:", "Tiempo No Atención:",
            "Giro Izquierda:", "Giro Derecha:", "Giro Arriba:", "Giro Abajo:",
            "Cambio Mouse:", "Cambio Teclado:"
        ]
        
        for i, text in enumerate(labels):
            tk.Label(self.stats_frame, text=text, anchor="w").grid(row=i, column=0, sticky="w", padx=5, pady=2)
            self.stats_labels[text] = tk.Label(self.stats_frame, text="0.0s", anchor="e", fg="blue")
            self.stats_labels[text].grid(row=i, column=1, sticky="e", padx=5, pady=2)

    def toggle_exam_state(self):
        if not self.is_exam_running:
            #INICIAR EXAMEN
            self.is_exam_running = True
            self.exam_start_time = time.time()
            self.total_frames = 0
            self.total_attention_frames = 0
            self.face_detector.reset_stats()
            self.event_monitor.start_monitoring()
            self.btn_toggle.config(text="Detener Examen y Mostrar Resultados", bg="red", fg="white")
        else:
            #DETENER EXAMEN
            self.is_exam_running = False
            self.event_monitor.stop_monitoring()
            self.btn_toggle.config(text="Iniciar Examen", bg="green", fg="white")
            self.show_final_statistics()

    def update_video_stream(self):
        #Captura el frame de la cámara
        ret, frame = self.cap.read()

        if ret:
            #Procesar frame con el módulo de detección de rostro
            processed_frame, is_attentive = self.face_detector.process_frame(frame)
            
            #Convertir el frame de OpenCV a formato Tkinter
            processed_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(processed_frame))
            self.video_label.config(image=self.photo)
            
            if self.is_exam_running:
                self.total_frames += 1
                if is_attentive:
                    self.total_attention_frames += 1
                self.update_statistics_display()

        #Llamar a esta función nuevamente después de 'self.frame_delay' ms
        self.window.after(self.frame_delay, self.update_video_stream)

    def update_statistics_display(self):
        if self.exam_start_time is None: return

        current_duration = time.time() - self.exam_start_time
        
        #Convertir frames a tiempo (aproximación)
        #Tiempo por frame (Tpf) = Duración Total / Frames Totales
        Tpf = current_duration / self.total_frames if self.total_frames > 0 else 0
        
        #Estadísticas de Visión
        vision_stats = self.face_detector.get_stats()
        time_attentive = vision_stats["attention"] * Tpf
        time_non_attentive_vision = vision_stats["no_attention"] * Tpf

        #Estadísticas de Eventos
        event_stats = self.event_monitor.get_stats()
        
        #Tiempo de No Atención total (por simplificación y para evitar duplicidad de conteo (visión vs eventos), se usará el tiempo real de los eventos capturados por frame/seg.
        time_no_attention = (time.time() - self.exam_start_time) - time_attentive

        #Actualizar etiquetas
        self.stats_labels["Total Duración:"].config(text=f"{current_duration:.1f}s")
        self.stats_labels["Tiempo Atención:"].config(text=f"{time_attentive:.1f}s")
        self.stats_labels["Tiempo No Atención:"].config(text=f"{time_no_attention:.1f}s")
        
        #Distribución de No Atención (basado en conteo de frames)
        self.stats_labels["Giro Izquierda:"].config(text=f"{vision_stats['left'] * Tpf:.1f}s")
        self.stats_labels["Giro Derecha:"].config(text=f"{vision_stats['right'] * Tpf:.1f}s")
        self.stats_labels["Giro Arriba:"].config(text=f"{vision_stats['up'] * Tpf:.1f}s")
        self.stats_labels["Giro Abajo:"].config(text=f"{vision_stats['down'] * Tpf:.1f}s")

        #Conteo de eventos (no se usa tiempo, solo el conteo de acciones)
        self.stats_labels["Cambio Mouse:"].config(text=f"{event_stats['mouse_events']} eventos")
        self.stats_labels["Cambio Teclado:"].config(text=f"{event_stats['keyboard_events']} eventos")

    def show_final_statistics(self):
        final_stats = self.face_detector.get_stats()
        final_duration = time.time() - self.exam_start_time
        
        Tpf = final_duration / self.total_frames if self.total_frames > 0 else 0
        
        time_attentive = final_stats["attention"] * Tpf
        time_no_attention = final_duration - time_attentive
        
        #Cálculo de porcentaje de no atención
        if final_duration > 0:
            percent_no_attention = (time_no_attention / final_duration) * 100
        else:
            percent_no_attention = 0

        #Evaluar comportamiento sospechoso
        suspect_status = "NO"
        if percent_no_attention > 40:
            suspect_status = f"SÍ ({percent_no_attention:.1f}%)"

        #Resumen de eventos de ventana
        event_summary = self.event_monitor.get_stats()

        summary_text = (
            f"--- RESUMEN DEL EXAMEN ---\n\n"
            f"Duración Total: {final_duration:.1f}s\n"
            f"Tiempo de Atención: {time_attentive:.1f}s\n"
            f"Tiempo de No Atención: {time_no_attention:.1f}s\n\n"
            f"--- CAUSAS DE NO ATENCIÓN ---\n"
            f"  Giros Izquierda: {final_stats['left'] * Tpf:.1f}s\n"
            f"  Giros Derecha: {final_stats['right'] * Tpf:.1f}s\n"
            f"  Giros Arriba: {final_stats['up'] * Tpf:.1f}s\n"
            f"  Giros Abajo: {final_stats['down'] * Tpf:.1f}s\n\n"
            f"  Cambios de Mouse (Ventana): {event_summary['mouse_events']} veces\n"
            f"  Cambios de Teclado (Ventana): {event_summary['keyboard_events']} veces\n\n"
            f"--- EVALUACIÓN ---\n"
            f"Porcentaje de No Atención: {percent_no_attention:.1f}%\n"
            f"Comportamiento Sospechoso (>40%): {suspect_status}\n"
        )
        
        messagebox.showinfo("Resultados del Examen", summary_text)


    def on_close(self):
        #Limpieza de recursos al cerrar la aplicación
        if self.is_exam_running:
            self.event_monitor.stop_monitoring()
        if self.cap.isOpened():
            self.cap.release()
        self.window.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ProctoringApp(root)
    root.mainloop()