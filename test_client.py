from habr import HabrClient

cookies = """qrator_msid2=v2.0.1789233776.736.c26e090fe6WoVg5Z|nwAugEI47U2RP4ah|pgRfYDOszT2tZm/nUgKMleU3bxI+6zik31Z4CeB+z2OboD8pmQp9Aw0oc0yFTs2ZPHy5d3mplx0/sRBRvJ1pZw==-AUt/VyitsW97GjIpKdELYxhh8gA=; hw_acg=1; _pk_id.7.3577=29fe87301aba15f3.1789233748.; _pk_ses.7.3577=1; habr_web_home_feed=/feed/; hl=ru; fl=ru; habr_uuid=Wxn52KwjnjczQLrSChXt6lj4lycC%2FflJPRpqtcouWL79izPFaddnxYcZ%2F77MWPsDqFVAgcZbjYjRkJee%2FBkGMw; connect_sid=s%3AMcpcS9_AdMmpEu0wXdg7H9win3DyTprc.iXLcgUPpvnvipCsxbqim5dYCuoRAh4XKN1s%2FsqgFIBQ; habrsession_id=habrsession_id_8f174267f3f9f1dce6f860d8857910aa; s61687262000a=cjGs6tVoG9C6DW29lZMrT1-3ONtrMIjhvvaxE5_jN-krxxUj04zvNCXwBCB8yM6T; s69676e616c=d1ycZwsci2l/GXxM3jVtpg==; PHPSESSID=e3e00dc0d2c462b6bb500199dfeef0d5; hsec_id=94ac56e4ea52469d7f84b9e2d8b6f7ba; habr_web_ga_uid=5b6ed2f523eb6c4c0bbe5e853e3004e2; habr_web_hide_ads=false; habr_web_user_id=5962554; a_s_id=3cc54551-8f50-489d-bd5b-107934d656e5; a_s_la=2026-09-12 17:29:45"""

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
