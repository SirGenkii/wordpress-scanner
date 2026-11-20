#!/usr/bin/env python3
"""Triage public de sites WordPress — observations, jamais certification."""
from __future__ import annotations

import argparse
import csv
import hashlib
import http.client
import ipaddress
import json
import re
import socket
import ssl
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

AGENT = "WP-Public-Triage"
USER_AGENT = AGENT + "/0.1 (public-page diagnostic)"
MAX_BYTES = 1024 * 1024
SPAM = re.compile(r"\b(?:viagra|cialis|casino|casinos|slots|porn|pornhub|levitra|kamagra)\b", re.I)
DEFACED = re.compile(r"\b(?:hacked\s+by|pwned\s+by|defaced\s+by)\b", re.I)
VOID = set("area base br col embed hr img input link meta param source track wbr".split())
MUTED = {"script", "style", "noscript", "template", "head"}
SKIP_PATH = re.compile(r"(?:wp-admin|wp-login|wp-json|wp-content|wp-includes|xmlrpc|\.git|\.env)", re.I)
SOCIAL = {"facebook.com", "instagram.com", "linkedin.com", "twitter.com", "x.com", "youtube.com", "youtu.be", "tiktok.com", "pinterest.com", "wordpress.org", "wordpress.com", "google.com", "maps.google.com", "wa.me"}
REQUEST_TIMES = {}
LIMITATIONS = [
    "Observations publiques uniquement ; aucun accès aux fichiers, à la base ou aux journaux du serveur.",
    "JavaScript et CSS externes non exécutés ; contenu conditionnel ou interne potentiellement invisible.",
    "Aucun indice ne signifie pas site sain ; revue humaine nécessaire avant toute prise de contact.",
    "Les profils modifient seulement User-Agent/Referer ; ce ne sont pas de vrais navigateurs mobiles.",
]


def utcnow():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalize_url(value):
    value = value.strip()
    if not value or re.search(r"[\x00-\x20\x7f]", value):
        raise ValueError("URL vide ou caractères de contrôle/espaces")
    if "://" not in value:
        value = "https://" + value
    p = urlsplit(value)
    if p.scheme not in {"http", "https"} or p.username is not None or p.password is not None:
        raise ValueError("HTTP(S) sans identifiants uniquement")
    host = (p.hostname or "").rstrip(".").lower()
    if not host or "%" in host or "\\" in host:
        raise ValueError("Nom d’hôte invalide")
    try:
        host = str(ipaddress.ip_address(host))
    except ValueError:
        host = host.encode("idna").decode("ascii")
        if not re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", host):
            raise ValueError("Nom d’hôte invalide")
    port = p.port or (443 if p.scheme == "https" else 80)
    if port != (443 if p.scheme == "https" else 80):
        raise ValueError("Ports HTTP/HTTPS standards uniquement")
    if any(key.lower() in {"action", "logout", "add-to-cart", "_wpnonce"} for key in parse_qs(p.query)):
        raise ValueError("URL avec action potentiellement modificatrice ignorée")
    netloc = "[" + host + "]" if ":" in host else host
    return urlunsplit((p.scheme, netloc, p.path or "/", p.query, ""))


def host_key(url):
    host = urlsplit(url).hostname or ""
    return host[4:] if host.startswith("www.") else host


def origin(url):
    p = urlsplit(url)
    return p.scheme + "://" + p.netloc


def public_endpoint(url):
    p = urlsplit(normalize_url(url))
    port = 443 if p.scheme == "https" else 80
    answers = socket.getaddrinfo(p.hostname, port, type=socket.SOCK_STREAM)
    addresses = list(dict.fromkeys(answer[4][0] for answer in answers))
    if not addresses:
        raise ValueError("Résolution DNS vide")
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global or ip.is_multicast or ip.is_reserved or ip.is_unspecified:
            raise ValueError("Adresse réseau non publique bloquée")
        if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
            raise ValueError("Adresse IPv4 encapsulée bloquée")
        if isinstance(ip, ipaddress.IPv6Address) and any(ip in ipaddress.ip_network(prefix) for prefix in ("64:ff9b::/96", "64:ff9b:1::/48", "2002::/16", "2001::/32")):
            raise ValueError("Adresse IPv6 de transition bloquée")
    return addresses[0], port


