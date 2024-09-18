import psutil
import requests
import tkinter as tk
from tkinter import Toplevel
from PIL import Image, ImageTk
import asyncio
import aiohttp
import io

# Function to fetch and load the image from the URL
async def fetch_image(session, url):
    async with session.get(url) as response:
        if response.status == 200:
            return await response.read()
        return None

# Function to download and convert the image from URL to a format usable in Tkinter
async def set_background(window, canvas):
    image_url = "https://i.ibb.co/dfhmPqN/your-image-name.png"  # Background image URL
    async with aiohttp.ClientSession() as session:
        image_data = await fetch_image(session, image_url)
        
        if image_data:
            background = Image.open(io.BytesIO(image_data))
            background = background.resize((600, 400), Image.Resampling.LANCZOS)  # Resize for the window size
            background_img = ImageTk.PhotoImage(background)

            # Create a canvas to set the background image
            canvas.create_image(0, 0, anchor="nw", image=background_img)
            canvas.image = background_img  # Keep a reference to prevent garbage collection

# Function to set the window icon
async def set_window_icon(window):
    icon_url = "https://i.ibb.co/L0GNxWT/Design-sans-titre.png"  # New logo URL
    async with aiohttp.ClientSession() as session:
        icon_data = await fetch_image(session, icon_url)
        
        if icon_data:
            icon = Image.open(io.BytesIO(icon_data))
            icon = icon.resize((32, 32), Image.Resampling.LANCZOS)  # Resize for the window icon
            icon_img = ImageTk.PhotoImage(icon)
            
            # Set the icon for the window
            window.iconphoto(False, icon_img)
            window.iconphoto(True, icon_img)  # Set for both 32x32 and 16x16

# Function to get public IP and geolocation for a given process and ports
def get_public_ip_for_process(process_name, ports):
    processes = [p for p in psutil.process_iter(['pid', 'name']) if process_name.lower() in p.info['name'].lower()]
    
    if not processes:
        return None

    for process in processes:
        try:
            connections = process.connections(kind='inet')
            
            for conn in connections:
                remote_ip = conn.raddr.ip if conn.raddr else 'N/A'
                remote_port = conn.raddr.port if conn.raddr else 'N/A'
                
                if remote_ip != 'N/A' and remote_port in ports:
                    location = get_geolocation(remote_ip)
                    if location:
                        location['Port'] = remote_port
                        return location
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass

    return None

# Function to get geolocation information
def get_geolocation(ip):
    try:
        response = requests.get(f'https://ipinfo.io/{ip}/json')
        data = response.json()
        location = {
            'IP': ip,
            'City': data.get('city', 'N/A'),
            'Region': data.get('region', 'N/A'),
            'Country': data.get('country', 'N/A'),
            'ISP': data.get('org', 'N/A')  # ISP info
        }
        return location
    except requests.RequestException:
        return None

# Function to get network statistics for a given process
def get_network_stats(process_name):
    processes = [p for p in psutil.process_iter(['pid', 'name']) if process_name.lower() in p.info['name'].lower()]

    if not processes:
        return None

    for process in processes:
        try:
            net_io = psutil.net_io_counters(pernic=True)
            process_net_io = {nic: net_io[nic] for nic in net_io if psutil.net_if_addrs()[nic][0].address in process.connections(kind='inet')}
            if process_net_io:
                return process_net_io
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass

    return None

# Function to update the Discord information
async def update_discord_info():
    if discord_var.get():
        discord_ports = {443, 5000, 6500}
        discord_location = get_public_ip_for_process("discord.exe", discord_ports)

        if discord_location:
            discord_info_label.config(
                text=f"IPv4: {discord_location['IP']}    Port: {discord_location['Port']}"
            )
            logo_label.config(image=discord_logo_img)  # Display Discord logo
            discord_info_label.bind("<Button-1>", lambda e: open_detail_window(discord_location))

            # Update network statistics
            net_stats = get_network_stats("discord.exe")
            if net_stats:
                sent_data = sum([net.bytes_sent for net in net_stats.values()])
                recv_data = sum([net.bytes_recv for net in net_stats.values()])
                net_stats_label.config(
                    text=f"Sent: {sent_data / (1024 ** 2):.2f} MB    Received: {recv_data / (1024 ** 2):.2f} MB"
                )
            else:
                net_stats_label.config(text="• Network stats not available")
        else:
            discord_info_label.config(text="• No IP connection found")
            logo_label.config(image='')  # Hide Discord logo if no connection is found
            net_stats_label.config(text="")
    else:
        discord_info_label.config(text="")
        logo_label.config(image='')  # Hide Discord logo if unchecked
        net_stats_label.config(text="")

    window.after(1000, lambda: asyncio.run(update_discord_info()))  # Refresh every 1 second

