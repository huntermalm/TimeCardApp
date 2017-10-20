from urllib.request import urlopen as uReq
from bs4 import BeautifulSoup as soup


def get_latest_version(project_url):
    if project_url[-1] == "/":
        project_url = project_url[0:-1]

    latest_release_url = f"{project_url}/releases/latest"

    uClient = uReq(latest_release_url)
    page_html = uClient.read()
    uClient.close()

    page_soup = soup(page_html, "html.parser")

    header = page_soup.findAll("div", {"class": "release-header"})[0]

    return header.h1.a.contents[0]
