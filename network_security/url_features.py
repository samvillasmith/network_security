import ipaddress
import re
import socket
import warnings
from datetime import datetime, timezone
from urllib.parse import urlparse

import dns.resolver
import requests
import urllib3
import whois
from bs4 import BeautifulSoup

warnings.filterwarnings("ignore", category=UserWarning, module="whois")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HTTP_TIMEOUT = 6
MAX_RESPONSE_BYTES = 2_000_000
USER_AGENT = "Mozilla/5.0 (PhishingClassifier demo)"
BLOCKED_HOSTS = {"localhost", "metadata.google.internal", "metadata"}


class UnsafeURLError(ValueError):
    pass


def _assert_safe_url(url: str) -> None:
    parsed = urlparse(url if "://" in url else "http://" + url)
    host = (parsed.hostname or "").lower()
    if not host:
        raise UnsafeURLError("URL has no host.")
    if host in BLOCKED_HOSTS:
        raise UnsafeURLError(f"Blocked host: {host}")
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        try:
            resolved = socket.getaddrinfo(host, None)
            ip = ipaddress.ip_address(resolved[0][4][0])
        except Exception:
            return  # DNS may fail — that's fine; we'll handle it during fetch
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
        raise UnsafeURLError(f"Refusing to fetch internal/reserved address: {ip}")

SHORTENERS = {
    "bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly", "is.gd",
    "buff.ly", "rebrand.ly", "cutt.ly", "shorte.st", "short.io",
    "adf.ly", "tiny.cc", "bl.ink", "lnkd.in", "trib.al",
}

REPUTATION_DEFAULTS = {
    "web_traffic": 0,
    "Page_Rank": 0,
    "Google_Index": 0,
    "Links_pointing_to_page": 0,
    "Statistical_report": 0,
}


def extract_features(url: str) -> dict:
    """Best-effort URL -> 30-feature vector.

    Returns a dict with every feature name. Features that can't be determined
    from the URL/HTML/WHOIS/DNS path fall back to 0 (ambiguous). Reputation
    features (rank, blocklists) always default to 0 - they require paid APIs.
    """
    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    _assert_safe_url(url)

    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    features = {}

    # URL-structure (cheap, deterministic)
    features["having_IP_Address"] = -1 if _is_ip(host) else 1
    features["URL_Length"] = _url_length_bucket(url)
    features["Shortining_Service"] = -1 if host in SHORTENERS else 1
    features["having_At_Symbol"] = -1 if "@" in url else 1
    features["double_slash_redirecting"] = -1 if url.rfind("//") > 7 else 1
    features["Prefix_Suffix"] = -1 if "-" in host else 1
    features["having_Sub_Domain"] = _subdomain_bucket(host)
    features["HTTPS_token"] = -1 if "https" in host else 1
    features["port"] = -1 if (parsed.port and parsed.port not in (80, 443)) else 1

    # HTTP fetch (single shot, follow redirects)
    html, redirects, ssl_ok = _fetch(url)
    features["SSLfinal_State"] = _ssl_state(parsed, ssl_ok)
    features["Redirect"] = _redirect_score(redirects)

    # WHOIS
    info = _whois(host)
    features["Domain_registeration_length"] = _registration_length(info)
    features["age_of_domain"] = _domain_age(info)
    features["Abnormal_URL"] = _abnormal_url(host, info)

    # DNS
    features["DNSRecord"] = _dns_record(host)

    # HTML content
    base = _base_domain(host)
    if html:
        soup = BeautifulSoup(html, "html.parser")
        features["Favicon"] = _favicon(soup, base)
        features["Request_URL"] = _request_url(soup, base)
        features["URL_of_Anchor"] = _url_of_anchor(soup, base)
        features["Links_in_tags"] = _links_in_tags(soup, base)
        features["SFH"] = _sfh(soup, base)
        features["Submitting_to_email"] = _submitting_to_email(soup)
        features["on_mouseover"] = -1 if re.search(r"onmouseover\s*=.*window\.status", html, re.I) else 1
        features["RightClick"] = -1 if re.search(r"event\.button\s*==\s*2|contextmenu", html, re.I) else 1
        features["popUpWidnow"] = -1 if re.search(r"window\.open\s*\(", html, re.I) else 1
        features["Iframe"] = _iframe(soup)
    else:
        for k in ("Favicon", "Request_URL", "URL_of_Anchor", "Links_in_tags", "SFH",
                  "Submitting_to_email", "on_mouseover", "RightClick", "popUpWidnow", "Iframe"):
            features[k] = 0

    features.update(REPUTATION_DEFAULTS)
    return features


# --- helpers ---

def _is_ip(host):
    for fam in (socket.AF_INET, socket.AF_INET6):
        try:
            socket.inet_pton(fam, host)
            return True
        except (OSError, TypeError):
            continue
    return False


