import logging
import sys
import requests
import re
import csv
from html import unescape

def get_category_list(content):
    
    return category_pat.findall(content)


def get_book_list(content):
    
    content = content.replace("\n", " ")
    
    return book_list_pat.findall(content)


def get_product_details(content):
    
    image_base = "http://books.toscrape.com/"
    
    result = img_pat.findall(content)
    if len(result) == 0:
        logging.warning("Image url not found!")
        image_url = ""
    else:
        img_url = result[0]
        img_url = img_url.replace("../../", "")
        image_url = image_base + img_url

    result = desc_pat.findall(content)
    if len(result) == 0:
        logging.warning("Description not found!")
        description = ""
    else:
        description = unescape(result[0])

    result = upc_pat.findall(content)
    if len(result) == 0:
        logging.warning("UPC not found!")
        upc = ""
    else:
        upc = result[0]

    result = price_pat.findall(content)
    if len(result) == 0:
        logging.warning("Price not found!")
        price = ""
    else:
        price = result[0]

    result = avail_pat.findall(content)
    if len(result) == 0:
        logging.warning("Availability not found!")
        availability = ""
    else:
        availability = result[0]

    return upc, price, image_url, availability, description


def get_page_content(url):
    
    try:
        response = requests.get(url)
    except requests.exceptions.RequestException as e:
        logging.error(e)

    if response.ok:
        return response.text
    
    logging.error("Can not get content from URL:" + url)
    
    return ""


def get_next_page(url, content):
    
    result = next_page_pat.findall(content)
    if len(result) == 0:
        return None
    i = url.rfind("/")
    
    return url[0:i+1] + result[0]


def scrape_book_info(book_info, category_name):
    
    book_url, book_name = book_info
    book_name = unescape(book_name)
    book_dict = {"Name": book_name, "Category": category_name}

    book_url = book_url.replace("../../../", "")
    book_url = "http://books.toscrape.com/catalogue/" + book_url
    book_dict["URL"] = book_url

    print("Scraping book", book_name)
    logging.info("Scraping : " + book_url)

    content = get_page_content(book_url)
    content = content.replace("\n", " ")

    upc, price, image_url, availability, desc = get_product_details(content)
    book_dict["UPC"] = upc 
    book_dict["Price"] = price
    book_dict["ImageURL"] = image_url
    book_dict["Availability"] = availability
    book_dict["Description"] = desc

    csv_writer.writerow(book_dict)


def crawl_category(category_name, category_url):
    
    while True:
        content = get_page_content(category_url)
        
        book_list = get_book_list(content)

        for book in book_list:
            scrape_book_info(book, category_name)
        
        next_page = get_next_page(category_url, content)
        if next_page is None:
            break

        category_url = next_page


def crawl_website():
    
    url = "http://books.toscrape.com/index.html"
    host_name = "books.toscrape.com"

    content = get_page_content(url)
    if content == "" :
        logging.critical("Got empty content from " + url)
        sys.exit(1)

    category_list = get_category_list(content)

    for category in category_list:
        category_url, category_name = category
        category_url = "http://" + host_name + "/" + category_url
        crawl_category(category_name, category_url)


if __name__ == "__main__":
    category_pat = re.compile(
        r'<li>\s*<a href="(catalogue/category/books/.*?)">\s*(\w+[\s\w]+\w)\s*?<', re.M | re.DOTALL)
    next_page_pat = re.compile(
        r'<li class="next"><a href="(.*?)">next</a></li>')
    book_list_pat = re.compile(
        r'<h3><a href="(.*?)" title="(.*?)">')
    img_pat = re.compile(
        r'<div class="item active">\s*<img src="(.*?)"')
    desc_pat = re.compile(
        r'<div id="product_description" class="sub-header">.*?<p>(.*?)</p>')
    upc_pat = re.compile(
        r'<th>UPC</th>\s*<td>(.*?)</td>')
    price_pat = re.compile(
        r'<th>Price \(incl. tax\)</th>\s*<td>\D+([\d.]+?)</td>')
    avail_pat = re.compile(
        r'<th>Availability</th>\s*<td>(.*?)</td>')

    logging.basicConfig(
        format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', 
        filename="book_crawler.log", level=logging.DEBUG)
    
    header_fields = [
        "Name", "Category", "UPC", "URL", "ImageURL", 
        "Price", "Availability", "Description"
        ]
        
    with open("book_list.csv", "w", encoding="ISO-8859-1") as csvf:
        csv_writer = csv.DictWriter(csvf, fieldnames=header_fields)
        csv_writer.writeheader()

        crawl_website()
        print("Crawling Done!")