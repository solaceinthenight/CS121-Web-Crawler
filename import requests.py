import requests
from bs4 import BeautifulSoup

url = "https://www.informatics.uci.edu/"

# Make a request to the webpage
response = requests.get(url)

# Parse the HTML content using BeautifulSoup
soup = BeautifulSoup(response.content, "html.parser")

# Find all the anchor tags on the page
links = soup.find_all("a")

# Print all the links
for link in links:
  print(link.get("href"))
