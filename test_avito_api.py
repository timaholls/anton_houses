import os

import dotenv
import requests
dotenv.load_dotenv()

# 🔹 URL API Авито
TOKEN_URL = "https://api.avito.ru/token"
reviews_URL = f"https://api.avito.ru/ratings/v1/reviews"

# 🔹 Функция для получения токена
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")


def get_access_token():
    """Получает токен доступа к API Avito."""
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    response = requests.post(TOKEN_URL, data=data, headers=headers)
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data["access_token"]
        print(f"✅ Access Token получен: {access_token}")
        return access_token
    else:
        print(f"❌ Ошибка при получении токена: {response.status_code}")
        print(response.text)
        exit()

