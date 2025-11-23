import cv2
import numpy as np

class FaceDetectionModule:
    """
    Módulo de detección de rostro y estimación de dirección de cabeza:
    - Usa Haar cascades para localizar el rostro en cada frame.
    - Durante unos cuantos frames iniciales calibra una posición "neutral".
    - Después clasifica giros en: left, right, up, down.
    - Acumula TIEMPOS (en segundos) de atención y no atención.
    """

    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.reset_stats()

    def reset_stats(self):
        #Tiempos en segundos
        self.stats = {
            "left": 0.0,
            "right": 0.0,
            "up": 0.0,
            "down": 0.0,
            "attention": 0.0,
            "no_attention": 0.0,  #solo por giros / pérdida de rostro, no incluye ventana
        }
        #Calibración de posición neutral
        self.neutral_center = None
        self.calibration_frames = 0
        self.max_calibration_frames = 30  #~1 segundo si va a ~30 FPS
        self.last_direction = "center"

    def process_frame(self, frame, dt):
        """
        Procesa un frame de la cámara.
        Parámetros:
        - frame: imagen BGR de OpenCV.
        - dt: tiempo (en segundos) transcurrido desde el frame anterior.
        Devuelve:
        - frame_annotated: frame con dibujos/etiquetas.
        - is_attentive: bool, True si consideramos que el alumno miró al frente.
        - direction: string con la última dirección estimada.
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(60, 60),
            flags=cv2.CASCADE_SCALE_IMAGE,
        )

        gaze_direction = "center"
        is_attentive = True

        if len(faces) > 0:
            #Toma el rostro más grande
            faces_sorted = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
            x, y, w, h = faces_sorted[0]
            cx = x + w // 2
            cy = y + h // 2

            #Dibujar bbox (para señalar el rostro)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

            #Fase de calibración: asumime que el alumno está "mirando al frente"
            if self.neutral_center is None and self.calibration_frames < self.max_calibration_frames:
                self.calibration_frames += 1
                if self.neutral_center is None:
                    self.neutral_center = (float(cx), float(cy))
                else:
                    #Promedio exponencial suave
                    nx, ny = self.neutral_center
                    alpha = 0.1
                    self.neutral_center = (nx * (1 - alpha) + cx * alpha,
                                           ny * (1 - alpha) + cy * alpha)
                #Durante la calibración se considera atento
                if dt > 0:
                    self.stats["attention"] += dt
                gaze_direction = "center"
                is_attentive = True
            else:
                if self.neutral_center is None:
                    # Si no se logra calibrar usa el centro del propio rostro.
                    center_x, center_y = cx, cy
                else:
                    center_x, center_y = self.neutral_center

                #Umbral relativo al tamaño del rostro (más robusto que píxeles fijos)
                thresh_x = w * 0.25
                thresh_y = h * 0.15

                dx = cx - center_x
                dy = cy - center_y

                if dx < -thresh_x:
                    gaze_direction = "left"
                elif dx > thresh_x:
                    gaze_direction = "right"
                elif dy < -thresh_y:
                    gaze_direction = "up"
                elif dy > thresh_y:
                    gaze_direction = "down"
                else:
                    gaze_direction = "center"

                if gaze_direction == "center":
                    is_attentive = True
                    if dt > 0:
                        self.stats["attention"] += dt
                else:
                    is_attentive = False
                    if dt > 0:
                        self.stats[gaze_direction] += dt
                        self.stats["no_attention"] += dt

            self.last_direction = gaze_direction
        else:
            #No se detectó el rostro: se cuenta como no atención por pérdida de cara.
            is_attentive = False
            if dt > 0:
                self.stats["no_attention"] += dt
            gaze_direction = "not_detected"

        #Etiqueta visual
        cv2.putText(
            frame,
            f"Direccion: {gaze_direction}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )

        return frame, is_attentive, gaze_direction

    def get_stats(self):
        return dict(self.stats)