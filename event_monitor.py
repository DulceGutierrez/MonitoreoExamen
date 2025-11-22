from pynput import mouse, keyboard
import threading
import time

class EventMonitor:
    """
    Monitorea eventos globales de mouse y teclado para simular cambios de ventana.
    """
    def __init__(self, update_interval=1.0):
        self.keyboard_events = 0
        self.mouse_events = 0
        self.is_running = False
        self.update_interval = update_interval
        
        self.mouse_listener = None
        self.keyboard_listener = None

    #Listeners (se ejecutan en threads separados)
    def on_key_release(self, key):
        #Incrementa el contador por cada liberación de tecla (simulando cambio)
        self.keyboard_events += 1

    def on_mouse_click(self, x, y, button, pressed):
        if pressed:
            #Incrementa el contador por cada click (simulando cambio)
            self.mouse_events += 1
    
    #Control de Monitoreo
    def start_monitoring(self):
        if self.is_running:
            return
        
        self.reset_stats()
        self.is_running = True
        
        #Inicia el listener de teclado
        self.keyboard_listener = keyboard.Listener(on_release=self.on_key_release)
        self.keyboard_listener.start()
        
        #Inicia el listener de mouse
        self.mouse_listener = mouse.Listener(on_click=self.on_mouse_click)
        self.mouse_listener.start()
        
    def stop_monitoring(self):
        if self.is_running:
            self.is_running = False
            if self.keyboard_listener:
                self.keyboard_listener.stop()
            if self.mouse_listener:
                self.mouse_listener.stop()

    def get_stats(self):
        return {
            "mouse_events": self.mouse_events,
            "keyboard_events": self.keyboard_events
        }

    def reset_stats(self):
        self.keyboard_events = 0
        self.mouse_events = 0