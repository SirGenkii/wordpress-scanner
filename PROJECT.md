# Cadrage critique — découverte et qualification de sites

Version de travail du 20 novembre 2026. Ce document propose une structure ; il ne fige ni fournisseur, ni budget, ni interface.

## 1. Demandes explicites

- Réutiliser le dépôt créé depuis la v0 WP Public Triage.
- Développer ensuite avec Codex dans PhpStorm.
- Permettre à Codex de créer les skills et outils de projet qui deviennent utiles.
- Prioriser les agences proposant du développement WordPress, découvertes par zone géographique, puis leurs références et sites clients.
- Permettre ensuite une recherche directe d'entreprises susceptibles d'utiliser WordPress.
- Conserver les listes et gérer l'exploration des pages et sites.
- Séparer l'identification du CMS, des technologies et de l'état public du site des analyses de sécurité et des rapports.
- Critiquer le plan et lever ses ambiguïtés avant de le considérer comme définitif.

## 2. Finalité commerciale

La sortie utile est un site dont l'identité, la provenance et, plus tard, le problème public sont vérifiables. Le nombre brut de domaines ne mesure pas cette valeur.

Deux usages commerciaux restent distincts : identifier une agence susceptible de devenir partenaire ; identifier une entreprise susceptible de demander une réparation. Le canal de découverte ne décide pas automatiquement qui sera contacté.

L'hypothèse « les références d'agences fourniront suffisamment de besoins de réparation » doit être testée. Elles pourraient aussi surreprésenter des sites récents ou suivis. Ce biais est plausible, pas mesuré. Le canal entreprises permettra une comparaison ultérieure.

## 3. Principales faiblesses du plan initial

| Sujet | Risque | Traitement proposé |
| --- | --- | --- |
| Acquisition | La v0 demande des URL sources ; elle ne trouve pas encore des agences à partir d'une région. | Définir et tester une source réelle avant de déclarer la découverte automatisée terminée. |
| Stockage des résultats | Une API techniquement adaptée peut ne pas autoriser la base durable souhaitée. | Choisir le fournisseur après vérification de ses droits, de sa couverture et de son coût réel. |
| Géographie | Une page « agence WordPress Lyon » peut désigner une zone commerciale, pas une implantation. | Séparer zone de recherche, établissements observés et zones desservies. |
| Agence WordPress | Le CMS du site vitrine de l'agence ne prouve pas sa prestation. | Rechercher une offre ou une référence WordPress ; analyser ensuite chaque site client séparément. |
| Extraction | Un portfolio peut passer par plusieurs pages internes ou ne proposer aucun lien sortant. | Explorer quelques pages pertinentes et conserver les références non résolues. |
| Attribution | Un lien externe peut être un fournisseur, un réseau social, une démonstration ou un partenaire. | Exiger le contexte du lien et une relation typée ; conserver l'ambiguïté. |
| Actualité | Une ancienne référence peut pointer un domaine vendu, migré ou repris par un autre prestataire. | Conserver les dates et revérifier l'identité actuellement servie. |
| Répétitions | Plusieurs agences ou villes peuvent conduire au même site. | Une identité partagée et plusieurs provenances, sans écrasement des relations. |
| Sécurité | Confondre panne, version vulnérable et piratage fausse la qualification. | Produire des analyses distinctes et conserver leurs preuves et limites. |
| Autonomie de Codex | Multiplier les skills, scripts jetables et services ralentit le projet. | Code réutilisable pour le produit ; skills seulement pour les procédures récurrentes de développement. |

## 4. Segmentation géographique proposée

Utiliser des lots de recherche définis par pays, langue, zone, villes et type de cible. La région sert à organiser les lots ; les requêtes sont suffisamment précises pour être évaluables, par exemple ville + prestation.

Exemple de pilote possible, non validé : Auvergne-Rhône-Alpes, avec Lyon, Saint-Étienne et une petite commune ou un bassin voisin. Varier la taille des localités plutôt que couvrir immédiatement toutes les grandes villes françaises.

Défaut proposé pour le canal agences : rechercher l'implantation des agences dans la zone, tout en conservant leurs références hors zone. La localisation de chaque client reste une information séparée et éventuellement inconnue.

Défaut proposé pour le canal entreprises : vérifier un établissement dans la zone. Ne pas déduire sa localisation d'une adresse IP, d'une extension de domaine ou du seul terme de recherche. Distinguer siège et établissement lorsque cela devient utile.

