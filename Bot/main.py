# Import dependencies
import os
import re
import queue
import urllib
import dotenv
import logging
import requests
import threading
from bot import run_bot
from drive import DriveHandler
from flask import Flask, request

# Flask App
app = Flask(__name__)

# Function to download reel based on a link
def download_reel(reel):
    """
    Downloads reel by making a request to the
    saveig's endpoint and writes it to a file

    Args:
        reel: The url of reel to download

    Returns:
        path: The path of the reel downloaded

    """

    # Create Url, payload and headers
    url = "https://v3.saveig.app/api/ajaxSearch"
    payload = f"q={urllib.parse.quote(reel, safe='')}&t=media&lang=en"
    headers = {
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
    }

    # Regex pattern to find the link in the data
    pattern = re.compile(r'href="([^"]+)"')

    # Send a POST request to req a reel
    with requests.post(url=url, data=payload, headers=headers) as response:
        # Procced if the status code is 200
        if response.status_code == 200:
            # Extract the link and Download it's content
            data = response.json()["data"]
            link = pattern.findall(data)[0]
            with requests.get(link) as reel_response:
                with open("video.mp4", "wb") as file:
                    file.write(reel_response.content)
                    return os.path.abspath("video.mp4")

    return None

# Setup Logging
def setup_logger():
    # Create a logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # Check if the logger already has handlers to avoid adding multiple handlers
    if not logger.hasHandlers():
        # Create a console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Create a formatter and set it for the console handler
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)

        # Add the console handler to the logger
        logger.addHandler(console_handler)

    return logger

# Worker function
def worker():
    while True:
        reel, acc = pending_tasks.get()
        logger.info("The queue unblocked and a Task was found.")

        try:
            path = download_reel(reel)
            if path:
                logger.info("The requested Reel was downloaded.")
                user_drive.upload(path, 'video/mp4', "reel.mp4", acc)
                os.remove(path)
        except Exception as e:
            logger.info(f"Error processing task: {e}")
        else:
            logger.info("The Reel was uploaded.")
        finally:
            pending_tasks.task_done()

# Homepage
@app.route("/")
def home():
    return "<h1>You have reached Bot's Server Side.</h1>"

# Endpoint to handle reels request
@app.route('/reel', methods=['POST'])
def handle_reel():
    # Verify incoming requests
    if request.headers.get("token", None) == TOKEN:
        logger.info("A verified request for a reel received.")
        data = request.get_json()

        # Extract Information
        account = data.get("acc")
        reel = data.get("reel")

        # Put this in task with accordance to its folder id
        if account == "luxury":
            pending_tasks.put([reel, LUXURY])
        elif account == "anime":
            pending_tasks.put([reel, ANIME])
        else:
            return "No folder found", 404

        return 'success', 200
    else:
        # 400 response for every req
        return "Bad request", 400

if __name__ == '__main__':
    # Setup .env data
    dotenv.load_dotenv()

    # Get the configured logger
    logger = setup_logger()

    # initialize variables
    TOKEN = os.getenv("TOKEN")          # Verification Token
    ANIME = os.getenv("ANIME")          # Constant for a drive folder
    LUXURY = os.getenv("LUXURY")        # Constant for a drive folder
    pending_tasks = queue.Queue()       # Task queue for pending tasks
    user_drive = DriveHandler('creds.json', os.getenv("PARENT_FOLDER"))         # G-Drive Instance

    # Run the worker Thread
    worker_thread = threading.Thread(target=worker)
    worker_thread.daemon = True
    worker_thread.start()

    # Run the Server thread
    # Run the app on port 10000
    server_thread = threading.Thread(target=app.run, args=["0.0.0.0",10000])
    server_thread.daemon = True
    server_thread.start()

    # Run the Bot
    run_bot()
