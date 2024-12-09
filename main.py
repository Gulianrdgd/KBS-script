import os
import pickle
import random
import ssl
import time
from email.mime.multipart import MIMEMultipart

import cssutils
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager  # Optional: if you want to automatically manage the driver

load_dotenv()

class House:
    def __init__(self, title: str, price: float, location: str, image: str, full: bool, link: str):
        self.title = title
        self.price = price
        self.location = location
        self.image = image
        self.full = full
        self.link = link

    def __str__(self):
        return f"Title: {self.title}, Price: {self.price}, Location: {self.location}, Image: {self.image}, Full: {self.full}, Link: {self.link}"

    def __repr__(self):
        return f"Title: {self.title}, Price: {self.price}, Location: {self.location}, Image: {self.image}, Full: {self.full}, Link: {self.link}"

    def __eq__(self, other):
        return self.link == other.link

    def __hash__(self):
        return hash(self.link)

    def filter(self, location, price):
        return (not self.full) and (location in self.location) and (self.price <= price)

    def to_html(self):
        return f"<br/><div>{self.title} - {self.price} euro </div><br/><img style='width:300px;height:200px;background-size: cover;background-position: center;background-repeat: no-repeat;' src='{self.image}'> <br/> \n <a href='{self.link}'>Link</a> {self.full} <br/>"

def send_email(houses: list[House], receiver):
    port = 465  # For SSL

    # Create a secure SSL context
    context = ssl.create_default_context()

    email = os.getenv('GMAIL_USERNAME')
    password = os.getenv('GMAIL_PASS')

    message = MIMEMultipart("alternative")
    message["Subject"] = "Nieuwe kamers!"
    message["From"] = email
    message["To"] = receiver

    text = "Nieuwe huizen gevonden! \n\n" + "\n".join(
        list(map(lambda h: h.to_html(), houses)))

    print("SENDING EMAIL:", text)
    # plain = MIMEText(text, "html")
    #
    # message.attach(plain)
    #
    # with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
    #     server.login(email, password)
    #     server.sendmail(email, receiver, message.as_string())


def extract_house_mvx(house) -> House:
    title = house.find_next('h2').text
    price = house.find('dd').text
    price = price_parser(price)
    location = house.find_next('p').text
    link = "https://mvxvastgoedbeheer.nl" + house['href']
    image = house.find('img')['src']
    verhuurd = house.find_next('div', class_="bg-orange")
    if verhuurd is not None:
        full = verhuurd.text == 'Verhuurd'
    else:
        full = False

    return House(
        title,
        price,
        location,
        image,
        full,
        link
    )


def extract_house_nederwoon(house) -> House:
    text_block = house.find_all('div', class_='click-see-page-button')
    text_block_ps = text_block[0].find_all('p')

    title = text_block[0].find_next('a').text

    price = text_block[1].find_next('p').text
    price = price_parser(price)

    location = 'Nijmegen'

    link = 'https://www.nederwoon.nl' + text_block[0].find_next('a')['href']
    image = 'https://www.nederwoon.nl' + house.find_next('img')['data-src']
    full = False

    return House(
        title,
        price,
        location,
        image,
        full,
        link
    )


def extract_house_wouw(house) -> House:
    title = house.find_next('h4').find_next('a').text
    if len(house.select('div.pt-cv-ctf-prijs')) == 0:
        return Exception('No price found')
    price = house.find('div', class_="pt-cv-ctf-prijs").find_next('div').text
    price = price.replace('.', '', price.count('.') - 1)

    location = 'Nijmegen'
    link = house.find('a')['href']
    image = house.find('a').find_next('img')['src']
    full = house.find('div', class_="pt-cv-ctf-status").find_next('div').text != "Te huur"

    return House(
        title,
        price,
        location,
        image,
        full,
        link
    )


