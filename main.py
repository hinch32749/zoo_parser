import threading
import requests
import datetime
from bs4 import BeautifulSoup

list_ = []


def parser(page):
    url = f"https://garfield.by/catalog/dogs/suhie-korma-dlya-sobak.html?PAGEN_{page}=1&SIZEN_1=18"
    response = requests.get(url=url).text
    soup = BeautifulSoup(response, "lxml")
    items = soup.find("div", class_="catalog_items_container").find_all("div", class_="product-item-container")
    for item in items:
        dict_ = {}
        url_product = item.find("div", class_="product-item-title").find("a").get("href")
        url_product = f"https://garfield.by{url_product}"
        product_response = requests.get(url=url_product).text
        soup_product = BeautifulSoup(product_response, "lxml")
        product = soup_product.find("div", class_="product-card__info")
        product_title = product.find("h1").text
        product_brand = product.find("div", class_="product-card__producer-img").find("img").get("alt")
        product_prices = product.find("div", class_="product-item__tree").find_all("li")
        dict_["title"] = product_title
        dict_["brand"] = product_brand
        for p in product_prices:
            goods = p.find("span", class_="product-card__assortiment-item-wt pc_text15").text.strip()
            price = p.find("span", class_="product-card__assortiment-item-price pc_text16b").text.strip()
            dict_["goods"] = goods
            dict_["price"] = price
            list_.append(dict_)


def st():
    for page in range(1, 4):
        # parser(page)
        thread = threading.Thread(target=parser, args=(page,))
        thread.start()
        # thread.join()
    print(len(list_))


if __name__ == "__main__":
    start = datetime.datetime.now()
    st()
    print(datetime.datetime.now() - start)
