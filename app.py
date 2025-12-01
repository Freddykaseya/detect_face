"""
Lanceur combiné: Système de détection + Dashboard Web
"""

import subprocess
import time
import webbrowser
import sys
import os

print("="*60)
print("🚀 Lancement du Système Anti-Somnolence avec Dashboard")
print("="*60)

# Lancer le dashboard web en arrière-plan (sans fenêtre)
print("\n📊 Démarrage du dashboard web...")

# Lancer le serveur Flask en arrière-plan (afficher les erreurs pour debug)
dashboard_process = subprocess.Popen(
    [sys.executable, "dashboard_server.py"],
    stdout=subprocess.DEVNULL,
    stderr=None  # Afficher les erreurs dans le terminal
)

# Attendre que le serveur démarre
time.sleep(3)

# Ouvrir le navigateur
print("🌐 Ouverture du navigateur...")
webbrowser.open('http://localhost:5000')

print("\n✅ Dashboard ouvert dans le navigateur")
print("📹 Le système de détection va maintenant démarrer...")
print("\nAppuyez sur 'q' dans la fenêtre vidéo pour quitter\n")

time.sleep(2)

# Lancer le système de détection (bloquant)
try:
    detection_process = subprocess.run(
        [sys.executable, "main.py"],
        check=False
    )
except KeyboardInterrupt:
    print("\n⚠️  Interruption par l'utilisateur")
except Exception as e:
    print(f"\n❌ Erreur lors de l'exécution: {e}")
finally:
    # Arrêter le dashboard (toujours exécuté)
    print("\n🛑 Arrêt du dashboard...")
    try:
        dashboard_process.terminate()
        dashboard_process.wait(timeout=5)
    except:
        dashboard_process.kill()
    
    print("✅ Système arrêté proprement")
