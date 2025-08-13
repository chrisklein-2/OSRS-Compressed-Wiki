from playwright.async_api import async_playwright
from bs4 import BeautifulSoup


async def scrape_osrs_mob_location(mob_name):

    url = f"https://oldschool.runescape.wiki/w/{mob_name.replace(' ', '_')}"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        response = await page.goto(url, wait_until="domcontentloaded")

        # if no response or status is not 200, return message
        # aka if the page doesn't exist
        if not response or response.status != 200:
            await browser.close()
            return f"No locations found for '{mob_name}'.\n\n"

        try:
            await page.wait_for_selector("table.wikitable th:has-text('Location')", timeout=5000)
        except:
            await browser.close()
            return f"No locations found for '{mob_name}'.\n\n"

        # get page content
        html = await page.content()
        soup = BeautifulSoup(html, "lxml")

        locations = None

        # find the drop table with "Source" header
        for table in soup.find_all("table", class_="wikitable"):
            headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
            if "location" in headers and "levels" in headers:
                locations = table
                break

        # if no drop table found, return message
        if not locations:
            await browser.close()
            return f"No locations found for '{mob_name}'.\n\n"


        rows = locations.find_all("tr")[1:]

        # if no rows found, return message
        if not rows:
            await browser.close()
            return f"No locations found for '{mob_name}'.\n\n"

        # get corrected item name from page title
        page_title = await page.title()
        corrected_name = page_title.split(" - ")[0]
        results_found = [ f"Locations for {corrected_name}:\n"]

        # extract location names, levels, and number of spawns along with links
        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 3:
                monster_link = cells[0].find("a")
                link = monster_link['href'][3:]
                link = f"https://oldschool.runescape.wiki/w/{link}"
                location = monster_link.get_text(" ", strip=True) if monster_link else cells[0].get_text(" ", strip=True)
                levels = cells[1].get_text(strip=True)                
                spawns = cells[3].get_text(strip=True)
                results_found.append(f"- {location} — Levels: {levels} — Number of Spaws: {spawns} --- {link}")
        results_found.append("\n")
        await browser.close()
        return "\n".join(results_found)