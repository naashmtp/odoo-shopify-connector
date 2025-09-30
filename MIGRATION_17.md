# Migration vers Odoo 17

## Changements effectués

### 1. __manifest__.py

#### Version
- **Avant (v16)**: `'version': '16.0.1.0.0'`
- **Après (v17)**: `'version': '17.0.1.0.0'`

#### Assets
Les bundles d'assets ont été rendus plus explicites pour améliorer les performances et la maintenabilité.

**Avant (v16)**:
```python
'assets': {
    'web.assets_backend': [
        'shopify_integration/static/src/js/**/*',
        'shopify_integration/static/src/css/**/*',
        'shopify_integration/static/src/xml/**/*',
    ],
},
```

**Après (v17)**:
```python
'assets': {
    'web.assets_backend': [
        'shopify_integration/static/src/js/shopify_dashboard.js',
        'shopify_integration/static/src/css/**/*.css',
        'shopify_integration/static/src/xml/**/*.xml',
    ],
},
```

**Raison**: Odoo 17 recommande de lister explicitement les fichiers JS importants et d'utiliser des globs plus précis avec extensions pour éviter de charger des fichiers inutiles.

### 2. static/src/js/shopify_dashboard.js

#### Import OWL
Ajout de `onWillUnmount` dans les imports OWL.

**Avant (v16)**:
```javascript
import { Component, useState, onWillStart, onMounted } from "@odoo/owl";
```

**Après (v17)**:
```javascript
import { Component, useState, onWillStart, onMounted, onWillUnmount } from "@odoo/owl";
```

#### Lifecycle hooks
Déplacement de la logique de nettoyage de `willUnmount()` vers `onWillUnmount()`.

**Avant (v16)**:
```javascript
setup() {
    // ...
    onMounted(() => {
        this.startAutoRefresh();
    });
}

willUnmount() {
    if (this.refreshInterval) {
        clearInterval(this.refreshInterval);
    }
}
```

**Après (v17)**:
```javascript
setup() {
    // ...
    onMounted(() => {
        this.startAutoRefresh();
    });

    onWillUnmount(() => {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
    });
}
```

**Raison**: Dans Odoo 17, tous les lifecycle hooks doivent être déclarés dans `setup()` pour une meilleure cohérence et traçabilité du cycle de vie des composants.

## Différences avec v16

### Ce qui a changé
1. **Assets**: Syntaxe plus stricte et explicite pour les bundles
2. **OWL Lifecycle**: Tous les hooks doivent être dans `setup()`
3. **Numéro de version**: Passage à 17.0.x.x.x

### Ce qui reste identique
- **Modèles Python**: 100% compatibles, aucun changement requis
- **Vues XML**: Compatibles, aucun changement requis
- **Structure du module**: Identique
- **API ORM**: Aucun changement dans les appels `orm.call()`, `orm.searchRead()`, etc.
- **Services**: `useService()` fonctionne de la même manière
- **Actions**: Format des actions inchangé

## Notes de compatibilité

### Compatible sans modification
- Tous les modèles Python (`models/`)
- Toutes les vues XML (`views/`)
- Les wizards
- Les contrôleurs
- Les données (`data/`)
- Les règles de sécurité (`security/`)
- Les tests

### Modifications requises
- Fichier manifest (version + assets)
- Composants OWL JavaScript (lifecycle hooks)

### Points d'attention
1. **Performance**: Les assets explicites améliorent le temps de chargement
2. **OWL**: Plus strict sur la déclaration des hooks mais plus prévisible
3. **Debugging**: Les bundles explicites facilitent le débogage
4. **Maintenance**: Code plus clair et respectant les nouvelles conventions

## Compatibilité ascendante

Ce module migré vers v17 **n'est pas compatible** avec Odoo 16. Pour supporter les deux versions:
- Maintenir deux branches séparées (16.0 et 17.0)
- Ou utiliser des conditions dans le code (non recommandé)

## Prochaines étapes recommandées

1. Tester le module sur une instance Odoo 17
2. Vérifier le chargement du dashboard
3. Tester la synchronisation Shopify
4. Valider les performances des assets
5. Mettre à jour la documentation si nécessaire

## Ressources

- [Odoo 17 Release Notes](https://www.odoo.com/odoo-17)
- [OWL Documentation](https://github.com/odoo/owl)
- [Migration Guide](https://www.odoo.com/documentation/17.0/developer/howtos/upgrade.html)