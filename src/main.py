from ai.metadata_extractor import MetadataExtractor
from utils.yaml_utils import read_yaml
from parsers.pdf_parser import first_n_pages_to_text
from pathlib import Path
from download.pdf_downloader import download_pdf
from database.postgres_client import PostgresClient
from logging import getLogger
from download.pdf_collector import collect_pdf_urls
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

logger = getLogger(__name__)

# Thread-local storage for database connections
thread_local = threading.local()

def get_postgres_client():
    """Get thread-local PostgreSQL client."""
    if not hasattr(thread_local, 'postgres_client'):
        thread_local.postgres_client = PostgresClient()
    return thread_local.postgres_client

def process_pdf(pdf_link, raw_dir, config):
    """Process a single PDF: download, parse, extract metadata, and save to DB."""
    try:
        # Download PDF
        pdf_path = download_pdf(pdf_link, raw_dir, max_mb=20)
        if pdf_path is None:
            logger.warning(f"Failed to download: {pdf_link}")
            return None
        
        # Parse PDF text
        text = first_n_pages_to_text(Path(pdf_path))
        
        # Extract metadata
        metadata_extractor = MetadataExtractor()
        prompt = config['prompts']['user_prompt_template']
        sys_prompt = config['prompts']['sys_prompt']
        responce_keys = config['prompts']['responce_keys']
        
        data = metadata_extractor.extract(
            input_text=text, 
            prompt=prompt, 
            sys_prompt=sys_prompt,
            responce_keys=responce_keys
        )
        data['pdf_path'] = str(pdf_path)
        
        # Save to database
        postgres_client = get_postgres_client()
        postgres_client.insert_row("pdf_library", "pdf_metadata", data)
        
        logger.info(f"Processed: {pdf_link}")
        return data
        
    except Exception as e:
        logger.error(f"Error processing {pdf_link}: {e}")
        return None

if __name__ == "__main__":
    config = read_yaml()
    api_url = config['pdf_search']['api_url']
    pdf_links = collect_pdf_urls(api_url=api_url, max_pdfs=2000)
    raw_dir = Path("data/raw")
    
    # Use ThreadPoolExecutor for concurrent processing
    max_workers = 2
    processed_count = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_link = {
            executor.submit(process_pdf, pdf_link, raw_dir, config): pdf_link 
            for pdf_link in pdf_links
        }
        
        # Process completed tasks
        for future in as_completed(future_to_link):
            pdf_link = future_to_link[future]
            try:
                result = future.result()
                if result:
                    processed_count += 1
                    print(f"Completed {processed_count}/{len(pdf_links)}: {pdf_link}")
            except Exception as e:
                logger.error(f"Task failed for {pdf_link}: {e}")
    
    # Clean up thread-local database connections
    if hasattr(thread_local, 'postgres_client'):
        thread_local.postgres_client.close()
    
    print(f"Processing complete. Successfully processed {processed_count}/{len(pdf_links)} PDFs.")