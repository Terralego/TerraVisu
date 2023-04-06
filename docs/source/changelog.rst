=========
CHANGELOG
=========

2.0.0      (XXXX-XX-XX)
-----------------------

* New Version

* New Simplified Installation

* New documentation

* Bug fixes:
  * Fix and allow date usage in source fields and imported data
  * Fix group creation / edition in admin
  * Fix LayerTree cache management
  * Fix bug when no base layer defined in scene (#109)


* New features:
  * Use icon and patterns in point / polygon styles


* Improvements:
  * Direct use elasticsearch connector for data indexation instead of terra-bonobo-nodes
  * Better layer duplication
  * Some instance configuration managed in config panel (/config/)
    - Logo
    - Favicon
    - Title
    - Credits
    - Map default configuration (extent, zoom levels, center ...)
    - MapBox token
    - External page links
    - Sprite icons


* Maintenance
  * From Python 3.6 to 3.10
  * From Django 2.2 to 4.1
  * All python packages updated
  * Admin node-js from 12 to 18