def _url_length_bucket(url):
    n = len(url)
    if n < 54: return 1
    if n <= 75: return 0
    return -1


def _subdomain_bucket(host):
    if not host: return 0
    # Strip 'www.' for a fair count.
    h = host[4:] if host.startswith("www.") else host
    dots = h.count(".")
    if dots <= 1: return 1
    if dots == 2: return 0
    return -1


def _fetch(url):
    """Returns (html, redirect_count, ssl_ok) - ssl_ok: True/False/None."""
    headers = {"User-Agent": USER_AGENT}
    try:
        r = requests.get(url, timeout=HTTP_TIMEOUT, headers=headers, allow_redirects=True)
        return r.text, len(r.history), True
    except requests.exceptions.SSLError:
        try:
            r = requests.get(url, timeout=HTTP_TIMEOUT, headers=headers, allow_redirects=True, verify=False)
            return r.text, len(r.history), False
        except Exception:
            return None, 0, False
    except Exception:
        return None, 0, None


def _ssl_state(parsed, ssl_ok):
    if parsed.scheme != "https":
        return -1
    if ssl_ok is True:
        return 1
    if ssl_ok is False:
        return -1
    return 0


def _redirect_score(n):
    if n <= 1: return 1
    if n <= 3: return 0
    return -1


def _whois(host):
    try:
        return whois.whois(host)
    except Exception:
        return None


def _as_datetime(value):
    if isinstance(value, list):
        value = value[0] if value else None
    if not isinstance(value, datetime):
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _registration_length(info):
    if not info: return 0
    exp = _as_datetime(getattr(info, "expiration_date", None))
    if not exp: return 0
    return 1 if (exp - datetime.now(timezone.utc)).days > 365 else -1


def _domain_age(info):
    if not info: return 0
    created = _as_datetime(getattr(info, "creation_date", None))
    if not created: return 0
    return 1 if (datetime.now(timezone.utc) - created).days > 180 else -1


def _abnormal_url(host, info):
    if not info: return 0
    name = getattr(info, "domain_name", None)
    if isinstance(name, list): name = name[0] if name else None
    if not name: return 0
    return 1 if name.lower() in host else -1


def _dns_record(host):
    if not host: return -1
    try:
        dns.resolver.resolve(host, "A", lifetime=5)
        return 1
    except Exception:
        return -1


def _base_domain(host):
    parts = host.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def _is_internal(link, base):
    if not link: return True
    if link.startswith(("/", "#", "?", "javascript:", "mailto:", "tel:")):
        return True
    try:
        h = (urlparse(link).hostname or "").lower()
    except Exception:
        return True
    return (not h) or (base in h)


def _favicon(soup, base):
    link = soup.find("link", rel=lambda v: v and "icon" in " ".join(v).lower() if isinstance(v, list) else (v and "icon" in v.lower()))
    href = link.get("href") if link else None
    if not href: return 0
    return 1 if _is_internal(href, base) else -1


def _request_url(soup, base):
    items = soup.find_all(["img", "audio", "embed", "iframe"])
    if not items: return 1
    ext = sum(1 for t in items if not _is_internal(t.get("src") or "", base))
    frac = ext / len(items)
    if frac < 0.22: return 1
    if frac <= 0.61: return 0
    return -1


def _url_of_anchor(soup, base):
    anchors = soup.find_all("a")
    if not anchors: return 1
    bad = 0
    for a in anchors:
        href = (a.get("href") or "").strip()
        if not href or href == "#" or href.lower().startswith("javascript:"):
            bad += 1
        elif not _is_internal(href, base):
            bad += 1
    frac = bad / len(anchors)
    if frac < 0.31: return 1
    if frac <= 0.67: return 0
    return -1


def _links_in_tags(soup, base):
    tags = soup.find_all(["meta", "script", "link"])
    if not tags: return 1
    def link_of(t):
        return t.get("src") or t.get("href") or ""
    ext = sum(1 for t in tags if link_of(t) and not _is_internal(link_of(t), base))
    total = sum(1 for t in tags if link_of(t))
    if total == 0: return 1
    frac = ext / total
    if frac < 0.17: return 1
    if frac <= 0.81: return 0
    return -1


def _sfh(soup, base):
    forms = soup.find_all("form")
    if not forms: return 1
    for f in forms:
        action = (f.get("action") or "").strip()
        if action == "" or action.lower() == "about:blank":
            return -1
        if not _is_internal(action, base):
            return 0
    return 1


def _submitting_to_email(soup):
    for f in soup.find_all("form"):
        if (f.get("action") or "").lower().startswith("mailto:"):
            return -1
    return 1


def _iframe(soup):
    frames = soup.find_all("iframe")
    if not frames: return 1
    for f in frames:
        style = (f.get("style") or "").lower()
        if f.get("frameborder") == "0" or "border:0" in style.replace(" ", ""):
            return -1
    return 1
