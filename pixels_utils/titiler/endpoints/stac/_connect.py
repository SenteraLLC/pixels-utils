from requests import get

from pixels_utils.titiler._connect import online_status_titiler


def online_status_stac(titiler_endpoint: str, stac_endpoint: str):
    """
    Checks the online status of both the Titiler and STAC endpoints.

    Args:
        titiler_endpoint (str): Titiler endpoint (e.g., `"https://pixels.sentera.com"`).
        stac_endpoint (str): STAC endpoint (e.g.,
        `"https://earth-search.aws.element84.com/v1/collections/sentinel-2-l2a/items/S2B_10TGS_20220608_0_L2A"`).
    """
    online_status_titiler(titiler_endpoint)
    assert (
        get(stac_endpoint).status_code == 200
    ), f'STAC endpoint "{stac_endpoint}" is either not available or not online.'
