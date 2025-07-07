import os
import time
import requests
from tqdm import tqdm

def collect_pdf_urls(api_url: str = None, max_pdfs: int = 1000):
    """
    Collect PDF URLs from OpenAlex API with pagination.
    
    Args:
        api_url: Custom API URL (optional)
        max_pdfs: Maximum number of PDFs to collect
    
    Returns:
        List of PDF URLs
    """
    if api_url is None:
        api_url = "https://api.openalex.org/works?filter=concept.id:C121332964,has_pmid:true,primary_location.source.type:journal,publication_year:2022-2025&per_page=200&page={page}"
    
    pdf_urls = []
    page = 1
    pbar = tqdm(desc="Searching for articles", unit="work")
    
    while len(pdf_urls) < max_pdfs:
        url = api_url.format(page=page)
        r = requests.get(url, headers={"User-Agent": "PDF-harvester/1.0"}, timeout=30)
        r.raise_for_status()
        payload = r.json()
        batch = 0
        
        for work in payload.get("results", []):
            loc = work.get("best_oa_location") or {}
            pdf = loc.get("pdf_url")
            if pdf and pdf not in pdf_urls:
                pdf_urls.append(pdf)
                batch += 1
                if len(pdf_urls) >= max_pdfs:
                    break
        
        if batch == 0:  # Empty page → no point continuing
            break
            
        page += 1
        pbar.update(batch)
        time.sleep(0.2)  # ≤ 5 req/s (OpenAlex limit is 10 req/s)
    
    pbar.close()
    return pdf_urls[:max_pdfs] 