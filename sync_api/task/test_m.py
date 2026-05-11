import os
import sys
import django
import time
from datetime import datetime
# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sync_api.settings')
django.setup()
# Setup Django environment


from task.models import Task
from task.services import scrape_url  # or scrape_url

# URLS_TO_TEST = [
#     "https://httpbin.org/html",  
#     "https://books.toscrape.com",  
#     "https://quotes.toscrape.com",  
#     "https://www.python.org",  #
#     "https://coreyms.com",  
# ]
URLS_TO_TEST = [
    "https://en.wikipedia.org/wiki/Python_(programming_language)",
    "https://en.wikipedia.org/wiki/Django_(web_framework)",
    "https://news.ycombinator.com",
    "https://www.python.org",
    "https://httpbin.org/html",
    "https://en.wikipedia.org/wiki/Main_Page",
    "https://www.wikipedia.org",
    "https://github.com",
    "https://stackoverflow.com",
    "https://www.reddit.com",
]


def test_single_url_performance():
    
    print(f"Testing {len(URLS_TO_TEST)} URLs (one task each)")
    print(f"Started at: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'-'*50}\n")
    
    successful = 0
    failed = 0
    total_time = 0
    
    for url in URLS_TO_TEST:
        # Create task for each URL
        task = Task.objects.create(
            url=url,
            status='PENDING'
        )
        
        # Timing the URL
        start_time = time.time()
        scrape_url(task.id)
        end_time = time.time()
        
        url_time = end_time - start_time
        total_time += url_time
        
    
        task.refresh_from_db()
        if task.status == 'COMPLETED' and task.result:
            successful += 1
            
            results_list = task.result.get('results', [])
            first_result = results_list[0] if results_list else {}
            title = first_result.get('title', 'No title')[:50] if first_result else 'No title'
            print(f"(SUCCESS) {url[:40]}... ({url_time:.2f}s) - {title}")
        else:
            failed += 1
            error = task.error_field or 'Unknown error'
            print(f"(FAILED){url[:40]}... ({url_time:.2f}s) - {error[:50]}")
    
    avg_time = total_time / len(URLS_TO_TEST)
    
    print(f"\n{'='*50}")
    print(f"RESULTS:")
    print(f"  Total URLs: {len(URLS_TO_TEST)}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  Total time: {total_time:.2f} seconds")
    print(f"  Average per URL: {avg_time:.2f} seconds")
    print(f"  Success rate: {(successful/len(URLS_TO_TEST))*100:.1f}%")
    print(f"{'='*50}\n")
    
    return {
        'total_urls': len(URLS_TO_TEST),
        'successful': successful,
        'failed': failed,
        'total_time': total_time,
        'avg_time': avg_time,
        'success_rate': (successful/len(URLS_TO_TEST))*100
    }

if __name__ == "__main__":
    test_single_url_performance()
