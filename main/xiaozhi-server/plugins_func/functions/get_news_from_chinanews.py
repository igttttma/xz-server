import random
import httpx
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from config.logger import setup_logging
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler


TAG = __name__
logger = setup_logging()

GET_NEWS_FROM_CHINANEWS_FUNCTION_DESC = {
    "type": "function",
    "function": {
        "name": "get_news_from_chinanews",
        "description": (
            "Call when the user asks to view or listen to news (e.g. 'give me a news item', 'what's in the news today'). "
            "The user can specify a news type, such as society news, technology news, or international news. "
            "If not specified, society news is read by default."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "News category, for example society, technology, international. Optional; the default category is used if not provided",
                },
                "detail": {
                    "type": "boolean",
                    "description": "Whether to get detailed content; defaults to false. If true, gets the detailed content of the previous news item",
                },
                "lang": {
                    "type": "string",
                    "description": "The language code used by the user for the response, for example zh_CN/zh_HK/en_US/ja_JP; defaults to zh_CN",
                },
            },
            "required": ["lang"],
        },
    },
}


async def fetch_news_from_rss(rss_url):
    """Get the news list from an RSS feed"""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0, connect=3.0)) as client:
            response = await client.get(rss_url)

        # Parse the XML
        root = ET.fromstring(response.content)

        # Find all item elements (news entries)
        news_items = []
        for item in root.findall(".//item"):
            title = (
                item.find("title").text if item.find("title") is not None else "No title"
            )
            link = item.find("link").text if item.find("link") is not None else "#"
            description = (
                item.find("description").text
                if item.find("description") is not None
                else "No description"
            )
            pubDate = (
                item.find("pubDate").text
                if item.find("pubDate") is not None
                else "Unknown time"
            )

            news_items.append(
                {
                    "title": title,
                    "link": link,
                    "description": description,
                    "pubDate": pubDate,
                }
            )

        return news_items
    except Exception as e:
        logger.bind(tag=TAG).error(f"Failed to get RSS news: {e}")
        return []


async def fetch_news_detail(url):
    """Get the news detail page content and summarize it"""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=3.0)) as client:
            response = await client.get(url)

        soup = BeautifulSoup(response.content, "html.parser")

        # Try to extract the body content (the selectors here may need adjustment for the actual site structure)
        content_div = soup.select_one(
            ".content_desc, .content, article, .article-content"
        )
        if content_div:
            paragraphs = content_div.find_all("p")
            content = "\n".join(
                [p.get_text().strip() for p in paragraphs if p.get_text().strip()]
            )
            return content
        else:
            # If the specific content area is not found, try getting all paragraphs
            paragraphs = soup.find_all("p")
            content = "\n".join(
                [p.get_text().strip() for p in paragraphs if p.get_text().strip()]
            )
            return content[:2000]  # Limit the length
    except Exception as e:
        logger.bind(tag=TAG).error(f"Failed to get news details: {e}")
        return "Unable to get detailed content"


def map_category(category_text):
    """Map the category entered by the user to the category key in the config file"""
    if not category_text:
        return None

    # Category mapping dictionary; society, world and finance news are supported for now; see the config file for more types
    category_map = {
        # Society news
        "society": "society_rss_url",
        "society news": "society_rss_url",
        # World news
        "international": "world_rss_url",
        "international news": "world_rss_url",
        # Finance news
        "finance": "finance_rss_url",
        "finance news": "finance_rss_url",
        "financial": "finance_rss_url",
        "economy": "finance_rss_url",
    }

    # Convert to lowercase and strip spaces
    normalized_category = category_text.lower().strip()

    # Return the mapping result, or the original input if there is no match
    return category_map.get(normalized_category, category_text)


@register_function(
    "get_news_from_chinanews",
    GET_NEWS_FROM_CHINANEWS_FUNCTION_DESC,
    ToolType.SYSTEM_CTL,
)
async def get_news_from_chinanews(
    conn: "ConnectionHandler",
    category: str = None,
    detail: bool = False,
    lang: str = "zh_CN",
):
    """Get the news and randomly select one item to read, or get the details of the previous news item"""
    try:
        # If detail is True, get the detailed content of the previous news item
        if detail:
            if (
                not hasattr(conn, "last_news_link")
                or not conn.last_news_link
                or "link" not in conn.last_news_link
            ):
                return ActionResponse(
                    Action.REQLLM,
                    "Sorry, no recently queried news was found. Please get a news item first.",
                    None,
                )

            link = conn.last_news_link.get("link")
            title = conn.last_news_link.get("title", "Unknown title")

            if link == "#":
                return ActionResponse(
                    Action.REQLLM, "Sorry, this news item has no available link for detailed content.", None
                )

            logger.bind(tag=TAG).debug(f"Getting news details: {title}, URL={link}")

            # Get the news details
            detail_content = await fetch_news_detail(link)

            if not detail_content or detail_content == "Unable to get detailed content":
                return ActionResponse(
                    Action.REQLLM,
                    f"Sorry, unable to get the detailed content of \"{title}\". The link may have expired or the site structure may have changed.",
                    None,
                )

            # Build the detail report
            detail_report = (
                f"Respond to the user's news detail query in {lang} based on the following data:\n\n"
                f"News title: {title}\n"
                f"Detailed content: {detail_content}\n\n"
                f"(Summarize the news content above, extract the key information, and read it to the user in a natural, fluent way; "
                f"do not mention that it is a summary, just tell it like a complete news story)"
            )

            return ActionResponse(Action.REQLLM, detail_report, None)

        # Otherwise, get the news list and randomly select one item
        # Get the RSS URL from the config
        rss_config = conn.config.get("plugins", {}).get("get_news_from_chinanews", {})
        default_rss_url = rss_config.get(
            "default_rss_url", "https://www.chinanews.com.cn/rss/society.xml"
        )

        # Map the category entered by the user to the category key in the config
        mapped_category = map_category(category)

        # If a category is provided, try to get its URL from the config
        rss_url = default_rss_url
        if mapped_category and mapped_category in rss_config:
            rss_url = rss_config[mapped_category]

        logger.bind(tag=TAG).info(
            f"Getting news: original category={category}, mapped category={mapped_category}, URL={rss_url}"
        )

        # Get the news list
        news_items = await fetch_news_from_rss(rss_url)

        if not news_items:
            return ActionResponse(
                Action.REQLLM, "Sorry, unable to fetch news information. Please try again later.", None
            )

        # Randomly select one news item
        selected_news = random.choice(news_items)

        # Save the current news link on the connection object for later detail queries
        if not hasattr(conn, "last_news_link"):
            conn.last_news_link = {}
        conn.last_news_link = {
            "link": selected_news.get("link", "#"),
            "title": selected_news.get("title", "Unknown title"),
        }

        # Build the news report
        news_report = (
            f"Respond to the user's news query in {lang} based on the following data:\n\n"
            f"News title: {selected_news['title']}\n"
            f"Published at: {selected_news['pubDate']}\n"
            f"News content: {selected_news['description']}\n"
            f"(Read this news to the user in a natural, fluent way; you may summarize the content appropriately. "
            f"Just read the news directly without any extra content. "
            f"If the user asks for more details, tell the user they can say 'please introduce this news in detail' to get more content)"
        )

        return ActionResponse(Action.REQLLM, news_report, None)

    except Exception as e:
        logger.bind(tag=TAG).error(f"Error getting news: {e}")
        return ActionResponse(
            Action.REQLLM, "Sorry, an error occurred while getting the news. Please try again later.", None
        )
