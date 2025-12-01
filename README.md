# Système de Détection de Somnolence

**Projet Licence 3 - OpenCV & Vision par Ordinateur**

Ce projet détecte la somnolence au volant en temps réel grâce à l'analyse vidéo du visage du conducteur. L'idée est simple : surveiller les yeux et la posture de la tête pour détecter les signes de fatigue avant qu'il ne soit trop tard.

Le système analyse la vidéo de la webcam, calcule des métriques (comme l'EAR pour les yeux), et déclenche des alertes sonores progressives. Tout est visualisable sur un dashboard web qui se met à jour en direct.

## Pourquoi ce projet ?

La somnolence au volant cause énormément d'accidents. On voulait créer un système pratique qui pourrait aider à prévenir ces situations dangereuses. Le projet utilise des technos modernes (MediaPipe, OpenCV) pour analyser 468 points du visage et détecter :

- Les yeux qui restent fermés trop longtemps
- La tête qui penche vers l'avant (signe qu'on pique du nez)
- Les mouvements de tête erratiques typiques de quelqu'un qui lutte contre le sommeil

Quand le système détecte un problème, il commence par des bips légers, puis passe à des alertes vocales, et finalement une sirène continue si la situation devient critique.

## Ce que ça fait concrètement

### Partie Détection (Backend)

Le backend tourne sur votre machine et analyse la vidéo de la webcam en continu. Voici ce qu'il surveille :

**Les yeux** : On calcule l'EAR (Eye Aspect Ratio) à chaque frame. Si l'EAR passe sous 0.23 et reste comme ça pendant plus de 1.5 secondes, ça veut dire que les yeux sont fermés trop longtemps. Le système déclenche une alerte.

**La tête qui tombe** : Si l'angle de la tête (pitch) descend en dessous de -15°, c'est que la personne baisse la tête. Signe classique de fatigue.

**Les mouvements bizarres** : Quand on commence à somnoler, la tête fait des petits mouvements saccadés. On track les changements de direction (yaw) et si ça dépasse 12° de variation, c'est louche.

**Les alertes progressives** : Le système est pas brutal. Il commence doucement :

- 1.5s → Petit bip discret
- 3s → Bip plus insistant
- 8s → Message vocal "Attention, repos nécessaire"
- 12s+ → Sirène continue jusqu'à ce que ça s'arrête

### Dashboard Web

J'ai créé une interface web pour voir tout ça en direct. Ça se lance automatiquement dans le navigateur et ça montre :

- Les valeurs en temps réel (EAR, PERCLOS, angles de la tête)

## Comment ça marche techniquement

Le projet est découpé en plusieurs morceaux qui communiquent entre eux :

**app.py** : C'est le fichier principal que vous lancez. Il s'occupe de démarrer le serveur web en arrière-plan, d'ouvrir le navigateur, puis de lancer la détection vidéo. Quand vous arrêtez tout, il s'assure que tout se ferme proprement.

**main.py** : C'est le cœur du système. Il capture la vidéo de la webcam, utilise MediaPipe pour détecter les 468 points du visage, calcule l'EAR et les angles, et déclenche les alertes. Il enregistre aussi tout dans des fichiers JSON pour que le dashboard puisse afficher les données.

**dashboard_server.py** : Un petit serveur Flask qui tourne sur le port 5000. Il sert l'interface web et propose 4 endpoints API pour récupérer les données en JSON (session stats, alertes, données temps réel, etc.).

**dashboard_exporter.py** : C'est le module qui fait le pont entre la détection et le dashboard. Il prend toutes les données calculées par main.py et les écrit dans des fichiers JSON que le serveur web va lire.

**templates/index.html** : L'interface web. Elle fait des requêtes toutes les secondes aux API pour récupérer les nouvelles données et met à jour l'affichage. J'ai utilisé Chart.js pour les graphiques.

Le système génère automatiquement 4 fichiers JSON :

