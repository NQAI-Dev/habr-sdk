import os
from habr import HabrClient

# Load session cookies from environment variable if set
cookies = os.getenv("HABR_COOKIES", "")

client = HabrClient(cookies=cookies)

me = client.get_me()
print("Me alias:", me.get("alias"))
print("Me ID:", me.get("id"))

card = client.get_user_card("NQAI")
print("Card score:", card.get("scoreStats"))

whois = client.get_user_whois("NQAI")
print("Badgets:", [b.get("title") for b in whois.get("badgets", [])])

hub = client.get_hub_info("go")
print("Hub title:", hub.get("titleHtml"))
