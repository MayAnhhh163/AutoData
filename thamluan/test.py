"""
Test script cho workflow mới (article-based, không cần PDF)
"""
import asyncio
import logging
from core.auto import run_workflow_async

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_workflow():
    """Test workflow mới với article-based approach"""

    print("=" * 80)
    print("TESTING NEW WORKFLOW (Article-Based, No URL Required)")
    print("=" * 80)

    # Chỉ cần project name - KHÔNG CẦN URL!
    project_name = " Dự thảo Luật trí tuệ nhân tạo 2025 mới nhất"

    print(f"\n📋 Topic: {project_name}")
    print("🔗 URL: Not required!\n")

    try:
        result = await run_workflow_async(project_name)

        print("\n" + "=" * 80)
        print("✅ WORKFLOW COMPLETED SUCCESSFULLY!")
        print("=" * 80)

        # Summary
        print("\n📊 SUMMARY:")
        print(f"  - News Articles Found: {len(result.get('news_articles', []))}")
        print(f"  - Keywords Extracted: {len(result.get('extracted_keywords', {}).get('main_keywords', []))}")
        print(f"  - Opinion Articles Analyzed: {len(result.get('analyzed_articles', []))}")
        print(f"  - CSV Output: {result.get('csv_output_path', 'N/A')}")
        print(f"  - Errors: {len(result.get('errors', []))}")

        # Show extracted keywords
        keywords = result.get('extracted_keywords')
        if keywords:
            print("\n🔑 TOP KEYWORDS:")
            for i, kw in enumerate(keywords.main_keywords[:10], 1):
                print(f"  {i}. {kw}")

        # Show sentiment distribution
        analyzed = result.get('analyzed_articles', [])
        if analyzed:
            sentiments = {}
            for art in analyzed:
                sent = art.get('sentiment', 'unknown')
                sentiments[sent] = sentiments.get(sent, 0) + 1

            print("\n😊 SENTIMENT DISTRIBUTION:")
            for sent, count in sentiments.items():
                print(f"  {sent}: {count}")

        return result

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("\n🚀 Starting new workflow test...\n")
    result = asyncio.run(test_workflow())

    if result:
        print("\n✅ Test completed successfully!")
    else:
        print("\n❌ Test failed!")
