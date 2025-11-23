import tkinter as tk
from tkinter import messagebox
import cv2
import time
from PIL import Image, ImageTk
from face_detection_module import FaceDetectionModule
from event_monitor import EventMonitor


class ProctoringApp:
    """
    Aplicación principal:
    - Muestra la cámara.
    - Botón para iniciar/detener el "examen".
    - Integra:
        * FaceDetectionModule (giros de cabeza).
        * EventMonitor (cambios de ventana por mouse/teclado).
    """

    def __init__(self, window, window_title="Monitoreo de Examen"):
        self.window = window
        self.window.title(window_title)

        #-----------Cámara-----------
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise RuntimeError("No se pudo abrir la cámara.")

        #-----------Módulos-----------
        self.face_detector = FaceDetectionModule()
        self.event_monitor = EventMonitor()

        #------Estado del examen------
        self.is_exam_running = False
        self.exam_start_time = None
        self.last_frame_time = None

        #Tiempos globales
        self.total_exam_time = 0.0
        self.attention_time = 0.0
        self.no_attention_time = 0.0

        #Tiempos por cambios de pantalla
        self.mouse_window_time = 0.0
        self.keyboard_window_time = 0.0

        #-------Interfaz Gráfica-------
        # Frame superior para el botón
        top_frame = tk.Frame(self.window)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        self.btn_toggle = tk.Button(
            top_frame,
            text="Iniciar Examen",
            command=self.toggle_exam_state,
            width=40,
        )
        self.btn_toggle.pack(side="top", padx=5, pady=5)

        #Label de video al centro
        self.video_label = tk.Label(self.window)
        self.video_label.pack(padx=5, pady=5)

        # Stats abajo, en dos columnas (izquierda/derecha)
        bottom_frame = tk.Frame(self.window)
        bottom_frame.pack(padx=10, pady=5, fill=tk.X)

        self.stats_label_left = tk.Label(
            bottom_frame,
            text="Examen no iniciado",
            font=("Arial", 11),
            justify="left",
            anchor="nw",
        )
        self.stats_label_left.pack(side=tk.LEFT, padx=150, pady=5, expand=True, fill=tk.BOTH)

        self.stats_label_right = tk.Label(
            bottom_frame,
            text="",
            font=("Arial", 11),
            justify="left",
            anchor="nw",
        )
        self.stats_label_right.pack(side=tk.LEFT, padx=3, pady=5, expand=True, fill=tk.BOTH)
    
        #Cerrar
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        #Arrancar loop de video
        self.update_frame()

    #--------Control del examen----------

    def reset_global_stats(self):
        self.total_exam_time = 0.0
        self.attention_time = 0.0
        self.no_attention_time = 0.0
        self.mouse_window_time = 0.0
        self.keyboard_window_time = 0.0

    def toggle_exam_state(self):
        if not self.is_exam_running:
            #INICIAR
            self.is_exam_running = True
            self.exam_start_time = time.time()
            self.last_frame_time = self.exam_start_time

            self.face_detector.reset_stats()
            self.event_monitor.reset_stats()
            self.reset_global_stats()

            #La ventana actual será la "ventana de examen"
            self.event_monitor.start_monitoring()

            self.btn_toggle.config(
                text="Detener Examen y Mostrar Resultados",
                bg="red",
                fg="white",
            )
            self.stats_label_left.config(text="Examen en curso...")
            self.stats_label_right.config(text="")
        else:
            #DETENER
            self.is_exam_running = False
            self.event_monitor.stop_monitoring()
            self.btn_toggle.config(
                text="Iniciar Examen",
                bg=self.window.cget("bg"),
                fg="black",
            )
            self.show_results()

    #-----------Bucle de video------------

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            self.stats_label_left.config(text="No se pudo leer de la cámara.")
            self.stats_label_right.config(text="")
        else:
            frame = cv2.flip(frame, 1)  # espejo

            #Calculamos dt
            now = time.time()
            if self.last_frame_time is None:
                dt = 0.0
            else:
                dt = now - self.last_frame_time
            self.last_frame_time = now

            #Procesamiento solo si el examen corre
            if self.is_exam_running and dt > 0:
                on_exam_window, cause = self.event_monitor.check_window()

                if not on_exam_window:
                    #Tiempo de no atención por cambio de pantalla
                    self.total_exam_time += dt
                    self.no_attention_time += dt

                    if cause == "mouse":
                        self.mouse_window_time += dt
                    elif cause == "keyboard":
                        self.keyboard_window_time += dt

                    #No procesamos cabeza para no mezclar causas
                    processed_frame = frame
                    is_attentive = False
                else:
                    processed_frame, head_attentive, _ = self.face_detector.process_frame(
                        frame, dt
                    )

                    self.total_exam_time += dt
                    if head_attentive:
                        self.attention_time += dt
                        is_attentive = True
                    else:
                        self.no_attention_time += dt
                        is_attentive = False

                #Actualizar texto de estadísticas en vivo
                self.update_statistics_display()
            else:
                #Examen parado: solo mostramos cámara sin contar tiempos
                processed_frame, _, _ = self.face_detector.process_frame(frame, 0.0)

            #Convertir para Tkinter
            processed_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(processed_frame)
            self.photo = ImageTk.PhotoImage(image=img)
            self.video_label.config(image=self.photo)

        #Re-programar llamada
        self.window.after(20, self.update_frame)

    def update_statistics_display(self):
        if self.total_exam_time <= 0:
            self.stats_label_left.config(text="Recopilando datos...")
            self.stats_label_right.config(text="")
            return

        att_pct = (self.attention_time / self.total_exam_time) * 100.0
        non_att_pct = (self.no_attention_time / self.total_exam_time) * 100.0

        fd_stats = self.face_detector.get_stats()
        em_stats = self.event_monitor.get_stats()

        left_text = (
            f"Duracion: {self.total_exam_time:5.1f} s\n"
            f"Atencion: {self.attention_time:5.1f} s ({att_pct:4.1f}%)\n"
            f"No atencion: {self.no_attention_time:5.1f} s ({non_att_pct:4.1f}%)\n\n"
            f"Giros izquierda: {fd_stats['left']:4.1f} s\n"
            f"Giros derecha:  {fd_stats['right']:4.1f} s\n"
            f"Giros arriba:   {fd_stats['up']:4.1f} s\n"
            f"Giros abajo:    {fd_stats['down']:4.1f} s\n\n"
        )
        right_text = (
            f"Tiempo fuera por mouse:    {self.mouse_window_time:4.1f} s\n"
            f"Tiempo fuera por teclado:  {self.keyboard_window_time:4.1f} s\n"
            f"Cambios ventana mouse:     {em_stats['mouse_changes']}\n"
            f"Cambios ventana teclado:   {em_stats['keyboard_changes']}"
        )
        self.stats_label_left.config(text=left_text)
        self.stats_label_right.config(text=right_text)

    #-------------Resultados finales---------------

    def show_results(self):
        if self.total_exam_time <= 0:
            messagebox.showinfo(
                "Resultados del Examen",
                "No se registraron datos suficientes.",
            )
            return

        att_pct = (self.attention_time / self.total_exam_time) * 100.0
        non_att_pct = (self.no_attention_time / self.total_exam_time) * 100.0

        fd_stats = self.face_detector.get_stats()
        em_stats = self.event_monitor.get_stats()

        summary = []
        summary.append("--- RESUMEN DEL EXAMEN ---")
        summary.append(f"Duracion Total: {self.total_exam_time:4.1f}s")
        summary.append(f"Tiempo de Atencion: {self.attention_time:4.1f}s")
        summary.append(f"Tiempo de No Atencion: {self.no_attention_time:4.1f}s")
        summary.append("")
        summary.append("--- CAUSAS DE NO ATENCION (GIROS) ---")
        summary.append(f"Giros Izquierda: {fd_stats['left']:4.1f}s")
        summary.append(f"Giros Derecha:   {fd_stats['right']:4.1f}s")
        summary.append(f"Giros Arriba:    {fd_stats['up']:4.1f}s")
        summary.append(f"Giros Abajo:     {fd_stats['down']:4.1f}s")
        summary.append("")
        summary.append("--- CAMBIOS DE PANTALLA ---")
        summary.append(f"Cambios Mouse (ventana):   {em_stats['mouse_changes']} veces")
        summary.append(f"Cambios Teclado (ventana): {em_stats['keyboard_changes']} veces")
        summary.append(
            f"Tiempo fuera por Mouse:    {self.mouse_window_time:4.1f}s"
        )
        summary.append(
            f"Tiempo fuera por Teclado:  {self.keyboard_window_time:4.1f}s"
        )
        summary.append("")
        summary.append("--- EVALUACION ---")
        summary.append(f"Porcentaje de No Atencion: {non_att_pct:4.1f}%")
        sospechoso = "SI" if non_att_pct > 40.0 else "NO"
        summary.append(f"Comportamiento Sospechoso (>40%): {sospechoso}")

        summary_text = "\n".join(summary)
        messagebox.showinfo("Resultados del Examen", summary_text)

    #-------------Limpieza-------------

    def on_close(self):
        if self.is_exam_running:
            self.event_monitor.stop_monitoring()
        if self.cap.isOpened():
            self.cap.release()
        self.window.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ProctoringApp(root)
    root.mainloop()