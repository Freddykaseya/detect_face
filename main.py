import cv2
import numpy as np
import mediapipe as mp
import math
import time
import threading
import pyttsx3
from collections import deque
import winsound  # Pour les bips sonores (Windows)
from dashboard_exporter import DashboardExporter  # 📊 Export pour dashboard


# -----------------------
# PARAMÈTRES À RÉGLER
# -----------------------
EAR_THRESHOLD = 0.23          # seuil de fermeture des yeux (à ajuster après test)
MIN_CLOSED_SECONDS = 1.5      # durée minimale yeux fermés pour déclencher l'alerte
ALERT_REPEAT_INTERVAL = 5.0   # répéter l'alerte toutes les 5 secondes
BEEP_INTERVAL = 1.0           # bip sonore toutes les 1 seconde pendant alerte
PERCLOS_WINDOW = 60.0         # fenêtre (secondes) pour estimer le "PERCLOS light"

# Paramètres détection mouvements de tête
HEAD_MOVEMENT_THRESHOLD = 12.0  # degrés de rotation pour considérer un mouvement
HEAD_MOVEMENT_WINDOW = 6.0      # fenêtre de temps (secondes) pour compter les mouvements
MIN_HEAD_MOVEMENTS = 4          # nombre minimum de changements de direction
HEAD_DROWSY_DURATION = 3.0      # durée minimale de balancement pour confirmer somnolence

# Paramètres détection tête baissée
HEAD_DOWN_THRESHOLD = -15.0     # pitch négatif = tête baissée (ajuster selon besoin)
HEAD_DOWN_DURATION = 2.0        # durée minimale tête baissée pour alerte
HEAD_DOWN_BEEP_INTERVAL = 1.5   # intervalle entre bips pour tête baissée


# -----------------------
# SYSTÈME D'ALERTE SONORE
# -----------------------
class AlertSystem:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 180)
        self.engine.setProperty('volume', 1.0)
        self.voice_lock = threading.Lock()
        self.is_speaking = False
        self.voice_queue = []
        
        # Pour le bip continu
        self.continuous_beep_active = False
        self.continuous_beep_thread = None
        
    def beep(self, frequency=2000, duration=200):
        """Bip sonore non bloquant"""
        def play_beep():
            try:
                winsound.Beep(frequency, duration)
            except:
                pass  # Si erreur, on ignore (peut arriver sur Linux/Mac)
        
        threading.Thread(target=play_beep, daemon=True).start()
    
    def start_continuous_beep(self, frequency=2500):
        """Démarre un bip VRAIMENT continu (piiiiiiii)"""
        if self.continuous_beep_active:
            return
        
        self.continuous_beep_active = True
        
        def continuous_loop():
            while self.continuous_beep_active:
                try:
                    winsound.Beep(frequency, 2000)  # Bip de 2 secondes
                except:
                    pass
        
        self.continuous_beep_thread = threading.Thread(target=continuous_loop, daemon=True)
        self.continuous_beep_thread.start()
    
    def stop_continuous_beep(self):
        """Arrête le bip continu"""
        self.continuous_beep_active = False
    
    def say_async(self, text, force=False):
        """Parle de façon non bloquante"""
        def speak():
            with self.voice_lock:
                self.is_speaking = True
                try:
                    self.engine.say(text)
                    self.engine.runAndWait()
                except:
                    pass
                self.is_speaking = False
        
        # Si force=True ou pas déjà en train de parler
        if force or not self.is_speaking:
            threading.Thread(target=speak, daemon=True).start()
            return True
        return False


mp_face_mesh = mp.solutions.face_mesh

LEFT_EYE = {"outer": 33, "inner": 133, "upper": 159, "lower": 145}
RIGHT_EYE = {"outer": 263, "inner": 362, "upper": 386, "lower": 374}

# Points pour calculer l'orientation de la tête
NOSE_TIP = 1
CHIN = 152
FOREHEAD = 10
LEFT_EAR = 234
RIGHT_EAR = 454


def dist(p1, p2):
    return math.hypot(p1[0]-p2[0], p1[1]-p2[1])


def eye_aspect_ratio(landmarks, eye_idx, w, h):
    def pt(i):
        return (int(landmarks[i].x * w), int(landmarks[i].y * h))
    outer = pt(eye_idx["outer"])
    inner = pt(eye_idx["inner"])
    upper = pt(eye_idx["upper"])
    lower = pt(eye_idx["lower"])
    vertical = dist(upper, lower)
    horizontal = dist(outer, inner)
    if horizontal == 0:
        return 0.0, (outer, inner, upper, lower)
    return (vertical / horizontal), (outer, inner, upper, lower)