- `realtime_data.json` : Les valeurs actuelles (EAR, angles, statut)
- `session_report.json` : Les stats globales de la session
- `dialogue_log.json` : L'historique des messages d'alerte
- `alert_history.json` : Toutes les alertes déclenchées avec leur niveau index.html │ │ (auto-générés) │
  │ │ │ │
  │ • Chart.js graphs │ │ • realtime_data │
  │ • Fetch API (1s) │ │ • session_report │
  │ • Cache-busting │ │ • dialogue_log │
  │ • Purple gradient │ │ • alert_history │
  └──────────────────────┘ └──────────────────────┘

```

### 📁 Structure des Fichiers

```

detect_visage/
├── app.py # 🚀 Point d'entrée principal
├── main.py # 🎥 Backend détection (654 lignes)
├── dashboard_server.py # 🌐 Serveur Flask API REST
├── dashboard_exporter.py # 💾 Export données → JSON
├── requirements.txt # 📦 Dépendances Python
├── .gitignore # 🚫 Fichiers à ignorer
│
├── templates/
│ └── index.html # 🎨 Interface dashboard (603 lignes)
│
├── README.md # 📖 Documentation principale
├── README_INTERFACE.md # 📘 Guide développement frontend
└── STRUCTURE.md # 🗺️ Architecture détaillée

### Organisation des fichiers

```
detect_visage/
├── app.py                    # Lance tout le système
├── main.py                   # Détection vidéo (le gros du code)
├── dashboard_server.py       # Serveur web Flask
├── dashboard_exporter.py     # Écrit les JSON
├── requirements.txt          # Liste des dépendances
├── templates/
│   └── index.html           # Interface web
├── README.md
├── README_INTERFACE.md      # Infos pour modifier le frontend
└── STRUCTURE.md             # Doc technique détaillée

Les fichiers JSON sont créés automatiquement au lancement :
├── realtime_data.json       # Données de la frame actuelle
├── session_report.json      # Stats de la session
├── dialogue_log.json        # Les alertes sous forme de messages
└── alert_history.json       # Historique complet des alertes
```

## Installation

### Ce qu'il vous faut

- Python 3.8 minimum (j'ai testé avec 3.11)
- Une webcam qui marche
- Windows de préférence (pour les sons avec winsound)

### Étapes d'installation

Clonez le projet et installez les dépendances :

```bash
git clone <votre-repo-url>
cd detect_visage
pip install -r requirements.txt
```

Les packages principaux :

- **opencv-python** : Pour la capture et le traitement vidéo
- **mediapipe** : Pour détecter les points du visage
- **Flask** : Pour le serveur web
- **pyttsx3** : Pour les alertes vocales
- **numpy** : Pour les calculs

## Utilisation

### Lancer le système complet

La façon la plus simple :

```bash
python app.py
```

Ça va démarrer le serveur web, ouvrir le dashboard dans votre navigateur, et lancer la détection vidéo. Le dashboard va se mettre à jour automatiquement toutes les secondes.

Pour arrêter, appuyez sur **ESC** dans la fenêtre vidéo ou **Ctrl+C** dans le terminal.

### Autres modes

Si vous voulez juste tester la détection sans le dashboard :

```bash
python main.py
```

Ou si vous bossez sur l'interface et voulez juste le serveur web :

```bash
python dashboard_server.py
```

Puis ouvrez http://localhost:5000 dans votre navigateur.

**Ajuster selon votre usage :**

- Environnement lumineux faible → **Augmenter** `EAR_THRESHOLD` (0.25)
- Conducteur portant lunettes → **Baisser** `EAR_THRESHOLD` (0.21)
- Routes avec virages fréquents → **Augmenter** `HEAD_MOVEMENT_THRESHOLD` (15.0)

## Configuration

### Ajuster les seuils de détection

Les paramètres sont dans `main.py` (lignes 42-45). Vous pouvez les modifier selon vos besoins :

```python
EAR_THRESHOLD = 0.23            # En dessous de ça = yeux fermés
MIN_CLOSED_SECONDS = 1.5        # Attendre 1.5s avant d'alerter
HEAD_DOWN_THRESHOLD = -15.0     # Angle pour "tête baissée"
HEAD_MOVEMENT_THRESHOLD = 12.0  # Variation d'angle pour détecter les mouvements
```

Quelques cas d'usage :

- Si vous êtes dans une pièce sombre, augmentez l'EAR_THRESHOLD à 0.25
- Si vous portez des lunettes épaisses, baissez-le à 0.21
- Pour les routes avec beaucoup de virages, montez HEAD_MOVEMENT_THRESHOLD à 15

### Changer le port du serveur

Par défaut le dashboard tourne sur le port 5000. Si ce port est déjà pris, changez-le dans `dashboard_server.py` :

```python
app.run(host='0.0.0.0', port=8080)
```

### Modifier le refresh rate

Le dashboard se rafraîchit toutes les secondes. Si vous trouvez ça trop rapide ou trop lent, éditez `templates/index.html` (ligne 589) :

```javascript
setInterval(updateDashboard, 2000); // 2 secondes au lieu d'1
```

"head_down_duration": 0.0,
"head_drowsy": false,
"eyes_alert_active": false,
"head_alert_active": false,
"head_down_alert_active": false,
"eyes_continuous_mode": false,
"head_continuous_mode": false
}