class PinnedHTTP(http.client.HTTPConnection):
    def connect(self):
        self.sock = socket.create_connection((self.public_ip, self.port), self.timeout)


class PinnedHTTPS(http.client.HTTPSConnection):
    def connect(self):
        sock = socket.create_connection((self.public_ip, self.port), self.timeout)
        try:
            self.sock = self._context.wrap_socket(sock, server_hostname=self.host)
        except Exception:
            sock.close()
            raise


class Fetcher:
    """GET bornés, IP épinglée, robots, aucune destination externe suivie."""
    def __init__(self, timeout=10, delay=1.05, max_requests=18):
        self.timeout, self.delay, self.max_requests = timeout, delay, max_requests
        self.requests = 0
        self.last_request, self.robots_cache, self.crawl_delays = REQUEST_TIMES, {}, {}

    def _single(self, url, profile):
        if self.requests >= self.max_requests:
            raise ValueError("Budget de requêtes atteint")
        url = normalize_url(url)
        ip, port = public_endpoint(url)
        p = urlsplit(url)
        domain = host_key(url)
        delay = max(self.delay, self.crawl_delays.get(origin(url), 0))
        remaining = delay - (time.monotonic() - self.last_request.get(domain, 0))
        if remaining > 0:
            time.sleep(remaining)
        headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml,text/plain", "Accept-Encoding": "identity"}
        if profile == "mobile":
            headers["User-Agent"] = "Mozilla/5.0 (Linux; Android 13; Mobile) " + USER_AGENT
        elif profile == "referrer":
            headers["Referer"] = "https://www.google.com/"
        connection_type = PinnedHTTPS if p.scheme == "https" else PinnedHTTP
        conn = connection_type(p.hostname, port=port, timeout=self.timeout)
        conn.public_ip = ip
        self.requests += 1
        self.last_request[domain] = time.monotonic()
        try:
            conn.request("GET", p.path + ("?" + p.query if p.query else ""), headers=headers)
            response = conn.getresponse()
            body = response.read(MAX_BYTES + 1)
            truncated = len(body) > MAX_BYTES
            body = body[:MAX_BYTES]
            content_type = response.getheader("Content-Type", "")
            charset = re.search(r"charset\s*=\s*[\"']?([\w-]+)", content_type, re.I)
            encoding = charset.group(1) if charset else "utf-8"
            try:
                text = body.decode(encoding, errors="replace")
            except LookupError:
                text = body.decode("utf-8", errors="replace")
            return {"status": response.status, "text": text, "content_type": content_type,
                    "location": response.getheader("Location"), "truncated": truncated,
                    "sha256": hashlib.sha256(body).hexdigest(),
                    "compressed": response.getheader("Content-Encoding", "identity").lower() not in {"", "identity"}}
        finally:
            conn.close()

    def robots_allowed(self, url):
        key = origin(url)
        if key not in self.robots_cache:
            result = self.fetch(key + "/robots.txt", respect_robots=False)
            status = result.get("status")
            if result.get("error") or result.get("external_redirect") or result.get("truncated") or result.get("compressed"):
                self.robots_cache[key] = (None, "robots.txt illisible")
            elif status in {404, 410}:
                self.robots_cache[key] = (True, "robots.txt absent")
            elif status is not None and 200 <= status < 300:
                if "text/html" in result.get("content_type", "").lower() or re.search(r"<!doctype\s+html|<html\b|<title\b", result.get("text", ""), re.I):
                    self.robots_cache[key] = (None, "robots.txt renvoie une page HTML/challenge ; non interprétée")
                    return False, self.robots_cache[key][1]
                parser = RobotFileParser()
                parser.parse(result.get("text", "").splitlines())
                wait = parser.crawl_delay(AGENT) or parser.crawl_delay("*") or 0
                rate = parser.request_rate(AGENT) or parser.request_rate("*")
                if rate and rate.requests:
                    wait = max(wait, rate.seconds / rate.requests)
                if wait > 30:
                    self.robots_cache[key] = (None, "robots.txt demande un délai supérieur à 30 s")
                else:
                    self.crawl_delays[key] = wait
                    self.robots_cache[key] = (parser, "robots.txt lu")
            else:
                self.robots_cache[key] = (None, "robots.txt inaccessible (HTTP %s)" % status)
        rule, reason = self.robots_cache[key]
        if rule is None:
            return False, reason
        if rule is True:
            return True, reason
        return rule.can_fetch(AGENT, url), "robots.txt interdit cette URL"

    def fetch(self, url, profile="direct", respect_robots=True):
        result = {"requested_url": url, "final_url": url, "profile": profile, "fetched_at": utcnow(), "redirects": []}
        try:
            current = normalize_url(url)
            initial_host = host_key(current)
            seen = set()
            for _ in range(4):
                if current in seen:
                    raise ValueError("Boucle de redirection")
                seen.add(current)
                if respect_robots:
                    allowed, reason = self.robots_allowed(current)
                    if not allowed:
                        raise ValueError(reason)
                page = self._single(current, profile)
                result.update(page)
                result["final_url"] = current
                if page["status"] not in {301, 302, 303, 307, 308} or not page.get("location"):
                    return result
                destination = normalize_url(urljoin(current, page["location"]))
                result["redirects"].append({"url": current, "status": page["status"], "destination": destination})
                if host_key(destination) != initial_host:
                    result["external_redirect"] = destination
                    return result
                current = destination
            raise ValueError("Limite de redirections atteinte")
        except (OSError, ValueError, http.client.HTTPException, ssl.SSLError) as exc:
            result["error"] = str(exc)[:250]
            return result


