# Odoo Shopify Connector

Module d'intégration Shopify pour Odoo développé pour casser le prix du marché.

## Fonctionnalités principales

### 1. Configuration & Authentification
- Gestion des instances Shopify multiples
- Authentification OAuth et API
- Assistant de configuration en 4 étapes
- Test de connexion et validation des credentials

### 2. Gestion des Produits
- Import/Export de produits avec variantes et images
- Synchronisation des stocks multi-entrepôts
- Gestion des prix et listes de prix
- Mapping par SKU et gestion des attributs

### 3. Gestion des Commandes
- Import automatique des commandes
- Workflow de traitement automatisé
- Gestion des statuts et suivi
- Support des commandes partielles

### 4. Gestion des Clients
- Synchronisation des clients et adresses
- Gestion des tags et types de clients
- Support des adresses multiples

### 5. Gestion Financière
- Import des virements Shopify
- Réconciliation automatique des paiements
- Gestion des remboursements et avoirs
- Création automatique des factures

### 6. Webhooks
- Configuration automatique des webhooks
- Traitement en temps réel des événements
- Validation des signatures

### 7. Planificateurs et Files d'attente
- Jobs automatisés pour la synchronisation
- Gestion des erreurs et reprises
- Monitoring des performances

### 8. Rapports et Analytique
- Tableaux de bord KPI
- Rapports de ventes et profits
- Analytics des canaux de vente

## Structure du module

```
shopify_integration/
├── models/           # Modèles de données
├── views/            # Vues et interfaces
├── controllers/      # Contrôleurs pour webhooks
├── wizards/          # Assistants de configuration
├── data/             # Données par défaut
├── security/         # Règles de sécurité
├── static/           # Ressources statiques
└── tests/            # Tests unitaires
```

## Installation

1. Copier le module dans le dossier addons d'Odoo
2. Redémarrer le serveur Odoo
3. Aller dans Apps et installer "Shopify Integration"
4. Suivre l'assistant de configuration

## Configuration

1. Créer une instance Shopify
2. Configurer les clés API
3. Tester la connexion
4. Configurer les mappings

## Commandes utiles

- Tests: `python -m pytest tests/`
- Lint: `pylint models/ views/ controllers/`

## Support

Pour toute question ou problème, créer une issue sur le repository.