def extract_house_rotsvast(house) -> House:
    title = house.find('div', class_='residence-street').text + " " + house.find('div',
                                                                                 class_='residence-zipcode-place').text
    status = house.find('div', class_='status').text
    full = "Verhuurd" in status or status == "Bezichtiging vol"

    price = house.find('div', class_='residence-price').text
    price = price_parser(price)

    image_style = house.find('div', class_='residence-image')['style']
    style = cssutils.parseStyle(image_style)
    image = style['background-image'].replace('url(', '').replace(')', '')

    location = house.find('div', class_='residence-zipcode-place').text
    location = location.split(" ")[1]
    link = house.find('a')['href']

    return House(
        title,
        price,
        location,
        image,
        full,
        link
    )


def extract_house_kbs(house) -> House:
    title = house.find('p').text
    full = False
    if title == 'Bezichtiging vol / Viewing list full' or 'Verhuurd / Rented out':
        title = house.find_next('p').find_next('p').text
        full = True

    price = house.find('div', class_='gb-container')
    price = price.find_next('p').find_next('p').text
    price = price_parser(price)

    sep = house.find('hr')
    image = house.find('img')['src']
    location = sep.find_all_next('p')[1].text
    link = house['href']

    return House(
        title,
        price,
        location,
        image,
        full,
        link
    )


def extract_house_hans_janssen(house) -> House:
    title = house.find('div', class_='card-house__title').find_next('h6').text
    full = house.find('div', class_='card-house__label')
    if full is not None:
        full = full.text.strip() == 'Verhuurd'
    else:
        full = False

    price = house.find('div', class_='card-house__price').text
    price = price_parser(price)

    image = 'https://www.hansjanssen.nl' + house.find_all('img')[1]['src']

    if not full:
        link = house.find_next('a')['href']
    else:
        link = 'unknown'

    location = 'Nijmegen'

    return House(
        title,
        price,
        location,
        image,
        full,
        link
    )


def extract_house_dolfijn(house) -> House:
    data_short = house.find('div', class_='datashort')
    title = data_short.find('span', class_='street').text
    location = data_short.find('span', class_='location').text

    status = house.find('span', class_='object_status')
    if status is not None:
        full = status.text.strip() == 'Verhuurd'
    else:
        full = False

    if not full:
        price = data_short.find('span', class_='obj_price').text
        price = price_parser(price)
    else:
        price = 0

    image = house.find('img')['src']
    link = 'https://dolfijnwonen.nl' + house.find('a')['href']

    return House(
        title,
        price,
        location,
        image,
        full,
        link
    )

def extract_house_holland2stay(house) -> House:
    title = house.find('h5', class_='residence_name').text
    location = "Nijmegen"
    full = False

    price = house.find('h4', class_='price_text').text

    if price is not None:
        price = price_parser(price)
    else:
        price = 0

    image = house.find('img', class_="rounded-image")['src']
    link = 'https://holland2stay.com/residences/' + title.replace(" ", "-").lower() + ".html"

    return House(
        title,
        price,
        location,
        image,
        full,
        link
    )


def price_parser(price):
    price = price.replace('€', '').replace('p/m', '').replace("*", "").replace("per month", "").replace('per maand', '').replace(' ', '').replace(',-', '').replace('/mnd', '').replace('p/m','').replace(' ', '').replace('excl.', '').replace('incl.', '').replace(",", ".").replace("nd", "").strip()
    price = price.replace('.', '', price.count('.') - 1)

    if "." in price and len(price.split('.')[1]) > 2:
        price = price.replace('.', '')

    return float(price)


def parse_html_of_houses(soup, site, html_element_type, html_element_class):
    houses = []

    for house_div in soup.find_all(html_element_type, class_=html_element_class):
        try:
            if site == 'mvx':
                houses.append(extract_house_mvx(house_div))
            elif site == 'nederwoon':
                houses.append(extract_house_nederwoon(house_div))
            elif site == 'wouw':
                houses.append(extract_house_wouw(house_div))
            elif site == 'rosvast':
                houses.append(extract_house_rotsvast(house_div))
            elif site == 'kbs':
                houses.append(extract_house_kbs(house_div))
            elif site == 'hans_janssen':
                houses.append(extract_house_hans_janssen(house_div))
            elif site == 'dolfijn':
                houses.append(extract_house_dolfijn(house_div))
            elif site == 'holland2stay':
                houses.append(extract_house_holland2stay(house_div))
        except Exception as e:
            print(f"parse_html_of_houses error from: {site}\n", e)
            return []

    return houses