class PageParser(HTMLParser):
    def __init__(self, url):
        super().__init__(convert_charrefs=True)
        self.url, self.stack, self.anchors, self.active_anchors = url, [], [], []
        self.visible, self.titles, self.headings, self.wp_signals = [], [], [], set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        hidden = bool(self.stack and self.stack[-1][1]) or "hidden" in attrs
        style = re.sub(r"\s+", "", attrs.get("style") or "").lower()
        hidden |= "display:none" in style or "visibility:hidden" in style
        muted = bool(self.stack and self.stack[-1][2]) or tag in MUTED
        for key in ("src", "href"):
            path = attrs.get(key) or ""
            try:
                asset = urljoin(self.url, path)
                if host_key(asset) == host_key(self.url):
                    if "/wp-content/" in urlsplit(asset).path:
                        self.wp_signals.add("ressource locale wp-content")
                    if "/wp-includes/" in urlsplit(asset).path:
                        self.wp_signals.add("ressource locale wp-includes")
            except ValueError:
                pass
        if tag == "meta" and (attrs.get("name") or "").lower() == "generator" and "wordpress" in (attrs.get("content") or "").lower():
            self.wp_signals.add("meta generator WordPress")
        if tag == "link" and "https://api.w.org/" in (attrs.get("rel") or ""):
            self.wp_signals.add("relation API WordPress")
        if tag == "a" and len(self.anchors) < 500:
            anchor = {"href": attrs.get("href") or "", "text": "", "hidden": hidden}
            self.anchors.append(anchor)
            self.active_anchors.append(anchor)
        if tag not in VOID:
            self.stack.append((tag, hidden, muted))

    def handle_endtag(self, tag):
        if tag == "a" and self.active_anchors:
            self.active_anchors.pop()
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        tags = [entry[0] for entry in self.stack]
        if "title" in tags:
            self.titles.append(data)
        if "h1" in tags:
            self.headings.append(data)
        if not self.stack or not (self.stack[-1][1] or self.stack[-1][2]):
            self.visible.append(data)
        for anchor in self.active_anchors:
            if len(anchor["text"]) < 300:
                anchor["text"] += data

    @property
    def title(self):
        return " ".join(" ".join(self.titles).split())[:300]

    @property
    def visible_text(self):
        return " ".join(" ".join(self.visible).split())[:60000]

    def links(self, external):
        found = []
        for anchor in self.anchors:
            try:
                href = anchor["href"]
                if not href or href.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
                    continue
                url = normalize_url(urljoin(self.url, href))
                if (host_key(url) != host_key(self.url)) == external:
                    found.append(dict(anchor, url=url))
            except (ValueError, UnicodeError):
                continue
        return found


