import requests

def can_access_telegram(token):
    """
    Checks if access to Telegram is possible by attempting to make a request to the Telegram API.
    Returns True if access is possible, False otherwise.
    """
    try:
        response = requests.get('https://api.telegram.org/bot'+token+'/getMe')  # Replace <your_bot_token> with your bot token
        if response.status_code == 200:
            return True
        else:
            return False
    except requests.exceptions.RequestException:
        return False
