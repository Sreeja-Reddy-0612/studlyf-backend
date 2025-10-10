from apscheduler.schedulers.background import BackgroundScheduler
import asyncio, json
from crawler import main as crawl_tools
from ai_categorizer import categorize_tool
from models import add_tool_from_dict

def job():
    print("🔄 Running AI tool crawler + categorizer job...")
    tools = asyncio.run(crawl_tools())
    for tool in tools:
        try:
            extra = categorize_tool(tool["name"], tool["short_description"])
            data = json.loads(extra)
            tool["tags"] = data.get("tags", [])
            tool["supported_tech"] = []
            tool["use_cases"] = [data.get("category", "General")]
            tool["long_description"] = data.get("long_summary", "")
            add_tool_from_dict(tool)
        except Exception as e:
            print("❌ Error processing tool:", e)

scheduler = BackgroundScheduler()
scheduler.add_job(job, "interval", minutes=1)  # For testing: every 1 min
scheduler.start()

if __name__ == "__main__":
    print("✅ Scheduler started. Fetching AI tools...")
    job()  # Run immediately
