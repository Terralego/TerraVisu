=========
CHANGELOG
=========

XXXX.X.X       (2023-06-09)
---------------------------

**Improvements:**

- Ability to define default text for SSO and internal login buttons in frontend and admin


2023.6.3       (2023-06-08)
---------------------------

**Bugfix**

- Fix instance config panel with new dashboard
- Fix user login state after an SSO login in frontend


2023.6.2       (2023-06-07)
---------------------------

**New feature**

- Complete OIDC login feature in frontend and admin

**Improvements:**

- In admin layer style, ability to choose if icon style overlaps or not


2023.6.1       (2023-06-01)
---------------------------

**Improvements:**

- Provide user and initial token in both frontend and admin settings API
- Provide login and logout urls in API settings in case of SSO authentification enabled


2023.5.5       (2023-05-31)
---------------------------

**Improvements:**

- Implement JWT token generation to authenticate through sessions


2023.5.4       (2023-05-30)
---------------------------

**Improvements:**

- Allow icon_allow_overlap in layer admin style definition


2023.5.3       (2023-05-25)
---------------------------

**Improvements:**

- Allow customization by providing var/conf/{static | templates} folders tu override and adding custom files


2023.5.2       (2023-05-17)
---------------------------

**Improvements:**

- Frontend CSS simplified location


2023.5.1       (2023-05-17)
---------------------------

**Bugfix**

- Fix style image already loaded in frontend

**Improvements:**

- Layer legend title is not required anymore


2023.5.0       (2023-05-10)
---------------------------

**Bugfix**

- Fix legend null values in admin


2023.4.9       (2023-04-26)
---------------------------

**Bugfix**

- Prevent deleted style key in admin to keep null value

**Improvements:**

- Increase style categorization from 20 to 100 element max in admin layer style.


2023.4.8       (2023-04-24)
---------------------------

**Bugfix**

- Fix permission management on source list in admin
- Fix regression with style category color picker in admin


2023.4.7       (2023-04-21)
---------------------------

**Bugfix**

- Fix layer duplication and notification in admin


2023.4.6       (2023-04-20)
---------------------------

**Improvements:**

- Layer duplication in admin improved and now made by backend duplication


2023.4.5       (2023-04-20)
---------------------------

**Improvements:**

- Disable autocomplete / autofill on PostGIS source form in admin

**Bugfix**

- Allow PostGIS source form edition in admin without retype password


2023.4.4       (2023-04-19)
---------------------------

**Improvements:**

- Improve admin to define polygons patterns
- Filter frontend with non empty views
- Default view is now the first ordered for an user (authenticated or not)


2023.4.3       (2023-04-13)
---------------------------

**Improvements:**

- Allow to set group access to extra menu items
- Include basic certificates in docker image


2023.4.2       (2023-04-11)
---------------------------

**New features:**

- Allow using style images patterns in polygon advanced styles


2023.4.1       (2023-04-07)
---------------------------

**New Version**

**New Simplified Installation**

**New documentation**

**Bug fixes:**

- Fix and allow date usage in source fields and imported data
- Fix group creation / edition in admin
- Fix LayerTree cache management
- Fix bug when no base layer defined in scene (#109)

**New features:**

- Use icon and patterns in point / polygon styles


**Improvements:**

- Direct use elasticsearch connector for data indexation instead of terra-bonobo-nodes
- Better layer duplication
- Some instance configuration managed in config panel (/config/)

**Maintenance**

- From Python 3.6 to 3.10
- From Django 2.2 to 4.1
- All python packages updated
- Admin node-js from 12 to 18
