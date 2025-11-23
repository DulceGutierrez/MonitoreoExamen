from pynput import mouse, keyboard
import platform

#Para Windows: utilidad para obtener el título de la ventana activa
if platform.system() == "Windows":
    import ctypes
    from ctypes import wintypes 

    user32 = ctypes.windll.user32
    GetForegroundWindow = user32.GetForegroundWindow
    GetWindowTextW = user32.GetWindowTextW
    GetWindowTextLengthW = user32.GetWindowTextLengthW

    def get_active_window_title() -> str:
        hwnd = GetForegroundWindow()
        if hwnd == 0:
            return ""
        length = GetWindowTextLengthW(hwnd)
        if length == 0:
            return ""
        buff = ctypes.create_unicode_buffer(length + 1)
        GetWindowTextW(hwnd, buff, length + 1)
        return buff.value
else:
    #Para otros SO devolvemos cadena vacía en lugar de penalizar
    def get_active_window_title() -> str:  # type: ignore[override]
        return ""


class EventMonitor:
    """
    Monitorea eventos globales de mouse y teclado
    y detecta si el foco de ventana cambia (sale del examen).
    """

    def __init__(self):
        #Contadores de cambios de pantalla
        self.mouse_window_changes = 0
        self.keyboard_window_changes = 0

        #Último tipo de entrada que se usó
        self.last_input_type = "unknown"  # "mouse" | "keyboard" | "unknown"

        #Título de la ventana del examen
        self.exam_window_title: str | None = None

        #Estado anterior (dentro o fuera del examen)
        self._last_on_exam: bool = True

        #Listeners globales
        self.mouse_listener: mouse.Listener | None = None
        self.keyboard_listener: keyboard.Listener | None = None
        self.current_out_cause = None  # "mouse" | "keyboard" | None

        self.is_running = False

    #Callbacks de entrada
    def _on_mouse_click(self, x, y, button, pressed):
        if pressed:
            self.last_input_type = "mouse"

    def _on_key(self, key):
        self.last_input_type = "keyboard"

    #Control de monitor
    def start_monitoring(self):
        """Arranca listeners y fija la ventana actual como 'ventana de examen'."""
        if self.is_running:
            return

        self.exam_window_title = get_active_window_title() or None
        print("[EventMonitor] Ventana de examen:", self.exam_window_title)
        self._last_on_exam = True  # asumimos que empezamos dentro

        #Listeners globales
        self.mouse_listener = mouse.Listener(on_click=self._on_mouse_click)
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key,
            on_release=self._on_key,
        )
        self.mouse_listener.start()
        self.keyboard_listener.start()

        self.is_running = True

    def stop_monitoring(self):
        """Detiene listeners."""
        if not self.is_running:
            return

        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None

        self.is_running = False

    #Lógica principal
    def check_window(self):
        """
        Debe llamarse periódicamente.
        Devuelve:
        - on_exam_window: bool -> True si la ventana activa sigue siendo la del examen.
        - cause_state: "mouse" | "keyboard" | None ->mientras este FUERA de la ventana del examen indica qué tipo de entrada provocó que saliera (mouse o teclado). Si esta DENTRO, vale None.
        """
        if not self.exam_window_title:
            #No hay referencia; no penaliza.
            return True, None

        current_title = get_active_window_title()
        on_exam = (current_title == self.exam_window_title)

        #Detectar flancos
        if self._last_on_exam and not on_exam:
            #Acaba de salir de la ventana del examen
            if self.last_input_type == "mouse":
                self.mouse_window_changes += 1
                self.current_out_cause = "mouse"
            elif self.last_input_type == "keyboard":
                self.keyboard_window_changes += 1
                self.current_out_cause = "keyboard"
            else:
                self.current_out_cause = None

        elif (not self._last_on_exam) and on_exam:
            #Acaba de regresar a la ventana del examen
            self.current_out_cause = None

        self._last_on_exam = on_exam

        #Si esta fuera, devolve la causa actual;
        #si esta dentro, devolve None.
        cause_state = self.current_out_cause if not on_exam else None
        return on_exam, cause_state

    #Stats
    def get_stats(self):
        return {
            "mouse_changes": self.mouse_window_changes,
            "keyboard_changes": self.keyboard_window_changes,
        }

    def reset_stats(self):
        self.mouse_window_changes = 0
        self.keyboard_window_changes = 0
        self.last_input_type = "unknown"
        self._last_on_exam = True