# `endpoint_sql` : endpoint sans ES

## Contexte

TerraVisu utilise **django-geostore** pour stocker des données géospatiales (communes, etc.) dans PostgreSQL/PostGIS.
On va donc essayer de fournir des **endpoints d'API légers en SQL brut** pour servir des données géographiques au format GeoJSON.

En deux étapes :
- **`endpoint_sql`** (v1) : prototype simple avec une couche et des filtres définis en dur
- **`endpoint_sql2`** (v2) : version générique avec filtres dynamiques, opérateurs, et détection de types

L'objectif final est d'arriver à un **endpoint complet, robuste mais surtout qu'on puisse changer facilement les requêtes.** On doit être capable de servir n'importe quelle couche géographique avec des filtres avancés.

---

## `endpoint_sql` (v1) - proto

**URL :** `/api/endpoint-sql/communes/`

Ce qui a été fait :

- Une **view fonction** Django toute simple (pas de ViewSet, pas de serializer)
- Une **requête SQL brute** qui joint `geostore_feature` et `geostore_layer` et utilise `ST_AsGeoJSON` pour le geometry
- Paramètres : `limit`, `offset`, `nom`, `code`, `order_by`
- Filtrage textuel avec `unaccent` et `ILIKE` pour l'insensibilité aux accents/casse
- **Prefix boosting** : les résultats dont le `nom` commence par la valeur cherchée remontent en premier
- Retourne un `FeatureCollection` GeoJSON

```python
# extrait clé - la jointure et la clause WHERE
SELECT properties, ST_AsGeoJSON(geom)::json as geom_json
FROM geostore_feature f
JOIN geostore_layer l ON f.layer_id = l.id
WHERE l.name = 'communes-simplifiees'
```

---

## `endpoint_sql2` (v2) - version générique et améliorée

**URL :** `/api/endpoint-sql2/<layer_name>/`

Ce qui a été ajouté :

---

## On branche au front ??