def calculate_head_pose(landmarks, w, h):
    """Calcule l'angle d'inclinaison de la tête (pitch et yaw)"""
    def pt3d(i):
        return np.array([landmarks[i].x * w, landmarks[i].y * h, landmarks[i].z * w])
    
    nose = pt3d(NOSE_TIP)
    chin = pt3d(CHIN)
    forehead = pt3d(FOREHEAD)
    left_ear = pt3d(LEFT_EAR)
    right_ear = pt3d(RIGHT_EAR)
    
    # Calcul du yaw (rotation gauche-droite)
    ear_diff = left_ear[0] - right_ear[0]
    ear_distance = np.linalg.norm(left_ear - right_ear)
    if ear_distance > 0:
        yaw = math.degrees(math.asin(np.clip(ear_diff / ear_distance, -1.0, 1.0)))
    else:
        yaw = 0.0
    
    # Calcul du pitch (inclinaison haut-bas)
    vertical_vec = forehead - chin
    if np.linalg.norm(vertical_vec[:2]) > 0:
        pitch = math.degrees(math.atan2(vertical_vec[2], np.linalg.norm(vertical_vec[:2])))
    else:
        pitch = 0.0
    
    return pitch, yaw


def draw_eye_points(frame, pts):
    for p in pts:
        cv2.circle(frame, p, 2, (0, 255, 0), -1)


class PerclosWindow:
    def __init__(self, window_seconds=60.0):
        self.window = deque()
        self.window_seconds = window_seconds

    def update(self, closed_now):
        now = time.time()
        self.window.append((now, closed_now))
        cutoff = now - self.window_seconds
        while self.window and self.window[0][0] < cutoff:
            self.window.popleft()

    def perclos(self):
        if not self.window:
            return 0.0
        closed = sum(1 for _, c in self.window if c)
        return closed / len(self.window)


class HeadMovementDetector:
    def __init__(self, window_seconds=HEAD_MOVEMENT_WINDOW, threshold=HEAD_MOVEMENT_THRESHOLD):
        self.movements = deque()
        self.window_seconds = window_seconds
        self.threshold = threshold
        self.last_direction = None
        self.direction_changes = 0
        self.movement_start_time = None
        self.last_update_time = None
        
    def update(self, pitch, yaw):
        now = time.time()
        
        # Détermine la direction actuelle
        current_direction = "center"
        if abs(yaw) > self.threshold:
            current_direction = "right" if yaw > 0 else "left"
        elif abs(pitch) > self.threshold:
            current_direction = "down" if pitch > 0 else "up"
        
        # Détecte un changement de direction
        if current_direction != "center" and self.last_direction and current_direction != self.last_direction:
            self.direction_changes += 1
            if self.movement_start_time is None:
                self.movement_start_time = now
        
        # Ajoute le point
        self.movements.append((now, pitch, yaw, current_direction))
        
        # Élagage
        cutoff = now - self.window_seconds
        while self.movements and self.movements[0][0] < cutoff:
            self.movements.popleft()
        
        # Reset si pas de mouvement récent (inactivité de 2s)
        if self.last_update_time and (now - self.last_update_time) > 2.0:
            if current_direction == "center":
                self.direction_changes = 0
                self.movement_start_time = None
        
        if current_direction != "center":
            self.last_direction = current_direction
        
        self.last_update_time = now
        return current_direction
    
    def is_drowsy_head_movement(self):
        """Retourne True si détecte un pattern de balancement typique de somnolence"""
        if not self.movements or self.movement_start_time is None:
            return False
        
        now = time.time()
        movement_duration = now - self.movement_start_time
        
        return (self.direction_changes >= MIN_HEAD_MOVEMENTS and 
                movement_duration >= HEAD_DROWSY_DURATION)
    
    def get_stats(self):
        """Retourne statistiques pour affichage"""
        duration = 0.0
        if self.movement_start_time:
            duration = time.time() - self.movement_start_time
        return self.direction_changes, duration
    
    def reset(self):
        """Reset le détecteur"""
        self.direction_changes = 0
        self.movement_start_time = None
        self.last_direction = None


