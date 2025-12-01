"""
Module d'export des données de détection vers JSON
Pour intégration avec le dashboard frontend

Ce module est importé par le backend (sleep_detection_2_test.py)
et exporte automatiquement toutes les données en temps réel
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any


class DashboardExporter:
    """Exporte les données de détection vers fichiers JSON pour le dashboard"""
    
    def __init__(self):
        self.session_start = datetime.now()
        self.total_blinks = 0
        self.total_alerts = 0
        self.dialogue_log = []
        self.alert_history = []
        
        # Initialiser fichiers JSON vides
        self._init_files()
    
    def _init_files(self):
        """Crée les fichiers JSON initiaux"""
        default_realtime = {
            "ear": 0.0,
            "perclos": 0.0,
            "status": "Initialisation...",
            "alert_level": 0,
            "blink_rate": 0.0,
            "head_movements": 0,
            "pitch": 0.0,
            "yaw": 0.0,
            "eyes_closed_duration": 0.0,
            "head_down_duration": 0.0,
            "head_drowsy": False,
            "eyes_alert_active": False,
            "head_alert_active": False,
            "head_down_alert_active": False,
            "eyes_continuous_mode": False,
            "head_continuous_mode": False
        }
        
        default_session = {
            "duration_seconds": 0,
            "total_blinks": 0,
            "total_alerts": 0,
            "average_perclos": 0.0,
            "start_time": self.session_start.isoformat()
        }
        
        self._write_json("realtime_data.json", default_realtime)
        self._write_json("session_report.json", default_session)
        self._write_json("dialogue_log.json", [])
        self._write_json("alert_history.json", [])
    
    def _write_json(self, filename: str, data: Any):
        """Écrit données JSON de manière sécurisée"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Erreur export {filename}: {e}")
    
    def update_realtime(self, 
                       ear: float,
                       perclos: float,
                       status: str,
                       closed_duration: float,
                       pitch: float,
                       yaw: float,
                       head_movements: int,
                       head_down_duration: float,
                       head_drowsy: bool,
                       eyes_alert_active: bool,
                       head_alert_active: bool,
                       head_down_alert_active: bool,
                       eyes_continuous_mode: bool,
                       head_continuous_mode: bool):
        """Met à jour les données temps réel"""
        
        # Déterminer niveau alerte
        alert_level = 0
        if eyes_continuous_mode or head_continuous_mode:
            alert_level = 3  # CRITIQUE
        elif eyes_alert_active or head_alert_active:
            alert_level = 2  # WARNING
        elif head_down_alert_active:
            alert_level = 1  # INFO
        
        # Calculer taux clignements (estimation)
        session_duration = (datetime.now() - self.session_start).total_seconds()
        blink_rate = (self.total_blinks / (session_duration / 60)) if session_duration > 60 else 0
        
        realtime_data = {
            "ear": round(ear, 3),
            "perclos": round(perclos * 100, 1),
            "status": status,
            "alert_level": alert_level,
            "blink_rate": round(blink_rate, 1),
            "head_movements": head_movements,
            "pitch": round(pitch, 1),
            "yaw": round(yaw, 1),
            "eyes_closed_duration": round(closed_duration, 1),
            "head_down_duration": round(head_down_duration, 1),
            "head_drowsy": head_drowsy,
            "eyes_alert_active": eyes_alert_active,
            "head_alert_active": head_alert_active,
            "head_down_alert_active": head_down_alert_active,
            "eyes_continuous_mode": eyes_continuous_mode,
            "head_continuous_mode": head_continuous_mode
        }
        
        self._write_json("realtime_data.json", realtime_data)
    
    def add_message(self, message: str, severity: str = "info"):
        """Ajoute un message au log dialogue"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "severity": severity
        }
        
        self.dialogue_log.append(entry)
        
        # Garder seulement les 50 derniers messages
        if len(self.dialogue_log) > 50:
            self.dialogue_log = self.dialogue_log[-50:]
        
        self._write_json("dialogue_log.json", self.dialogue_log)
    
    def add_alert(self, alert_type: str, level: int, duration: float):
        """Ajoute une alerte à l'historique"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": alert_type,
            "level": level,
            "duration": round(duration, 1)
        }
        
        self.alert_history.append(entry)
        self.total_alerts += 1
        
        # Garder seulement les 100 dernières alertes
        if len(self.alert_history) > 100:
            self.alert_history = self.alert_history[-100:]
        
        self._write_json("alert_history.json", self.alert_history)
    
    def increment_blink(self):
        """Incrémente le compteur de clignements"""
        self.total_blinks += 1
    
    def update_session(self, perclos_avg: float):
        """Met à jour les statistiques de session"""
        session_duration = (datetime.now() - self.session_start).total_seconds()
        
        session_data = {
            "duration_seconds": round(session_duration, 1),
            "total_blinks": self.total_blinks,
            "total_alerts": self.total_alerts,
            "average_perclos": round(perclos_avg * 100, 1),
            "start_time": self.session_start.isoformat(),
            "last_update": datetime.now().isoformat()
        }
        
        self._write_json("session_report.json", session_data)
    
    def finalize(self, perclos_avg: float):
        """Finalise la session (appelé à la fermeture)"""
        self.update_session(perclos_avg)
        
        # Ajouter message final
        self.add_message(
            f"Session terminée. Durée: {(datetime.now() - self.session_start).total_seconds():.0f}s, "
            f"Clignements: {self.total_blinks}, Alertes: {self.total_alerts}",
            "info"
        )
        
        print(f"\n📊 Export terminé:")
        print(f"   - Clignements: {self.total_blinks}")
        print(f"   - Alertes: {self.total_alerts}")
        print(f"   - Messages: {len(self.dialogue_log)}")