def observation(code, category, message, evidence):
    return {"code": code, "category": category, "message": message, "evidence": evidence}


def analyze_page(page):
    public = {key: value for key, value in page.items() if key not in {"text", "location", "compressed"}}
    public["title"], public["wordpress_signals"], public["observations"] = "", [], []
    obs = public["observations"]
    if page.get("external_redirect"):
        obs.append(observation("external_redirect", "verification", "Redirection vers un autre hôte ; peut être légitime", page["external_redirect"]))
    if page.get("error"):
        return public, None
    status = page.get("status", 0)
    if status in {401, 403, 429}:
        public["error"] = "Accès limité par le serveur (HTTP %s)" % status
        return public, None
    if status >= 500:
        obs.append(observation("http_5xx", "technical", "Erreur du serveur ; cause indéterminée", "HTTP %s" % status))
    elif status in {404, 410}:
        obs.append(observation("page_missing", "technical", "Page absente ; ne prouve pas un piratage", "HTTP %s" % status))
    if page.get("compressed"):
        public["error"] = "Réponse compressée malgré Accept-Encoding: identity ; non analysée"
        return public, None
    content_type = page.get("content_type", "").lower()
    if content_type and not any(mime in content_type for mime in ("text/html", "application/xhtml+xml", "text/plain")):
        public["error"] = "Type de document non analysé : " + content_type[:100]
        return public, None
    parser = PageParser(page["final_url"])
    parser.feed(page.get("text", ""))
    public["title"] = parser.title
    public["wordpress_signals"] = sorted(parser.wp_signals)
    text = parser.visible_text
    challenge_title = re.fullmatch(r"just a moment[.!…]*|attention required!?\s*\|\s*cloudflare|verify (?:that )?you are human[.!…]*|checking your browser[.!…]*|security verification|captcha", parser.title.strip(), re.I)
    challenge_marker = re.search(r"(?:cf-chl-|/cdn-cgi/challenge-platform/)", page.get("text", ""), re.I)
    if status == 200 and (challenge_title or (challenge_marker and len(text) < 1500 and re.search(r"verify|verifying|checking|vérifi", text, re.I))):
        public["error"] = "Page de vérification anti-robot ; contenu du site non observé"
        return public, None
    if len(text) < 2000 and re.search(r"error establishing a database connection|erreur lors de la connexion à la base de données|there has been a critical error|une erreur critique est survenue", text, re.I):
        obs.append(observation("wordpress_error", "technical", "Message de panne WordPress ; ne prouve pas un piratage", text[:250]))
    if SPAM.search(parser.title):
        obs.append(observation("topic_keyword", "verification", "Mot-clé à contextualiser dans le titre ; peut correspondre à l’activité", parser.title))
    external = parser.links(external=True)
    spam_links = [link for link in external if SPAM.search(link["text"])]
    hidden_spam = list({(link["url"], link["text"]): link for link in spam_links if link["hidden"]}.values())
    if hidden_spam:
        obs.append(observation("hidden_external_spam_links", "verification", "Liens externes masqués avec ancres à vérifier ; menu ou contenu légitime possible", [{"url": link["url"], "anchor": link["text"][:120]} for link in hidden_spam[:5]]))
    elif len(spam_links) >= 3:
        obs.append(observation("external_spam_links", "verification", "Plusieurs liens externes sur des sujets à contextualiser", [{"url": link["url"], "anchor": link["text"][:120]} for link in spam_links[:5]]))
    heading = " ".join(parser.headings)[:1000]
    if DEFACED.search(parser.title + " " + heading):
        obs.append(observation("defacement_claim", "verification", "Formule de défiguration dans le titre ou H1 ; article légitime possible", (parser.title + " | " + heading)[:300]))
    return public, parser