def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Impossible d'ouvrir la caméra.")
        print("Essayez de changer : cv2.VideoCapture(1)")
        return

    alert_system = AlertSystem()
    perclos = PerclosWindow(PERCLOS_WINDOW)
    head_detector = HeadMovementDetector()
    
    # 📊 Initialiser export dashboard
    exporter = DashboardExporter()
    print("📊 Dashboard activé : http://localhost:5000")

    # Variables pour yeux fermés
    closed_start_time = None
    eyes_alert_active = False
    last_eyes_voice_alert = 0.0
    last_eyes_beep = 0.0
    eyes_continuous_mode = False  # Pour savoir si on est en mode sirène continue
    
    # Variables pour mouvements tête
    head_alert_active = False
    last_head_voice_alert = 0.0
    last_head_beep = 0.0
    head_continuous_mode = False  # Pour savoir si on est en mode sirène continue
    
    # Variables pour tête baissée
    head_down_start_time = None
    head_down_alert_active = False
    last_head_down_beep = 0.0
    last_head_down_voice = 0.0
    
    status_text = "✓ OK"

    with mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as face_mesh:

        print("🎥 Système de détection de somnolence démarré")
        print(f"⚙️  Seuil EAR: {EAR_THRESHOLD}")
        print(f"⚙️  Durée yeux fermés: {MIN_CLOSED_SECONDS}s")
        print(f"⚙️  Alerte vocale toutes les: {ALERT_REPEAT_INTERVAL}s")
        print(f"⚙️  Bip sonore toutes les: {BEEP_INTERVAL}s")
        print("Press ESC pour quitter\n")

        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Flux vidéo interrompu.")
                break

            h, w = frame.shape[:2]
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(frame_rgb)

            now = time.time()

            if results.multi_face_landmarks:
                landmarks = results.multi_face_landmarks[0].landmark
                
                # ===== DÉTECTION YEUX =====
                left_ear, left_pts = eye_aspect_ratio(landmarks, LEFT_EYE, w, h)
                right_ear, right_pts = eye_aspect_ratio(landmarks, RIGHT_EYE, w, h)
                ear = (left_ear + right_ear) / 2.0
                draw_eye_points(frame, left_pts + right_pts)

                # Gestion fermeture yeux
                eye_closed = ear < EAR_THRESHOLD
                if eye_closed:
                    if closed_start_time is None:
                        closed_start_time = now
                    closed_duration = now - closed_start_time
                else:
                    closed_start_time = None
                    closed_duration = 0.0
                    if eyes_alert_active:
                        eyes_alert_active = False
                        eyes_continuous_mode = False
                        alert_system.stop_continuous_beep()
                        print("👁️  Yeux ouverts - alerte désactivée")

                perclos.update(eye_closed)

                # ===== DÉTECTION MOUVEMENTS TÊTE =====
                pitch, yaw = calculate_head_pose(landmarks, w, h)
                head_direction = head_detector.update(pitch, yaw)
                head_drowsy = head_detector.is_drowsy_head_movement()
                
                # ===== DÉTECTION TÊTE BAISSÉE =====
                head_is_down = pitch < HEAD_DOWN_THRESHOLD
                if head_is_down:
                    if head_down_start_time is None:
                        head_down_start_time = now
                    head_down_duration = now - head_down_start_time
                else:
                    head_down_start_time = None
                    head_down_duration = 0.0
                    if head_down_alert_active:
                        head_down_alert_active = False
                        print("🙂 Tête relevée - alerte tête baissée désactivée")
                
                if not head_drowsy and head_alert_active:
                    head_alert_active = False
                    head_continuous_mode = False
                    alert_system.stop_continuous_beep()
                    print("🧘 Tête stable - alerte désactivée")

                # ===== ALERTE YEUX FERMÉS =====
                if eye_closed and closed_duration >= MIN_CLOSED_SECONDS:
                    if not eyes_alert_active:
                        # PREMIÈRE ALERTE
                        print(f"🚨 [YEUX] ALERTE ACTIVÉE ! Durée: {closed_duration:.1f}s")
                        alert_system.say_async("Attention ! Tes yeux sont fermés ! Réveille-toi !", force=True)
                        alert_system.beep(2000, 300)
                        last_eyes_voice_alert = now
                        last_eyes_beep = now
                        eyes_alert_active = True
                        # 📊 Export dashboard
                        exporter.add_message(f"ALERTE YEUX ! Yeux fermés depuis {closed_duration:.1f}s", "warning")
                        exporter.add_alert("Yeux fermés", 2, closed_duration)
                    else:
                        # Passage en mode SIRÈNE CONTINUE après 12 secondes
                        if closed_duration >= 12 and not eyes_continuous_mode:
                            print(f"💀 [YEUX] MODE SIRÈNE CONTINUE ACTIVÉ ! {closed_duration:.1f}s")
                            alert_system.start_continuous_beep(2800)
                            alert_system.say_async("Ohhhh ! Tu vas mourir ! Réveille-toi maintenant !", force=True)
                            eyes_continuous_mode = True
                            last_eyes_voice_alert = now
                            # 📊 Export dashboard
                            exporter.add_message(f"DANGER CRITIQUE ! Yeux fermés {closed_duration:.1f}s - MODE SIRÈNE", "critical")
                            exporter.add_alert("Yeux fermés - Critique", 3, closed_duration)
                        
                        # Si pas encore en mode continu
                        if closed_duration < 12:
                            # BIP qui devient progressivement rapide
                            if closed_duration < 3:
                                beep_interval = 1.0
                                beep_duration = 200
                                freq = 2500
                                status = "Bips séparés"
                            elif closed_duration < 5:
                                beep_interval = 0.5
                                beep_duration = 250
                                freq = 2500
                                status = "Bips rapprochés"
                            elif closed_duration < 8:
                                beep_interval = 0.2
                                beep_duration = 150
                                freq = 2600
                                status = "Bips très rapides"
                            else:  # 8-12s
                                beep_interval = 0.1
                                beep_duration = 90
                                freq = 2700
                                status = "Quasi-continu"
                            
                            if (now - last_eyes_beep) >= beep_interval:
                                alert_system.beep(freq, beep_duration)
                                last_eyes_beep = now
                                if int(closed_duration) != int(closed_duration - 0.5):
                                    print(f"🔊 [YEUX] {status} - {closed_duration:.1f}s")
                        
                        # VOIX répétée toutes les 5 secondes
                        if (now - last_eyes_voice_alert) >= ALERT_REPEAT_INTERVAL:
                            print(f"🔔 [YEUX] Alerte vocale répétée ! Durée: {closed_duration:.1f}s")
                            if eyes_continuous_mode:
                                # Message DRAMATIQUE en mode critique
                                alert_system.say_async("Ohhhh ! Tu vas mourir ! Réveille-toi maintenant !", force=True)
                            else:
                                alert_system.say_async("Alerte ! Tes yeux sont toujours fermés ! Arrête-toi immédiatement !", force=True)
                            last_eyes_voice_alert = now

                # ===== ALERTE MOUVEMENTS TÊTE =====
                if head_drowsy:
                    if not head_alert_active:
                        # PREMIÈRE ALERTE
                        changes, duration = head_detector.get_stats()
                        print(f"🚨 [TÊTE] ALERTE ACTIVÉE ! Mvts: {changes}, Durée: {duration:.1f}s")
                        alert_system.say_async("Attention ! Tu as sommeil ! Ta tête balance ! Repose-toi !", force=True)
                        alert_system.beep(1500, 300)
                        last_head_voice_alert = now
                        last_head_beep = now
                        head_alert_active = True
                        # 📊 Export dashboard
                        exporter.add_message(f"ALERTE TÊTE ! Mouvements de somnolence ({changes} mvts)", "warning")
                        exporter.add_alert("Mouvements tête", 2, duration)
                    else:
                        # Passage en mode SIRÈNE CONTINUE après 16 secondes
                        changes, head_duration = head_detector.get_stats()
                        if head_duration >= 16 and not head_continuous_mode:
                            print(f"💀 [TÊTE] MODE SIRÈNE CONTINUE ACTIVÉ ! {head_duration:.1f}s")
                            alert_system.start_continuous_beep(2200)
                            alert_system.say_async("Ohhhh ! Tu vas mourir ! Réveille-toi maintenant !", force=True)
                            head_continuous_mode = True
                            last_head_voice_alert = now
                            # 📊 Export dashboard
                            exporter.add_message(f"DANGER CRITIQUE ! Somnolence tête {head_duration:.1f}s - MODE SIRÈNE", "critical")
                            exporter.add_alert("Mouvements tête - Critique", 3, head_duration)
                        
                        # Si pas encore en mode continu
                        if head_duration < 16:
                            # BIP qui devient progressivement rapide
                            if head_duration < 5:
                                beep_interval = 1.0
                                beep_duration = 200
                                freq = 1800
                                status = "Bips séparés"
                            elif head_duration < 8:
                                beep_interval = 0.5
                                beep_duration = 250
                                freq = 1900
                                status = "Bips rapprochés"
                            elif head_duration < 12:
                                beep_interval = 0.2
                                beep_duration = 150
                                freq = 2000
                                status = "Bips très rapides"
                            else:  # 12-16s
                                beep_interval = 0.1
                                beep_duration = 90
                                freq = 2100
                                status = "Quasi-continu"
                            
                            if (now - last_head_beep) >= beep_interval:
                                alert_system.beep(freq, beep_duration)
                                last_head_beep = now
                                if int(head_duration) != int(head_duration - 0.5):
                                    print(f"🔊 [TÊTE] {status} - {head_duration:.1f}s")
                        
                        # VOIX répétée toutes les 5 secondes
                        if (now - last_head_voice_alert) >= ALERT_REPEAT_INTERVAL:
                            changes, duration = head_detector.get_stats()
                            print(f"🔔 [TÊTE] Alerte vocale répétée ! Mvts: {changes}, Durée: {duration:.1f}s")
                            if head_continuous_mode:
                                # Message DRAMATIQUE en mode critique
                                alert_system.say_async("Ohhhh ! Tu vas mourir ! Réveille-toi maintenant !", force=True)
                            else:
                                alert_system.say_async("Danger ! Tu continues à somnoler ! Arrête le véhicule maintenant !", force=True)
                            last_head_voice_alert = now

                # ===== ALERTE TÊTE BAISSÉE =====
                if head_is_down and head_down_duration >= HEAD_DOWN_DURATION:
                    if not head_down_alert_active:
                        # PREMIÈRE ALERTE tête baissée
                        print(f"⚠️ [TÊTE BAISSÉE] ALERTE ! Durée: {head_down_duration:.1f}s")
                        alert_system.say_async("Attention ! Ta tête est baissée ! Relève-toi !", force=True)
                        alert_system.beep(2200, 300)
                        head_down_alert_active = True
                        last_head_down_beep = now
                        last_head_down_voice = now
                        # 📊 Export dashboard
                        exporter.add_message(f"ALERTE ! Tête baissée depuis {head_down_duration:.1f}s", "info")
                        exporter.add_alert("Tête baissée", 1, head_down_duration)
                    else:
                        # BIP répété pour tête baissée
                        if (now - last_head_down_beep) >= HEAD_DOWN_BEEP_INTERVAL:
                            alert_system.beep(2200, 200)
                            last_head_down_beep = now
                            print(f"🔔 [TÊTE BAISSÉE] Bip ! {head_down_duration:.1f}s")
                        
                        # VOIX répétée toutes les 5 secondes
                        if (now - last_head_down_voice) >= ALERT_REPEAT_INTERVAL:
                            print(f"🔔 [TÊTE BAISSÉE] Alerte vocale ! {head_down_duration:.1f}s")
                            alert_system.say_async("Relève ta tête ! Tu t'endors !", force=True)
                            last_head_down_voice = now

                # ===== MISE À JOUR STATUT =====
                if eyes_alert_active and head_alert_active:
                    status_text = "🚨🚨 DANGER CRITIQUE"
                elif eyes_alert_active and head_down_alert_active:
                    status_text = "🚨🚨 DANGER - Yeux + Tête baissée"
                elif eyes_alert_active:
                    status_text = f"🚨 ALERTE YEUX ({closed_duration:.1f}s)"
                elif head_alert_active:
                    changes, duration = head_detector.get_stats()
                    status_text = f"🚨 ALERTE TÊTE ({changes}mvts)"
                elif head_down_alert_active:
                    status_text = f"⚠️ TÊTE BAISSÉE ({head_down_duration:.1f}s)"
                elif eye_closed:
                    status_text = f"⚠️ Yeux... {closed_duration:.1f}s"
                elif head_is_down:
                    status_text = f"⚠️ Tête baissée... {head_down_duration:.1f}s"
                elif head_detector.direction_changes > 0:
                    changes, _ = head_detector.get_stats()
                    status_text = f"⚠️ Tête... {changes}mvts"
                else:
                    status_text = "✓ OK"

                # ===== AFFICHAGE HUD =====
                cv2.putText(frame, f"EAR: {ear:.3f}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
                color = (0, 0, 255) if ear < EAR_THRESHOLD else (0, 200, 0)
                bar_width = int(min(max(ear, 0.0), 0.5) * 400)
                cv2.rectangle(frame, (10, 40), (10 + bar_width, 60), color, -1)

                cv2.putText(frame, f"Seuil: {EAR_THRESHOLD:.2f}", (10, 85),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)

                cv2.putText(frame, f"Fermes: {closed_duration:.1f}s", (10, 110),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 200, 0), 2)

                cv2.putText(frame, f"PERCLOS: {perclos.perclos()*100:.1f}%", (10, 135),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 200, 0), 2)

                cv2.putText(frame, f"Pitch:{pitch:+5.1f}° Yaw:{yaw:+5.1f}°", (10, 160),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                
                # Indicateur tête baissée
                if head_is_down:
                    head_down_color = (0, 0, 255) if head_down_alert_active else (255, 165, 0)
                    cv2.putText(frame, f"TETE BAISSEE ! ({head_down_duration:.1f}s)", (10, 185),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, head_down_color, 2)
                    y_offset = 210
                else:
                    y_offset = 185
                
                # Mouvements
                changes, duration = head_detector.get_stats()
                head_color = (0, 0, 255) if head_drowsy else (255, 150, 0) if changes > 0 else (200, 200, 200)
                head_status = "SOMNOLENCE" if head_drowsy else f"{changes}mvts" if changes > 0 else "Normal"
                cv2.putText(frame, f"Tete: {head_status} ({duration:.1f}s)", (10, y_offset),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, head_color, 2)

                st_color = (0, 0, 255) if "ALERTE" in status_text or "DANGER" in status_text else \
                          (255, 165, 0) if "⚠️" in status_text else (0, 255, 0)
                cv2.putText(frame, f"STATUT: {status_text}", (10, y_offset + 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, st_color, 2)
                
                y_pos = y_offset + 60
                if eyes_alert_active:
                    # Effet clignotant pour attirer l'attention
                    blink = int(time.time() * 2) % 2
                    color = (0, 0, 255) if blink else (0, 100, 255)
                    cv2.putText(frame, "[ALERTE YEUX ACTIVE]", (10, y_pos),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                    y_pos += 25
                if head_alert_active:
                    blink = int(time.time() * 2) % 2
                    color = (0, 0, 255) if blink else (0, 100, 255)
                    cv2.putText(frame, "[ALERTE TETE ACTIVE]", (10, y_pos),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                    y_pos += 25
                if head_down_alert_active:
                    blink = int(time.time() * 2) % 2
                    color = (0, 165, 255) if blink else (255, 165, 0)
                    cv2.putText(frame, "[ALERTE TETE BAISSEE]", (10, y_pos),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                
                # 📊 Update temps réel dashboard
                exporter.update_realtime(
                    ear=ear,
                    perclos=perclos.perclos(),
                    status=status_text,
                    closed_duration=closed_duration,
                    pitch=pitch,
                    yaw=yaw,
                    head_movements=head_detector.direction_changes,
                    head_down_duration=head_down_duration,
                    head_drowsy=head_drowsy,
                    eyes_alert_active=eyes_alert_active,
                    head_alert_active=head_alert_active,
                    head_down_alert_active=head_down_alert_active,
                    eyes_continuous_mode=eyes_continuous_mode,
                    head_continuous_mode=head_continuous_mode
                )
                exporter.update_session(perclos.perclos())

            else:
                perclos.update(False)
                if eyes_alert_active or head_alert_active or head_down_alert_active:
                    eyes_alert_active = False
                    head_alert_active = False
                    head_down_alert_active = False
                    eyes_continuous_mode = False
                    head_continuous_mode = False
                    alert_system.stop_continuous_beep()
                    print("😶 Visage perdu - alertes désactivées")
                
                cv2.putText(frame, "Visage non detecte", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

            cv2.imshow("Detection Somnolence - ESC pour quitter", frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break

    # 📊 Finaliser export dashboard
    exporter.finalize(perclos.perclos())
    
    cap.release()
    cv2.destroyAllWindows()
    print("\n✅ Système arrêté")


if __name__ == "__main__":
    main() 