import cv2
import numpy as np
import time

class FaceDetectionModule:
    """
    Gestiona la detección de rostros y clasifica los giros de cabeza.
    Basado en los principios de tracking de objetos en tiempo real (Capítulo 8, Beyeler).
    """
    def __init__(self):
        # Usamos el clasificador pre-entrenado de Haar Cascade para detección de rostro
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.stats = {
            "left": 0, "right": 0, "up": 0, "down": 0, 
            "attention": 0, "no_attention": 0
        }
        self.frame_center = None
        self.threshold = 40  #Umbral de píxeles para considerar un giro

    def process_frame(self, frame):
        if self.frame_center is None:
            h, w = frame.shape[:2]
            self.frame_center = (w // 2, h // 2)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        #Detección multi-escala para encontrar rostros
        faces = self.face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1, 
            minNeighbors=5, 
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        gaze_direction = "center"
        is_attentive = True
        
        #Lógica de detección (sólo procesa el rostro más grande/primero)
        if len(faces) > 0:
            (x, y, w, h) = faces[0]
            face_center_x = x + w // 2
            face_center_y = y + h // 2
            
            #Dibujar rectángulo en el rostro detectado
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

            #Clasificar dirección del giro
            if face_center_x < self.frame_center[0] - self.threshold:
                gaze_direction = "left"
            elif face_center_x > self.frame_center[0] + self.threshold:
                gaze_direction = "right"
            elif face_center_y < self.frame_center[1] - self.threshold:
                gaze_direction = "up"
            elif face_center_y > self.frame_center[1] + self.threshold:
                gaze_direction = "down"
            else:
                gaze_direction = "center"

            #Actualizar estadísticas (giros)
            if gaze_direction != "center":
                is_attentive = False
                self.stats[gaze_direction] += 1
                self.stats["no_attention"] += 1
            else:
                self.stats["attention"] += 1

        else:
            #Si no detecta rostro, asume no atención
            is_attentive = False
            gaze_direction = "undetected"
            self.stats["no_attention"] += 1


        #Muestra la dirección del giro en el frame
        cv2.putText(frame, f"Giro: {gaze_direction}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        return frame, is_attentive

    def get_stats(self):
        return self.stats

    def reset_stats(self):
        self.stats = {
            "left": 0, "right": 0, "up": 0, "down": 0, 
            "attention": 0, "no_attention": 0
        }