# Open a new window for detailed IP information
def open_detail_window(location):
    detail_window = Toplevel(window)
    detail_window.title("IP Details")
    detail_window.geometry("300x200")
    detail_window.configure(bg='black')

    tk.Label(detail_window, text=f"ISP: {location['ISP']}", fg='white', bg='black', font=("Arial", 12)).pack(pady=10)
    tk.Label(detail_window, text=f"City: {location['City']}", fg='white', bg='black', font=("Arial", 12)).pack(pady=10)
    tk.Label(detail_window, text=f"Country: {location['Country']}", fg='white', bg='black', font=("Arial", 12)).pack(pady=10)
    tk.Label(detail_window, text=f"Region: {location['Region']}", fg='white', bg='black', font=("Arial", 12)).pack(pady=10)

# Initialize the main window
window = tk.Tk()
window.title("TryKushi Network Scanner")
window.geometry("600x500")  # Adjust window size for better UI space
window.configure(bg='black')

# Set the window icon
asyncio.run(set_window_icon(window))

# Create a canvas to manage the background
canvas = tk.Canvas(window, width=600, height=500)
canvas.pack(fill="both", expand=True)

# Start the background image display
asyncio.run(set_background(window, canvas))

# Variables for the Discord scan toggle
discord_var = tk.BooleanVar()

# Create a frame for the options and place it at the top-left
options_frame = tk.Frame(window, bg='black')
options_frame.place(relx=0.05, rely=0.1)

# Create a frame to hold Discord scan information
discord_frame = tk.Frame(options_frame, bg='black')
discord_frame.pack(anchor='nw', padx=5, pady=5)

# Create checkboxes for selecting scans
discord_checkbox = tk.Checkbutton(
    discord_frame, text="Discord Scan", variable=discord_var, onvalue=True, offvalue=False, 
    command=lambda: asyncio.run(update_discord_info()), bg='black', fg='white', 
    selectcolor='gray', font=("Arial", 12)
)
discord_checkbox.pack(side=tk.LEFT)

# Create a frame to hold the IP information and add a border around it
discord_border_frame = tk.Frame(discord_frame, bg='white', bd=2, relief='groove')
discord_border_frame.pack(side=tk.LEFT, padx=10)

# Create label to display Discord scanning results (inside the border)
discord_info_label = tk.Label(discord_border_frame, text="", fg='black', bg='white', font=("Arial", 12), justify='left')
discord_info_label.pack(side=tk.LEFT, padx=10)

# Create a label to display the Discord logo at the end of the information line
logo_label = tk.Label(discord_frame, bg='black')
logo_label.pack(side=tk.RIGHT, padx=5)

# Create a label to display network statistics (sent/received packets)
net_stats_label = tk.Label(discord_frame, text="", fg='white', bg='black', font=("Arial", 12), justify='left')
net_stats_label.pack(side=tk.BOTTOM, pady=5)

# Load the small logo for Discord to be used at the end of the line
async def set_discord_logo():
    logo_url = "https://i.ibb.co/vYZfRds/seven-kingdoms-9.png"  # Discord logo URL
    async with aiohttp.ClientSession() as session:
        logo_data = await fetch_image(session, logo_url)
        
        if logo_data:
            discord_logo = Image.open(io.BytesIO(logo_data))
            discord_logo = discord_logo.resize((32, 32), Image.Resampling.LANCZOS)  # Resize for display
            global discord_logo_img
            discord_logo_img = ImageTk.PhotoImage(discord_logo)

# Start loading the Discord logo
asyncio.run(set_discord_logo())

# Run the main Tkinter loop
window.mainloop()
