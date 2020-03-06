import requests
from bs4 import BeautifulSoup
from pandas import DataFrame
from selenium.webdriver import Chrome

URL = "https://www.familyeducation.com/baby-names/browse-origin/surname/indian?page="
names, genders = [], []

last_names = []
for i in range(1, 6):
    resp = requests.get(URL + str(i))
    soup = BeautifulSoup(resp.content, features='html.parser')
    ul_names = soup.find("ul", attrs={'class': "baby-names-list"})
    for x in ul_names.find_all("li"):
        if x.text:
            last_names.append(x.text.lower().strip())
