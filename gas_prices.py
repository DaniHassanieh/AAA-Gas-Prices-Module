import os
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json
from datetime import date


def get_gas_prices(element):
    place_data = {}
    # get state gas price table
    table = element.find("table", {"class": "table-mob"})
    # get fuel type row of table
    fuel_types = table.find("thead").find("tr").find_all("th")
    # get table of gas prices
    table_prices = table.find("tbody").find_all("tr")

    for i in range(len(fuel_types)):
        # skip column of time descriptions
        if fuel_types[i].text == "":
            continue

        fuel = {}

        for row_prices_element in table_prices:
            # get row
            row_prices = row_prices_element.find_all("td")
            # get time
            time = row_prices[0].text
            # get gas price at that time
            price = row_prices[i].text
            # add average fuel price at time to category
            fuel[time] = price

        # add category to place data
        place_data[fuel_types[i].text] = fuel

    return place_data


# create options and add arguments
options = Options()
# options.add_argument("--headless")
options.add_extension("./ublock.crx")
# create webdriver
driver = webdriver.Chrome(options=options)

url = "https://gasprices.aaa.com/?state="

data = {}
formatted_data = {
    "date": f"{date.today()}"
}

with open("states.json") as f:
    states_file = json.load(f)
    data.update(states_file)

    country = data["country"]
    # navigate to url
    country_abbreviation = country["abbreviation"]
    country_url = url + country_abbreviation
    driver.get(country_url)
    # get page source
    soup = BeautifulSoup(driver.page_source, features="lxml")
    # get gas prices
    country["Average Gas Prices"] = get_gas_prices(soup)
    states = {}
    formatted_data[country_abbreviation] = country

    for state in data["country"]["states"]:
        # navigate to url
        country_url = url + state["abbreviation"]
        driver.get(country_url)
        # get page source
        soup = BeautifulSoup(driver.page_source, features="lxml")
        # get gas prices
        state["Average Gas Prices"] = get_gas_prices(soup)

        # get all metropolises
        metros = soup.find_all("h3", {"id": re.compile(r"ui-id-")})
        metro_data = {}

        for metro in metros:
            new_id = metro.get("aria-controls")
            metro_popout = soup.find("div", {"id": new_id})
            # get metro data
            metro_data[metro.text] = get_gas_prices(metro_popout)

        # add metro data
        state["Metropolises"] = metro_data

        states.update({state["abbreviation"]: state})

    del formatted_data[country_abbreviation]["states"]
    country["states"] = states


# check if output directory doesn't exist
if not os.path.exists("./gas-prices-output/"):
    os.makedirs("./gas-prices-output/")

# write json file
with open(f"./gas-prices-output/gas-prices-{date.today()}.json", "w") as outfile:
    data_write = json.dumps(formatted_data, indent=4)
    outfile.write(data_write)

driver.quit()
