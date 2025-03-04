import argparse
import json
import time
import pika
import pymongo
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from lxml import html
from newspaper import Article
import language_tool_python
from bson import ObjectId

# MongoDB Configuration
MONGO_URI = "mongodb+srv://palashemperor7:u7AkeNu6ys6M3iEs@cluster0.zyqwl.mongodb.net/web_scraper?retryWrites=true&w=majority"
DB_NAME = "web_scraper"
COLLECTION_NAME = "url_data"

# Setup MongoDB Connection
client = pymongo.MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# CloudAMQP Credentials
AMQP_URL = "amqps://yoplxstm:MtvBypPhs4ifk8A5jj35qxzJzSTA6i-D@kebnekaise.lmq.cloudamqp.com/yoplxstm"
QUEUE_NAME = "url_queue"

# Setup RabbitMQ Connection
def get_rabbitmq_channel():
    params = pika.URLParameters(AMQP_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    return connection, channel

# Function to add URL to MongoDB and RabbitMQ
def add_url(url):
    data = {"url": url, "status": "pending", "timestamp": time.time()}
    inserted = collection.insert_one(data)  # Save in MongoDB

    # Convert MongoDB ObjectId to a string
    data["_id"] = str(inserted.inserted_id)

    _, channel = get_rabbitmq_channel()
    channel.basic_publish(exchange="", routing_key=QUEUE_NAME, body=json.dumps(data))

    print(f"✅ URL {url} added to queue")

# Function to fetch webpage content
def fetch_content(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code} error.")

        if len(response.content) < 100000:  # If < 100KB, use Selenium
            print("⚠️ Using Selenium for dynamic content")
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            service = Service("/path/to/chromedriver")  # Update path
            driver = webdriver.Chrome(service=service, options=options)
            driver.get(url)
            html_content = driver.page_source
            driver.quit()
        else:
            html_content = response.text
        
        return html_content
    
    except Exception as e:
        raise Exception(f"Error fetching {url}: {e}")

# Function to extract text content
def extract_text(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        if not article.text:
            raise Exception("No extractable text found.")
        return article.text
    except Exception as e:
        raise Exception(f"Error extracting text: {e}")

# Function to extract outbound links
def extract_links(html_content):
    tree = html.fromstring(html_content)
    return tree.xpath('//a/@href')

# Function to check grammar
def check_grammar(text):
    tool = language_tool_python.LanguageTool("en-US")
    matches = tool.check(text)
    return [{"offset": m.offset, "error": m.message} for m in matches]

# Function to process a single URL
def process_url(url):
    start_time = time.time()
    
    try:
        html_content = fetch_content(url)
        if not html_content:
            raise Exception("Failed to fetch content.")

        links = extract_links(html_content)

        text = extract_text(url)
        if not text:
            raise Exception("Failed to extract text.")

        grammar_errors = check_grammar(text)

        processing_time = time.time() - start_time

        # Update MongoDB with successful processing details
        collection.update_one(
            {"url": url},
            {"$set": {
                "status": "processed",
                "content": text,
                "links": links,
                "grammar_errors": grammar_errors,
                "processing_time": processing_time
            }}
        )
        print(f"✅ Processed {url} in {processing_time:.2f}s")

    except Exception as e:
        # Update MongoDB with failure status and reason
        collection.update_one(
            {"url": url},
            {"$set": {
                "status": "failed",
                "reason": str(e),
                "processing_time": time.time() - start_time
            }}
        )
        print(f"❌ Failed to process {url}: {e}")

# Function to start consuming RabbitMQ queue
def start_service():
    print("🚀 Service started... Listening for URLs.")
    connection, channel = get_rabbitmq_channel()

    def callback(ch, method, properties, body):
        data = json.loads(body)
        url = data.get("url")
        if url:
            print(f"📥 Processing {url}")
            process_url(url)
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
    channel.start_consuming()

# Argparse to handle CLI arguments
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Web Scraper Service")
    parser.add_argument("command", choices=["add_url", "start_service"], help="Command to run")
    parser.add_argument("--url", help="URL to process (required for add_url)")
    
    args = parser.parse_args()
    
    if args.command == "add_url":
        if not args.url:
            print("❌ Please provide a URL using --url")
        else:
            add_url(args.url)
    elif args.command == "start_service":
        start_service()