def filter_per_person(houses: list[House], location: str, price: float, email: str, old_houses: list[House]):
    houses_per_person: list[House] = list(
        filter(lambda x: x.filter(location, price), houses))

    houses_ready_to_email = []

    for house in houses_per_person:
        if not (house in old_houses):
            houses_ready_to_email.append(house)

    if len(houses_ready_to_email) > 0:
        send_email(houses_ready_to_email, email)


def main():
    old_houses = {}

    if os.path.exists('old_houses.pkl'):
        with open('old_houses.pkl', 'rb') as f:
            old_houses = pickle.load(f)

    config = {
        "kbs": {
            "url": "https://kbsvastgoedbeheer.nl/aanbod/",
            "html_element_type": "a",
            "html_element_class": "gb-container",
        },
        "mvx": {
            "url": "https://mvxvastgoedbeheer.nl/aanbod?city=Nijmegen&sort-by=price-ascending",
            "html_element_type": "a",
            "html_element_class": "bg-ice",
        },
        "wouw": {
            "url": "https://www.vdwouwvastgoedbeheer.nl/aanbod/",
            "html_element_type": "div",
            "html_element_class": "pt-cv-ifield",
        },
        "rosvast": {
            "url": "https://www.rotsvast.nl/woningaanbod/rotsvast-nijmegen/",
            "html_element_type": "div",
            "html_element_class": "residence-gallery",
        },
        "nederwoon": {
            "url": "https://www.nederwoon.nl/search?search_type=&type=&rooms=&completion=&sort=1&city=Nijmegen",
            "html_element_type": "div",
            "html_element_class": "location",
        },
        "hans_janssen": {
            "url": "https://www.hansjanssen.nl/wonen/zoeken/Nijmegen/huur/",
            "html_element_type": "div",
            "html_element_class": "js-house-item",
        },
        "dolfijn": {
            "url": "https://dolfijnwonen.nl/woningaanbod/huur",
            "html_element_type": "article",
            "html_element_class": "objectcontainer",
        },
        "holland2stay": {
            "url": "https://holland2stay.com/residences?page=1&city%5Bfilter%5D=Nijmegen%2C6217&available_to_book%5Bfilter%5D=Available+to+book%2C179&available_to_book%5Bfilter%5D=Available+in+lottery%2C336",
            "html_element_type": "div",
            "html_element_class": "residence_block",
        }
    }

    # Should be changed to the actual searchers
    searchers = [{
        "email": "test@test.com",
        "location": "Nijmegen",
        "price": 900
    },
        {
            "email": "test2@test.com",
            "location": "Nijmegen",
            "price": 500
        },
    ]

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("start-maximized")
    options.add_argument("disable-infobars")
    options.add_argument("--disable-extensions")
    my_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36"
    options.add_argument(f"user-agent={my_user_agent}")

    service = Service(ChromeDriverManager().install())  # This will download the correct chromedriver version

    while True:
        houses = []

        for key, value in config.items():
            try:
                print(f"Visiting website {key}, {value['url']}")
                driver = webdriver.Chrome(options=options)
                # driver = webdriver.Chrome(service=service, options=options)
                driver.get(value['url'])
                if key == 'holland2stay':
                    time.sleep(5)
                else:
                    time.sleep(1)
                html_resp = driver.page_source
                driver.quit()
                # response = requests.get(value['url'])
                soup = BeautifulSoup(html_resp, 'html.parser')
                houses += parse_html_of_houses(soup, key, value['html_element_type'], value['html_element_class'])
            except Exception as e:
                print(f"Trying to visit website {key}. But got an error: ", e)


        for searcher in searchers:
            filter_per_person(houses, searcher['location'], searcher['price'], searcher['email'], old_houses)

        old_houses = list(set(houses))
        print(old_houses)

        with open('old_houses.pkl', 'wb') as f:
            pickle.dump(old_houses, f)

        time.sleep(300 + random.randint(0, 100))


if __name__ == "__main__":
    main()
