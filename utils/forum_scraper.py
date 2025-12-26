from bs4 import BeautifulSoup
import requests
import re
import json


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

def format_as_dict(updates):
    dict = {}
    for i in range(len(updates)):
        dict[updates[i][0]] = {"beta": updates[i][1], "release_id": updates[i][2]}
    return dict

def write_to_json(dict):
    with open("update_info.json", "w") as f:
        json.dump(dict, f, indent=4)
    f.close()

def get_latest_update_info_from_dict(beta=False):
    with open("update_info.json", "r") as f:
        dict = json.load(f)
    f.close()
    for i in dict:
        if dict[i]["beta"] != beta:
            continue
        return i
        
def update_dict():
    updates = get_past_update_info()
    updated_dict = format_as_dict(updates)
    write_to_json(updated_dict)


# updates = get_past_update_info()
# updated_dict = format_as_dict(updates)
# write_to_json(updated_dict)

# print(get_latest_update_info_from_dict(beta=False))

# print(updates)
# print(updated_dict)