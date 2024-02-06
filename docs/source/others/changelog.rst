==========
Changelog
==========


2024.02.4+dev  (XXXX-XX-XX)
---------------------------

**Improvements:**

- Sources in admin can now be sorted / filtered by model type and update date


2024.02.4      (2024-02-05)
---------------------------

**Improvements:**

- Add source layers in admin list
- Add source status and report status filter in admin
- Add new source status, "In Progress"
- Add author to Source, auto linked at creation
- Add info tab to source details

**Documentation:**

- Add configuration dashboard doc

**Bugfix:**

- Admin : Fix widgets form crashing on existing widget-less layers


2024.02.3      (2024-02-02)
---------------------------

**Breaking changes**

- To access new debug panel, you should add 'debug' exception in nginx configuration file.

**Improvements:**

- Split Config dashboard debug entries in another /debug/ panel.


2024.02.2      (2024-02-01)
---------------------------

**Improvements:**

- Switch from django-grappelli to django-admin-interface for config dashboard
- Improve config dashboard


2024.02.1      (2024-02-01)
---------------------------

**New features :**

- Admin interface for widgets configuration (admin)
- Widgets can now have an icon and a title (admin & front)
- Widgets can be limited to a specified bbox (admin & front)
- Option to deactivate search in layers (config & front)

**Bug fixes :**

- Fix build non-split for CSS overrides


2024.01.1      (2024-01-22)
---------------------------

**Improvements:**
- Terra-front is now part of Visu-front

**New features:**
- Support for layers grouped by variables (admin & front)

**Bug fixes:**
- New icon for layer's informations (front)
- Fix piecharts going over legends (front)
- Remove options to display labels on secondary styles (admin)


2024.01.0      (2024-01-12)
---------------------------

**Improvements:**

- Backend preparation to group layer by variables


2023.11.2      (2023-11-22)
---------------------------

**Improvements:**

- Tooltips added to buttons without text in admin


2023.11.1      (2023-11-20)
---------------------------

**New features**

- Ability to manage and use permanent access token to auto login.


2023.11.0      (2023-11-16)
---------------------------

**Improvements:**

- Layers information popup now renders HTML content (front)
- Improvements on source list and report tab (admin)


**Bugfix**

- Fix admin's layerlist filter on view (#458)
- Fix admin layout issues


**New features**

- Embed dialog (admin and front)
- Label option on polygon, line and circle layers (admin and front)


2023.10.7      (2023-10-25)
---------------------------

**Improvements:**

- Enable sentry in frontend and admin, configuration with new environment variables (cf. doc)
- Remove logo from pdf print (#394)
- Add some color to login/logout button to improve login status visibility.


**Bugfix**

- Fix data tab being empty on datasource edit page (#410)


2023.10.6      (2023-10-24)
---------------------------

**Bugfix**

- Search control is now above legends and other map controls (#413)
- Map style is now correctly set at layer creation (#349)
- WMTS source group access is now working (no public by default) (#406)


2023.10.5      (2023-10-16)
---------------------------

**New features:**

- It is now possible to configure a legend for wmts sources

**Bugfix**

- Fix elasticsearch index type error on json data type


2023.10.4      (2023-10-11)
---------------------------

**Bugfix**

- Fix missing translation for label in search control results
- Fix map base layer labels and selection by URL


2023.10.3      (2023-10-11)
---------------------------

**Bugfix**

- Fix new search location feature usage


2023.10.2      (2023-10-06)
---------------------------

**Bugfix**

- Check if report existing to update it when celery task fail
- Source auto refresh exclude PENDING source now


2023.10.1      (2023-10-01)
---------------------------

**Improvements:**

- Ability to go on direct view with base layer defined by ID


2023.10.0      (2023-1-02)
---------------------------

**New features:**

- Add search providers configuration to improve search locations

**Improvements:**

- Improve frontend translations
- Disable errors in console when style image already loaded


2023.9.0       (2023-09-28)
---------------------------

**Bugfix**

- Increase max body size for upload files


2023.8.4       (2023-08-04)
---------------------------

**New features:**

- Add distance measurement map control (draw on the map and return the distance measured of the drawing)

**Bugfix**

- Allow numbers in source filters


2023.8.3       (2023-08-29)
---------------------------

**Improvements:**

- Optimize source refresh and ES indexation process


2023.8.2       (2023-08-10)
---------------------------

**Improvements:**

- Add close button to partners modal
- Improve source reporting interface in admin

**Bugfix**

- Allow numbers in source filter variables in admin


2023.8.1       (2023-08-03)
---------------------------

**Improvements:**

- Add filter feature for layers tree
- Make some A11y enhancements

**Bugfix**

- Remove legend scaling
- Fix invisible splash-screen catching clicks


2023.7.2       (2023-07-25)
---------------------------

**Improvements:**

- Add icon categorization in layers in admin.

**Bugfix**

- Fix tooltip on menubar in frontend.


2023.7.1       (2023-07-11)
---------------------------

**Improvements:**

- Enable legends for WMTS layers.
- Piecharts are now clickable.
- Piecharts are disabled in extra styles.
- Icons can now be categorized in layer admin.


2023.7.0       (2023-07-03)
---------------------------

**Improvements:**

- Pie charts improvements


2023.6.13      (2023-06-30)
---------------------------

**Bugfix**

- Fix content overflow in storytelling


**Improvements:**

- Pie charts legend definition


2023.6.12      (2023-06-27)
---------------------------

**Bugfix**

- Fix unauthenticated access to Source API endpoint exception.
- Legend title, content and box width are fixed


2023.6.11      (2023-06-23)
---------------------------

**New features:**

- Map visualization with circular diagrams

**Bugfix**

- Fix info content overflow if height taller than window


2023.6.10      (2023-06-22)
---------------------------

**Improvements:**

- Add more options to info content editor in config dashboard


2023.6.9       (2023-06-21)
---------------------------

**Bugfix**

- Fix duplicated legends


2023.6.8       (2023-06-20)
---------------------------

**New features:**

- Allow to define and display pie charts in layer style

**Improvements:**

- Split default info content template in multiple blocks to enhance customization


2023.6.7       (2023-06-19)
---------------------------

**Bugfix**

- Fix upper white ribbon in responsive view
- Use autocomplete field for source in layer secondary style and list filter
- Fix map PDF export
- Fix API filters


2023.6.6       (2023-06-14)
---------------------------

**Improvements:**

- Customize info menu content in config dashboard

**Bugfix**

- Fix restricted menus not showing after login


2023.6.5       (2023-06-14)
---------------------------

**Bugfix**

- Use an autocomplete widget to select source in layer definition in admin (Not limited to 100 elements anymore)


2023.6.4       (2023-06-09)
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
