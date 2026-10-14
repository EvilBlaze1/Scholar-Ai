
import ipaddress
import socket
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


TIMEOUT_SECONDS = 15
MAX_REDIRECTS = 5
MAX_RESPONSE_BYTES = 2_000_000

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/154.0 Safari/537.36"
    )
}

UNWANTED_TAGS = [
    "script",
    "style",
    "noscript",
    "header",
    "footer",
    "nav",
    "aside",
    "svg",
    "iframe",
    "form",
    "button",
]


def validate_url(url: str) -> str:
    """Accept public HTTP(S) URLs and reject private or local destinations."""
    if not isinstance(url, str) or not url.strip():
        raise ValueError("A valid webpage URL is required.")

    parsed = urlparse(url.strip())

    if parsed.scheme not in ("http", "https"):
        raise ValueError("Only HTTP and HTTPS URLs are supported.")

    if not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Invalid webpage URL.")

    if parsed.port not in (None, 80, 443):
        raise ValueError("This URL uses an unsupported port.")

    hostname = parsed.hostname.lower()

    if hostname == "localhost" or hostname.endswith(".localhost"):
        raise ValueError("Local URLs are not allowed.")

    try:
        addresses = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise ValueError("The webpage hostname could not be resolved.") from exc

    if not addresses:
        raise ValueError("The webpage hostname could not be resolved.")

    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])

        if not ip.is_global:
            raise ValueError("Private or non-public URLs are not allowed.")

    return url.strip()


def _fetch_response(url: str) -> requests.Response:
    """Fetch a page while validating each redirect destination."""
    current_url = url

    for _ in range(MAX_REDIRECTS + 1):
        validate_url(current_url)

        # Disable automatic redirects so every destination is validated.
        with requests.get(
            current_url,
            headers=HEADERS,
            timeout=TIMEOUT_SECONDS,
            stream=True,
            allow_redirects=False,
        ) as response:
            if response.is_redirect or response.is_permanent_redirect:
                location = response.headers.get("Location")

                if not location:
                    raise ValueError("The webpage returned an invalid redirect.")

                current_url = urljoin(current_url, location)
                continue

            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "").lower()

            if content_type and not (
                "text/html" in content_type
                or "application/xhtml+xml" in content_type
                or "text/plain" in content_type
            ):
                raise ValueError("The URL did not return readable webpage content.")

            content_length = response.headers.get("Content-Length")

            if content_length and int(content_length) > MAX_RESPONSE_BYTES:
                raise ValueError("The webpage is too large to process.")

            chunks = []
            total_bytes = 0

            for chunk in response.iter_content(chunk_size=16_384):
                if not chunk:
                    continue

                total_bytes += len(chunk)

                if total_bytes > MAX_RESPONSE_BYTES:
                    raise ValueError("The webpage is too large to process.")

                chunks.append(chunk)

            response._content = b"".join(chunks)
            response._content_consumed = True
            return response

    raise ValueError("The webpage exceeded the redirect limit.")


def fetch_webpage(url: str) -> str:
    """
    Retrieve readable text from a public webpage.

    Raises an exception if the page cannot be fetched or processed.
    Callers can catch failures and continue with other search results.
    """
    response = _fetch_response(url)

    content_type = response.headers.get("Content-Type", "").lower()

    if "text/plain" in content_type:
        return " ".join(response.text.split())

    soup = BeautifulSoup(response.content, "html.parser")

    for element in soup(UNWANTED_TAGS):
        element.decompose()

    # Prefer the main content when available.
    main_content = soup.find("main") or soup.find("article") or soup.body or soup

    text = main_content.get_text(separator=" ", strip=True)

    return " ".join(text.split())