def classify(pages):
    observations = [o for page in pages for o in page.get("observations", [])]
    categories = {o["category"] for o in observations}
    families = {o["code"] for o in observations if o["code"] in {"defacement_claim", "conditional_external_redirect"}}
    if any(o["code"] == "hidden_external_spam_links" and len(o["evidence"]) >= 2 for o in observations):
        families.add("hidden_external_spam_links")
    if len(families) >= 2:
        return "revue_prioritaire"
    if "verification" in categories:
        return "a_verifier"
    if "technical" in categories:
        return "incident_technique"
    if not pages or any(page.get("error") or page.get("truncated") for page in pages):
        return "inconclusif"
    return "aucun_indice"


def scan_site(url, compare_profiles=False, fetcher=None):
    fetcher = fetcher or Fetcher()
    result = {"input_url": url, "checked_at": utcnow(), "pages": [], "limitations": LIMITATIONS}
    baseline = fetcher.fetch(url)
    public, parser = analyze_page(baseline)
    result["pages"].append(public)
    if parser and not baseline.get("external_redirect") and baseline.get("status") == 200:
        internal = []
        for link in parser.links(external=False):
            target = link["url"]
            p = urlsplit(target)
            if target == baseline["final_url"] or p.query or SKIP_PATH.search(p.path) or re.search(r"\.(?:pdf|zip|jpe?g|png|webp|gif|svg|mp[34]|xml|json|css|js)$", p.path, re.I):
                continue
            if target not in internal:
                internal.append(target)
        internal.sort(key=lambda value: not bool(re.search(r"blog|news|actualit|service|a-propos|about", value, re.I)))
        for target in internal[:2]:
            page, _ = analyze_page(fetcher.fetch(target))
            result["pages"].append(page)
    if compare_profiles and not public.get("error") and not baseline.get("external_redirect") and baseline.get("status") == 200:
        for profile in ("mobile", "referrer"):
            page, _ = analyze_page(fetcher.fetch(url, profile=profile))
            if not page.get("error") and (page.get("external_redirect") != public.get("external_redirect") or page.get("title") != public.get("title") or page.get("status") != public.get("status")):
                evidence = {"baseline": {"title": public.get("title"), "status": public.get("status"), "external_redirect": public.get("external_redirect")}, "profile": profile, "observed": {"title": page.get("title"), "status": page.get("status"), "external_redirect": page.get("external_redirect")}}
                page["observations"].append(observation("profile_difference", "verification", "Titre, statut ou redirection différents selon le profil ; variation légitime possible", evidence))
                if page.get("external_redirect") and page.get("external_redirect") != public.get("external_redirect"):
                    page["observations"].append(observation("conditional_external_redirect", "verification", "Redirection externe observée uniquement sur ce profil ; peut être légitime", evidence))
            result["pages"].append(page)
    signatures = sorted({s for page in result["pages"] for s in page.get("wordpress_signals", [])})
    result["wordpress"] = {"confidence": "forte" if len(signatures) >= 2 else "probable" if signatures else "indeterminee", "signals": signatures}
    result["classification"] = classify(result["pages"])
    result["requests"] = fetcher.requests
    result["needs_human_review"] = result["classification"] in {"revue_prioritaire", "a_verifier"}
    return result


