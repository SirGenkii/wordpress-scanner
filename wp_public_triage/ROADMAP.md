# Feuille de route

## Objectif produit

Trouver des anomalies WordPress actuelles, documentées et utiles à une proposition de réparation. L'indicateur principal est le nombre de dossiers pertinents après revue, rapporté au temps total de recherche, de qualification et de contact.

## Étape 1 — Valider la qualification

Utiliser la v0 sur un petit corpus choisi. Séparer les marqueurs WordPress, les symptômes d'incident et les indices de compromission. Comparer avec des cas connus et conserver les faux positifs pour améliorer les règles. Ne pas régler une règle sur tous les cas puis évaluer sur ces mêmes cas.

Livrable : observations JSON/CSV et revue humaine. Aucun seuil chiffré de fiabilité n'est encore établi.

## Étape 2 — Améliorer la couverture publique

- Parcours borné des sitemaps annoncés dans robots.txt et des liens internes pertinents.
- Conservation de l'URL exacte découverte, même si plusieurs URL partagent un domaine.
- Détection des redirections meta refresh et de motifs JavaScript, en les distinguant d'une redirection effectivement exécutée.
- Source documentée de signatures/indicateurs, avec date de validité et exception pour ressources partagées.
- Web Risk Lookup optionnel, avec cache conforme, expiration, quotas, limites de dépense et attribution des verdicts au fournisseur.
- Comparaison desktop/mobile/referrer sur les pages qui ont réellement déclenché l'alerte.

Livrable : couverture étendue et taux de faux positifs mesuré sur le corpus réservé.

## Étape 3 — Observer le rendu JavaScript

Ajouter Playwright uniquement pour les candidats qui le justifient : contexte isolé, navigateur maintenu à jour, aucune session personnelle, téléchargements et permissions désactivés, plafonds de durée et de trafic. Contrôler les destinations réseau de toutes les sous-requêtes, pas seulement la navigation principale. Un simple BrowserContext ne constitue pas une isolation de sécurité suffisante contre une page hostile.

Conserver capture, URL finale, requêtes réseau utiles et différences observées. Répéter les alertes pour vérifier leur fraîcheur. Une différence visuelle normale ne doit pas devenir un verdict de malware.

## Étape 4 — Automatiser la découverte à plus grande échelle

Choisir un connecteur de recherche ou un jeu de données dont les droits permettent réellement l'usage et la conservation prévus. Prévoir une interface commune : URL exacte, source, date de découverte, raison de sélection et restrictions d'utilisation.

Deux axes possibles : entreprises d'un métier et d'une zone ; références publiques d'agences. Common Crawl devient une option si le volume justifie le traitement historique. Ne pas confondre listes de domaines et moteur de recherche de contenu.

## Étape 5 — Qualification commerciale et exploitation

Créer une petite base SQLite contenant sites, observations, preuves, sources et état de revue. Les champs commerciaux restent séparés du diagnostic : activité actuelle, contact professionnel pertinent, lien agence à confirmer, opposition, dernière sollicitation.

Une interface de revue doit afficher : ce qui a été observé, où, quand, dans quel contexte, et les limites. Recontrôler les cas avant contact. Les messages sont validés humainement ; l'outil n'envoie pas de campagne automatiquement.

## Étape 6 — Liaison avec la toolbox de réparation

Après accord et accès du client, lancer les vérifications qui nécessitent le serveur : intégrité des fichiers, extensions, base de données, comptes administrateurs, tâches planifiées, journaux et mécanismes de persistance. Associer le diagnostic interne et la réparation au dossier sans exposer les accès dans les exports de prospection.

Prévoir une nouvelle observation publique après intervention. L'amélioration du rendu public n'est pas, à elle seule, la preuve que toute persistance a été supprimée.
