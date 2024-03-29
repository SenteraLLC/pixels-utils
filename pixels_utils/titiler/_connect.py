from requests import get
from retry import retry


@retry((RuntimeError, KeyError), tries=3, delay=2)
def online_status_titiler(titiler_endpoint: str):
    """
    Checks the online status of the Titiler endpoint.

    Args:
        titiler_endpoint (str): Titiler endpoint (e.g., `"https://pixels.sentera.com"`).
    """
    assert (
        get(f"{titiler_endpoint}/docs").status_code == 200
    ), f'Titiler endpoint "{titiler_endpoint}" is either not available or not online.'