def safe_cell(value):
    value = str(value if value is not None else "")
    if value.startswith(("\t", "\r", "\n")) or value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def read_targets(path, limit):
    targets, seen = [], set()
    for line in Path(path).read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line not in seen:
            targets.append(line)
            seen.add(line)
        if len(targets) >= limit:
            break
    return targets


def write_scan(results, output):
    output.mkdir(parents=True, exist_ok=True)
    (output / "report.json").write_text(json.dumps({"version": "0.1", "generated_at": utcnow(), "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    with (output / "report.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["url", "date_utc", "wordpress", "classification", "titre", "indices", "erreurs", "requêtes"])
        for result in results:
            pages = result["pages"]
            row = [result["input_url"], result["checked_at"], result["wordpress"]["confidence"], result["classification"], pages[0].get("title", "") if pages else "", "; ".join(sorted({o["code"] for p in pages for o in p.get("observations", [])})), "; ".join(sorted({p["error"] for p in pages if p.get("error")})), result["requests"]]
            writer.writerow([safe_cell(value) for value in row])


def discover(urls, output, limit):
    candidates, sources = {}, []
    for url in urls:
        fetcher = Fetcher(max_requests=8)
        page = fetcher.fetch(url)
        public, parser = analyze_page(page)
        sources.append(public)
        if not parser or page.get("status") != 200 or page.get("external_redirect"):
            continue
        for link in parser.links(external=True):
            key = host_key(link["url"])
            if key in SOCIAL or any(key.endswith("." + item) for item in SOCIAL):
                continue
            candidate = origin(link["url"]) + "/"
            if key not in candidates and len(candidates) < limit:
                candidates[key] = {"url": candidate, "source_pages": [url], "relationship_verified": False}
            elif key in candidates and url not in candidates[key]["source_pages"]:
                candidates[key]["source_pages"].append(url)
    output.mkdir(parents=True, exist_ok=True)
    (output / "candidates.txt").write_text("".join(item["url"] + "\n" for item in candidates.values()), encoding="utf-8")
    (output / "sources.json").write_text(json.dumps({"generated_at": utcnow(), "note": "Liens externes directs seulement. Relation client/agence non vérifiée. Ces domaines ne sont pas nécessairement WordPress ou défectueux.", "candidates": list(candidates.values()), "source_observations": sources}, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(candidates)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("scan", "discover"):
        sub = commands.add_parser(command)
        sub.add_argument("--input", required=True, help="Texte UTF-8 : une URL/un domaine par ligne")
        sub.add_argument("--out", required=True, type=Path, help="Dossier des résultats")
        sub.add_argument("--limit", type=int, default=50, help="Maximum de cibles/résultats (défaut 50, maximum 200)")
        if command == "scan":
            sub.add_argument("--compare-profiles", action="store_true", help="Deux GET supplémentaires : UA mobile puis Referer Google")
    args = parser.parse_args()
    if not 1 <= args.limit <= 200:
        parser.error("--limit doit être compris entre 1 et 200")
    urls = read_targets(args.input, args.limit if args.command == "scan" else min(args.limit, 20))
    if args.command == "discover":
        count = discover(urls, args.out, args.limit)
        print("%s domaines candidats ; provenance dans %s" % (count, args.out / "sources.json"))
        return
    results = []
    for index, url in enumerate(urls, 1):
        result = scan_site(url, compare_profiles=args.compare_profiles)
        results.append(result)
        print("[%s/%s] %s : %s (WordPress : %s)" % (index, len(urls), url, result["classification"], result["wordpress"]["confidence"]), flush=True)
        write_scan(results, args.out)
    if not results:
        write_scan([], args.out)
    print("Rapports : %s et %s" % (args.out / "report.csv", args.out / "report.json"))


if __name__ == "__main__":
    main()
