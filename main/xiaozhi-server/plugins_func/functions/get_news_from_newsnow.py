import random
import httpx
from io import BytesIO
from markitdown import MarkItDown, StreamInfo
from config.logger import setup_logging
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler


TAG = __name__
logger = setup_logging()

CHANNEL_MAP = {
    "V2EX": "v2ex-share",
    "Zhihu": "zhihu",
    "Weibo": "weibo",
    "Lianhe Zaobao": "zaobao",
    "Coolapk": "coolapk",
    "MKTNews": "mktnews-flash",
    "Wallstreetcn": "wallstreetcn-quick",
    "36Kr": "36kr-quick",
    "Douyin": "douyin",
    "Hupu": "hupu",
    "Baidu Tieba": "tieba",
    "Toutiao": "toutiao",
    "ITHome": "ithome",
    "The Paper": "thepaper",
    "Sputnik": "sputniknewscn",
    "Cankaoxiaoxi": "cankaoxiaoxi",
    "PCbeta": "pcbeta-windows11",
    "CLS": "cls-depth",
    "Xueqiu": "xueqiu-hotstock",
    "Gelonghui": "gelonghui",
    "FastBull": "fastbull-express",
    "Solidot": "solidot",
    "Hacker News": "hackernews",
    "Product Hunt": "producthunt",
    "Github": "github-trending-today",
    "Bilibili": "bilibili-hot-search",
    "Kuaishou": "kuaishou",
    "Kaopu News": "kaopu",
    "Jin10": "jin10",
    "Baidu Hot Search": "baidu",
    "Nowcoder": "nowcoder",
    "SSPAI": "sspai",
    "Juejin": "juejin",
    "ifeng": "ifeng",
    "Chongbuluo": "chongbuluo-latest",
}

# Default news source dictionary, used when the config does not specify one
DEFAULT_NEWS_SOURCES = "The Paper;Baidu Hot Search;CLS"

def _get_newsnow_config(conn):
    # Get from the connection config
    plugins = conn.config.get("plugins", {})
    newsnow = plugins.get("get_news_from_newsnow", {})
    sources = newsnow.get("news_sources", "")
    if isinstance(sources, str) and sources.strip():
        return sources

    return ""

def get_news_sources_from_config(conn):
    """Get the news sources string from the config"""
    try:
        result = _get_newsnow_config(conn)
        if result:
            logger.bind(tag=TAG).debug(f"Using the configured news sources: {result}")
            return result

        logger.bind(tag=TAG).debug("No news source config found; using the default config")
        return DEFAULT_NEWS_SOURCES

    except Exception as e:
        logger.bind(tag=TAG).error(f"Failed to get the news source config: {e}; using the default config")
        return DEFAULT_NEWS_SOURCES


# Get the available news source names from the default config (dynamically fetched at runtime by get_news_sources_from_config)
example_sources_str = DEFAULT_NEWS_SOURCES.replace(";", ", ")

GET_NEWS_FROM_NEWSNOW_FUNCTION_DESC = {
    "type": "function",
    "function": {
        "name": "get_news_from_newsnow",
        "description": "Call when the user asks to view or listen to news (e.g. 'give me a news item', 'what's in the news today').",
        "parameters": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": f"The standard name of the news source, for example {example_sources_str}, etc. Optional; the default news source is used if not provided",
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


async def fetch_news_from_api(conn: "ConnectionHandler", source="thepaper"):
    """Get the news list from the API"""
    try:
        api_url = f"https://newsnow.busiyi.world/api/s?id={source}"

        news_config = conn.config.get("plugins", {}).get("get_news_from_newsnow", {})
        if news_config.get("url"):
            api_url = news_config["url"] + source

        headers = {"User-Agent": "Mozilla/5.0"}
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=3.0)) as client:
            response = await client.get(api_url, headers=headers)

        data = response.json()

        if "items" in data:
            return data["items"]
        else:
            logger.bind(tag=TAG).error(f"Invalid news API response format: {data}")
            return []

    except Exception as e:
        logger.bind(tag=TAG).error(f"Failed to call the news API: {e}")
        return []


