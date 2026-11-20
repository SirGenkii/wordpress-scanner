# Roadmap proposée — découverte avant diagnostic avancé

Statut : cadrage provisoire, 20 novembre 2026. L'ordre ci-dessous reprend l'objectif de réparation à terme et donne la priorité à la découverte d'agences et de leurs références. Aucun jalon n'est déclaré terminé par ce document.

## Jalon 0 — Audit et décisions de départ

Objectif : obtenir un plan compatible avec le dépôt réel et une voie crédible d'acquisition des données.

- Lire le code, les tests et les consignes existantes ; exécuter les vérifications locales pertinentes si possible.
- Distinguer ce qui est déjà opérationnel, simulé, absent ou fragile.
- Examiner la source de découverte : requêtes géographiques, pagination, coûts, quota, attribution et droits de conservation.
- Comparer au plus quelques options réalistes ; recommander une source, avec les éléments restant à confirmer.
- Définir le premier lot : zone, type d'agences, limites et règle de localisation des clients.
- Proposer le modèle minimal de provenance, d'identités et d'historique.
- Produire une liste courte de décisions bloquantes et un premier incrément borné.

Critère de sortie : on sait comment obtenir les candidats réels, ce qu'on peut conserver, ce que coûte le test et ce que le premier incrément doit démontrer. Une simple liste d'API ne suffit pas.

## Jalon 1 — Agence → référence → site, avec persistance

Objectif : un parcours complet et vérifiable sur un petit lot.

- Mettre en place un seul connecteur réel, plus l'import utile pour les tests et les sources manuelles.
- Conserver les paramètres et la provenance du lot.
- Qualifier les indices d'implantation et de prestation WordPress de l'agence sans exiger WordPress sur son propre site.
- Explorer les pages de réalisations puis les fiches internes, dans des limites définies.
- Extraire URL exacte, ancre, contexte et relation supposée ; garder les références non résolues.
- Stocker dans une base commune les sites, relations, preuves et observations.
- Rendre le lot reprenable, dédupliquer les identités et préserver toutes les provenances.
- Fournir un export et une vue de revue minimale ; ajuster le niveau d'interface au choix utilisateur.

Critères de sortie : provenance complète de chaque domaine ; pas de faux client créé depuis un lien social ou fournisseur ; mêmes résultats identitaires après relance ; reprise après interruption ; cas non extractibles explicités.

Validation proposée : petit échantillon réel d'environ dix agences, au plus cinq références examinées par agence, complété par des fixtures pour les cas difficiles. Ces nombres sont un budget de pilote proposé, pas un rendement attendu. Ne pas limiter l'évaluation aux agences dont le portfolio est facile à extraire.

## Jalon 2 — Revue et identification technique

Objectif : obtenir des listes réellement exploitables et estimer la part de sites WordPress.

- Réutiliser les observations collectées pour CMS, technologies et état public.
- Conserver les indices et les états inconnus ; distinguer incident technique et blocage de collecte.
- Gérer listes nommées, acceptation/rejet d'une relation et remarques de revue.
- Ajouter une actualisation explicite et un historique consultable.
- Évaluer si un rendu navigateur ciblé débloque suffisamment de références ou d'observations pour justifier son coût.

Critères de sortie : les décisions humaines survivent à une relance ; plusieurs listes partagent une fiche ; les résultats expliquent leur origine et leur fraîcheur ; aucune absence d'indice n'est présentée comme une certitude.

## Jalon 3 — Entreprises directement par zone

Objectif : ajouter un second canal sans dupliquer la base ni l'explorateur.

- Segmenter par zone et activité ; conserver recherche et localisation observée séparément.
- Rapprocher l'organisation et son domaine avec preuve, sans inventer d'adresse.
- Réutiliser déduplication, observation, identification et revue.
- Comparer les deux canaux sur coût par site correctement attribué, part WordPress, ambiguïtés et temps de qualification.

Critère de sortie : le même site trouvé par une agence et une recherche d'entreprise partage ses observations et garde ses deux provenances.

## Jalon 4 — Anomalies publiques et fiches de diagnostic

Objectif : identifier des cas utiles à une proposition de dépannage.

- Séparer fonctionnement, contenu suspect, redirections conditionnelles et réputation externe.
- Conserver preuves récentes et limites de couverture.
- Tester les règles sur cas confirmés et cas sains variés ; garder des exemples à l'écart du réglage.
- Produire les rapports depuis la base commune.
- Prévoir une nouvelle observation avant qualification commerciale d'un cas ancien.

Critère de sortie : chaque alerte est expliquée et reproductible lorsqu'elle est annoncée comme actuelle ; faux positifs et temps de revue sont mesurés. Les tests logiciels seuls ne valident pas la précision terrain.

## Jalon 5 — Vulnérabilités potentielles et liaison réparation

Objectif : enrichir seulement si cela apporte une valeur commerciale ou technique mesurable.

- Vérifier le niveau de certitude des empreintes et versions avant rapprochement avec une base de vulnérabilités.
- Vérifier la licence, la fraîcheur et les limites de cette source.
- Garder les hypothèses de vulnérabilité séparées des indices de compromission.
- Prévoir un dossier de diagnostic interne après accord et accès du client, relié à la toolbox de réparation.
- Isoler tout audit actif dans un mode autorisé et borné.

## Hors périmètre initial

Pas de couverture nationale exhaustive promise, de moteur de recherche maison, de microservices distribués, d'envoi commercial automatique, de collecte massive de coordonnées ou de création systématique d'un skill par cas. Les skills de développement apparaissent lorsque leur utilité devient concrète.

## Questions à résoudre avant de considérer ce plan comme fixé

1. Quelle source de recherche et quel plafond de coût par lot ?
2. Quelle première zone, et confirme-t-on que les clients des agences peuvent être hors zone ?
3. Quelle revue initiale : CLI + export, ou petite interface locale ?

La priorité commerciale entre partenariat agence et réparation directe reste un choix par dossier à préciser avant la prospection.
