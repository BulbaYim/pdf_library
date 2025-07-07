import os
import json
import logging
from typing import Dict, Optional
from openai import OpenAI, OpenAIError
from database.postgres_client import PostgresClient
import datetime
import time
from dotenv import load_dotenv
import threading

load_dotenv()

logger = logging.getLogger(__name__)

class MetadataExtractor:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-3.5-turbo",
        max_tokens: int = 300,
        temperature: float = 0.0,
        requests_per_minute: int = 60,
    ):
        """
        Initialize the metadata extractor.

        Args:
            api_key: OpenAI API key
            model: Model to use for extraction
            max_tokens: Max tokens in response
            temperature: Sampling temperature
            requests_per_minute: Rate limit for API calls
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY env var not set and api_key not provided.")

        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # Rate limiting
        self.requests_per_minute = requests_per_minute
        self.request_times = []
        self.rate_limit_lock = threading.Lock()
    
    def _rate_limit(self):
        """Simple rate limiter to respect API limits."""
        with self.rate_limit_lock:
            current_time = time.time()
            # Remove requests older than 1 minute
            self.request_times = [t for t in self.request_times if current_time - t < 60]
            
            if len(self.request_times) >= self.requests_per_minute:
                # Wait until we can make another request
                sleep_time = 60 - (current_time - self.request_times[0])
                if sleep_time > 0:
                    logger.info(f"Rate limit reached, waiting {sleep_time:.1f} seconds")
                    time.sleep(sleep_time)
                    current_time = time.time()
            
            self.request_times.append(current_time)

    def extract(self, 
                input_text: str, 
                prompt: str,
                sys_prompt: str,
                responce_keys: Optional[list] = None
                ) -> Dict[str, Optional[str]]:
        """
        Extract metadata from input text and log the extraction process to PostgreSQL.

        Args:
            input_text: The text to analyze.
            prompt: User prompt template.
            sys_prompt: System prompt.
            responce_keys: Expected response keys.

        Returns:
            Dict of metadata fields.
        """
        if sys_prompt is None:
            sys_prompt = ""
        if prompt is None:
            prompt = ""
        if input_text is None:
            input_text = ""
        prompt = str(prompt).format(input_text=str(input_text))
        start_time = time.time()
        status = "success"
        error_message = None
        metadata = None
        content = ""
        
        try:
            # Apply rate limiting
            self._rate_limit()
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            content = response.choices[0].message.content
            logger.info(f"Raw response: {content}")
            if content is None:
                content = ""
            else:
                content = content.strip()
            
            # Clean up markdown code blocks if present
            if content.startswith("```json"):
                content = content[7:]  # Remove ```json
            if content.endswith("```"):
                content = content[:-3]  # Remove ```
            content = content.strip()
            
            metadata = json.loads(content)
        except OpenAIError as e:
            logger.error("OpenAI API error: %s", e)
            status = "openai_error"
            error_message = str(e)
            metadata = {}
            content = ""
        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON: %s\nRaw response:\n%s", e, content)
            status = "json_error"
            error_message = f"JSONDecodeError: {e}"
            metadata = {}
        except Exception as e:
            logger.error("Unexpected error: %s", e)
            status = "unexpected_error"
            error_message = str(e)
            metadata = {}
        duration = time.time() - start_time
        if responce_keys:
            for key in responce_keys:
                metadata.setdefault(key, None)
        pg_client = PostgresClient()
        log_data = {
            "sys_prompt": sys_prompt,
            "prompt": prompt,
            "response": content,
            "status": status,
            "error_message": error_message,
            "duration_sec": duration,
            "timestamp": datetime.datetime.now(),
        }
        try:
            pg_client.insert_row("pdf_library", "extraction_logs", log_data)
        except Exception as e:
            logger.error("Failed to log extraction to DB: %s", e)
        finally:
            pg_client.close()
        return metadata 