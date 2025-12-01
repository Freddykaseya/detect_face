# 📂 Structure du Projet

```
detect_visage/
│
├── 🎯 FICHIERS PRINCIPAUX
│   ├── main.py                      ⭐ Backend détection (code validé collègues)
│   ├── dashboard_exporter.py        📊 Module export JSON temps réel
│   ├── dashboard_server.py          🌐 Serveur Flask pour dashboard
│   └── launch_with_dashboard.py    🚀 Lanceur système complet
│
├── 📄 DOCUMENTATION
│   ├── README.md                    📖 Documentation principale
│   └── README_INTERFACE.md          🎨 Guide frontend détaillé
│
├── ⚙️ CONFIGURATION
│   ├── requirements.txt             📦 Dépendances Python
│   └── .gitignore                   🚫 Fichiers ignorés Git
│
├── 🎨 INTERFACE WEB
│   └── templates/
│       └── dashboard_simple.html    💻 Dashboard professionnel
│
├── 🧪 DONNÉES TEST
│   └── test_data/
│       ├── realtime_data_mock.json
│       ├── session_report_mock.json
│       ├── dialogue_log_mock.json
│       └── alert_history_mock.json
│
└── 📊 DONNÉES GÉNÉRÉES (auto)
    ├── realtime_data.json           ⚡ Données instantanées
    ├── session_report.json          📈 Stats session
    ├── dialogue_log.json            💬 Messages alertes
    └── alert_history.json           🗂️ Historique alertes
```

## 🔄 Flux de Données

```
┌─────────────────┐
│   Caméra USB    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│        main.py                  │
│  (Backend Détection)            │
│  • MediaPipe Face Mesh          │
│  • Calcul EAR/PERCLOS          │
│  • Détection alertes           │
│  • Alertes audio/visuelles     │
└────────┬────────────────────────┘
         │
         ▼ (export automatique)
┌─────────────────────────────────┐
│   dashboard_exporter.py         │
│  • Génère 4 fichiers JSON       │
│  • Update temps réel            │
└────────┬────────────────────────┘
         │
         ▼ (lecture JSON)
┌─────────────────────────────────┐
│   dashboard_server.py           │
│  • Flask REST API               │
│  • 4 endpoints                  │
│  • Port 5000                    │
└────────┬────────────────────────┘
         │
         ▼ (fetch API)
┌─────────────────────────────────┐
│   dashboard_simple.html         │
│  • Interface temps réel         │
│  • Graphiques Chart.js          │
│  • Rafraîchissement 2s          │
└─────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│   Navigateur    │
│  localhost:5000 │
└─────────────────┘
```

## 🎮 Commandes Rapides

### 🚀 Lancement Complet

```bash
python launch_with_dashboard.py
```

✅ Lance backend + dashboard + navigateur

### 🔧 Backend Seul

```bash
python main.py
```

✅ Détection sans dashboard

### 🌐 Dashboard Seul

```bash
python dashboard_server.py
```

✅ Interface sans backend (mode dev)

### 📦 Installation

```bash
pip install -r requirements.txt
```

## 📊 APIs Dashboard

| Endpoint        | Description                               | Update        |
| --------------- | ----------------------------------------- | ------------- |
| `/`             | Page dashboard                            | -             |
| `/api/realtime` | Données instantanées (EAR, PERCLOS, etc.) | Chaque frame  |
| `/api/session`  | Statistiques session                      | Chaque 2s     |
| `/api/dialogue` | Messages alertes                          | Chaque alerte |
| `/api/stats`    | Toutes stats combinées                    | Chaque 2s     |

## 🎯 Fichiers par Responsabilité

### 👥 Backend (Collègues)

- `main.py` - Logique de détection

### 🎨 Frontend (Vous)

- `templates/dashboard_simple.html` - Interface web
- `dashboard_server.py` - API REST

### 🔗 Intégration (Vous)

- `dashboard_exporter.py` - Export JSON
- `launch_with_dashboard.py` - Orchestration

### 📚 Documentation (Partagée)

- `README.md` - Doc générale
- `README_INTERFACE.md` - Guide technique

## 🧹 Nettoyage Effectué

✅ **Supprimé :**

- `backend_wrapper.py` (obsolète)
- `main_fixed.py` (test)
- `fix_indent.py` (temporaire)
- `export_points.py` (notes dev)
- `test_api.py` (test obsolète)
- `dashboard_mock_server.py` (remplacé)
- `config_interface.json` (info dans README)
- Tous les anciens Markdown (FUSION*NOTES, GUIDE*\*, etc.)

✅ **Gardé :**

- Fichiers essentiels au fonctionnement
- Documentation utile
- Données de test
- Structure propre et claire

## 📝 Prochaines Étapes

1. ✅ **Tester** : `python launch_with_dashboard.py`
2. ✅ **Vérifier** : Dashboard affiche données temps réel
3. ✅ **Personnaliser** : Modifier CSS dans dashboard_simple.html
4. ✅ **Documenter** : Ajouter noms équipe dans README.md

---

**Projet Licence 3 - OpenCV**  
**Système Anti-Somnolence Temps Réel**  
© 2025
