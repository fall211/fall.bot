from bs4 import BeautifulSoup
import requests
import re



def get_past_update_info():
    page = requests.get("https://forums.kleientertainment.com/game-updates/dst/")
    soup = BeautifulSoup(page.content, "html.parser")
    raw_updates = soup.find_all("li", class_="cCmsRecord_row")

    updates = []

    for i in raw_updates:
        version = i.find("h3", class_="ipsType_sectionHead ipsType_break")
        version_id, beta = format_version_id(version)
        release_id = i.find("a", class_="cRelease")["data-releaseid"]
        # print(version_id, beta, release_id)
        updates.append((version_id, beta, release_id))

    updates.sort(key=lambda x: x[0], reverse=True)
    return updates

def format_version_id(version_id):
    text = version_id.get_text()
    text = re.sub(r"\s", "", text).strip()

    beta = text.endswith("Test")
    text = text[:6]
    return text, beta

# updates = get_past_update_info()
# print(updates)