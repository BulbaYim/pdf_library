import os
import requests
import time
import logging
import random
from pathlib import Path
from urllib.parse import urlparse, unquote
from typing import Optional
from database.postgres_client import PostgresClient
import datetime

logger = logging.getLogger(__name__)

def get_random_user_agent():
    """Get a random user agent to avoid detection."""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59",
    ]
    return random.choice(user_agents)

def download_pdf(
    url: str,
    dest_dir: Path,
    max_mb: int = 20,
    timeout: int = 30,
    max_retries: int = 3,
    retry_delay: float = 2.0
) -> Optional[str]:
    """
    Download a PDF file from URL to the specified directory.
    
    Args:
        url: URL of the PDF to download
        dest_dir: Destination directory for the PDF
        max_mb: Maximum file size in MB (default: 20)
        timeout: Request timeout in seconds (default: 30)
        max_retries: Maximum number of retry attempts (default: 3)
        retry_delay: Delay between retries in seconds (default: 2.0)
    
    Returns:
        Path to downloaded file, or None if download fails
    """
    start_time = time.time()
    status = "success"
    error_message = None
    file_path = None
    retry_count = 0
    
    try:
        # Create destination directory if it doesn't exist
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename from URL
        parsed_url = urlparse(url)
        filename = unquote(parsed_url.path.split('/')[-1])
        
        # If no filename or empty, generate one from URL
        if not filename or '.' not in filename:
            filename = f"downloaded_{int(time.time())}.pdf"
        
        # Ensure .pdf extension
        if not filename.lower().endswith('.pdf'):
            filename += '.pdf'
        
        file_path = dest_dir / filename
        
        # Check if file already exists
        if file_path.exists():
            logger.info(f"File already exists: {file_path}")
            status = "already_exists"
            return str(file_path)
        
        # Enhanced headers to avoid detection
        headers = {
            "User-Agent": get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Referer": parsed_url.scheme + "://" + parsed_url.netloc,
        }
        
        # Retry logic for failed downloads
        while retry_count < max_retries:
            try:
                response = requests.get(
                    url, 
                    headers=headers, 
                    timeout=timeout, 
                    stream=True,
                    allow_redirects=True
                )
                
                # Handle different HTTP status codes
                if response.status_code == 200:
                    break
                elif response.status_code == 403:
                    error_message = f"Access forbidden (403) - URL may require authentication or be blocked"
                    logger.warning(f"403 Forbidden for {url} - attempt {retry_count + 1}/{max_retries}")
                    status = "access_forbidden"
                    if retry_count < max_retries - 1:
                        time.sleep(retry_delay * (retry_count + 1))  # Exponential backoff
                        retry_count += 1
                        continue
                    else:
                        return None
                elif response.status_code == 404:
                    error_message = f"File not found (404)"
                    logger.error(f"404 Not Found for {url}")
                    status = "not_found"
                    return None
                elif response.status_code == 429:
                    error_message = f"Rate limited (429) - too many requests"
                    logger.warning(f"Rate limited for {url} - attempt {retry_count + 1}/{max_retries}")
                    status = "rate_limited"
                    if retry_count < max_retries - 1:
                        time.sleep(retry_delay * (retry_count + 1) * 2)  # Longer delay for rate limiting
                        retry_count += 1
                        continue
                    else:
                        return None
                else:
                    response.raise_for_status()
                    
            except requests.exceptions.RequestException as e:
                retry_count += 1
                if retry_count < max_retries:
                    logger.warning(f"Download attempt {retry_count} failed for {url}: {e}")
                    time.sleep(retry_delay * retry_count)
                    continue
                else:
                    raise e
        
        content_type = response.headers.get('content-type', '').lower()
        if 'pdf' not in content_type and not filename.lower().endswith('.pdf'):
            logger.warning(f"Warning: Content-Type is {content_type}, not PDF")
        
        content_length = response.headers.get('content-length')
        if content_length:
            file_size_mb = int(content_length) / (1024 * 1024)
            if file_size_mb > max_mb:
                error_message = f"File too large: {file_size_mb:.1f}MB > {max_mb}MB"
                logger.error(error_message)
                status = "file_too_large"
                return None
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Downloaded: {file_path}")
        return str(file_path)
        
    except requests.exceptions.RequestException as e:
        error_message = f"Download failed: {str(e)}"
        logger.error(f"Download failed for {url}: {e}")
        status = "request_error"
        return None
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        logger.error(f"Unexpected error downloading {url}: {e}")
        status = "unexpected_error"
        return None
    finally:
        duration = time.time() - start_time
        log_data = {
            "url": url,
            "local_path": str(file_path) if file_path else None,
            "status": status,
            "error_message": error_message,
            "duration_sec": duration,
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        try:
            pg_client = PostgresClient()
            pg_client.insert_row("pdf_library", "download_logs", log_data)
            logger.debug(f"Download log saved to database for {url}")
        except Exception as e:
            logger.error(f"Failed to log download to DB: {e}")
        finally:
            if 'pg_client' in locals():
                pg_client.close() 