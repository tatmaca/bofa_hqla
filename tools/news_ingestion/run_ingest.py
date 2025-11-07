import subprocess, sys, datetime as dt
from db import init_db, start_ingestion_run, complete_ingestion_run

def run():
    init_db()
    run_date = start_ingestion_run()
    print(f">> Starting ingestion run for {run_date}")
    
    rss_processed, rss_skipped = 0, 0
    crawl_processed, crawl_skipped = 0, 0
    status = "completed"
    error_message = None
    
    try:
        print(">> RSS ingest")
        result = subprocess.run([sys.executable, "ingest_rss.py"], 
                              capture_output=True, text=True, check=False)
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        # Parse output for stats (basic - could be improved)
        for line in result.stdout.split('\n'):
            if '[RSS] Processed:' in line:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        rss_processed = int(parts[1].rstrip(','))
                        rss_skipped = int(parts[3]) if len(parts) > 3 else 0
                    except:
                        pass
        
        print(">> Web crawl")
        result = subprocess.run([sys.executable, "crawl_web.py"], 
                              capture_output=True, text=True, check=False)
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
            
    except Exception as e:
        status = "failed"
        error_message = str(e)
        print(f"[ERROR] Ingestion failed: {e}", file=sys.stderr)
    
    new_articles = complete_ingestion_run(
        run_date, rss_processed, rss_skipped, 
        crawl_processed, crawl_skipped, status, error_message
    )
    print(f">> Done. New articles: {new_articles}")

if __name__ == "__main__":
    run()
