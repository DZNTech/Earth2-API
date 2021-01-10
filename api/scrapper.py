from bs4 import BeautifulSoup
import json
import re

def extract_settings_json(html_doc):
    soup=BeautifulSoup(html_doc,'html.parser')
    data=soup.find(text=re.compile("riot.auth0user"))
    if not data:
        return None
    data=re.findall("riot.auth0user.*}",data)[0] or None
    json_str= data.split(" = ")[1].replace("'",'"') or None
    json_data = json.loads(json_str)
    country = soup.find("div",class_="selected-flag").get("title") or ""
    json_data["country"] = country
    return json_data

def scrape_settings(html_doc):
    try:
        settings_json = {
            "id":"",
            "username":"",
            "country":"",
            "email":"",
            "phone":"",
            "referral_code":"",
            "image_url":"",
            "property_count":"",
            "balance":"",
            "net_worth":"",
            "profit_increase_net":"",
            "profit_increase_pct":""
        }
        error=False
        json_data = extract_settings_json(html_doc)
        if not json_data:    
            return {"error":"Something went wrong"}
        profit= json_data["networth"]-json_data["spent"]
        profit_percent = (profit*100)/json_data["spent"]

        settings_json["id"]=json_data["id"]
        settings_json["username"]=json_data["username"]
        settings_json["country"]=json_data["country"]
        settings_json["email"]=json_data["email"]
        settings_json["phone"]=json_data["phoneNumber"]
        settings_json["referral_code"]=json_data["referralCodeId"]
        settings_json["image_url"]=json_data["picture"]
        settings_json["property_count"]=json_data["totalTiles"]
        settings_json["balance"]=json_data["balance"]
        settings_json["net_worth"]=json_data["networth"]
        settings_json["profit_increase_net"]=profit
        settings_json["profit_increase_pct"]=profit_percent
    except:
        error=True
    return error, settings_json

def extract_property_json(property_html):
    property_json = {
        "latitude":"",
        "longitude":"",
        "location":"",
        "image_url":"",
        "tiles_count":"",
        "land_title":"",
        "purchase_value":"",
        "market_value":""
    }
    if property_html:
        for i_tag in property_html.find_all("i"):
            i_tag.decompose()
        latlng = property_html.find("div",class_="location").text.split(" ")
        property_json["latitude"] = latlng[0]
        property_json["longitude"] = latlng[1]
        property_json["location"] = property_html.find("div",class_="coordinates").text
        property_json["image_url"] = property_html.find("img")["src"]
        property_json["tiles_count"] = property_html.find("div",class_="tile-count").text
        property_json["land_title"] = property_html.find("div",class_="description").text
        property_json["purchase_value"] = property_html.find("span",class_="trade-value").text.strip() 
        property_json["market_value"] = property_html.find("div",class_="price").text.strip().split(" ")[0] or ""
    return property_json


def scrape_properties(html_doc):
    try:
        error=False
        soup = BeautifulSoup(html_doc,"html.parser")
        propertyList = soup.find_all("div",class_="card")
        property_json_list = []
        for item in propertyList:
            property_json_list.append(extract_property_json(item))
    except:
        error=True
    return error,property_json_list