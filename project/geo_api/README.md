# GeoAPI

Base path: `/api/geo-api/{layer_name}/`

- `{layer_name}` can be a layer slug or a layer numeric ID.
- `{identifier}` accepts either the feature PK (integer) or the `identifier` value (string).
- `{format}` can be any DRF format suffix (e.g. `json`, `api`, `geojson`, `kml`, `gpx`).
- Authentication: read operations are public; write operations require the
  `geostore.can_manage_layers` permission. Layers restricted through
  `authorized_groups` are only readable by members of those groups.

---

## Sommaire

| Méthode | URL | Description |
|---------|-----|-------------|
| GET, POST | `/api/geo-api/{layer_name}/feature/` | Liste paginée / Création d'une entité |
| GET, PUT, PATCH, DELETE | `/api/geo-api/{layer_name}/feature/{identifier}/` | Détail / Modification / Suppression |
| GET | `/api/geo-api/{layer_name}/feature/count/` | Nombre d'entités filtrées |
| GET | `/api/geo-api/{layer_name}/feature/extent/` | BBOX de toute la couche |
| GET | `/api/geo-api/{layer_name}/feature/stats/{field}/` | Statistiques sur une propriété |
| GET | `/api/geo-api/{layer_name}/feature/stats/{field}/distribution/` | Histogramme, boxplot et échantillon |
| GET | `/api/geo-api/{layer_name}/feature/discretize/{field}/` | Bornes de classes pour une légende |
| GET | `/api/geo-api/{layer_name}/feature/distinct/{field}/` | Valeurs distinctes d'une propriété |
| GET | `/api/geo-api/{layer_name}/feature/distinct/all/{field}/` | Idem, sans pagination |
| GET | `/api/geo-api/{layer_name}/feature/{identifier}/extent/` | BBOX d'une entité |
| GET, PUT, PATCH, DELETE | `/api/geo-api/{layer_name}/feature/{identifier}/extra_geometry/{id_extra_feature}/` | Gestion des géométries supplémentaires |
| POST | `/api/geo-api/{layer_name}/feature/{identifier}/extra_layer/{id_extra_layer}/` | Création d'une géométrie supplémentaire |
| GET | `/api/geo-api/{layer_name}/feature/{identifier}/relation/{id_relation}/features/` | Entités liées par une relation |

Tous les endpoints acceptent un suffixe de format optionnel : `.{format}` (e.g. `.json`, `.geojson`, `.kml`, `.gpx`).

---

## Feature list & create

```
GET    /api/geo-api/{layer_name}/feature/
```

`GET` retourne les entités paginées (sans géométrie par défaut).  

### Paramètres de filtre 

| Param | Type | Description |
|-------|------|-------------|
| `search` | string | Full-text search across all properties (accent-insensitive) |
| `limit` | int | Page size (default 100, max 100000) |
| `offset` | int | Pagination offset |
| `ordering` | string | Sort field (prefix `-` for descending). Property names are accepted. |
| `fields` | string | Comma-separated property keys to include |
| `geometry` | bool | Set `true` to include geometry in response |
| `all` | bool | Include geometry + all properties |
| `bbox` | `min_lng,min_lat,max_lng,max_lat` | Spatial filter (intersects) |
| `{key}` | string | Filter on a top-level property (e.g. `?nom=Paris`). Accent-insensitive. |
| `{key}` | `val1,val2` | `IN` filter on a property |
| `{key}` | `>=val`, `<=val`, `>val`, `<val` | Operator filter |
| `{key}` | `min-max` | Range filter |
| `properties__{key}` | string | Exact match on a property (e.g. `?properties__code=75056`) |



### Réponse  

```json
GET /api/geo-api/communes-simplifiees/feature/?search=paris&limit=2

{
    "count": 10,
    "next": "http://localhost:8000/api/geo-api/communes-simplifiees/feature/?limit=2&offset=2&search=paris",
    "previous": null,
    "results": {
        "type": "FeatureCollection",
        "features": [
            {
                "id": 98178,
                "identifier": "75056",
                "properties": {
                    "nom": "Paris",
                    "code": "75056",
                    "search_match": "nom"
                }
            },
            {
                "id": 103895,
                "identifier": "71343",
                "properties": {
                    "nom": "Paris-l'Hôpital",
                    "code": "71343",
                    "search_match": "nom"
                }
            }
        ]
    }
}
```

### Avec géométrie

```json
GET /api/geo-api/communes-simplifiees/feature/?search=paris&geometry=true&limit=1

{
    "count": 10,
    "next": "http://localhost:8000/api/geo-api/communes-simplifiees/feature/?geometry=true&limit=1&offset=1&search=paris",
    "previous": null,
    "results": {
        "type": "FeatureCollection",
        "features": [
            {
                "id": 98178,
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [...]
                },
                "properties": {
                    "nom": "Paris",
                    "code": "75056",
                    "search_match": "nom"
                }
            }
        ]
    }
}
```


