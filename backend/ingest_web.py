import trafilatura
import json

def scrape_university_policy(url, tenant_name):
    print(f"Targeting: {url}...")
    
    # Step 1: The Harvester - Fetch the raw HTML
    downloaded = trafilatura.fetch_url(url)
    
    if downloaded is None:
        print(f"❌ Failed to download: {url}")
        return None

    # Step 2: The Filter - Extract only the clean, relevant text
    clean_text = trafilatura.extract(
        downloaded,
        include_links=False,    # We don't want raw HTTP links messing up the text
        include_images=False,   # AI doesn't need image tags
        include_tables=True,    # CRITICAL: Keeps course prerequisites and tables intact
        no_fallback=False       # Uses secondary extraction methods if the primary fails
    )

    if clean_text is None:
        print(f"⚠️ No usable text found on: {url}")
        return None

    # Step 3: The Packager - Format it for the Vector Database
    document = {
        "text": clean_text,
        "metadata": {
            "source": url,
            "tenant": tenant_name,
            "content_type": "official_policy_web"
        }
    }
    
    return document

# ==========================================
# 🚀 TEST DRIVE THE PIPELINE
# ==========================================
if __name__ == "__main__":
    # The heavy engineering program requirements page
    test_url = "https://calendar.carleton.ca/undergrad/undergradprograms/engineering/"
    
    print("Initiating Trafilatura Extraction Engine...")
    result = scrape_university_policy(test_url, tenant_name="carleton")
    
    if result:
        print("\n✅ EXTRACTION SUCCESSFUL!")
        print(f"Tenant: {result['metadata']['tenant']}")
        print(f"Source: {result['metadata']['source']}")
        print("-" * 40)
        # Print the first 1000 characters to verify the noise is gone
        print(result['text'][:1000] + "\n...\n[TEXT TRUNCATED FOR PREVIEW]")