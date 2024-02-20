import os
import random
import smtplib, ssl
import requests
from bs4 import BeautifulSoup
import time
from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

load_dotenv()

def send_email(houses):

    port = 465  # For SSL

    # Create a secure SSL context
    context = ssl.create_default_context()

    email = os.getenv('GMAIL_USERNAME')
    password = os.getenv('GMAIL_PASS')
    receiver = os.getenv('RECEIVER_EMAIL')

    message = MIMEMultipart("alternative")
    message["Subject"] = "Nieuwe kamers!"
    message["From"] = email
    message["To"] = receiver

    text = "Nieuwe huizen gevonden! \n\n" + "\n".join(
        list(map(lambda h: f"{h['title']} - {h['price']} euro <br> <img src='{h['image']}'>- {h['type']} \n <a href='{h['link']}'>Link</a> ", houses)))
    plain = MIMEText(text, "html")

    message.attach(plain)

    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(email, password)
        server.sendmail(email, receiver, message.as_string())

def extract_houses(soup):
    houses = []
    for house in soup.find_all('div', class_='woning'):
        title = house.find('p').text
        full = False
        if title == 'Bezichtiging vol / Viewing list full' or 'Verhuurd / Rented out':
            title = house.find_next('p').find_next('p').text
            full = True
        price = house.find('div', class_='gb-container').find_all('p')[1].text

        sep = house.find('hr')
        image = house.find('img')['src']
        type = sep.find_next('p').text
        location = sep.find_next('p').find_next('p').text
        link = house.find('a')['href']
        houses.append({
            'title': title,
            'price': price,
            'type': type,
            'image': image,
            'location': location,
            'link': link,
            'full': full
        })
    return houses



def main():
    old_houses = {}

    while(True):
        url = "https://kbsvastgoedbeheer.nl/aanbod/"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        houses = extract_houses(soup)

        houses = list(filter(lambda x: not x['full'] and 'Nijmegen' in x['location'] and float(x['price']) < 900, houses))
        print(houses)

        houses_ready_to_email = []

        for house in houses:
            if not (house['link'] in old_houses):
                print("Not in!")
                houses_ready_to_email.append(house)
                old_houses[house['link']] = house

        if len(houses_ready_to_email) > 0:
            send_email(houses_ready_to_email)

        print(old_houses)

        time.sleep(300 + random.randint(0, 100))


if __name__ == "__main__":
    main()