```
## Format des données

À chaque lancement, le système crée 4 fichiers JSON (ils sont écrasés à chaque nouvelle session) :
  "duration_seconds": 125.7,
  "total_blinks": 42,
  "total_alerts": 3,
  "average_perclos": 8.3,
  "start_time": "2025-12-01T10:30:15.123456",
  "last_update": "2025-12-01T10:32:20.789012"
}
```

### 3️⃣ `dialogue_log.json` (Array, max 50)

```json
[
  {
    "timestamp": "2025-12-01T10:31:45.234567",
    "message": "ALERTE YEUX ! Yeux fermés depuis 2.0s",
    "severity": "warning"
  }
]
```

### 4️⃣ `alert_history.json` (Array, max 100)

```json
[
  {
    "timestamp": "2025-12-01T10:31:45.234567",
    "type": "eyes",
    "level": 2,
    "duration": 2.0
  }
]
```

**Niveaux d'alerte :**

- `1` : Info (tête baissée)
- `2` : Warning (yeux/tête, phase initiale)
- `3` : Critical (sirène continue)

---

## 📝 Documentation Technique

### API REST Endpoints

| Endpoint        | Méthode | Description                    | Refresh Rate |
| --------------- | ------- | ------------------------------ | ------------ |
| `/`             | GET     | Page HTML du dashboard         | -            |
| `/api/session`  | GET     | Statistiques de session        | 1s           |
| `/api/dialogue` | GET     | Historique messages            | 1s           |
| `/api/realtime` | GET     | Données temps réel (16 params) | 1s           |
| `/api/stats`    | GET     | Données combinées + graphiques | 1s           |

**Headers anti-cache :**
Tous les endpoints incluent :

```
Cache-Control: no-cache, no-store, must-revalidate
Pragma: no-cache
Expires: 0
```

### Guides Complémentaires

- 📘 **`README_INTERFACE.md`** : Guide développement frontend, contrat API
  Les niveaux d'alerte c'est :
- Level 1 : Info (tête qui commence à baisser)
- Level 2 : Warning (yeux fermés ou mouvements suspects)
- Level 3 : Critical (situation dangereuse, sirène)

## APIs disponibles

Le serveur Flask expose ces endpoints :

- `GET /` : La page HTML du dashboard
- `GET /api/session` : Stats de la session en cours
- `GET /api/dialogue` : Les messages d'alerte récents
- `GET /api/realtime` : Les données de la frame actuelle
- `GET /api/stats` : Tout combiné pour les graphiques

J'ai ajouté des headers anti-cache partout pour que le navigateur ne garde pas de vieilles données en mémoire. Ça force le refresh à chaque requête.

Plus de détails techniques dans `README_INTERFACE.md` et `STRUCTURE.md`.

## Problèmes courants

### La caméra ne démarre pas

Si vous voyez des warnings du genre "Unable to stop the stream", c'est souvent qu'une autre app utilise déjà la webcam. Fermez Teams, Zoom, etc.

Vous pouvez aussi essayer de changer l'index de la caméra dans `main.py` ligne 255 :

```python
cap = cv2.VideoCapture(1)  # Essayez 0, 1, ou 2
```

### Le dashboard affiche une page noire