async def fetch_news_detail(url):
    """Get the news detail page content and clean the HTML with MarkItDown"""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=3.0)) as client:
            response = await client.get(url, headers=headers)

        # Clean the HTML content with MarkItDown
        md = MarkItDown(enable_plugins=False)
        result = md.convert_stream(
            BytesIO(response.content),
            stream_info=StreamInfo(
                mimetype="text/html",
                extension=".html",
                charset=response.encoding or "utf-8",
            ),
        )

        # Get the cleaned text content
        clean_text = result.text_content

        # If the cleaned content is empty, return a hint message
        if not clean_text or len(clean_text.strip()) == 0:
            logger.bind(tag=TAG).warning(f"Cleaned news content is empty: {url}")
            return "Unable to parse the news detail content; the site structure may be unusual or the content may be restricted."

        return clean_text
    except Exception as e:
        logger.bind(tag=TAG).error(f"Failed to get news details: {e}")
        return "Unable to get detailed content"


@register_function(
    "get_news_from_newsnow",
    GET_NEWS_FROM_NEWSNOW_FUNCTION_DESC,
    ToolType.SYSTEM_CTL,
)
async def get_news_from_newsnow(
    conn: "ConnectionHandler",
    source: str = "The Paper",
    detail: bool = False,
    lang: str = "zh_CN",
):
    """Get the news and randomly select one item to read, or get the details of the previous news item"""
    try:
        # Get the currently configured news sources
        news_sources = get_news_sources_from_config(conn)

        # If detail is True, get the detailed content of the previous news item
        detail = str(detail).lower() == "true"
        if detail:
            if (
                not hasattr(conn, "last_newsnow_link")
                or not conn.last_newsnow_link
                or "url" not in conn.last_newsnow_link
            ):
                return ActionResponse(
                    Action.REQLLM,
                    "Sorry, no recently queried news was found. Please get a news item first.",
                    None,
                )

            url = conn.last_newsnow_link.get("url")
            title = conn.last_newsnow_link.get("title", "Unknown title")
            source_id = conn.last_newsnow_link.get("source_id", "thepaper")
            source_name = CHANNEL_MAP.get(source_id, "Unknown source")

            if not url or url == "#":
                return ActionResponse(
                    Action.REQLLM, "Sorry, this news item has no available link for detailed content.", None
                )

            logger.bind(tag=TAG).debug(
                f"Getting news details: {title}, source: {source_name}, URL={url}"
            )

            # Get the news details
            detail_content = await fetch_news_detail(url)

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
                # f"News source: {source_name}\n"
                f"Detailed content: {detail_content}\n\n"
                f"(Summarize the news content above, extract the key information, and read it to the user in a natural, fluent way; "
                f"do not mention that it is a summary, just tell it like a complete news story)"
            )

            return ActionResponse(Action.REQLLM, detail_report, None)

        # Otherwise, get the news list and randomly select one item
        # Convert the name to the English ID
        english_source_id = None

        # Check whether the input name is among the configured news sources
        news_sources_list = [
            name.strip() for name in news_sources.split(";") if name.strip()
        ]
        if source in news_sources_list:
            # If the input name is among the configured news sources, look up its English ID in CHANNEL_MAP
            english_source_id = CHANNEL_MAP.get(source)

        # If no matching English ID is found, use the default source
        if not english_source_id:
            logger.bind(tag=TAG).warning(f"Invalid news source: {source}; using the default source The Paper")
            english_source_id = "thepaper"
            source = "The Paper"

        logger.bind(tag=TAG).info(f"Getting news: source={source}({english_source_id})")

        # Get the news list
        news_items = await fetch_news_from_api(conn, english_source_id)

        if not news_items:
            return ActionResponse(
                Action.REQLLM,
                f"Sorry, unable to fetch news information from {source}. Please try again later or try another news source.",
                None,
            )

        # Randomly select one news item
        selected_news = random.choice(news_items)

        # Save the current news link on the connection object for later detail queries
        if not hasattr(conn, "last_newsnow_link"):
            conn.last_newsnow_link = {}
        conn.last_newsnow_link = {
            "url": selected_news.get("url", "#"),
            "title": selected_news.get("title", "Unknown title"),
            "source_id": english_source_id,
        }

        # Build the news report
        news_report = (
            f"Respond to the user's news query in {lang} based on the following data:\n\n"
            f"News title: {selected_news['title']}\n"
            # f"News source: {source}\n"
            f"(Read this news title to the user in a natural, fluent way, "
            f"and tell the user they can ask for the detailed content, which will fetch the news details.)"
        )

        return ActionResponse(Action.REQLLM, news_report, None)

    except Exception as e:
        logger.bind(tag=TAG).error(f"Error getting news: {e}")
        return ActionResponse(
            Action.REQLLM, "Sorry, an error occurred while getting the news. Please try again later.", None
        )
