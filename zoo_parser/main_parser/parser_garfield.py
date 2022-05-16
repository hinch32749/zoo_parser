import requests
from bs4 import BeautifulSoup
import time


url = "https://garfield.by/"
headers = {"accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"}

response = requests.get(url=url, headers=headers).text
soup = BeautifulSoup(response, "lxml")
animals = soup.find_all("a", class_="header-nav__link")

for animal in animals[:-3]:
    print("----------------------------")
    print(animal.text)
    print("----------------------------")

    response_category = requests.get("https://garfield.by" + animal.get("href")).text
    soup_category = BeautifulSoup(response_category, "lxml")
    categories = soup_category.find("ul", class_="bx_catalog_tile_ul").find_all("li", class_="catalog_section_snipet")

    for category in categories[:-2]:
        print(f'-- {category.find("h2", class_="bx_catalog_tile_title").text}')
        print(f'   https://garfield.by{category.find("h2", class_="bx_catalog_tile_title").find("a").get("href")}')