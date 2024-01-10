import argparse
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup


def get_gas_prices(element, place):
    data = ""
    # go to first table
    table = element.find("table", {"class": "table-mob"})
    # head row of table
    head = table.find("thead").find("tr")
    # first row with data
    row = table.find("tbody").find("tr")
    # head columns
    col_headers = head.find_all("th")
    # data columns
    cols = row.find_all("td")

    # make output
    for i in range(len(cols)):
        if i != 0:
            data += col_headers[i].text + ": "
        data += cols[i].text
        if i == 0:
            data += f" in {place}"
        data += "\n"

    return data


STATES = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA",
          "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
          "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
          "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
          "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]

# gas price average taken from how long ago
TIMES = ["current", "yesterday", "week", "month", "year"]

# parse command line arguments
parser = argparse.ArgumentParser(description="Gas Prices.")
parser.add_argument("--state", default="US", metavar="",
                    help="State Abbreviation | Example Input: TX | (US is default with no flag)")
group = parser.add_mutually_exclusive_group()
group.add_argument("--metro", metavar="",
                   help="Metro | Example Input: Dallas | Example Input: \"San Antonio\" | (Cannot be used if for US)")
group.add_argument("--list", action="store_true", help="List metropolises in state. If US, then lists states")
args = parser.parse_args()

# if state abbreviation does not exist, exit program. if states are being listed, list states and exit program
if args.state not in STATES and args.state != "US":
    exit("Incorrect. This program died and the blood is on your hands.")
elif args.list and args.state == "US":
    exit(STATES)

# set up driver
options = Options()
# options.add_argument("--headless")
options.add_extension("./ublock.crx")
driver = webdriver.Chrome(options=options)

# navigate to url
url = "https://gasprices.aaa.com/?state=" + args.state
driver.get(url)

# get page source
source = driver.page_source

# soup instance created
soup = BeautifulSoup(source, features="lxml")

output = ""

if args.metro is None and not args.list:  # case that state or country gas prices are requested
    output += get_gas_prices(soup, args.state)

elif args.metro is None and args.list:  # case that list of metros is being requested
    # make list of metros for state
    pattern = re.compile(r"ui-id-")
    results = soup.find_all("h3", {"id": pattern})
    output += f"Metropolises in {args.state}:\n"
    for metro in results:
        output += metro.text + "\n"

elif args.metro is not None:  # case that gas prices in metro is being requested
    pattern = re.compile(r"ui-id-")
    metros = soup.find_all("h3", {"id": pattern})
    metro_found = False
    for metro in metros:
        if metro.text == args.metro:
            metro_found = True
            new_id = metro.get("aria-controls")
            metro_popout = soup.find("div", {"id": new_id})
            output += get_gas_prices(metro_popout, args.metro)
            break
    if not metro_found:
        driver.close()
        exit(f"{args.metro} isn't a metro :c")

# if last character newline, print without newline
if output == "":
    pass
elif output[-1] == "\n":
    print(output[0:-1])
else:
    print(output)

driver.close()
