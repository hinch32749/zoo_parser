import threading
import requests
import datetime
from bs4 import BeautifulSoup

list_ = []


def parser():
    # url = f"https://garfield.by/catalog/dogs/suhie-korma-dlya-sobak.html?PAGEN_{page}=1&SIZEN_1=18"
    # response = requests.get(url=url).text
    # soup = BeautifulSoup(response, "lxml")
    # items = soup.find("div", class_="catalog_items_container").find_all("div", class_="product-item-container")
    # for item in items:
    #     dict_ = {}
    #     url_product = item.find("div", class_="product-item-title").find("a").get("href")
    #     url_product = f"https://garfield.by{url_product}"
    dict_ = {}
    product_response = requests.get(url="https://garfield.by/catalog/cats/korrektsiya-povedeniya/matatabi-ustraneniya-stressa-na-prieme-u-vracha-i-grumera-1-gr.html").text
    soup_product = BeautifulSoup(product_response, "lxml")
    product = soup_product.find("div", class_="product-card__info")
    product_title = product.find("h1").text
    product_brand = product.find("div", class_="product-card__producer-img").find("img").get("alt")
    dict_["title"] = product_title
    dict_["brand"] = product_brand
    try:
        product_prices = product.find("div", class_="product-item__tree").find_all("li")
        for p in product_prices:
            goods = p.find("span", class_="product-card__assortiment-item-wt pc_text15").text.strip()
            price = p.find("span", class_="product-card__assortiment-item-price pc_text16b").text.strip()
            dict_["goods"] = goods
            dict_["price"] = price
            list_.append(dict_)
    except:
        actual = product.find("div", class_="product-card__price-wt").text.strip()
        if 'нет' in actual:
            dict_["goods"] = 'нет в наличии'
            dict_["price"] = 'нет в наличии'
        else:
            dict_["goods"] = 'в наличии'
            dict_["price"] = product.find("div", class_="product-card__price-main").text.strip()
        dict_["title"] = product_title
        dict_["brand"] = product_brand
        list_.append(dict_)

parser()
print(list_)
# def st():
#     for page in range(1, 4):
#         # parser(page)
#         thread = threading.Thread(target=parser, args=(page,))
#         thread.start()
#         # thread.join()
#     print(len(list_))
#
#
# if __name__ == "__main__":
#     start = datetime.datetime.now()
#     st()
#     print(datetime.datetime.now() - start)
