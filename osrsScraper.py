from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def scrape_osrs_item_drops(item_name: str, browser, page):
    # Format the URL for the OSRS Wiki item page
    url = f"https://oldschool.runescape.wiki/w/{item_name.replace(' ', '_')}"
    

    # Go to the page and wait until DOM content loaded (faster than full load)
    page.goto(url, wait_until="domcontentloaded", timeout=60000)

    # Get the page title (browser tab title)
    page_title = page.title()

    try:
        # Wait specifically for the "Dropped by" table header to show up (max 15s)
        page.wait_for_selector("table.wikitable th:has-text('Source')", timeout=15000)
    except:
        print(f"No drop table found for '{item_name}'.")
        browser.close()
        return

    item_name = page_title.split(" - ")[0]

    # Get the fully rendered page HTML including JS-generated content
    html = page.content()

    # Use BeautifulSoup to parse the HTML
    soup = BeautifulSoup(html, "lxml")

    # Find the drop table (the first wikitable containing 'Source' column)
    drop_table = None
    for table in soup.find_all("table", class_="wikitable"):
        header_cells = table.find_all("th")
        headers = [th.get_text(strip=True).lower() for th in header_cells]
        if "source" in headers:
            drop_table = table
            break
    
    if not drop_table:
        print(f"No drop table found for '{item_name}'.")
        browser.close()
        return

    # Process each row (skip header)
    rows = drop_table.find_all("tr")[1:]
    if not rows:
        print(f"No drop data rows found for '{item_name}'.")
        browser.close()
        return

    print(f"Monsters that drop '{item_name}':")
    for row in rows:
        cells = row.find_all("td")
        if len(cells) >= 3:
            # Extract monster name (text of first <a> tag or cell text)
            monster_link = cells[0].find("a")
            monster = monster_link.get_text(" ", strip=True) if monster_link else cells[0].get_text(" ", strip=True)
            
            # Quantity - clean text, digits or '-'
            quantity = ''.join(ch for ch in cells[2].get_text(strip=True) if ch.isdigit() or ch == '-')
            
            # Rarity - text
            rarity = cells[3].get_text(strip=True)

            print(f"- {monster} — Qty: {quantity} — Rarity: {rarity}")



def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print("Welcome to the OSRS Item Drop Scraper!\nPress Ctrl+C to exit at any time.\n")
        try:
            while True:
                item_to_search = input("Enter OSRS item name: ")
                if item_to_search == "exit":
                    print("Exiting... Goodbye!")
                    break
                scrape_osrs_item_drops(item_to_search, browser, page)


        except KeyboardInterrupt:
            print("\nExiting... Goodbye!")

# Example usage:
if __name__ == "__main__":
   main()