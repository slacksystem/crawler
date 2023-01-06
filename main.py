from http.client import HTTPResponse
from http.cookiejar import CookieJar
import os
import random
from time import sleep
import mechanize
from typing import Iterable, List, Optional, Union
import logging
import logging.handlers
from rich import print
from rich.logging import RichHandler
from rich.traceback import install

mechanize.UserAgentBase

install(show_locals=True, word_wrap=True, width=180)

file_handler = logging.handlers.RotatingFileHandler("Logs/log.txt")
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[
        file_handler,
        RichHandler(
            rich_tracebacks=True,
            markup=True,
            tracebacks_show_locals=True,
            tracebacks_width=180,
        ),
    ],
)

need_roll = os.path.isfile("./Logs/log.txt")

link_delay = 2

logger = logging.getLogger()

blacklisted_links: List[str] = []

domain: str = "creationkit.com"


def link_to_ignore(link: mechanize.Link) -> bool:
    bad_text: List[str] = ["login", "log in", "sign up", "page does not exist"]
    bad_urls: List[str] = [
        "oldid",
        "fallout4",
        "user_talk",
        "filehistory",
        "#",
        "action=edit",
    ]

    bad_text = list(map(str.casefold, bad_text))
    bad_urls = list(map(str.casefold, bad_urls))

    link_url = link.absolute_url
    if bads := [
        bad_string for bad_string in bad_text if bad_string in link.text.casefold()
    ]:
        logger.info(f"Ignoring link {link_url} because of bad text: {bads[0]}")
        return True
    if badu := [bad_url for bad_url in bad_urls if bad_url in link_url.casefold()]:
        logger.info(f"Ignoring link {link_url} because it contains {badu[0]}")
        return True
    if domain.casefold() not in link_url.casefold():
        logger.info(f"Ignoring link {link_url} because it is not in {domain}")

        return True
    return False


def crawl_website(
    url, visited_urls: List[str], br: mechanize.Browser, cj: CookieJar
) -> List[str]:
    """
    Crawls a website for all links

    :param url: The url to start crawling from
    :param visited_urls: A list of urls that have already been crawled
    :param br: The browser object to use
    :param cj: The cookie jar to use
    :return: A list of all links found on the website
    """

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
        sleep(link_delay + random.uniform(0, 2))
        logger.debug(
            f"{link.absolute_url=} and {visited_urls=} and {link_to_ignore(link)=}"
        )
        # Check if the link has been visited
        if link.absolute_url not in visited_urls and not link_to_ignore(link):
            # Try to follow the link
            logger.info(
                f"Found link [blue]{link.absolute_url}[/] with text [yellow]{link.text}"
            )
            try:
                response = br.follow_link(link)  # type: ignore
            except mechanize.HTTPError as error:
                # If an HTTPError occurs, then we will not follow the link

                logger.error(
                    f"Failed to follow link {link.absolute_url}. "
                    f"Error {error.getcode()}: {error.info()}"
                )
                continue
            if response:
                content_type = response.info()["Content-Type"]
                logger.info(f"Content type is {content_type}")

                if "text/html".casefold() not in content_type.casefold():
                    br.back()
                    continue
            logger.debug(f"br.geturl() is {br.geturl()}")
            # Recursively crawl the new page
            # Add the new URL to the list of visited URLs
            visited_urls.append(link.absolute_url)
            visited_urls = crawl_website(link.absolute_url, visited_urls, br, cj)

    logger.info(f"Returning to previous page {br._history._history[-1]}")  # type: ignore
    br.back()
    return visited_urls


def main():
    # Create the browser object and configure it
    # The browser object is used to navigate the web pages
    # The browser object is configured to follow links
    br = mechanize.Browser()
    cj = CookieJar()

    br.set_handle_robots(False)
    br.set_cookiejar(cj)
    # br.set_handle_equiv(True)
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    br.set_seekable_responses(False)
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
    # Start crawling the website at the specified URL
    br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)  # type: ignore
    links: List[str] = crawl_website(
        "https://www.creationkit.com/index.php?title=Main_Page", [], br, cj
    )
    print(links)


if __name__ == "__main__":
    if need_roll:
        handlers = logger.handlers
        print(logger.handlers)
        logger.handlers[0].doRollover()  # type: ignore
    main()
