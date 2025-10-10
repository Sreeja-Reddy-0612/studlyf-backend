import asyncio
from playwright.async_api import async_playwright
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import AITool, Base

DB_FILE = "ai_tools.db"  # SQLite DB file


async def safe_goto(page, url, retries=3, delay=2):
    """Navigate to a page with retries"""
    for attempt in range(retries):
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            return True
        except Exception as e:
            print(f"⚠️ Attempt {attempt+1} failed for {url}: {e}")
            await asyncio.sleep(delay)
    return False


async def scrape_theresanaiforthat():
    url = "https://theresanaiforthat.com/ai-tools"
    print(f"🌐 Opening {url}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # set True for headless
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/117.0 Safari/537.36"
            )
        )
        page = await context.new_page()

        # Load main page
        if not await safe_goto(page, url, retries=3):
            print("⚠️ Failed to load main page. Exiting.")
            await browser.close()
            return
        print("✅ Page loaded successfully")

        # Scroll to load all tools
        print("🔄 Scrolling to load all tools...")
        max_scroll_attempts = 50
        scroll_count = 0
        previous_height = 0

        while scroll_count < max_scroll_attempts:
            current_height = await page.evaluate("document.body.scrollHeight")
            if current_height == previous_height:
                break
            previous_height = current_height
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)
            scroll_count += 1
        print("✅ Page fully scrolled")

        # Wait for tool cards
        await page.wait_for_selector("a.ai_link.new_tab", timeout=60000)
        tool_cards = await page.query_selector_all("div.li_right")
        print(f"✅ Found {len(tool_cards)} AI tools")

        tools_data = []

        # Loop through each tool card
        for idx, card in enumerate(tool_cards, 1):
            try:
                name_el = await card.query_selector("a.ai_link.new_tab span")
                name = await name_el.inner_text() if name_el else "Unknown"

                internal_link_el = await card.query_selector("a.ai_link.new_tab")
                internal_link = await internal_link_el.get_attribute("href") if internal_link_el else None
                if internal_link and not internal_link.startswith("http"):
                    internal_link = f"https://theresanaiforthat.com{internal_link}"

                # 🔍 Extract "Use Tool" button (the direct external URL)
                external_link = None
                if internal_link:
                    try:
                        async with context.new_page() as tool_page:
                            if await safe_goto(tool_page, internal_link):
                                try:
                                    await tool_page.wait_for_selector("a#ai_top_link", timeout=5000)
                                    external_el = await tool_page.query_selector("a#ai_top_link")
                                    external_link = await external_el.get_attribute("href") if external_el else None
                                except Exception:
                                    pass
                    except Exception as e:
                        print(f"⚠️ Failed to open internal link {internal_link}: {e}")

                website_url = external_link or internal_link

                desc_el = await card.query_selector("div.short_desc")
                description = await desc_el.inner_text() if desc_el else "No description"

                cat_el = await card.query_selector("a.task_label")
                category = await cat_el.inner_text() if cat_el else "Uncategorized"

                tools_data.append({
                    "name": name.strip(),
                    "website_url": website_url,
                    "source_url": internal_link,
                    "short_description": description.strip(),
                    "tags": [category.strip()],
                })

                print(f"✅ Parsed tool {idx}: {name}")

            except Exception as e:
                print(f"⚠️ Error parsing tool {idx}: {e}")
                continue

        print(f"💾 Extracted {len(tools_data)} tools")

        # Save to database
        engine = create_engine(f"sqlite:///{DB_FILE}")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        new_count = 0
        for t in tools_data:
            if not session.query(AITool).filter_by(name=t["name"]).first():
                tool = AITool(**t)
                session.add(tool)
                new_count += 1

        session.commit()
        session.close()
        print(f"✅ Stored {new_count} new tools into {DB_FILE}!")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(scrape_theresanaiforthat())
