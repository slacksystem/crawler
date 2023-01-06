from http.client import HTTPResponse
from http.cookiejar import CookieJar
from time import sleep
import mechanize
from typing import Iterable, List, Optional, Union
import logging
from rich.logging import RichHandler
from rich import print


logging.basicConfig(
    level="NOTSET",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, markup=True)],
)

logger = logging.getLogger("rich")

blacklisted_links: List[str] = []

domain: str = "creationkit.com"


def link_to_ignore(link: mechanize.Link) -> bool:
    bad_text: List[str] = ["login", "log in", "sign up"]

    bad_text = list(map(str.casefold, bad_text))
    if link.text.casefold() in bad_text:
        return True
    if domain.casefold() not in link.url.casefold():
        return True
    return False


def crawl_website(url, visited_urls: Optional[List[str]] = None) -> List[str]:
    """
    Crawls a website for all links

    :param url: The url to start crawling from
    :param visited_urls: A list of urls that have already been crawled
    :return: A list of all links found on the website
    """
    # Create a browser instance
    br: mechanize.Browser = mechanize.Browser()
    cj = CookieJar()
    br.set_handle_robots(False)
    br.set_cookiejar(cj)
    br.set_handle_equiv(True)
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

    # Set the user agent
    br.addheaders = [
        (
            "User-agent",
            "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; InfoPath.3; AskTB5.6)",
        ),
        ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
        ("Accept-Charset", "ISO-8859-1,utf-8;q=0.7,*;q=0.3"),
        ("Accept-Encoding", "none"),
        ("Accept-Language", "en-US,en;q=0.8"),
        ("Connection", "keep-alive"),
    ]

    # Initialize visited_urls if not present
    if visited_urls is None:
        visited_urls = []

    # Navigate to the starting URL
    try:
        br.open(url)
    except mechanize.HTTPError as error:
        # If an HTTPError occurs, then we will not follow the link
        logger.error(
            f"Failed to follow link {url}. " f"Error {error.getcode()}: {error.info()}"
        )

    # Crawl the website
    # View the HTML source of the page
    html = br.response().read()  # type: ignore

    links: Iterable[mechanize.Link] = br.links()
    # Find all the links on the page
    for link in links:
        response: Union[HTTPResponse, None] = None
        sleep(1)
        new_url = link.absolute_url
        # Check if the link has been visited
        if new_url not in visited_urls and not link_to_ignore(link):
            # Check if the link is standard format
            if not link.url.casefold().startswith("http".casefold()):
                continue
            # Try to follow the link
            logger.info(f"Found link [blue]{new_url}[/] with text [yellow]{link.text}")
            try:
                response = br.follow_link(link)  # type: ignore
            except mechanize.HTTPError as error:
                # If an HTTPError occurs, then we will not follow the link

                logger.error(
                    f"Failed to follow link {new_url}. "
                    f"Error {error.getcode()}: {error.info()}"
                )
                continue
            if response:
                content_type = response.info()["Content-Type"]
                logger.info(f"Content type is {content_type}")

                if "text/html".casefold() not in content_type.casefold():
                    br.back()
                    continue
            logger.debug(f"Followed link {new_url}")
            logger.debug(f"br.geturl() is {br.geturl()}")
            # Recursively crawl the new page
            # Add the new URL to the list of visited URLs
            visited_urls.append(new_url)
            visited_urls.extend(crawl_website(new_url, visited_urls))
    return visited_urls


# Start crawling the website at the specified URL
links: List[str] = crawl_website(
    "https://www.creationkit.com/index.php?title=Main_Page"
)
print(links)