Deux possibilités :

1. Le cache du navigateur. Faites Ctrl+Shift+R pour forcer le refresh
2. Le serveur Flask n'est pas démarré. Vérifiez qu'il tourne sur le port 5000

Pour vérifier le port sous Windows :

```powershell
Get-NetTCPConnection -LocalPort 5000
```

Si rien ne répond, le serveur est mort. Relancez `python app.py`.

### Pas de sons

Sur Windows ça devrait marcher direct avec winsound. Si vous êtes sur Linux/Mac, il faudra remplacer winsound par une autre lib (pygame ou playsound).

### Le port 5000 est déjà utilisé

Changez le port dans `dashboard_server.py` ou tuez le processus qui squatte le 5000 :

```powershell
netstat -ano | findstr :5000
taskkill /PID <le_PID> /F
```

### Les alertes sont trop sensibles (ou pas assez)

Jouez avec les seuils dans `main.py`. Si c'est trop sensible, augmentez EAR_THRESHOLD et MIN_CLOSED_SECONDS. Si ça alerte pas assez, baissez-les. apt-get update && apt-get install -y libgl1-mesa-glx libglib2.0-0
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]

````

---

## 👥 Contributeurs

| Rôle | Responsable | Fichiers Clés |
|------|-------------|---------------|
| **Backend (Détection)** | Collègues validateurs | `main.py` |
| **Frontend (Dashboard)** | Développeur interface | `templates/index.html` |
| **Intégration & Export** | Développeur intégration | `dashboard_exporter.py`, `dashboard_server.py` |
| **Documentation** | Équipe complète | `README.md`, `STRUCTURE.md` |

---

## 📄 Licence

**Projet académique - Licence 3 OpenCV**
© 2025 - Tous droits réservés

Ce projet est développé dans un cadre pédagogique. Toute utilisation commerciale est interdite sans autorisation.

---

## 🙏 Technologies & Remerciements

| Technologie | Usage | Licence |
|-------------|-------|---------|
| **[MediaPipe](https://mediapipe.dev/)** | Détection 468 landmarks faciaux | Apache 2.0 |
| **[OpenCV](https://opencv.org/)** | Traitement vidéo et vision par ordinateur | Apache 2.0 |
| **[Flask](https://flask.palletsprojects.com/)** | Framework web Python | BSD-3 |
| **[Chart.js](https://www.chartjs.org/)** | Graphiques interactifs JavaScript | MIT |
| **[pyttsx3](https://pyttsx3.readthedocs.io/)** | Synthèse vocale multi-plateforme | MPL 2.0 |
| **[NumPy](https://numpy.org/)** | Calculs mathématiques et matrices | BSD |

**Merci à la communauté open source !** 🎉

---

## 📞 Support

Pour toute question ou problème :
## Améliorations possibles

Y'a plein de trucs qu'on pourrait ajouter si on avait plus de temps :

- Support Linux/Mac propre (remplacer winsound)
- Notifications push sur smartphone
- Sauvegarder l'historique dans une vraie base de données
- Profils utilisateurs avec statistiques personnalisées
- Export PDF des rapports de session
- Détection de bâillement (avec le MAR - Mouth Aspect Ratio)

Si vous voulez contribuer, n'hésitez pas !

## Déploiement

Pour créer un exécutable Windows :

```bash
pip install pyinstaller
pyinstaller --onefile --windowed app.py
````

Ou si vous voulez Dockeriser le tout :

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN apt-get update && apt-get install -y libgl1-mesa-glx libglib2.0-0
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

## Crédits

**Backend (détection)** : Développé et validé par mes collègues de groupe  
**Frontend (dashboard)** : Moi-même  
**Intégration** : Moi-même

Le projet utilise des technos open source géniales :

- MediaPipe (Google) pour la détection faciale
- OpenCV pour le traitement vidéo
- Flask pour le serveur web
- Chart.js pour les graphiques
- pyttsx3 pour la voix

Merci à toute la communauté open source !

## Licence

Projet académique - Licence 3 OpenCV  
© 2025

C'est un projet fait dans le cadre de nos études. Pas d'utilisation commerciale sans autorisation.