L'outil ne doit pas promettre un recensement exhaustif. Les sources et requêtes produisent un échantillon dont la couverture doit être décrite.

## 5. Parcours prioritaire

1. Définir un lot de recherche et ses limites.
2. Obtenir des agences candidates depuis une source réelle configurée ou un import explicitement présenté comme tel.
3. Vérifier les indices d'implantation et de prestation WordPress, en conservant les inconnus.
4. Repérer les pages de références, réalisations et études de cas.
5. Parcourir les fiches pertinentes dans un budget défini.
6. Extraire les liens vers les sites et leur contexte ; conserver les noms/logos sans URL dans une file de résolution distincte.
7. Dédupliquer les identités sans perdre les provenances ni fusionner abusivement les sites.
8. Enregistrer les relations et les preuves ; permettre la revue et l'export.
9. Enrichir les sites retenus avec les analyses techniques dans un jalon suivant.

Une référence sans lien n'autorise pas à inventer un domaine à partir du nom de l'entreprise. Une recherche secondaire éventuelle doit être bornée, sourcée et pouvoir conclure « ambigu ».

Une référence peut porter sur du SEO, de la publicité, une identité graphique ou une intervention ponctuelle. Distinguer « cité au portfolio » de « création du site explicitement revendiquée ». La nature de la prestation et sa date restent inconnues en l'absence de preuve ; aucune de ces relations n'établit automatiquement la maintenance actuelle.

## 6. Architecture proposée

Commencer par un seul projet Python modulaire et une base SQLite. Cette proposition réutilise la v0 ; l'utilisation de PhpStorm n'impose pas PHP. Ne créer des services indépendants qu'en présence d'un besoin démontré.

| Composant | Responsabilité |
| --- | --- |
| Sources de découverte | Produire des candidats et leur provenance ; un connecteur réel au départ. |
| Explorateur commun | Télécharger les pages selon une politique de visite, avec limites, cache et motifs d'échec. |
| Extraction de références | Proposer des relations agence–site à partir des pages observées. |
| Base et suivi de tâches | Identités, listes, historique, reprises, budgets et décisions humaines. |
| Identification technique | CMS, technologies et état public, avec preuve et niveau d'incertitude. |
| Analyses de sécurité | Indices de compromission et, ultérieurement, rapprochement documenté avec des vulnérabilités connues. |
| Revue et rapports | Présenter les données communes ; ne pas recrawler par défaut ni maintenir une base parallèle. |

Séparer le moteur d'exploration, qui visite les pages, de l'interface d'exploration, qui permet de parcourir les résultats. L'interface initiale reste à décider : commandes et exports, ou petite interface locale de revue.

Une observation peut être réutilisée par plusieurs analyses. Le besoin de fraîcheur est explicite : relancer un analyseur sur une observation existante ne doit pas produire de trafic réseau ; demander une actualisation crée une nouvelle observation.

## 7. Objets métier à préserver

Ce sont des concepts à maintenir ; ils n'imposent pas un schéma SQL définitif.

| Objet | Rôle |
| --- | --- |
| Organisation | Agence, entreprise ou autre acteur ; rôles non exclusifs. |
| Site | Unité d'observation technique stable, distincte de l'organisation. |
| URL et alias | Adresses observées, chemins, redirections et regroupements justifiés. |
| Relation | Référence de portfolio, réalisation revendiquée, propriété déclarée, maintenance déclarée, relation non résolue. |
| Preuve | URL source exacte, extrait/contextualisation, date, méthode et éventuellement empreinte. |
| Lot et tâche | Périmètre de recherche, source, paramètres, progression et résultat de l'exécution. |
| Observation | Résultat daté sur une URL et un profil, avec limites de couverture. |
| Liste et revue | Sélections de fiches existantes et décisions humaines persistantes. |

Une organisation peut exploiter plusieurs sites ; un site peut être cité par plusieurs agences. Les listes référencent ces objets, elles ne les copient pas.

La fusion des identités est une décision distincte de la découverte. Ne pas fusionner systématiquement tous les sous-domaines ou tous les sites d'une plateforme. Un domaine enregistré aide au regroupement, mais ne prouve ni identité commune ni autorisation de visiter tous ses sous-domaines.

