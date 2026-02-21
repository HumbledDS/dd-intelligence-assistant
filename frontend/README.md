# 🚀 DD Intelligence Assistant - Frontend

Plateforme d'intelligence économique moderne construite avec Next.js 14, TypeScript et Tailwind CSS.

## ✨ **Fonctionnalités Principales**

- 🔍 **Recherche Avancée** : Recherche d'entreprises par nom, SIRET, SIREN, secteur
- 📊 **Visualisation de Données** : Graphiques interactifs et tableaux de bord
- 🤖 **Assistant IA** : Intelligence artificielle pour l'analyse des données
- 👥 **Collaboration Équipe** : Gestion des utilisateurs et partage de rapports
- 💳 **Système de Facturation** : Intégration Stripe avec plans freemium
- 🔒 **Sécurité** : Authentification JWT et gestion des rôles
- 📱 **Responsive Design** : Interface optimisée pour tous les appareils

## 🛠 **Technologies Utilisées**

### **Frontend Core**
- **Next.js 14** - Framework React avec App Router
- **TypeScript** - Typage statique pour la robustesse
- **Tailwind CSS** - Framework CSS utilitaire
- **React 18** - Bibliothèque UI moderne

### **State Management & Data**
- **Zustand** - Gestion d'état légère et performante
- **TanStack Query** - Gestion des données serveur et cache
- **React Hook Form** - Gestion des formulaires
- **Zod** - Validation des schémas

### **UI Components**
- **Radix UI** - Composants accessibles et personnalisables
- **Lucide React** - Icônes modernes et cohérentes
- **Framer Motion** - Animations fluides
- **Headless UI** - Composants sans style

### **Charts & Visualization**
- **Recharts** - Graphiques React performants
- **Chart.js** - Bibliothèque de graphiques flexible
- **React Chart.js 2** - Wrapper React pour Chart.js

### **Payment & Billing**
- **Stripe** - Intégration de paiement complète
- **Stripe React** - Composants React pour Stripe

## 🚀 **Installation et Démarrage**

### **Prérequis**
- Node.js 18+ 
- npm ou yarn
- Git

### **Installation**

```bash
# Cloner le repository
git clone <repository-url>
cd dd-intelligence-assistant/frontend

# Installer les dépendances
npm install

# Copier le fichier d'environnement
cp env.example .env.local

# Configurer les variables d'environnement
# Éditer .env.local avec vos clés API

# Démarrer le serveur de développement
npm run dev
```

### **Variables d'Environnement**

Créez un fichier `.env.local` basé sur `env.example` :

```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_VERSION=v1

# Authentication
NEXT_PUBLIC_AUTH_DOMAIN=your-domain.auth0.com
NEXT_PUBLIC_AUTH_CLIENT_ID=your-client-id

# Stripe Configuration
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your_key
STRIPE_SECRET_KEY=sk_test_your_secret

# AI Services
NEXT_PUBLIC_OPENAI_API_KEY=your_openai_key
```

## 📁 **Structure du Projet**

```
src/
├── app/                    # Next.js 14 App Router
├── components/            # Composants réutilisables
│   ├── ui/               # Composants de base
│   ├── forms/            # Composants de formulaires
│   ├── charts/           # Composants de graphiques
│   ├── layout/           # Composants de mise en page
│   └── features/         # Composants spécifiques aux fonctionnalités
├── hooks/                # Hooks React personnalisés
├── services/             # Services API et externes
├── stores/               # Gestion d'état Zustand
├── types/                # Définitions TypeScript
├── utils/                # Fonctions utilitaires
├── lib/                  # Configuration des bibliothèques tierces
└── styles/               # Styles globaux et Tailwind
```

## 🧪 **Tests**

```bash
# Lancer tous les tests
npm test

# Tests en mode watch
npm run test:watch

# Couverture de code
npm run test:coverage

# Vérification des types TypeScript
npm run type-check
```

## 🔧 **Scripts Disponibles**

```bash
npm run dev          # Serveur de développement
npm run build        # Build de production
npm run start        # Serveur de production
npm run lint         # Vérification ESLint
npm run type-check   # Vérification TypeScript
npm test             # Exécution des tests
```

## 🎨 **Personnalisation**

### **Thème Tailwind**

Le fichier `tailwind.config.js` contient :
- Palette de couleurs personnalisée DD Intelligence
- Typographies Inter et JetBrains Mono
- Animations et transitions personnalisées
- Composants utilitaires

### **Composants UI**

Les composants sont organisés par domaine :
- **Base** : Boutons, inputs, cartes
- **Layout** : Navigation, sidebar, header
- **Features** : Recherche, graphiques, rapports

## 📱 **Responsive Design**

L'interface est optimisée pour :
- **Mobile** : 320px - 768px
- **Tablet** : 768px - 1024px
- **Desktop** : 1024px+

## 🔒 **Sécurité**

- **CSP Headers** : Protection contre XSS
- **JWT Tokens** : Authentification sécurisée
- **Input Validation** : Validation Zod côté client
- **HTTPS Only** : Communication sécurisée

## 🚀 **Déploiement**

### **Vercel (Recommandé)**
```bash
npm run build
# Déployer sur Vercel
```

### **Docker**
```bash
docker build -t dd-intelligence-frontend .
docker run -p 3000:3000 dd-intelligence-frontend
```

### **Autres Plateformes**
- **Netlify** : Compatible avec Next.js
- **AWS Amplify** : Déploiement automatisé
- **Azure Static Web Apps** : Intégration Azure

## 📊 **Performance**

### **Métriques Cibles**
- **LCP** : < 2.5s
- **FID** : < 100ms
- **CLS** : < 0.1
- **Bundle Size** : < 1MB initial

### **Optimisations**
- Code splitting automatique
- Images optimisées Next.js
- Lazy loading des composants
- Cache agressif avec TanStack Query

## 🤝 **Contribution**

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📄 **Licence**

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🆘 **Support**

- **Documentation** : `/docs`
- **Issues** : GitHub Issues
- **Discussions** : GitHub Discussions
- **Email** : support@dd-intelligence.com

## 🔮 **Roadmap**

### **Phase 1 (Actuel)**
- [x] Configuration de base
- [x] Page d'accueil
- [ ] Système d'authentification
- [ ] Recherche d'entreprises

### **Phase 2**
- [ ] Tableau de bord
- [ ] Visualisation des données
- [ ] Système de rapports

### **Phase 3**
- [ ] Assistant IA
- [ ] Facturation Stripe
- [ ] Collaboration équipe

---

**Développé avec ❤️ par l'équipe DD Intelligence**
