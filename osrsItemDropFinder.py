import asyncio
import tkinter as tk
from tkinter import scrolledtext
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def scrape_osrs_item_drops(item_name, output_widget):

    url = f"https://oldschool.runescape.wiki/w/{item_name.replace(' ', '_')}"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto(url, wait_until="domcontentloaded")
        response = await page.goto(url, wait_until="domcontentloaded")

        if not response or response.status != 200:
            append_output(f"No drop table found for '{item_name}'.\n\n")
            await browser.close()
            return
        try:
            await page.wait_for_selector("table.wikitable th:has-text('Source')", timeout=5000)
        except:
            append_output(f"No drop table found for '{item_name}'.\n\n")
            await browser.close()
            return

        html = await page.content()

        soup = BeautifulSoup(html, "lxml")

        drop_table = None
        for table in soup.find_all("table", class_="wikitable"):
            headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
            if "source" in headers:
                drop_table = table
                break

        if not drop_table:
            append_output(f"No drop table found for '{item_name}'.\n\n")
            await browser.close()
            return

        rows = drop_table.find_all("tr")[1:]
        if not rows:
            append_output(f"No drop data rows found for '{item_name}'.\n\n")
            await browser.close()
            return

        # get corrected item name from page title
        page_title = await page.title()
        corrected_name = page_title.split(" - ")[0]
        append_output( f"{corrected_name} droped by:\n")

        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 3:
                monster_link = cells[0].find("a")
                monster = monster_link.get_text(" ", strip=True) if monster_link else cells[0].get_text(" ", strip=True)
                quantity = cells[2].get_text(strip=True)                
                rarity = cells[3].get_text(strip=True)
                append_output(f"- {monster} — Qty: {quantity} — Rarity: {rarity}\n")
        append_output("\n")
        await browser.close()

def run_async_task(coroutine):
    asyncio.create_task(coroutine)

def start_scrape():
    item_name = entry.get()
    output_text.delete(1.0, tk.END)
    item_name  = ''.join(ch for ch in item_name if ch.isalpha() or ch == " ")
    # schedule the coroutine on the running event loop
    asyncio.create_task(scrape_osrs_item_drops(item_name, output_text))
    entry.delete(0, tk.END) 

background_color = "#1e1e1e"
entry_background_color = "#333333"
# setup Tkinter
root = tk.Tk()
root.title("OSRS Item Drop Scraper")
should_exit = False
root.configure(bg=background_color)

# handle window close event
def on_close():
    global should_exit
    should_exit = True
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)

tk.Label(root, text="Enter OSRS item name:",bg=background_color,   
                 fg="white",      
                 font=("Segoe UI", 12, "bold")).pack(pady=5)
entry = tk.Entry(root, width=50)
entry.pack(pady=5)
entry.focus()
entry.configure(bg=entry_background_color, fg="white", insertbackground="white", font=("Segoe UI", 11))

# pressing Enter triggers scrape
entry.bind("<Return>", lambda event: start_scrape())  

output_text = scrolledtext.ScrolledText(root, width=80, height=20)
output_text.pack(padx=10, pady=10, expand=True, fill='both')
output_text.configure(bg="#222222", fg="white", font=("Consolas", 11))

# make read only
output_text.config(state="disabled")

def append_output(text):
    output_text.config(state="normal")
    output_text.insert(tk.END, text)
    output_text.config(state="disabled")
    output_text.see(tk.END)

scrape_button = tk.Button(root, text="Search for drops", command=start_scrape)
scrape_button.pack(pady=5)
scrape_button.configure(bg="#007acc", fg="white", font=("Segoe UI", 14, "bold"), relief="raised", bd=3)


# run asyncio event loop alongside Tkinter
async def main_loop():
    global should_exit
    try:
        while not should_exit:
            root.update()
            await asyncio.sleep(0.01)
    except tk.TclError:
        # Tkinter window closed
        pass

asyncio.run(main_loop())
