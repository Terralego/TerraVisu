=============================
Module de fiches détaillées
=============================

Explorer les fiches détaillées
===============================

Le module de fiches détaillées permet d'explorer, d'analyser et de comparer les données associées à une entité.

L’accès à une fiche détaillée se fait via l’URL du visualiseur, suivie de ``/sheet/{id}``, où ``id`` représente l’identifiant du modèle de fiche détaillée configuré dans le module d’administration.

Par exemple :

::

   https://visu.mon-instance.fr/sheet/2

Les fiches détaillées sont entièrement configurables depuis `le module de configuration <https://terravisu.readthedocs.io/en/latest/user_manual/module_configuration.html#les-fiches-detaillees>`_.

Liste des fiches
-----------------

La page d'accueil du module affiche la liste des fiches disponibles.

Depuis cette interface, il est possible de :

* trier les colonnes par ordre alphabétique ou numérique ;
* effectuer une recherche dans les colonnes affichées ;
* accéder à une fiche détaillée en cliquant sur le nom d'une entité ;
* sélectionner jusqu'à trois entités afin de comparer leurs données.

.. figure:: ../_static/images/sheet/sheet_list.png
   :alt: Liste des fiches détaillées

   Liste des fiches détaillées.

Consulter une fiche détaillée unique
-------------------------------------

Une fiche détaillée regroupe l'ensemble des informations relatives à une entité.

Selon sa configuration, elle peut contenir différents types de contenus :

* champs descriptifs 
* tableaux de données 
* cartes interactives 
* visualisations immersives Panoramax 
* graphiques statistiques 
* images et médias 
* textes libres

Les informations sont organisées en sections afin de faciliter leur consultation.

.. figure:: ../_static/images/sheet/sheet_individuelle.png
   :alt: Consultation d'une fiche détaillée unique

   Consultation d'une fiche détaillée unique

Comparer plusieurs entités
---------------------------

Il est possible de sélectionner jusqu'à trois entités dans la liste afin de comparer leurs données côte à côte.

Pour accéder à la page de comparaison :

* Sélectionnez les entités à comparer depuis la liste (``/sheet/{id}``) ou `la table attributaire <https://terravisu.readthedocs.io/en/latest/user_manual/user_guide.html#la-table-attributaire>`_.
* Cliquez sur le bouton **Comparer ces données**.

La comparaison permet d'identifier rapidement les différences et similitudes entre plusieurs entités à travers l'ensemble des informations configurées dans la fiche.

.. figure:: ../_static/images/sheet/sheet_list_comparaison.png
   :alt: Comparaison de plusieurs entités

   Comparaison de plusieurs entités

Consulter une fiche détaillée en comparaison
----------------------------------------------

La page de comparaison affiche les informations de chaque entité côte à côte afin de faciliter l'analyse et l'identification des différences entre elles.

Les différentes sections configurées dans la fiche détaillée sont également disponibles dans la page de comparaison :

* champs descriptifs 
* tableaux de données 
* cartes interactives 
* visualisations immersives Panoramax 
* graphiques statistiques 
* images et médias 
* textes libres

Les valeurs de chaque entité sont affichées en colonnes afin de permettre une lecture comparative rapide entre les entités sélectionnées.

Afin d'éviter l'affichage d'informations incomplètes ou non pertinentes, certaines sections peuvent être masquées automatiquement dans la page de comparaison.

C'est notamment le cas des sections **Panoramax** : lorsqu'aucune image Panoramax n'est disponible pour l'ensemble des entités comparées, la section n'est pas affichée.

À l'inverse, si au moins une des entités dispose d'une image Panoramax, la section reste visible dans la comparaison.

.. figure:: ../_static/images/sheet/sheet_comparaison.png
   :alt: Consultation d'une fiche détaillée en comparaison

   Consultation d'une fiche détaillée en comparaison

Onglets
--------

Afin d'améliorer la lisibilité des fiches les plus riches, certaines sections peuvent être regroupées dans des onglets.

Cette organisation permet notamment de :

* limiter la longueur de la fiche ;
* regrouper des informations thématiques ;
* faciliter la navigation entre les différents jeux de données.

.. figure:: ../_static/images/sheet/sheet_onglet.png
   :alt: Consultation d'un onglet de fiche détaillée

   Consultation d'un onglet de fiche détaillée

Impression PDF
---------------

Chaque onglet d'une fiche détaillée peut être exporté au format PDF.

Cette fonctionnalité permet de générer rapidement un document imprimable ou partageable contenant les informations affichées dans l'onglet sélectionné.

.. figure:: ../_static/images/sheet/sheet_impression.png
   :alt: Bouton impression PDF

   Bouton impression PDF

Masquer les champs vides
-------------------------

Lorsque certaines données ne sont pas renseignées, il est possible d'activer l'option **Cacher les champs vides**.

Cette option masque automatiquement les champs ne contenant aucune valeur afin d'améliorer la lisibilité de la fiche.

.. figure:: ../_static/images/sheet/sheet_champvide.png
   :alt: Option "Masquer les champs vides" activée

   Option "Masquer les champs vides" activée