Préserver première découverte, dernière observation et périodes des relations connues. Une nouvelle analyse ne doit pas effacer une opposition, un rejet humain ou un contact déjà effectué.

## 8. Politiques d'exploration

Les trois usages réutilisent le transport, mais n'ont pas le même parcours :

- Références d'agence : liens internes pertinents, fiches de projets puis adresses des clients ; profondeur bornée.
- Identification technique : petit échantillon de pages choisies, réutilisation des observations disponibles.
- Vérification d'anomalie : URL concernée et profils nécessaires, avec budget distinct.

Conserver des raisons d'échec précises : refus explicite, indisponibilité, challenge, réponse robots non interprétable, portfolio JavaScript, absence de références, référence sans domaine. Ce ne sont pas des équivalents de « aucun client » ou « site sain ».

Prévoir reprises, délais de nouvelle tentative, plafond de retries, durée globale des tâches et consommation par source. Un serveur lent ne doit pas bloquer indéfiniment tout le lot.

Le rendu navigateur est un complément ciblé, après mesure du besoin. Conserver les pages comme données inertes, respecter les conditions de conservation et borner la rétention des contenus bruts.

## 9. Périmètre sécurité à clarifier

Séparer trois sorties : état de fonctionnement, indices publics de compromission, correspondances potentielles avec une base de vulnérabilités.

Une empreinte de version incertaine, une extension détectée sans version ou un paramètre d'asset ne suffit pas à établir qu'une faille s'applique. Une correspondance de version ne démontre pas une exploitation.

La prospection s'appuie sur l'observation publique. Un audit actif avec tests supplémentaires est un autre mode, attaché à un périmètre et une autorisation explicites. Ne pas le laisser se déclencher comme effet secondaire de la découverte régionale.

Les rapports sont des vues sur les observations et preuves. Une première fiche de provenance est utile avant même l'existence d'un rapport de sécurité.

## 10. Critères du premier jalon utile

- Chaque domaine exporté possède une URL source, un contexte de référence et une date.
- Les références ambiguës restent identifiables et ne deviennent pas automatiquement des clients vérifiés.
- Un même site trouvé dans deux lots conserve les deux provenances.
- Une relance enrichit l'historique et ne duplique pas les mêmes relations.
- Une interruption permet une reprise sans tout recommencer.
- Une collecte bloquée est distinguée d'une absence de résultat.
- Un import manuel et une découverte automatisée réelle sont clairement distingués dans le bilan.
- Le bilan rapporte domaines uniques attribués, diversité des agences contributrices, motifs d'échec, temps de revue et coût par résultat utile.

## 11. Décisions ouvertes

| Décision | Proposition initiale | Ce qui manque |
| --- | --- | --- |
| Fournisseur de découverte | Un connecteur remplaçable, après essai borné. | Couverture, droits de conservation et configuration disponible. |
| Budget | Plafond explicite par lot, incluant recherche secondaire et rendu éventuel. | Montant accepté ; le budget publicitaire évoqué antérieurement ne vaut pas abonnement API. |
| Géographie | Agences implantées dans la zone ; clients partout. | Confirmation de cette règle et choix du premier lot. |
| Interface | Petite revue locale si elle réduit le temps de qualification ; CLI conservée pour les tâches. | Préférence utilisateur et coût de cette première interface. |
| Contact commercial | Choix par dossier, indépendant de la provenance. | Priorité agence partenaire ou entreprise à réparer. |
| Usage de modèles dans l'extraction | Règles et extraction explicables en premier ; aide ciblée possible. | Valeur mesurée, coût, confidentialité et fiabilité avant généralisation. |

## 12. Sources de référence

Consultées le 20 novembre 2026 ; vérifier de nouveau avant un choix de service engageant.

- [OpenAI — consignes AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md).
- [OpenAI — skills et emplacement des skills de dépôt](https://learn.chatgpt.com/docs/build-skills).
- [Brave Search API — conditions, notamment conservation](https://api-dashboard.search.brave.com/terms-of-service).
- [Google — classement des résultats locaux](https://support.google.com/business/answer/7091?hl=fr).
- [WordPress — découverte de l'API](https://developer.wordpress.org/rest-api/using-the-rest-api/discovery/).
- [Google — familles de problèmes de sécurité](https://support.google.com/webmasters/answer/9044101?hl=en).
