# AGENTS.md — AI Coding Agent Instructions for TerraVisu

TerraVisu is a geospatial data visualization and territorial intelligence platform built by [Terralego](https://github.com/Terralego). It ingests vector and raster geospatial data from heterogeneous sources, organizes them into interactive map scenes with styling/filtering/analytics, and exposes both an internal visualization API and a read-only public OpenAPI/GeoJSON API.

---

## 1. Tech Stack & Services

### Backend
- **Language & Runtime**: Python `3.12` (`.python-version`)
- **Framework**: Django `5.2.*` with GeoDjango (`django.contrib.gis`), Django REST Framework (`djangorestframework`), `djangorestframework-gis`
- **Key Libraries**:
  - `django-geostore`: Two-column vector feature storage (`geom` + `properties` JSONB) and vector tile / GeoJSON rendering
  - `django-polymorphic`: Polymorphic data source models in `geosource`
  - `django-filter`: Declarative and dynamic query filtering
  - `drf-spectacular`: OpenAPI 3 schema generation, Swagger UI, and Redoc
  - `django-constance`: Dynamic instance configuration stored in DB/memory
  - `celery` + `redis`: Asynchronous source ingestion, refresh schedules, and exports
- **Dependency Management**: `uv` with `pyproject.toml` locked into `requirements.txt`, `requirements-dev.txt`, and `docs/requirements.txt`

### Infrastructure (`docker-compose.yml`)
- `db`: PostgreSQL 15 + PostGIS 3.3 (`postgis/postgis:15-3.3`, bound to `127.0.0.1:5432` in dev)
- `redis`: Redis 7 (`redis:7-alpine`, Celery broker & Django cache)
- `elasticsearch`: Elasticsearch `8.19.*` (analytics & Pivot QL queries for frontend widgets)
- `web`: Django development server (`:8000`)
- `celery`: Celery worker + Beat scheduler (`celery -A project worker -B`)
- `nginx`: Reverse proxy on `:8080` routing `/api`, `/config`, `/static_dj`, `/media`, `/private`, `/base-layers`, `/env.json` to `web:8000`, `/elasticsearch/` to ES, `/admin/` to the admin SPA, and `/` to the visualization SPA

### Frontend Submodules (`.gitmodules`)
- `front/` (`Terralego/visu-front`): Public map visualization SPA — React, MapLibre GL / Mapbox GL, BlueprintJS / MUI, Vite 7, Vitest 5, `oxlint`
- `admin/` (`Terralego/terra-admin`): Back-office administration SPA — React-Admin, MapLibre GL, BlueprintJS / MUI, Vite 7, Vitest 5, `oxlint`

---

## 2. Repository Structure & Django Apps

```text
.
├── project/                 # Django backend source code
│   ├── accounts/            # Custom User (email login), FunctionalPermission, tokens, JWT/OIDC
│   ├── visu/                # Instance settings (/env.json, /api/settings/), SPA bootstrap, menus, CSS
│   ├── geosource/           # Polymorphic data sources & typed Field definitions; syncs to geostore
│   ├── terra_layer/         # Scenes, LayerGroups, Layers, styles, filters, popups, reports, declarations
│   ├── geo_api/             # Internal feature & analytics API (/api/geo-api/) used by front/ and admin/
│   ├── public_api/          # External read-only per-layer API (/api/public/) + OpenAPI/Swagger/Redoc
│   ├── utils/               # Shared backend utilities (private media storages, JSONB SQL expressions)
│   ├── fixtures/            # Initial data fixtures (project/fixtures/initial.json)
│   ├── locales/             # Gettext catalogs (en, fr) — strictly checked in CI
│   └── settings/            # Base (__init__.py), dev.py, prod.py, tests.py, oidc.py
├── front/                   # Git submodule: public visualization frontend (Vite + React)
├── admin/                   # Git submodule: administration back-office (Vite + React-Admin)
├── docs/                    # Sphinx documentation
├── conf/                    # Nginx development configuration
├── .docker/                 # Dockerfiles & compose files for backend, front, and admin builds
├── Makefile                 # Canonical Docker-based developer commands
└── pyproject.toml           # Dependencies, Ruff linter/formatter config, coverage config
```

### API Boundaries (`project/urls.py`)
1. **Admin & Internal APIs (`/api/...`, `/api/geo-api/...`)**:
   - Consumed directly by `front/` and `admin/`.
   - **Do not introduce breaking changes** to serializer shapes, query parameter names, or URL routes in `accounts`, `visu`, `geosource`, `terra_layer`, or `geo_api` without coordinating frontend/admin changes.
2. **Public Read-Only API (`/api/public/...`)**:
   - External consumer API (`project/public_api/`).
   - Strictly read-only (`GET`, `HEAD`, `OPTIONS`).
   - Virtually separates the underlying two-column `geostore` storage into per-layer typed endpoints (`/api/public/layers/<id>/features/`), with dynamic typed `Serializer`s, dynamic `FilterSet`s, GeoJSON (`?format=geojson`) and JSON (`?format=json`) output, and scoped OpenAPI docs at `/api/public/schema/`, `/api/public/schema/swagger/`, and `/api/public/schema/redoc/`.

---

## 3. Domain Invariants & Pitfalls (Read Before Editing)

### Two-Column Feature Storage & Safe SQL Casting
- Vector features are stored in `geostore.models.Feature` with:
  - `geom`: PostGIS `GeometryField` (`SRID 4326`)
  - `properties`: PostgreSQL `jsonb` (`JSONField`)
  - `layer`: FK to `geostore.models.Layer` (matched via `geostore_layer.name == geosource.slug`)
- Field types (`String`, `Integer`, `Float`, `Boolean`, `Date`, `Undefined`) are declared on `geosource.models.Field`.
- **Dirty JSONB values**: Because `properties` is schemaless JSONB, a field typed as `Integer` or `Float` may still contain `""`, `"N/A"`, or malformed text in raw data. Never perform unguarded SQL `::double precision` / `::integer` casts on `properties` keys — reuse the shared SQL extraction/casting helpers in `project/utils/expressions.py` (`extract_text`, `extract_float`, `ToFloat`, `JsonbExtractText`) that return `NULL` on non-numeric strings instead of crashing with `psycopg2.DataError`.
- **Accent-insensitive search**: PostgreSQL has the `unaccent` extension enabled. Prefer `unaccent`-aware lookups when implementing text search on feature properties.

### Never Call `source.get_layer()` in Read-Only Request Paths
- `geosource.models.Source.get_layer()` triggers `layer_callback`, which **writes to the database** and resets `geostore.Layer.authorized_groups` from `source.groups`.
- In read-only views, serializers, permissions, and schema generators, look up the geostore layer without side effects:
  ```python
  GeostoreLayer.objects.filter(name=source.slug).first()
  ```

### Visibility & Permission Rules
- A `terra_layer.models.Layer` is **publicly accessible** (anonymous allowed) if and only if:
  1. `layer.in_tree is True`,
  2. `layer.group` belongs to an active `Scene` (`layer.group.view_id is not None`), and
  3. its backing `geosource.Source` has **no** restricted `groups` (`not source.groups.exists()`).
- If `source.groups` is non-empty, access requires an authenticated user who is either `is_superuser`, holds the `can_manage_layers` permission, or belongs to one of the authorized `django.contrib.auth.models.Group`s.
- **Duplicate permission codename gotcha**: `can_manage_layers` exists under both `accounts` and `geostore` content types. Always filter `Permission.objects` explicitly with `content_type__app_label="geostore"` (or `"accounts"` when targeting `FunctionalPermission`) to avoid `Permission.MultipleObjectsReturned`.

### Pivot QL `source_filter` Isolation
- Multiple `terra_layer.Layer` instances can share the same `geosource.Source` while filtering subsets of features via `layer.source_filter` (Pivot QL expression, e.g. `status = 'open' AND score >= 10`).
- Any endpoint exposing features of a `terra_layer.Layer` **must** apply its `source_filter` (see `project/public_api/source_filter.py`) so features excluded by the layer definition are never leaked via list, detail, search, or filter endpoints.

### Git Submodules
- `front/` and `admin/` are independent Git submodules. Do not stage or modify files inside `front/` or `admin/` unless the task explicitly targets the frontend or admin app.

---

## 4. Development Commands

### Environment Setup
Ensure `db.env` and `app.env` exist at the repository root:
```bash
cp -n db.env.dist db.env
cp -n app.env.dist app.env
```

### Workflow A: Docker Compose / Makefile (CI Parity)
```bash
make quality          # Run ruff check --fix and ruff format inside web container
make lint             # Run ruff check --fix project
make format           # Run ruff format project
make test             # Run full Django test suite (--settings=project.settings.tests)
make coverage         # Run test suite with coverage report
make messages         # Update .po files (makemessages) and compile .mo files
make deps             # Recompile requirements*.txt from pyproject.toml using uv
make docs_build       # Build Sphinx HTML documentation
make sphinx           # Build Sphinx HTML documentation with warnings as errors (-W, CI parity)
make django <cmd>     # Run arbitrary ./manage.py command in web container
```

### Workflow B: Fast Local Host Execution (`.venv` + Docker PostGIS)
When `.venv` and `ruff` are available on the host and `db` is running (`docker compose up -d db`), you can iterate much faster on targeted apps:
```bash
# Lint & format check
ruff check project
ruff format --check project

# Run targeted Django tests with coverage against local PostGIS container
mkdir -p var && set -a && . ./db.env && . ./app.env && set +a && \
  POSTGRES_HOST=127.0.0.1 .venv/bin/coverage run manage.py test project.geo_api project.public_api \
  --settings=project.settings.tests --keepdb && \
  .venv/bin/coverage report -m --include="project/geo_api/*,project/public_api/*" --fail-under=100
```
> Note: `pyproject.toml` sets `data_file = "var/.coverage"`, so ensure `var/` exists when running `coverage` on the host. Ensure `requirements-dev.txt` is installed in `.venv` (`uv pip install -r requirements-dev.txt`) when running test suites that rely on `factory_boy` or `responses` (e.g., `geosource`, `terra_layer`), or run the full suite via `make coverage`.

### Dependency Updates
- Never edit `requirements.txt`, `requirements-dev.txt`, or `docs/requirements.txt` manually.
- Update `pyproject.toml` first, then run `make deps` to regenerate all lockfiles cleanly.

### Frontend (`front/`) & Admin (`admin/`) Commands
Inside `front/` or `admin/` (Node + Vite 7 + Vitest 5 + `oxlint`):
```bash
npm ci --legacy-peer-deps
npm run start         # Start Vite dev server
npm run lint          # Lint with oxlint (npm run lint:fix to auto-fix)
npm run test          # Run Vitest unit tests once
npm run coverage      # Run Vitest unit tests with v8 coverage report
npm run build         # Production Vite build (or use make build_front / make build_admin)
```

---

## 5. Code Style & Ruff Rules (Enforced in CI)

CI (`.github/workflows/lint.yml`) runs `ruff check project` and `ruff format --check project` on Python `3.12` with line length `88` and double quotes.

Enabled rule families in `pyproject.toml`:
`["G", "INT", "E4", "E7", "E9", "F", "DJ", "LOG", "UP", "I", "T10", "EM", "T201"]`

Follow these mandatory patterns when writing Python code to avoid Ruff failures:

1. **Exception messages (`EM101` / `EM102`)** — Never pass string literals or f-strings directly to `raise`:
   ```python
   # BAD
   raise ValueError(f"Unsupported field type: {field_type}")

   # GOOD
   msg = f"Unsupported field type: {field_type}"
   raise ValueError(msg)
   ```
2. **Gettext interpolation (`INT001` / `INT002` / `INT003`)** — Never use f-strings inside `_()` or `.format()` on `_()`; always use `%(name)s` printf-style mapping:
   ```python
   # BAD
   _(f"Layer {name} not found")
   _("Layer {name} not found").format(name=name)

   # GOOD
   _("Layer %(name)s not found") % {"name": name}
   ```
3. **Logging (`LOG` / `G001`–`G004`)** — Instantiate module loggers with `logger = logging.getLogger(__name__)` and use lazy `%s` placeholders instead of f-strings or `%` formatting:
   ```python
   # BAD
   logger.warning(f"Failed to parse filter for layer {layer.pk}: {exc}")

   # GOOD
   logger.warning("Failed to parse filter for layer %s: %s", layer.pk, exc)
   ```
4. **No debug/print leftovers (`T201`, `T10`)** — Never leave `print()`, `breakpoint()`, or `pdb` calls in `project/` (management commands writing output must use `self.stdout.write(...)`).
5. **Django conventions (`DJ`)** — Define `__str__` on models, avoid `null=True` on `CharField`/`TextField` (use `blank=True, default=""`), and declare explicit `fields` on DRF serializers/ModelForms.
6. **Modern Python 3.12 typing & syntax (`UP`, `I`)** — Use `X | None` instead of `Optional[X]`, built-in generics (`list[str]`, `dict[str, Any]`), and let Ruff sort imports (`I`).

---

## 6. Internationalization (i18n) — Strict CI Gate

**Critical**: `.github/workflows/test.yml` executes `./manage.py makemessages -a --no-location --no-obsolete` and **fails the CI pipeline if any `.po` file has uncommitted diffs**.

### Rules
1. **English in code**: Write all user-facing strings, model `verbose_name` / `help_text`, DRF error messages, filter labels, and OpenAPI descriptions in **English** wrapped in `gettext_lazy as _` (or `gettext` inside request-time functions).
2. **French & English catalogs**: Keep both `project/locales/fr/LC_MESSAGES/django.po` and `project/locales/en/LC_MESSAGES/django.po` updated and compiled (`.mo`).
3. **Updating translations**:
   - **Via Docker (recommended)**:
     ```bash
     make messages
     ```
   - **On the host via `.venv`** — You **must** pass `-i` exclusions so `makemessages` does not scan `.venv`, submodules, or build artifacts (matching Docker behavior where only `project/` is present):
     ```bash
     .venv/bin/python manage.py makemessages -a --no-location --no-obsolete \
       -i .venv -i admin -i front -i frontend -i docs -i build -i public -i skills -i var
     ```
   - Translate new `msgid` entries in `project/locales/fr/LC_MESSAGES/django.po`, review and remove any `#, fuzzy` flags on verified translations, then compile:
     ```bash
     .venv/bin/python manage.py compilemessages -l fr -l en
     ```
4. **Dynamic schema/filter caching**: If you cache dynamically generated classes containing `gettext()` strings (such as per-layer `FilterSet`s or OpenAPI fragments), include `django.utils.translation.get_language()` in the cache key so `Accept-Language` switching works per request.

---

## 7. Migrations, Fixtures, Testing & 100% Coverage Mandate

- **Mandatory 100% Unit Test Coverage**:
  - **All new and modified code MUST achieve 100% unit test coverage (`--fail-under=100`)**.
  - Cover every branch, permission path, serializer/filter edge case, error handler, and fallback path with automated unit tests.
  - Never add `# pragma: no cover` to bypass missing tests on executable logic.
  - Coverage is configured in `pyproject.toml` (`[tool.coverage.run]` targeting `project/`, omitting `**/tests/*`, `**/settings/*`, `**/migrations/*`, `wsgi.py`, and `asgi.py`, with `data_file = "var/.coverage"`). When modifying `front/` or `admin/`, enforce 100% coverage on touched modules via `npm run coverage`.
- **Migrations**:
  - `project/settings/__init__.py` forces `LANGUAGE_CODE = "en-us"` during `makemigrations` so generated migration metadata is always in English.
  - Whenever models or model field metadata (`verbose_name`, `help_text`, `choices`) change, generate migrations and verify `makemigrations --check`.
- **Initial Fixtures**:
  - `project/fixtures/initial.json` is loaded in CI after `migrate`. Ensure schema changes remain compatible with `initial.json` (or update the fixture if required).
- **Test Settings (`project.settings.tests`)**:
  - Disables migrations for speed (`MIGRATION_MODULES` uses `DisableMigrations` for all apps except `geo_api`, which creates required PostgreSQL extensions like `unaccent` / `postgis`), runs Celery tasks eagerly (`CELERY_TASK_ALWAYS_EAGER = True`), uses `LocMemCache` and Constance `MemoryBackend`, and runs with `--parallel` in CI.
  - Keep unit tests isolated and parallel-safe (avoid hardcoding primary keys or relying on shared filesystem paths outside temporary directories).

---

## 8. Documentation & `AGENTS.md` Maintenance (Mandatory)

Documentation and agent instructions **must never drift** from the codebase. Whenever you introduce, modify, or remove behavior, update both in the **same task**:

1. **Always update `AGENTS.md`**:
   - Update `AGENTS.md` whenever you add/rename/remove a Django app, shared utility (`project/utils/`), API boundary, environment variable, dependency/tooling workflow, Makefile target, domain invariant, or CI gate.
2. **Always update project documentation (`docs/` & `README.md`)**:
   - Update the relevant Sphinx `.rst` files in `docs/source/` whenever changes affect:
     - Installation, environment variables, or instance settings (`django-constance` / `settings`) → `docs/source/installation_configuration/` (`install.rst`, `configuration.rst`, `troubleshooting.rst`)
     - End-user features, admin back-office workflows, or APIs → `docs/source/user_manual/` (`user_guide.rst`, `admin_user_guide.rst`, `module_configuration.rst`, `module_sheet.rst`)
     - Architecture, design decisions, translation, or contributor workflows → `docs/source/contribute/` (`design.rst`, `development.rst`, `contributing.rst`, `translating.rst`, `documentation.rst`)
   - Update `README.md` if top-level setup or quickstart instructions change.
3. **Strict Sphinx CI Gate (`SPHINXOPTS="-W"`)**:
   - `.github/workflows/doc.yml` compiles Sphinx documentation with `-W` (warnings treated as errors). Broken cross-references, invalid `.rst` directives, or heading underline mismatches will fail CI.
   - Always validate doc edits with `make sphinx` (Docker) or `cd docs && make html -e SPHINXOPTS="-W"` (local environment with `docs/requirements.txt`).

---

## 9. Pre-Completion Verification Checklist

Before considering any task complete, verify all CI gates and documentation requirements pass:

1. **Lint & Format**:
   - `ruff check project`
   - `ruff format --check project`
2. **Migrations & Fixtures** (when models/choices/metadata were touched):
   - `./manage.py makemigrations --check`
   - `./manage.py migrate`
   - `./manage.py loaddata project/fixtures/initial.json`
3. **Translations (`.po` & `.mo`)** (when any `_()` string was added, changed, or removed):
   - Run `makemessages -a --no-location --no-obsolete` (via Docker or with host `-i` exclusions), translate French entries in `project/locales/fr/LC_MESSAGES/django.po`, clear `#, fuzzy` markers, run `compilemessages`, and confirm re-running `makemessages` produces zero diff on `**/*.po`.
4. **Automated Tests & 100% Coverage**:
   - Run unit tests with `coverage` (`--settings=project.settings.tests`) and verify `coverage report -m --fail-under=100` on all created or modified files (plus `npm run coverage` when touching `front/` or `admin/`).
5. **Documentation & `AGENTS.md` Sync**:
   - Confirm `AGENTS.md` and `docs/source/**/*.rst` (plus `README.md` if applicable) have been updated to reflect any architectural, API, configuration, or feature changes, and verify Sphinx builds cleanly without warnings (`make sphinx` / `SPHINXOPTS="-W"`).
