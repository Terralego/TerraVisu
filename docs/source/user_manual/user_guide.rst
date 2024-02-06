======================
Plateforme TerraVisu 
======================

TerraVisu 
=========

L’application cartographique **TerraVisu** permet de manipuler un ensemble de données relatives aux différents champs de l’action publique : démographie, habitat, patrimoine, mobilité, environnement.

**TerraVisu** propose des outils d’observation et d’analyse pour comprendre l’évolution de vos territoires.

Vous voulez tester par vous-même? `Une instance de démonstration est accessible ici <https://demo-terravisu.solutions-territoriales.fr/>`_ !

**Résumé des fonctionnalités :**

* Naviguer dans l'interface cartographique
* Intéragir avec les couches (descriptif, filtres, table attributaire, transparence, zoom sur l'emprise, synthèse statistique)
* Interroger les objets géographiques (infobulle au survol, fiche descriptive)
* Afficher des fonds de cartes
* Utiliser les outils de navigation (recherche dans les données/lieux, gestion du zoom, orientation de la carte..) 
* Exporter et partager les cartes (impression PDF, partage de la carte sur les réseaux sociaux)

Les principales fonctionnalités
===============================

L'interface cartographique
------------------------------

L'interface cartographique est décomposée en 4 parties :

* Les vues : à gauche, le panneau des vues permet d'organiser les couches par grande famille ou thématique
* L'arbre des couches : entre les vues et la carte, l'arbre des couches permet d'afficher, de rechercher une couche et de filtrer les données à voir sur la carte
* La carte : au centre, un fond de plan cartographique sur lequel se superposent des données
* Les outils de navigation : à droite, se trouvent les outils incontournables d'une application cartographique (zoom, orientation) mais aussi d'autres outils additionnels comme le retour à l'emprise initiale, le changement de fond de plan, l'impression et le partage de la carte

**Exemple**

.. image :: ../_static/images/visu/visu_interfacecarto.png

Les données géographiques
-----------------------------

Les données géographiques sont organisées dans des couches qui rassemblent des entités de même nature. Chaque couche de carte permet d'afficher et d'utiliser un jeu de données SIG spécifique.

**TerraVisu** dispose d'un arbre des couches sur lequel une série d'outils permet d'agir sur les différentes couches de données visibles.

Au niveau d'une couche de données, vous pouvez ainsi activer les fonctionnalités suivantes :

* Afficher/masquer la couche
* Afficher/masquer le panneau d'informations de la couche
* Afficher/masquer la table attributaire
* Afficher/masquer le panneau de filtres
* Afficher/modifier la liste des filtres appliqués
* Afficher le widget de synthèse
* Afficher du contenu provenant d'une application externe (graphiques par exemple)
* Zoomer sur son étendue spatiale
* Changer son opacité


.. image :: ../_static/images/visu/visu_interfacecarto_couche.png

L'interface cartographique se met automatiquement à jour selon les fonctionnalités activées.

Les vues
~~~~~~~~~~~

Les couches sont réparties dans des vues et reflètent des thématiques ou des applications métier. 

Les vues sont représentées par des pictogrammes dans le bandeau latéral gauche. 

Pour changer de vue, cliquez sur le pictogramme concerné.

.. note::
	Chaque vue est indépendante et il n'est pas possible d'afficher deux vues à la fois. 
	Cela signifie qu'en cliquant sur une autre vue, la carte change.


L'arbre des couches
~~~~~~~~~~~~~~~~~~~~~~

Les données sont agencées de manière personnalisée dans l'arbre des couches. 

Vous pouvez créer autant de grandes catégories et de sous-catégories de groupes de données que vous le souhaitez.

Dans le cas où il y aurait un grand nombre de couches dans l'arbre, vous pouvez utiliser la barre de recherche présente en haut du panneau pour filtrer une couche par son nom.

.. note::
	Le filtrage de couche ne peut se faire que dans la vue en cours.

**Exemple de barre de filtre**

.. image :: ../_static/images/visu/visu_filtre_arbrecouches.png

L'affichage de la couche
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pour activer/désactiver une couche cliquez sur le curseur à gauche du nom.

La légende
^^^^^^^^^^

Quand les couches affichées ont des légendes, celles-ci s'affichent sur la partie droite de l'écran. C'est vous qui décidez si vous souhaitez affichez la légende et quel type de légende.

**Exemple de légende disponible**

.. image :: ../_static/images/visu/visu_legende.png

La configuration de la légende s’effectue depuis l'outil administration.

Le panneau d'informations
~~~~~~~~~~~~~~~~~~~~~~~~
Il est possible d'associer du contenu informatif à chaque couche. Ce contenu est mis à disposition de l'utilisateur via un panneau dédié, configurable dans l'interface d'administration de la plateforme **TerraVisu**.

**Exemple de panneau d'informations**

.. image :: ../_static/images/visu/visu_infos.png

La table attributaire
~~~~~~~~~~~~~~~~~~~~~~~~

**TerraVisu** propose l’affichage de la table des données contenues dans la couche. La table attributaire contient les caractéristiques **non spatiales** des données.

La table attributaire de **TerraVisu** comprend de nombreuses fonctionnalités telles que :

* Afficher le nombre de lignes du tableau
* Trier les données selon une colonne
* Filtrer les données par l'emprise de la carte
* Comparer jusqu'à trois lignes
* Exporter les données au format CSV et Excel
* Afficher/masquer des colonnes
* Agrandir la table

**Exemple d'une table attributaire**

.. image :: ../_static/images/visu/visu_table.png

Une fois la table exportée, vous pouvez travailler vos données avec votre tableur habituel et créer des graphiques, des tableaux dynamiques croisés, etc., depuis votre ordinateur.

Le filtrage des données
~~~~~~~~~~~~~~~~~~~~~~~~~~

Un jeu de données peut être filtré par ses données attributaires, c’est à dire des informations textuelles qui décrivent les caractéristiques diverses (géographiques, alphanumériques, etc.). 

Les éléments qui ne correspondent pas au filtre sont cachés et la carte est alors mise à jour.

**Exemple de filtres disponibles**

.. image :: ../_static/images/visu/visu_filtre.png

Les filtres peuvent prendre plusieurs formes (case à cocher, intervalle de valeurs, curseur, recherche, etc.) et sont paramétrables dans l'outil d'administration.

Le widget
~~~~~~~~~~~~

Le widget permet de récapituler dans un tableau dynamique, des indicateurs utiles à l'analyse de la couche. La synthèse des informations se réactualise en fonction des éléments qui se trouvent dans l'emprise spatiale. Le widget s’affiche à droite de l’écran.

**Exemple d'un widget**

.. image :: ../_static/images/visu/visu_widget.png

Les données à afficher dans le widget sont définies par l’utilisateur dans l'outil d'administration.

Le zoom sur l'étendue spatiale
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Cet outil permet de zoomer sur l'étendue spatiale d'une couche activée. Le zoom est particulièrement utile lorsque l'on souhaite voir l'emprise géographique des éléments filtrés d'une couche.

**Exemple d'un zoom**

.. image :: ../_static/images/visu/visu_zoomemprise.png

La table attributaire et le widget sont automatiquement mis à jour en fonction du zoom.

La modification de l'opacité 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pour changer l'opacité d'une couche, cliquez sur les trois petits points horizontaux à côté de l'outil filtre.

Faites glisser le curseur de droite à gauche pour modifier le pourcentage de transparence.

**Exemple de transparence sur la couche des lignes de bus**

.. image :: ../_static/images/visu/visu_transparence.png

Les contenus externes associés
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Des contenus configurés depuis une application externe, notamment graphiques, peuvent être ajoutés à une couche. Un pictogramme et un libellé, paramétrables depuis l'interface d'administration, permet d'identifier chacun d'entre eux dans la liste des informations et outils disponibles sur la couche.

**Exemple de graphique**

.. image :: ../_static/images/visu/visu_graphique.png

Les intéractions avec les données affichés sur la carte
---------------------------------------------------------

Si les couches ont été configurées pour, il est possible d'intéragir avec les objets affichés sur la carte.

La fiche descriptive
~~~~~~~~~~~~~~~~~~~~~~~

Les informations relatives aux données sont présentées dans une fiche à gauche de l'écran. Cette fiche apparaît au clic de l’objet cartographie (i.e. le point sur la carte).

**Exemple de fiche descriptive pour une station du métro toulousain**

.. image :: ../_static/images/visu/visu_minifiche.png

Depuis l'outil d'administration, vous pouvez personnaliser la fiche de manière avancée, en y intégrant du texte, des images ou des graphiques pour améliorer le rendu visuel. 

Il n'y a pas de limite au contenu de la fiche tant que l'information est disponible. La fiche peut contenir des liens vers des sites web et des mails. 

L'infobulle au survol
~~~~~~~~~~~~~~~~~~~~~~~~

Une information résumée de la donnée, sous la forme d'une infobulle, est disponible au survol des des objets cartographiques. Si la couche a été configurée dans ce sens dans l'outil d'administration, des infobulles peuvent apparaître au survol des objets cartographiques.

**Exemple d'infobulle au clic sur une station de métro toulousain**

.. image :: ../_static/images/visu/visu_infobulle.png

Le contenu de l'infobulle est entièrement personnalisable dans l'outil d'administration et peut comprendre toutes les information que vous souhaitez.

Les outils de navigation
---------------------------

**TerraVisu** dispose des contrôles classiques de navigation :

* Recherche de lieux/adresse et dans les données actives
* Retour à l'emprise d'origine
* Gestion du zoom
* Réorientation de la carte
* Gestion des fonds de carte
* Impression vers PDF
* Partage de la carte : hyperlien ou vers les réseaux sociaux

**Barre de navigation à gauche sur la carte**

.. image :: ../_static/images/visu/visu_outilnavigation.png

Quelques uns de ces outils de navigation sont détaillés ci-après.

La recherche sur la carte
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

La recherche sur la carte (via l'outil loupe) permet d'effectuer à la fois :

* une recherche de lieu ou d'adresse par à un appel à la base d'adresses Nominatim implémenté,
* une recherche dans les champs textuels d'une ou plusieurs couches activées (exemple : une parcelle par le nom du proprétaire).

Le fait de sélectionner un résultat dans les attributs de la ou les couches activées permet de zoomer sur ce résultat, de sélectionner l'objet en surbrillance et d'ouvrir la mini-fiche (si elle existe).

Le comportement est différent si on sélectionne un résultat pour la recherche de lieu puisqu'il permet uniquement de zoomer sur l'emprise géographique correspondante sans réaliser d'intéraction avec la ou les couches activées.


**Exemple de recherche**

.. image :: ../_static/images/visu/visu_recherche.png

Le retour à l'emprise d'origine
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pour revenir à l'emprise initiale du projet, cliquez sur l'icône en forme de maison.

La gestion du zoom
~~~~~~~~~~~~~~~~~~~~~~

Pour zoomer sur la carte utilisez la molette de la souris vers l'avant ou cliquez sur l'icône :guilabel:`+`.

Pour dézoomer sur la carte utilisez la molette de la souris vers l'arrière ou cliquez sur l'icône :guilabel:`-`.

La réorientation de la carte
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Par défaut la carte est orientée au nord. Pour changer l'orientation, cliquez sur l'icône en forme de boussole.

Pour avoir une meilleure expérience utilisateur sur les couches en 3D, effectuez la combinaison :guilabel:`CTRL` + :guilabel:`clic gauche` souris sur la carte pour incliner le plan.

La gestion des fonds de carte
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Plusieurs fonds de cartes sont disponibles par défaut et vos propres fonds de carte peuvent être ajoutés depuis l'`outil d'administration <https://terravisu.readthedocs.io/en/latest/user_manual/admin_user_guide.html#liste-des-fonds-de-carte>`_ 

L'impression de la carte au format PDF
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

La carte affichée à l'écran peut être imprimée en format PDF selon les deux dispositions (portait ou paysage).

**Exemple de la procédure d'impression**

.. image :: ../_static/images/visu/visu_impression.png

Le partage de la carte
~~~~~~~~~~~~~~~~~~~~~~~~~~

Il est possible de partager la carte soit en générant un hyperlien, soit en la partageant sur les réseaux sociaux (X, Facebook et Linkedin)

**Exemple de partage d'hyperlien**

.. image :: ../_static/images/visu/visu_impression.png

La visualisation en Storytelling
---------------------------------

TerraVisu dispose d'une fonction de Storytelling. C'est une autre forme de visualisation qui est accessible depuis une vue dédiée. Le storytelling comprend du texte et des images qui sont parcourues comme un « slideshow » (diaporama).

Cette fonctionnalité peut servir à la communication ou de manuel d'utilisation.

**Exemple de storytelling**

.. image :: ../_static/images/visu/visu_storytelling.png
