import requests
from django.conf import settings

class Paystack:
    PAYSTACK_SECRET_KEY = settings.PAYSTACK_SECRET_KEY
    BASE_URL = "https://api.paystack.co"

    def initialize_payment(self, email, amount):
        url = f"{self.BASE_URL}/transaction/initialize"
        headers = {
            "Authorization": f"Bearer {self.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "email": email,
            "amount": amount,  # Amount in kobo (e.g., NGN)
        }
        response = requests.post(url, headers=headers, json=payload)
        return response.json()

    def verify_payment(self, reference):
        url = f"{self.BASE_URL}/transaction/verify/{reference}"
        headers = {
            "Authorization": f"Bearer {self.PAYSTACK_SECRET_KEY}",
        }
        response = requests.get(url, headers=headers)
        return response.json()
