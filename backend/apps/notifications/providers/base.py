class ProviderError(Exception):
    """Raised when a provider rejects a request or is misconfigured."""


class BaseProvider:
    channel = ""

    def send(self, template, recipient, context):
        """Deliver one message. Returns a short detail string; raises ProviderError on failure."""
        raise NotImplementedError


def http_error(resp):
    try:
        data = resp.json()
    except ValueError:
        data = resp.text[:300]
    return ProviderError(f"HTTP {resp.status_code}: {data}")
