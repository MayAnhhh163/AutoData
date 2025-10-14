"""
Test Script cho HYBRID WORKFLOW (Full Pipeline)
Đúng theo đề tài: PDF Crawl → Opinion Crawl → NLP Analysis
"""
import asyncio
import logging
from core.auto import run_workflow_async

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_hybrid_workflow():
    """
    Test HYBRID workflow với full pipeline:
    1. Search law list (pagination)
    2. Download PDFs (hash dedup)
    3. Extract PDF content
    4. Store in Vector DB
    5. Search opinions
    6. Crawl FULL CONTENT opinions
    7. NLP analysis (sentiment + stance + topics)
    8. Export CSV
    """
    
    print("\n" + "=" * 80)
    print("🚀 TESTING HYBRID WORKFLOW (Full Pipeline)")
    print("=" * 80)
    print("\nWorkflow:")
    print("  1. Search law list → PDF URLs")
    print("  2. Download PDFs → hash dedup")
    print("  3. Extract content → keywords")
    print("  4. Store Vector DB")
    print("  5. Search opinions → URLs")
    print("  6. Crawl FULL CONTENT → opinions")
    print("  7. NLP analysis → sentiment + stance + topics")
    print("  8. Export CSV")
    print("=" * 80)
    
    # Test với topic thật
    topic = "Luật Khoa học, công nghệ và đổi mới sáng tạo 2025"
    
    print(f"\n📋 Topic: {topic}")
    print("🔗 URL: Not required\n")
    
    try:
        result = await run_workflow_async(topic)
        
        print("\n" + "=" * 80)
        print("✅ HYBRID WORKFLOW COMPLETED!")
        print("=" * 80)
        
        # Detailed summary
        print("\n📊 PHASE 1: LAW DOCUMENT CRAWLING")
        print(f"  - Law Documents Found: {len(result.get('law_documents', []))}")
        print(f"  - PDFs Downloaded: {len(result.get('pdf_paths', []))}")
        
        keywords = result.get('extracted_keywords')
        if keywords and hasattr(keywords, 'main_keywords'):
            print(f"  - Keywords Extracted: {len(keywords.main_keywords)}")
            print(f"  - Key Phrases: {len(keywords.key_phrases)}")
        
        print(f"\n📊 PHASE 2: OPINION CRAWLING")
        print(f"  - Opinion URLs Found: {len(result.get('opinion_urls', []))}")
        print(f"  - Opinions Crawled (Full Content): {len(result.get('opinions_raw', []))}")
        
        print(f"\n📊 PHASE 3: NLP ANALYSIS")
        analyzed = result.get('analyzed_opinions', [])
        print(f"  - Opinions Analyzed: {len(analyzed)}")
        
        # Sentiment distribution
        if analyzed:
            sentiments = {}
            stances = {}
            
            for op in analyzed:
                sent = op.get('sentiment', 'unknown')
                sentiments[sent] = sentiments.get(sent, 0) + 1
                
                stance_info = op.get('stance', {})
                if isinstance(stance_info, dict):
                    stance = stance_info.get('stance', 'unknown')
                    stances[stance] = stances.get(stance, 0) + 1
            
            print(f"\n  😊 Sentiment Distribution:")
            for sent, count in sentiments.items():
                print(f"      {sent}: {count}")
            
            print(f"\n  📍 Stance Distribution:")
            for stance, count in stances.items():
                print(f"      {stance}: {count}")
        
        print(f"\n📊 PHASE 4: EXPORT")
        print(f"  - CSV Output: {result.get('csv_output_path', 'N/A')}")
        print(f"  - Vector DB Collection: {result.get('vector_db_collection', 'N/A')}")
        
        # Show sample keywords
        if keywords and hasattr(keywords, 'main_keywords'):
            print(f"\n🔑 TOP 10 KEYWORDS:")
            for i, kw in enumerate(keywords.main_keywords[:10], 1):
                print(f"  {i}. {kw}")
        
        # Show sample opinions
        if analyzed:
            print(f"\n📰 SAMPLE OPINIONS:")
            for i, op in enumerate(analyzed[:3], 1):
                print(f"\n  {i}. {op.get('title', 'No title')[:60]}...")
                print(f"     Source: {op.get('source', 'unknown')}")
                print(f"     Sentiment: {op.get('sentiment', 'unknown')}")
                stance_info = op.get('stance', {})
                if isinstance(stance_info, dict):
                    print(f"     Stance: {stance_info.get('stance', 'unknown')} (confidence: {stance_info.get('confidence', 0):.2f})")
                print(f"     Content: {op.get('content', '')[:100]}...")
        
        # Show errors if any
        errors = result.get('errors', [])
        if errors:
            print(f"\n⚠️ ERRORS: {len(errors)}")
            for i, error in enumerate(errors[:3], 1):
                print(f"  {i}. {error.get('message', 'Unknown error')}")
        
        print("\n" + "=" * 80)
        print("📊 OVERALL STATISTICS")
        print("=" * 80)
        print(f"  Total Tasks: {len(result.get('task_history', []))}")
        print(f"  Completed: {len([t for t in result.get('task_history', []) if t.status.value == 'completed'])}")
        print(f"  Failed: {len([t for t in result.get('task_history', []) if t.status.value == 'failed'])}")
        print(f"  Errors: {len(errors)}")
        print("=" * 80)
        
        return result
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("\n🎯 Starting Hybrid Workflow Test...")
    print("This will test the FULL PIPELINE:")
    print("  ✓ PDF crawling with deduplication")
    print("  ✓ Opinion crawling with FULL CONTENT")
    print("  ✓ NLP analysis with sentiment + stance + topics")
    print("  ✓ Export to CSV\n")
    
    result = asyncio.run(test_hybrid_workflow())
    
    if result:
        print("\n✅ HYBRID WORKFLOW TEST PASSED!")
        print(f"\n📁 Check output: {result.get('csv_output_path', 'N/A')}")
    else:
        print("\n❌ HYBRID WORKFLOW TEST FAILED!")
