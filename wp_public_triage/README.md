# WP Public Triage — prototype v0

Un petit outil Python pour préparer une liste de sites à examiner avant de proposer un dépannage WordPress. Il collecte des observations publiques, distingue une panne d'un indice de compromission et conserve les éléments qui justifient le classement.

**Ce prototype produit des candidats à vérifier. Il ne confirme pas un piratage et ne certifie jamais qu'un site est sain.** Il ne mesure pas la rentabilité commerciale ni la précision réelle des détecteurs : celles-ci restent à mesurer sur un corpus contrôlé.

## Démarrage

Prérequis : Python 3.10 ou supérieur. Aucun paquet externe, compte ou abonnement requis pour cette version.

Décompresser l'archive, ouvrir un terminal dans son dossier, puis créer `targets.txt` avec une URL ou un domaine par ligne. Les lignes vides et celles commençant par `#` sont ignorées. Fournir l'URL exacte d'une page suspecte si elle est connue, et pas seulement la page d'accueil.

Exemple de forme, avec des adresses fictives à remplacer :

```text
https://entreprise.example/
https://autre-entreprise.example/page-a-verifier/
```

Lancer un premier lot :

```bash
python3 wp_triage.py scan --input targets.txt --out results --limit 50
```

Comparer aussi des profils HTTP simulés, sur une petite sélection :

```bash
python3 wp_triage.py scan --input targets.txt --out results_profiles --limit 10 --compare-profiles
```

Sur Windows, remplacer au besoin `python3` par `py -3`. Le fichier `examples/targets.txt` fourni ne contient que des commentaires afin de ne pas lancer de requêtes accidentelles.

### Découverte à partir de pages publiques

Dans `sources.txt`, inscrire les URL précises de pages contenant des liens vers des sites : par exemple, une page de références d'agence dont la consultation automatisée et la réutilisation sont permises.

```bash
python3 wp_triage.py discover --input sources.txt --out discovery --limit 50
python3 wp_triage.py scan --input discovery/candidates.txt --out results --limit 50
```

`discover` extrait des liens externes directs depuis les pages fournies. Ce n'est ni un moteur de recherche général, ni un explorateur récursif de portfolios. Une page sans liens HTML exploitables ne produira pas de candidats. La présence d'un lien ne prouve pas une relation client, et encore moins un contrat de maintenance en cours.

## Résultats

| Fichier | Contenu |
| --- | --- |
| `results/report.csv` | Vue de tri, ouvrable dans un tableur ; les cellules dangereuses pour les formules sont neutralisées. |
| `results/report.json` | Observations détaillées, dates, indices, empreintes et limites. |
| `discovery/candidates.txt` | Liste à relire avant analyse. |
| `discovery/sources.json` | Origine des liens et limites rencontrées pendant la découverte. |

Les exports ne contiennent pas de HTML brut exécutable. Les chaînes du JSON restent des données non fiables : une future interface devra les échapper, jamais les injecter avec `innerHTML`.

### Interpréter les statuts

| Statut | Sens |
| --- | --- |
| `revue_prioritaire` | Une combinaison de signaux justifie un examen rapide ; ce n'est pas un verdict d'infection. |
| `a_verifier` | Une anomalie ou un indice isolé reste ambigu. |
| `incident_technique` | Une panne a été observée ; sa cause n'est pas attribuée à un piratage. |
| `aucun_indice` | Les observations réalisées n'ont pas montré d'indice retenu par ces règles. |
| `inconclusif` | Le contenu n'a pas pu être suffisamment observé, notamment en cas de refus ou de problème réseau. |

La confiance WordPress est séparée (`forte`, `probable`, `indeterminee`). Même plusieurs marqueurs peuvent subsister sur un export statique. Un site sans marqueurs visibles n'est pas nécessairement un site sans WordPress.

## Ce que fait la v0

- Lit un lot borné de pages publiques par HTTP/HTTPS.
- Recherche des marqueurs WordPress dans les ressources, la balise generator et les liens d'API annoncés.
- Relève les codes HTTP, messages de panne, titres, liens externes et quelques motifs de contenu.
- Repère certains liens masqués par attribut ou style en ligne ; elle n'évalue pas une feuille CSS complète.
- Conserve les redirections HTTP et les destinations externes sans les suivre automatiquement.
- Peut comparer les réponses à des profils desktop, mobile et avec un referrer de moteur. Ces profils simulent des en-têtes : ils ne rendent pas la page comme un vrai navigateur.
- Classe les observations sans inventer de pourcentage de probabilité.
- Conserve des preuves textuelles courtes et des empreintes pour faciliter la revue.

Les mots associés au casino, aux médicaments ou au contenu adulte ne sont que des indices contextuels. Un article de sécurité, une pharmacie, un site multilingue ou une plateforme de jeux peut les utiliser légitimement. Une différence entre mobile et desktop peut elle aussi être normale.

## Limites à connaître

La v0 ne fait pas d'exécution JavaScript, de capture d'écran, de comparaison à un historique, de parcours exhaustif des sitemaps, de recherche plein texte sur le Web, d'analyse de pièces jointes ni de recherche de signatures de malware à jour. Elle n'intègre aucune API externe de réputation. Une page cachée, une redirection déclenchée en JavaScript, un comportement conditionné par l'adresse IP ou un malware uniquement côté serveur peuvent donc lui échapper.

Le crawl est très restreint. Même une analyse terminée ne couvre qu'une petite partie du site. Les liens externes ne sont pas visités automatiquement. Une migration légitime vers un autre domaine peut demander une nouvelle analyse manuelle de ce domaine.

