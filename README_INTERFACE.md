# 🎨 Interface Dashboard Anti-Somnolence

## 📋 Vue d'ensemble

Ce dossier contient **l'interface frontend** du système de détection de somnolence.  
L'interface est **indépendante du backend** et peut être développée/testée séparément.

---

## 🗂️ Structure des fichiers

```
detect_visage/
├── templates/
│   └── dashboard_simple.html          # Interface principale (VOTRE TRAVAIL)
│
├── dashboard_server.py                # Serveur Flask PRODUCTION (intègre backend)
├── dashboard_mock_server.py           # Serveur Flask DÉVELOPPEMENT (données simulées)
│
├── test_data/                         # Données mockées pour tests frontend
│   ├── realtime_data_mock.json
│   ├── session_report_mock.json
│   ├── dialogue_log_mock.json
│   └── alert_history_mock.json
│
├── config_interface.json              # Contrat Backend ↔ Frontend
│
└── README_INTERFACE.md                # Ce fichier
```

---

## 🚀 Démarrage rapide

### Mode Développement (sans backend)

```bash
python dashboard_mock_server.py
```

Ouvrir http://localhost:5000 dans le navigateur.  
L'interface affiche des **données simulées** qui varient aléatoirement.

### Mode Production (avec backend)

```bash
python launch_with_dashboard.py
```

Lance le backend de détection + le dashboard intégré.

---

## 🎯 Workflow de développement

### 1. Développer l'interface (VOUS)

```bash
# Lancer serveur de test
python dashboard_mock_server.py

# Modifier dashboard_simple.html
# Les changements sont visibles en rafraîchissant le navigateur
```

### 2. Tester avec données réalistes

Éditez les fichiers dans `test_data/` pour simuler différents scénarios :

- **Alerte faible** : `alert_level: 1`, `status: "⚠️ Info"`
- **Alerte moyenne** : `alert_level: 2`, `status: "⚠️ Attention"`
- **Alerte critique** : `alert_level: 3`, `status: "🚨 DANGER"`

### 3. Intégration backend (COLLÈGUES)

Quand le backend est prêt, il doit générer 4 fichiers JSON :

- `realtime_data.json` - Données instantanées (EAR, PERCLOS, etc.)
- `session_report.json` - Stats de session
- `dialogue_log.json` - Messages d'alerte
- `alert_history.json` - Historique pour graphiques

**Format des fichiers** : voir `config_interface.json`

### 4. Test intégration

```bash
python dashboard_server.py
```

Le serveur lit automatiquement les fichiers JSON générés par le backend.

---

## 📊 APIs disponibles

L'interface utilise 4 endpoints REST :

| Endpoint        | Description                         | Rafraîchissement |
| --------------- | ----------------------------------- | ---------------- |
| `/api/realtime` | Données instantanées (EAR, PERCLOS) | Toutes les 2s    |
| `/api/session`  | Stats session (durée, clignements)  | Toutes les 2s    |
| `/api/dialogue` | Messages d'alerte                   | Toutes les 2s    |
| `/api/stats`    | Toutes les stats combinées          | Toutes les 2s    |

---

## 🎨 Personnalisation interface

### Modifier les couleurs

Dans `dashboard_simple.html`, section `<style>` :

```css
/* Gradient principal */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Couleur primaire */
color: #667eea;
```

### Ajouter une section

```html
<!-- Exemple: Section IA -->
<div class="ai-assistant-section">
  <h3>💬 Assistant Intelligent</h3>
  <div id="ai-messages"></div>
</div>
```

### Modifier le graphique

Dans le JavaScript :

```javascript
// Changer type de graphique
type: "doughnut"; // ou 'pie', 'bar', 'line'

// Changer couleurs
backgroundColor: ["#36A2EB", "#FFCE56", "#FF6384"];
```

---

## 🔧 Troubleshooting

### Dashboard ne charge pas

✅ Vérifiez que le serveur Flask tourne :

```bash
python dashboard_mock_server.py
```

### Données ne s'actualisent pas

✅ Ouvrez la console navigateur (F12) et vérifiez les erreurs  
✅ Vérifiez que les fichiers JSON existent dans `test_data/`

### Erreur CORS

✅ Le serveur Flask a déjà Flask-CORS activé  
✅ Si problème persiste, vérifiez que vous accédez via `http://localhost:5000`

---

## 📝 Contrat Backend ↔ Frontend

### Ce que le BACKEND doit fournir :

4 fichiers JSON avec ce format (voir `config_interface.json` pour détails) :

1. **realtime_data.json** - Mis à jour chaque frame

   ```json
   {
     "ear": 0.28,
     "perclos": 12.5,
     "alert_level": 0,
     "status": "✓ OK"
   }
   ```

2. **session_report.json** - Mis à jour fin session

   ```json
   {
     "duration_seconds": 485.5,
     "total_blinks": 89,
     "total_alerts": 4
   }
   ```

3. **dialogue_log.json** - Ajouté à chaque alerte

   ```json
   [
     {
       "timestamp": "2025-11-29T10:30:45",
       "message": "⚠️ Attention !",
       "severity": "warning"
     }
   ]
   ```

4. **alert_history.json** - Ajouté à chaque alerte
   ```json
   [
     {
       "timestamp": "2025-11-29T10:30:45",
       "type": "Yeux fermés",
       "level": 2,
       "duration": 3.5
     }
   ]
   ```

### Ce que le FRONTEND garantit :

- ✅ Ne crashe jamais (valeurs par défaut si fichiers manquants)
- ✅ Rafraîchit automatiquement toutes les 2 secondes
- ✅ Affiche messages d'erreur clairs si problème
- ✅ Compatible tous navigateurs modernes

---

## 🚀 Prochaines étapes (optionnel)

### Module IA Intelligent

Ajouter génération de messages contextuels :

- Analyse du contexte (nombre d'alertes récentes)
- Messages variés (éviter répétition)
- Escalade du ton (calme → urgent)
- Animation typing effect
- Suggestions personnalisées

### Graphiques avancés

- Timeline des alertes (Chart.js line)
- Carte de chaleur PERCLOS
- Historique sur 7 jours

### Notifications navigateur

```javascript
if (Notification.permission === "granted") {
  new Notification("🚨 DANGER !", {
    body: "Yeux fermés depuis 8 secondes !",
  });
}
```

---

## 👥 Contact

**Frontend** : [Votre nom]  
**Backend** : [Noms collègues]  
**Projet** : Licence 3 - Détection de Somnolence

---

## 📄 Licence

Projet académique - Tous droits réservés
