"""
Test script cho LawListCrawler (Selenium version)
"""
import asyncio
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from tools.law_list_crawler import law_list_crawler

def test_crawler():
    """Test crawler với topic cụ thể"""
    
    print("\n" + "=" * 80)
    print("🧪 TESTING LAW LIST CRAWLER (SELENIUM)")
    print("=" * 80)
    
    # Test topics
    topics = [
        "Luật Khoa học",
        "Luật Đất đai",
        "Luật Giao thông",
    ]
    
    for topic in topics:
        print(f"\n📋 Testing topic: '{topic}'")
        print("-" * 80)
        
        result = law_list_crawler.crawl_law_list(
            topic=topic,
            max_results=10,
            similarity_threshold=0.3  # Lower threshold for better matching
        )
        
        if result.success:
            documents = result.data['documents']
            count = result.data['count']
            
            print(f"\n✅ SUCCESS: Found {count} documents")
            print(f"\n📚 Documents:")
            
            for i, doc in enumerate(documents, 1):
                print(f"\n  {i}. {doc.title}")
                print(f"     URL: {doc.url}")
                print(f"     Similarity: {doc.metadata.get('similarity', 0):.1%}")
                if doc.pdf_url:
                    print(f"     PDF: {doc.pdf_url}")
        else:
            print(f"\n❌ FAILED: {result.error}")
        
        print("-" * 80)
    
    print("\n" + "=" * 80)
    print("🎉 TEST COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    print("\n🚀 Starting Law Crawler Test (Selenium)...")
    print("This will:")
    print("  1. Use Selenium + Chrome headless")
    print("  2. Crawl from duthaoonline.quochoi.vn")
    print("  3. Find law documents matching topics")
    print("  4. Calculate similarity scores\n")
    
    test_crawler()