Un résultat de moteur ou un ancien scan de réputation peut rester alarmant après nettoyage. Toujours revérifier l'URL vivante et la date du constat avant de contacter une entreprise. Un domaine expiré puis revendu n'est pas nécessairement l'ancien propriétaire à dépanner.

Le programme respecte `robots.txt` de manière prudente et s'arrête en cas d'impossibilité d'interprétation fiable ou de refus. Il se limite aux requêtes GET et bloque les destinations réseau non publiques. Il ne tente ni connexion administrateur, ni exploitation, ni récupération de fichiers secrets. Ces limites font partie du périmètre de consultation publique de ce prototype.

Paramètres de la v0 : 50 cibles par défaut, maximum 200 par commande ; URL fournie et jusqu'à deux liens internes ; jusqu'à deux profils supplémentaires ; budget de 18 requêtes par cible incluant robots et redirections ; réponses limitées à 1 Mio. Le délai nominal est de 1,05 seconde entre deux départs de requêtes vers un même hôte au sein d'une analyse, augmenté si robots.txt demande davantage. Le délai socket de 10 secondes s'applique à une opération réseau, pas à la durée totale d'une analyse ni à la résolution DNS. Le programme n'est donc pas encore doté d'une échéance globale stricte contre les serveurs extrêmement lents. `discover` lit au plus 20 pages sources et produit au plus 50 candidats par défaut.

## Avant un contact commercial

1. Relire l'URL, l'heure, le profil et l'observation exacte.
2. Reproduire l'anomalie ; si un navigateur est nécessaire, employer un environnement isolé sans session personnelle.
3. Vérifier que l'entreprise exploite toujours le domaine et que le contenu est réellement étranger à son activité.
4. Déterminer qui contacter : entreprise ou agence, avec preuve du lien et sans présumer qui assure aujourd'hui la maintenance.
5. Formuler un constat précis et vérifiable, puis proposer une aide. Ne pas transformer le statut de l'outil en affirmation « votre site est piraté ».
6. Suivre les refus et éviter de solliciter à nouveau une personne qui s'y est opposée.

La collecte de données personnelles publiques et leur utilisation commerciale restent encadrées. Pour la France, consulter les recommandations CNIL citées ci-dessous : pertinence professionnelle de la sollicitation, information et possibilité d'opposition. Ce programme ne collecte pas de coordonnées et n'envoie aucun message.

## Vérification du prototype

Depuis le dossier du projet :

```bash
python3 -m unittest discover -s tests -v
```

Validation de cette livraison : **24 tests réussis**. Les tests utilisent des réponses simulées et des contenus synthétiques. Ils vérifient des comportements du programme ; ils ne constituent pas une évaluation de sa précision sur des sites compromis réels.

Pour cette évaluation, constituer un petit corpus de cas autorisés et confirmés : pages avant/après nettoyage si disponibles, sites sains variés, pannes connues. Garder une partie des cas à l'écart du réglage des règles. Mesurer en priorité la part des alertes réellement pertinentes après revue humaine et le temps nécessaire par dossier.

## Sources et choix d'architecture

Sources officielles consultées le 20 novembre 2026. Les prix et conditions de service peuvent évoluer ; les intégrations ci-dessous sont des pistes et ne sont pas implémentées.

- [WordPress — découverte de l'API REST](https://developer.wordpress.org/rest-api/using-the-rest-api/discovery/) : marqueurs annoncés par le site.
- [WordPress — erreurs courantes](https://developer.wordpress.org/advanced-administration/wordpress/common-errors/) : une erreur critique ou de base de données possède de nombreuses causes ordinaires.
- [Google — rapport de problèmes de sécurité](https://support.google.com/webmasters/answer/9044101?hl=en) : injections et comportements conditionnels ; certaines informations exigent l'accès du propriétaire à Search Console.
- [Google — règles antispam](https://developers.google.com/search/docs/essentials/spam-policies) : contenu piraté, cloaking, abus de domaines expirés.
- [Sucuri — limites du scanner distant](https://docs.sucuri.net/plugins/malware-scanning/) : le contenu malveillant peut rester invisible depuis les pages publiques.
- [Google Web Risk — tarifs](https://cloud.google.com/web-risk/pricing) : l'offre Lookup seule affiche 100 000 appels mensuels gratuits, puis 0,50 USD par 1 000. La grille Lookup + Update est différente. Une intégration exige configuration et conditions Google Cloud appropriées.
- [Google Safe Browsing — documentation](https://developers.google.com/safe-browsing/reference) : usage non commercial ; Google renvoie les usages générateurs de revenus vers Web Risk.
- [VirusTotal — API publique et premium](https://docs.virustotal.com/reference/public-vs-premium-api) : restrictions d'usage commercial de l'API publique.
- [Brave Search API — conditions](https://api-dashboard.search.brave.com/terms-of-service) et [FAQ](https://brave.com/search/api/) : les droits de stockage des résultats nécessitent une offre appropriée ; ne pas supposer qu'un abonnement standard autorise une base permanente de prospects.
- [Common Crawl — index d'URL](https://commoncrawl.org/url-index) : source de corpus historiques, avec un travail de traitement supplémentaire.
- [urlscan — FAQ](https://docs.urlscan.io/pages/faq) : les scans sont des instantanés ; les paramètres de visibilité et droits d'intégration doivent être examinés.
- [CNIL — prospection électronique](https://www.cnil.fr/fr/la-prospection-commerciale-par-courrier-electronique-sms-mms-et-automate-dappel).
- [CNIL — réutilisation commerciale de données publiques](https://www.cnil.fr/fr/reutilisation-de-vos-donnees-publiees-sur-internet-des-fins-commerciales-quels-sont-vos-droits).
