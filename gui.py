import tkinter as tk
from tkinter import scrolledtext
import asyncio
import webbrowser
from PIL import Image, ImageTk
from io import BytesIO
import requests
from location_scraper import scrape_osrs_mob_location
from item_scraper import scrape_osrs_item_drops

background_color = "#332C20"
secondary_background_color = "#7A7A60"
button_color = "#007acc"

class OSRSScraperGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("OSRS Item Drop Scraper")
        self.root.configure(bg=background_color)
        self.root.geometry("1000x800")
        self.should_exit = False
        self.setup_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_widgets(self):

        self.options = ["Item Drop", "Mob Location"]
        self.scraper_choice = tk.StringVar(value=self.options[0])  
        self.dropdown = tk.OptionMenu(self.root, self.scraper_choice, *self.options, command=self.update_prompt)
        self.dropdown.config(font=("Segoe UI", 12, "bold"), bg=secondary_background_color, fg="black", 
                                    activebackground=secondary_background_color, activeforeground="black")
        self.dropdown.pack(side="top", anchor="ne", padx=10, pady=10)

        self.thumbnail_image = tk.Label(self.root, image=None, bg=background_color)

        self.prompt_label = tk.Label(self.root, text=f"Enter OSRS {self.scraper_choice.get().split()[0]}:",bg=background_color,   
                 fg="white",      
                 font=("Segoe UI", 12, "bold"))
        self.prompt_label.pack(pady=5)

        self.entry = tk.Entry(self.root, width=50)
        self.entry.pack(pady=5)
        self.entry.focus()
        self.entry.bind("<Return>", lambda event: self.start_scrape())
        self.entry.configure(bg=secondary_background_color, fg="black", insertbackground="white", font=("Choc", 11))
        
        self.searching_label = tk.Label(
            self.root, text="", fg="yellow",
            bg=background_color,
            font=("Segoe UI", 12, "italic")
        )
        self.searching_label.pack(pady=(5, 0))
        
        self.output_text = scrolledtext.ScrolledText(self.root, width=80, height=20)
        self.output_text.pack(padx=25, pady=10, expand=True, fill='both')
        self.output_text.config(state="disabled")
        self.output_text.configure(bg=secondary_background_color, fg="white", font=("Choc", 11))
        
        self.scrape_button = tk.Button(self.root, text="Search Drops", command=self.start_scrape)
        self.scrape_button.pack(pady=5)
        self.scrape_button.configure(bg=button_color, fg="white", font=("Segoe UI", 14, "bold"), relief="raised", bd=3)

    def update_prompt(self, *args):
        self.prompt_label.config(text=f"Enter OSRS {self.scraper_choice.get().split()[0]}:")

    def open_link(self, url):
        webbrowser.open(url)

    def insert_link(self, length ,url, index):
        
        # 4 is number of spaces in "    Click me"
        start_index = length + 4
        self.append_output("    Click me\n")
        end_index = length + len("    Click me\n")

        # Add tag for the link part
        self.output_text.tag_add(url, f"{index}.{start_index}", f"{index}.{end_index}")
        self.output_text.tag_config(url, foreground="blue", underline=1)
        self.output_text.tag_bind(url, "<Enter>", lambda e: self.output_text.config(cursor="hand2"))
        self.output_text.tag_bind(url, "<Leave>", lambda e: self.output_text.config(cursor=""))

        def open_link(url):
            webbrowser.open(url)
        
        # Bind click event on the tag
        def callback(event, url=url):
            open_link(url)
        
        self.output_text.tag_bind(url, "<Button-1>", callback)
        

    # append text to output area
    # aka display results
    def append_output(self, text):        
        self.output_text.config(state="normal")
        self.output_text.insert(tk.END, text)
        self.output_text.config(state="disabled")
        self.output_text.see(tk.END)

    # when window is closed
    def on_close(self):
        self.should_exit = True
        self.root.destroy()

    # start scrape when button is pressed or Enter is hit
    def start_scrape(self):
        item_name = self.entry.get()
        item_name  = ''.join(ch for ch in item_name if ch.isalpha() or ch == " " or ch=="-")

        # disable input while scraping
        self.entry.config(state="disabled")
        self.scrape_button.config(state="disabled")

        # clear previous output
        self.output_text.config(state="normal")
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state="disabled")

        asyncio.create_task(self.scrape_and_display(item_name))

    # display lines with a delay for fun
    def display_lines_with_delay(self, lines, delay=70):

        def print_line(index):
            link, line = "", ""

            # gets link and line from current index
            # ensures that the link is only added if it exists
            if index < len(lines):
                line = lines[index].split("---")[0].strip()
                if " --- " in lines[index]:
                    link = lines[index].split("---")[-1]

            if index < len(lines) and line != "":
                self.append_output(line)
                if link != "":
                    self.insert_link(len(line), link, index+2)
                self.root.after(delay, lambda: print_line(index + 1))

        # initiate callback function
        print_line(0)

    # scrape and display results
    async def scrape_and_display(self, name):
        
        self.searching_label.config(text=f"Searching for {name}...")
        
        self.root.update_idletasks()

        if self.scraper_choice.get() == "Item Drop":
            results = await scrape_osrs_item_drops(name)
        elif self.scraper_choice.get() == "Mob Location":
            results = await scrape_osrs_mob_location(name)
        

        # re-enable input
        self.entry.config(state="normal")
        self.scrape_button.config(state="normal")
        self.entry.delete(0, tk.END)

        self.searching_label.config(text="")
        
        # red text for errors
        if "No " in results:
            self.output_text.config(fg="red")
            self.append_output(results)
            return
        else:
            self.output_text.config(fg="black")
        
        image_url = results[0]
        lines = results[1].split("\n")

        # if image_url is not None, display it
        if image_url:
            respone = requests.get(image_url)
            img_data = respone.content

            pil_image = Image.open(BytesIO(img_data))
            pil_image = pil_image.resize((150, 150))

            tk_image = ImageTk.PhotoImage(pil_image)
            self.thumbnail_image.config(image=tk_image)
            self.thumbnail_image.image = tk_image
            self.thumbnail_image.pack(pady=10)
            self.thumbnail_image.place(x=10, y=10)

        
        # print out first line as title then remove it from lines
        self.append_output(f"{lines[0]}\n")
        lines = lines[2:]

        self.display_lines_with_delay(lines)


    # main loop to run alongside Tkinter
    async def main_loop(self):
        try:
            while not self.should_exit:
                self.root.update()
                await asyncio.sleep(0.01)
        except tk.TclError:
            pass

    def run(self):
        asyncio.run(self.main_loop())
