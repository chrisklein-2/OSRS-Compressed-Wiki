from playwright.async_api import async_playwright
from bs4 import BeautifulSoup


async def scrape_osrs_item_drops(item_name):

    url = f"https://oldschool.runescape.wiki/w/{item_name.replace(' ', '_')}"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        response = await page.goto(url, wait_until="domcontentloaded")

        # if no response or status is not 200, return message
        # aka if the page doesn't exist
        if not response or response.status != 200:
            await browser.close()
            return f"No drop table found for '{item_name}'.\n\n"

        try:
            await page.wait_for_selector("table.wikitable th:has-text('Source')", timeout=5000)
        except:
            await browser.close()
            return f"No drop table found for '{item_name}'.\n\n"

        # get page content
        html = await page.content()
        soup = BeautifulSoup(html, "lxml")

        drop_table = None

        # find the drop table with "Source" header
        # aka the table that contains the drop data
        for table in soup.find_all("table", class_="wikitable"):
            headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
            if "source" in headers:
                drop_table = table
                break

        # if no drop table found, return message
        if not drop_table:
            await browser.close()
            return f"No drop table found for '{item_name}'.\n\n"


        rows = drop_table.find_all("tr")[1:]

        # if no rows found, return message
        if not rows:
            await browser.close()
            return f"No drop data rows found for '{item_name}'.\n\n"


        # get corrected item name from page title
        page_title = await page.title()
        corrected_name = page_title.split(" - ")[0]
        results_found = [ f"{corrected_name} droped by:\n"]
        
        # extract monster names, quantities, and rarities along with links
        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 3:
                monster_link = cells[0].find("a")
                link = monster_link['href'][3:]
                link = f"https://oldschool.runescape.wiki/w/{link}"
                monster = monster_link.get_text(" ", strip=True) if monster_link else cells[0].get_text(" ", strip=True)
                quantity = cells[2].get_text(strip=True)                
                rarity = cells[3].get_text(strip=True)
                results_found.append(f"- {monster} — Qty: {quantity} — Drop rate: {rarity} --- {link}")
        results_found.append("\n")
        await browser.close()
        return "\n".join(results_found)
