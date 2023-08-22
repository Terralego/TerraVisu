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
* Intéragir avec les couches (filtres, table attributaire, transparence, zoom sur l'emprise, synthèse statistique)
* Interroger les objets géographiques (infobulle au survol, fiche descriptive)
* Afficher des fonds de cartes
* Utiliser les outils de navigation (recherche dans les données/lieux, gestion du zoom, orientation de la carte..) 
* Exporter et partager les cartes (impression PDF, partage de la carte sur les réseaux sociaux)

Les principales fonctionnalités
===============================

L'interface cartographique
--------------------------

L'interface cartographique est décomposée en deux parties :

* Les données : à gauche, l'arbre des couches permet d'afficher, de filtrer les données à voir sur la carte
* La carte : au centre, un fond de plan cartographique sur lequel se superposent des données

**Exemple du TerraVisu déployé pour la Région Sud**

.. image :: ../_static/images/visu/visu_interfacecarto.png

Plusieurs fonds de cartes sont disponibles par défaut et vos propres fonds de carte peuvent être ajoutés.

Les données sont agencées de manière personnalisée. Vous pouvez créer autant de grandes catégories et de sous-catégories de groupes de données que vous le souhaitez.

Les données géographiques
-------------------------

Les données géographiques sont organisées dans des couches qui rassemblent des entités de même nature. Chaque couche de carte permet d'afficher et d'utiliser un jeu de données SIG spécifique

**TerraVisu** dispose d'un arbre des couches sur lequel une série d'outils permet d'agir sur les différentes couches de données visibles.

Au niveau de la couche de données, vous pouvez ainsi activez les fonctionnalités suivantes :

* Afficher/masquer des données
* Afficher/masquer la table attributaire des données de la couche
* Afficher/masquer le panneau de filtre de la couche de données
* Afficher/modifier la liste des filtres appliqués à la couche de données
* Afficher le widget de synthèse
* Zoomer sur l'étendue spatiale de la couche de données
* Changer l'opacité de la couche

.. image :: ../_static/images/visu/visu_interfacecarto_couche.png

L'interface géographique se met automatiquement à jour selon les fonctionnalités activées.

Le filtrage des données
-----------------------

Un jeu de données peut être filtré par ses données attributaires, c’est à dire des informations textuelles qui décrivent les caractéristiques diverses (géographiques, alphanumériques, etc.). 

Les éléments qui ne correspondent pas au filtre sont cachés et la carte est alors mise à jour.

**Exemple de filtres disponibles**

.. image :: ../_static/images/visu/visu_filtre.png

Les filtres peuvent prendre plusieurs formes (case à cocher, intervalle de valeurs, curseur, recherche, etc.) et sont paramétrables dans l'outil d'administration.

La fiche descriptive
--------------------

Les informations relatives aux données sont présentées dans une fiche à gauche de l'écran. Cette fiche apparaît au clic de l’objet cartographie (i.e. le point sur la carte).

**Exemple de fiche descriptive pour une station du métro toulousain**

.. image :: ../_static/images/visu/visu_minifiche.png

Depuis l'outil d'administration, vous pouvez personnaliser la fiche de manière avancée, en y intégrant du texte, des images ou des graphiques pour améliorer le rendu visuel. 

Il n'y a pas de limite au contenu de la fiche tant que l'information est disponible. La fiche peut contenir des liens vers des sites web et des mails. 

Les fiches sont exportables et peuvent donc être imprimées en format texte ou PDF.

L'infobulle au survol
---------------------

Une information résumée de la donnée, sous la forme d'une infobulle, est disponible au survol des des objets cartographiques. Si la couche a été configurée dans ce sens dans l'outil d'administration, des infobulles peuvent apparaître au survol des objets cartographiques.

**Exemple d'infobulle au clic sur une station de métro toulousain**

.. image :: ../_static/images/visu/visu_infobulle.png

Le contenu de l'infobulle est entièrement personnalisable dans l'outil d'administration et peut comprendre toutes les information que vous souhaitez.

Le widget
---------

Le widget permet de récapituler dans un tableau dynamique, des indicateurs utiles à l'analyse de la couche. La synthèse des informations se réactualise en fonction des éléments qui se trouvent dans l'emprise spatiale. Le widget s’affiche à droite de l’écran.

**Exemple d'un widget du TerraVisu de SCoT en action**

.. image :: ../_static/images/visu/visu_widget.png

Les données à afficher dans le widget sont définies par l’utilisateur dans l'outil d'administration.

La légende
----------

Quand les couches affichées ont des légendes, celles-ci s'affichent sur la partie droite de l'écran. C'est vous qui décidez si vous souhaitez affichez la légende et quel type de légende.

**Exemple de type légende disponible**

.. image :: ../_static/images/visu/visu_legende.png

La configuration de la légende s’effectue depuis l'outil administration.

La table attributaire
---------------------

**TerraVisu** propose l’affichage de la table des données contenues dans la couche. La table attributaire contient les caractéristiques **non spatiales** des données.

La table attributaire de **TerraVisu** comprend de nombreuses fonctionnalités telles que :

* Afficher le nombre de lignes du tableau
* Trier les données selon une colonne
* Filtrer les données par l'emprise de la carte
* Comparer jusqu'à trois lignes
* Exporter les données au format CSV et Excel
* Afficher/masquer des colonnes
* Agrandir la table

**Exemple d'une table attributaire du TerraVisu Sud Éco Foncier**

.. image :: ../_static/images/visu/visu_table.png

Une fois la table exportée, vous pouvez travailler vos données avec votre tableur habituel et créer des graphiques, des tableaux dynamiques croisés, etc., depuis votre ordinateur.

Le zoom sur les éléments d'une couche
-------------------------------------

Cet outil permet de zoomer sur l'étendue spatiale d'une couche activée. Le zoom est particulièrement utile lorsque l'on souhaite voir l'emprise géographique des éléments filtrés d'une couche.

**Exemple d'un zoom pour le TerraVisu de SeineYonne**

.. image :: ../_static/images/visu/visu_zoomemprise.png

La table attributaire et le widget sont automatiquement mis à jour en fonction du zoom.

Les outils de navigation
------------------------

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
-------------------------

La recherche sur la carte (via l'outil loupe) permet d'effectuer à la fois :

* une recherche de lieu ou d'adresse par à un appel à la base d'adresses Nominatim implémenté,
* une recherche dans les champs textuels d'une ou plusieurs couches activées (exemple : une parcelle par le nom du proprétaire).

Le fait de sélectionner un résultat dans les attributs de la ou les couches activées permet de zoomer sur ce résultat, de sélectionner l'objet en surbrillance et d'ouvrir la mini-fiche (si elle existe).

Le comportement est différent si on sélectionne un résultat pour la recherche de lieu puisqu'il permet uniquement de zoomer sur l'emprise géographique correspondante sans réaliser d'intéraction avec la ou les couches activées.


**Exemple de recherche pour le TerraVisu de SeineYonne**

.. image :: ../_static/images/visu/visu_recherche.png

L'impression de la carte au format PDF
--------------------------------------

La carte affichée à l'écran peut être imprimée en format PDF selon les deux dispositions (portait ou paysage).

**Exemple de la procédure d'impression**
.. image :: ../_static/images/visu/visu_impression.png


La visualisation en Storytelling
--------------------------------

TerraVisu dispose d'une fonction de Storytelling. C'est une autre forme de visualisation qui est accessible depuis une vue dédiée. Le storytelling comprend du texte et des images qui sont parcourues comme un « slideshow » (diaporama).

Cette fonctionnalité peut servir à la communication ou de manuel d'utilisation.

**Exemple du storytelling de Carto Collectivités**

.. image :: ../_static/images/visu/visu_storytelling.png