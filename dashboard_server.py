"""
Dashboard Web - Système Anti-Somnolence
Affiche les statistiques et alertes en temps réel avec graphiques
"""

from flask import Flask, render_template, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime
import threading
import time

app = Flask(__name__)
CORS(app)

# Fichiers de données
SESSION_FILE = "session_report.json"
DIALOGUE_FILE = "dialogue_log.json"
REALTIME_FILE = "realtime_data.json"  # Nouveau fichier pour données temps réel

def load_session_data():
    """Charge les données de session"""
    default_data = {
        'duration_seconds': 0,
        'total_blinks': 0,
        'total_yawns': 0,
        'total_alerts': 0,
        'average_perclos': 0
    }
    
    try:
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
    except Exception as e:
        print(f"Erreur chargement session: {e}")
    
    return default_data

def load_dialogue_data():
    """Charge l'historique des dialogues IA"""
    default_data = {'total_messages': 0, 'history': []}
    
    try:
        if os.path.exists(DIALOGUE_FILE):
            with open(DIALOGUE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Si c'est une liste, convertir
                if isinstance(data, list):
                    return {'total_messages': len(data), 'history': data}
                return data
    except Exception as e:
        print(f"Erreur chargement dialogue: {e}")
    
    return default_data

def load_realtime_data():
    """Charge les données temps réel"""
    default_data = {
        'ear': 0.0,
        'mar': 0.0,
        'perclos': 0.0,
        'blink_rate': 0,
        'status': 'En attente...',
        'alert_level': 0,
        'head_movements': 0,
        'pitch': 0.0,
        'yaw': 0.0
    }
    
    try:
        if os.path.exists(REALTIME_FILE):
            with open(REALTIME_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Erreur chargement realtime: {e}")
    
    return default_data

@app.route('/')
def index():
    """Page principale du dashboard - Version temps réel"""
    return render_template('index.html')

@app.route('/api/session')
def api_session():
    """API: Données de session"""
    response = jsonify(load_session_data())
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/api/dialogue')
def api_dialogue():
    """API: Historique dialogue IA"""
    response = jsonify(load_dialogue_data())
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/api/realtime')
def api_realtime():
    """API: Données temps réel"""
    response = jsonify(load_realtime_data())
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/api/stats')
def api_stats():
    """API: Statistiques combinées pour graphiques - VERSION SIMPLIFIÉE"""
    # Valeurs par défaut garanties
    result = {
        'session': load_session_data(),
        'dialogue': load_dialogue_data(),
        'alerts_by_level': {1: 0, 2: 0, 3: 0},
        'messages_by_category': {'info': 0, 'warning': 0, 'critical': 0},
        'realtime': load_realtime_data()
    }
    
    try:
        # Charger alert_history.json
        if os.path.exists("alert_history.json"):
            with open("alert_history.json", 'r', encoding='utf-8') as f:
                alert_history = json.load(f)
                if isinstance(alert_history, list):
                    for alert in alert_history:
                        level = alert.get('level', 1)
                        if level in [1, 2, 3]:
                            result['alerts_by_level'][level] += 1
    except:
        pass  # Ignorer les erreurs, garder les valeurs par défaut
    
    try:
        # Compter messages par catégorie
        for msg in result['dialogue'].get('history', []):
            cat = msg.get('severity', 'info')
            if cat in result['messages_by_category']:
                result['messages_by_category'][cat] += 1
    except:
        pass  # Ignorer les erreurs
    
    response = jsonify(result)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

def run_server():
    """Lance le serveur Flask"""
    print("\n" + "="*60)
    print("DASHBOARD WEB DEMARRE")
    print("="*60)
    print("Ouvrez votre navigateur a l'adresse:")
    print("   >> http://localhost:5000")
    print("="*60)
    print("Ctrl+C pour arreter le serveur\n")
    
    # Mode debug désactivé pour éviter les problèmes d'encodage
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    run_server()
