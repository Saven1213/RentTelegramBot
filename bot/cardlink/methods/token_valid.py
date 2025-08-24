import requests


def token_valid(token: str):
    url = "https://cardlink.link/api/v1/merchant/balance"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return True
    elif response.status_code == 401:
        return False


