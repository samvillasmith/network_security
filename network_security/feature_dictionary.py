FEATURE_NAMES = [
    "having_IP_Address",
    "URL_Length",
    "Shortining_Service",
    "having_At_Symbol",
    "double_slash_redirecting",
    "Prefix_Suffix",
    "having_Sub_Domain",
    "SSLfinal_State",
    "Domain_registeration_length",
    "Favicon",
    "port",
    "HTTPS_token",
    "Request_URL",
    "URL_of_Anchor",
    "Links_in_tags",
    "SFH",
    "Submitting_to_email",
    "Abnormal_URL",
    "Redirect",
    "on_mouseover",
    "RightClick",
    "popUpWidnow",
    "Iframe",
    "age_of_domain",
    "DNSRecord",
    "web_traffic",
    "Page_Rank",
    "Google_Index",
    "Links_pointing_to_page",
    "Statistical_report",
]


FEATURE_DICTIONARY = """All features are discretized to {-1, 0, 1} where -1 indicates a phishing-like signal, 1 indicates a legitimate-like signal, and 0 (where present) indicates an ambiguous/suspicious signal.

- having_IP_Address: Does the URL use a raw IP address instead of a domain name? -1 = raw IP (phishing-like), 1 = domain name.
- URL_Length: Overall length of the URL. -1 = very long (phishing-like), 0 = medium, 1 = short.
- Shortining_Service: Is the URL served via a link shortener (bit.ly, tinyurl, etc.)? -1 = yes, 1 = no.
- having_At_Symbol: Does the URL contain an '@' symbol (browsers ignore text before '@')? -1 = yes, 1 = no.
- double_slash_redirecting: Does the URL contain '//' in the path (beyond the protocol)? -1 = yes, 1 = no.
- Prefix_Suffix: Does the domain contain a hyphen (often used to imitate legitimate brands)? -1 = yes, 1 = no.
- having_Sub_Domain: Number of subdomains. -1 = many (phishing-like), 0 = one, 1 = none.
- SSLfinal_State: Quality of the HTTPS certificate. -1 = no HTTPS or untrusted issuer, 0 = trusted issuer but short-lived, 1 = trusted issuer and sufficient age.
- Domain_registeration_length: How long the domain is registered for. -1 = <= 1 year (phishing-like), 1 = > 1 year.
- Favicon: Is the favicon loaded from the same domain? -1 = external, 1 = same domain.
- port: Does the URL expose a non-standard port? -1 = suspicious port open, 1 = standard ports only.
- HTTPS_token: Does the domain name itself contain the string 'https' (spoofing)? -1 = yes, 1 = no.
- Request_URL: Fraction of page resources (images, scripts) loaded from a different domain. -1 = high external fraction, 0 = medium, 1 = low.
- URL_of_Anchor: Fraction of anchor tags pointing to a different domain or to '#'. -1 = high, 0 = medium, 1 = low.
- Links_in_tags: Fraction of <meta>, <script>, <link> tags referencing external domains. -1 = high, 0 = medium, 1 = low.
- SFH: Server Form Handler target. -1 = form submits to 'about:blank' or empty, 0 = form submits to a different domain, 1 = form submits to same domain.
- Submitting_to_email: Does a form submit via mailto:? -1 = yes, 1 = no.
- Abnormal_URL: Does the WHOIS record's hostname match the URL's domain? -1 = mismatch, 1 = match.
- Redirect: Number of redirects when loading the page. -1 = many redirects, 1 = few or none.
- on_mouseover: Does JavaScript change the browser status bar on mouseover (hiding the real link)? -1 = yes, 1 = no.
- RightClick: Is right-click disabled via JavaScript (to prevent inspection)? -1 = yes, 1 = no.
- popUpWidnow: Does the page open a popup window requesting personal info? -1 = yes, 1 = no.
- Iframe: Does the page contain iframes with no visible border (common phishing technique)? -1 = yes, 1 = no.
- age_of_domain: Age of the domain per WHOIS. -1 = < 6 months (phishing-like), 1 = >= 6 months.
- DNSRecord: Does the domain have a DNS record? -1 = no record, 1 = record present.
- web_traffic: Alexa-style traffic rank. -1 = not ranked / very low, 0 = mid rank, 1 = high rank.
- Page_Rank: PageRank value. -1 = low or none, 1 = high.
- Google_Index: Is the page indexed by Google? -1 = not indexed, 1 = indexed.
- Links_pointing_to_page: Count of inbound links. -1 = none (phishing-like), 0 = few, 1 = many.
- Statistical_report: Does the host IP or domain appear on known phishing blocklists (PhishTank/StopBadware)? -1 = yes, 1 = no.
"""