`{identifier}` accepte soit le PK numérique, soit la valeur du champ `identifier`.


---

## Count

```
GET /api/geo-api/{layer_name}/feature/count/
```

**Paramètres**: mêmes filtres que la liste (`search`, `bbox`, propriétés, etc.)

```json
GET /api/geo-api/communes-simplifiees/feature/count/?search=paris

{ "count": 10 }
```

---

## Layer extent

```
GET /api/geo-api/{layer_name}/feature/extent/
```

Retourne la bounding box de toute la couche.

```json
GET /api/geo-api/communes-simplifiees/feature/extent/

{ "bbox": [-5.13, 41.36, 9.55, 51.08] }
```

---

## Feature extent

```
GET /api/geo-api/{layer_name}/feature/{identifier}/extent/
```

Retourne la bounding box d'une seule entité.

```json
GET /api/geo-api/communes-simplifiees/feature/98178/extent/

{ "bbox": [2.224, 48.815, 2.469, 48.902] }
```

---

## Stats

```
GET /api/geo-api/{layer_name}/feature/stats/{field}/
```

Retourne les statistiques d'une propriété numérique. Les valeurs non numériques
sont ignorées (comptées comme nulles) plutôt que de faire échouer la requête.

```json
GET /api/geo-api/communes-simplifiees/feature/stats/population/

{
    "min": 0, "max": 2500000, "avg": 12500.42, "sum": 437514700,
    "count": 34999, "total_count": 35000, "std_dev": 48210.5,
    "median": 1780.0, "q1": 480.0, "q3": 6120.0
}
```

`count` compte les entités dont la propriété est numérique, `total_count` toutes
les entités de la couche.

---

## Distribution

```
GET /api/geo-api/{layer_name}/feature/stats/{field}/distribution/
```

Histogramme (bornes de classes calculées par la règle de Freedman-Diaconis,
plafonné à 100 classes), boxplot et échantillon d'au plus 1000 valeurs.

```json
{
    "bins": [{ "x0": 0, "x1": 500, "count": 12043 }],
    "boxplot": { "min": 0, "q1": 480, "median": 1780, "q3": 6120, "max": 2500000 },
    "sample": [12, 480, 1780]
}
```

---

## Discretize

```
GET /api/geo-api/{layer_name}/feature/discretize/{field}/
```

Retourne les bornes de classes d'une légende et le nombre d'entités par classe.

| Param | Type | Description |
|-------|------|-------------|
| `method` | string | `jenks` (défaut), `jenks_kmeans1d`, `quantile`, `equal_interval`, `manual` |
| `classes` | int | Nombre de classes, entre 1 et 100 (défaut 5). Ignoré si `method=manual` |
| `breaks` | `v1,v2,...` | Bornes croissantes, obligatoire et exclusif à `method=manual` |

```json
GET /api/geo-api/communes-simplifiees/feature/discretize/population/?classes=3

{
    "breaks": [0, 1200, 15000, 2500000],
    "entitiesByClass": [18000, 12000, 5000],
    "stats": { "min": 0, "max": 2500000, "...": "..." }
}
```

Un `method` inconnu ou un `classes` hors bornes renvoie `400`.

---

## Distinct values

```
GET /api/geo-api/{layer_name}/feature/distinct/{field}/
```

**Paramètres:**

| Param | Type | Description |
|-------|------|-------------|
| `q` | string | Filtre les valeurs distinctes (accent-insensitive) |

```json
GET /api/geo-api/communes-simplifiees/feature/distinct/nom/?q=par

["Paris", "Parisot", "Paris-l'Hopital", ...]
```


---

## Relations

```
GET /api/geo-api/{layer_name}/feature/{identifier}/relation/{id_relation}/features/
```

Retourne les entités liées à l'entité via la relation spécifiée. Supporte les mêmes paramètres de filtre que la liste (`search`, `bbox`, propriétés, etc.).

---

## Export KML / GPX

Utiliser le paramètre `?format=kml` ou `?format=gpx` :

```
GET /api/geo-api/{layer_name}/feature/?format=kml
GET /api/geo-api/{layer_name}/feature/?format=gpx
GET /api/geo-api/{layer_name}/feature/{identifier}/?format=kml
GET /api/geo-api/{layer_name}/feature/{identifier}/?format=gpx
```

Supportent `bbox`, `search` et tous les filtres par propriété. La géométrie est toujours incluse.

---

## Format suffixes

Tous les endpoints ci-dessus acceptent également un suffixe de format :

```
GET /api/geo-api/{layer_name}/feature.json
GET /api/geo-api/{layer_name}/feature.geojson
GET /api/geo-api/{layer_name}/feature.kml
GET /api/geo-api/{layer_name}/feature.gpx
GET /api/geo-api/{layer_name}/feature/98178.json
GET /api/geo-api/{layer_name}/feature/count.json
...
```
