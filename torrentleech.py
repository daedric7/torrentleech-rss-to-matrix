#!/usr/bin/python3


### Config ###
rss_link = 'https://rss24h.torrentleech.org/xxxxxxxxxxxxxxxxxxxxxx'

matrix_room = '!abcdefghijkl12345678:matrix.org'
matrix_server = 'matrix.org'
matrix_token = 'syt_thiscouldbe_avalidtoken_youknow'

wanted_categories = ['PC']

### End Config ###



# SQLite database file
db_file = "rss_links.db"

sleep_time = 5

import requests
import xml.etree.ElementTree as ET
import time
import sqlite3

# Function to initialize the database
def initialize_db():
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    # Create table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rss_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            link TEXT UNIQUE
        )
    """)
    conn.commit()
    conn.close()

# Function to check if a link exists in the database
def link_exists(link):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM rss_links WHERE link = ?", (link,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

# Function to store a link in the database
def store_link(link):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO rss_links (link) VALUES (?)", (link,))
        conn.commit()
    except sqlite3.IntegrityError:
        # Ignore duplicate entries
        pass
    conn.close()

# Function to send a message to a Matrix room
def send_to_matrix(room_id, server, token, message, formatted_message):
    url = f"https://{server}/_matrix/client/v3/rooms/{room_id}/send/m.room.message"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "msgtype": "m.text",
        "body": message,
        "format": "org.matrix.custom.html",  # Use HTML formatting
        "formatted_body": formatted_message  # HTML-formatted message
    }
    response = requests.post(url, json=payload, headers=headers)
    #if response.status_code == 200 or response.status_code == 201:
    #    print("Message sent successfully.")
    #else:
    #    print(f"Failed to send message. HTTP Status: {response.status_code}, Response: {response.text}")



# Initialize the database
initialize_db()


while True:

    #Get rss data
    rss_data = requests.get(rss_link)

    #If the RSS download got an error, wait and try again
    if rss_data.status_code != 200:
        time.sleep(sleep_time)
        continue

    # Get the raw content (in bytes)
    rss_feed = rss_data.content

    # Parse the RSS feed
    root = ET.fromstring(rss_feed)

    # Extract items
    for item in root.findall(".//item"):
        link = item.find("link").text.strip()
        # Skip the entry if the link already exists in the database
        if link_exists(link):
            #print(f"Skipping already processed link: {link}")
            continue

        title = item.find("title").text.strip()
        pub_date = item.find("pubDate").text.strip()
        category = item.find("category").text.strip()
        description = item.find("description").text.strip()

        if category not in wanted_categories:
            store_link(link)
            continue

        print(f"Title: {title}")
        print(f"Published Date: {pub_date}")
        print(f"Category: {category}")
        print(f"Download Link: {link}")
        print(f"Description: {description}")
        print("-" * 40)

        # Format the message
        message = (
            f"**Title:** {title}\n"
            f"**Published Date:** {pub_date}\n"
            f"**Category:** {category}\n"
            f"**Download Link:** {link}\n"
            f"**Description:** {description}"
        )

        # HTML-formatted message
        formatted_message = (
            f"<b>Title:</b> {title}<br>"
            f"<b>Published Date:</b> {pub_date}<br>"
            f"<b>Category:</b> {category}<br>"
            f"<b>Download Link:</b> <a href='{link}'>{link}</a><br>"
            f"<b>Description:</b> {description}"
        )

        # Send the message to the Matrix room
        send_to_matrix(matrix_room, matrix_server, matrix_token, message, formatted_message)

        # Store the link in the database
        store_link(link)

    time.sleep(sleep_time)


