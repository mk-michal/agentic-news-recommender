import requests
import time
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RateLimiter:
    """Simple rate limiter to avoid API limits"""
    max_requests: int = 100
    time_window: int = 3600  # 1 hour in seconds
    requests_made: List[datetime] = None
    
    def __post_init__(self):
        if self.requests_made is None:
            self.requests_made = []
    
    def can_make_request(self) -> bool:
        """Check if we can make a request within rate limits"""
        now = datetime.now()
        # Remove requests older than time window
        self.requests_made = [req_time for req_time in self.requests_made 
                             if now - req_time < timedelta(seconds=self.time_window)]
        
        return len(self.requests_made) < self.max_requests
    
    def record_request(self):
        """Record that a request was made"""
        self.requests_made.append(datetime.now())
    
    def wait_time(self) -> int:
        """Calculate how long to wait before next request"""
        if not self.requests_made:
            return 0
        
        oldest_request = min(self.requests_made)
        wait_until = oldest_request + timedelta(seconds=self.time_window)
        wait_seconds = (wait_until - datetime.now()).total_seconds()
        
        return max(0, int(wait_seconds))


class NewsAPIConnector:
    """
    API connector for NewsAPI.ai with rate limiting and error handling
    """
    
    def __init__(self, api_key: str, base_url: str = "https://newsapi.ai/api/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.rate_limiter = RateLimiter()
        self.session = requests.Session()
        
        # Set default headers for JSON requests
        self.session.headers.update({
            'User-Agent': 'NewsAPI-Python-Client/1.0',
            'Content-Type': 'application/json'
        })
    
    def _handle_rate_limit(self):
        """Handle rate limiting by waiting if necessary"""
        if not self.rate_limiter.can_make_request():
            wait_time = self.rate_limiter.wait_time()
            if wait_time > 0:
                logger.warning(f"Rate limit reached. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
    
    def _make_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make HTTP POST request with JSON payload
        
        Args:
            endpoint: API endpoint
            payload: Request payload as dictionary
            
        Returns:
            API response as dictionary
            
        Raises:
            requests.exceptions.RequestException: For HTTP errors
            ValueError: For API errors
        """
        self._handle_rate_limit()
        
        # Add API key to payload
        payload['apiKey'] = self.api_key
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            logger.info(f"Making POST request to {endpoint}")
            logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
            
            response = self.session.post(url, json=payload, timeout=30)
            self.rate_limiter.record_request()
            
            # Check HTTP status
            response.raise_for_status()
            
            # Parse JSON response
            data = response.json()
            
            # Check API-specific errors
            if 'error' in data:
                error_msg = data['error'].get('message', 'Unknown API error')
                logger.error(f"API Error: {error_msg}")
                raise ValueError(f"NewsAPI Error: {error_msg}")
            
            articles_count = len(data.get('articles', {}).get('results', []))
            logger.info(f"Successfully retrieved {articles_count} articles")
            return data
            
        except requests.exceptions.Timeout:
            logger.error("Request timed out")
            raise requests.exceptions.RequestException("Request timed out after 30 seconds")
        
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                logger.error("Rate limit exceeded")
                raise requests.exceptions.RequestException("Rate limit exceeded. Please try again later.")
            elif response.status_code == 401:
                logger.error("Invalid API key")
                raise requests.exceptions.RequestException("Invalid API key")
            elif response.status_code == 400:
                logger.error("Bad request parameters")
                raise requests.exceptions.RequestException("Bad request parameters")
            else:
                logger.error(f"HTTP Error {response.status_code}: {e}")
                raise
        
        except requests.exceptions.ConnectionError:
            logger.error("Connection error")
            raise requests.exceptions.RequestException("Failed to connect to NewsAPI")
        
        except json.JSONDecodeError:
            logger.error("Invalid JSON response")
            raise requests.exceptions.RequestException("Invalid JSON response from API")
        
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise
    
    def search_articles(
        self, 
        keyword: str, 
        articles_count: int = 10,
        articles_page: int = 1,
        articles_sort_by: str = "date",
        articles_sort_by_asc: bool = False,
        source_location_uri: Optional[List[str]] = None,
        ignore_source_group_uri: Optional[str] = None,
        data_type: Optional[List[str]] = None,
        force_max_data_time_window: int = 31,
        result_type: str = "articles"
    ) -> Dict[str, Any]:
        """
        Search for articles using NewsAPI.ai
        
        Args:
            keyword: Search keyword or phrase
            articles_count: Number of articles to retrieve (default: 10, max: 100)
            articles_page: Page number for pagination (default: 1)
            articles_sort_by: Sort order ("date", "rel", "sourceImportanceRank", "sourceAlexaGlobalRank", "sourceAlexaCountryRank", "socialScore", "facebook", "googlePlus", "linkedin", "pinterest", "reddit", "stumbleUpon", "twitter")
            articles_sort_by_asc: Sort ascending if True, descending if False
            source_location_uri: List of location URIs to filter sources
            ignore_source_group_uri: Source group URI to ignore (e.g., "paywall/paywalled_sources")
            data_type: List of data types to include (default: ["news", "pr"])
            force_max_data_time_window: Maximum number of days to search back (default: 31)
            result_type: Type of result to return (default: "articles")
            
        Returns:
            Dictionary containing search results
            
        Raises:
            ValueError: For invalid parameters
            requests.exceptions.RequestException: For API errors
        """
        # Validate parameters
        if not keyword or not keyword.strip():
            raise ValueError("Keyword cannot be empty")
        
        if not isinstance(articles_count, int) or articles_count < 1 or articles_count > 100:
            raise ValueError("articles_count must be an integer between 1 and 100")
        
        if not isinstance(articles_page, int) or articles_page < 1:
            raise ValueError("articles_page must be a positive integer")
        
        valid_sort_options = [
            "date", "rel", "sourceImportanceRank", "sourceAlexaGlobalRank", 
            "sourceAlexaCountryRank", "socialScore", "facebook", "googlePlus", 
            "linkedin", "pinterest", "reddit", "stumbleUpon", "twitter"
        ]
        if articles_sort_by not in valid_sort_options:
            raise ValueError(f"articles_sort_by must be one of: {', '.join(valid_sort_options)}")
        
        # Set default values
        if data_type is None:
            data_type = ["news", "pr"]
        
        if source_location_uri is None:
            source_location_uri = [
                "https://en.wikipedia.org/wiki/Czech_Republic",
                # "http://en.wikipedia.org/wiki/United_States",
                # "http://en.wikipedia.org/wiki/Canada",
                # "http://en.wikipedia.org/wiki/United_Kingdom"
            ]
        
        # Build request payload
        payload = {
            "action": "getArticles",
            "keyword": keyword.strip(),
            "sourceLocationUri": source_location_uri,
            "articlesPage": articles_page,
            "articlesCount": articles_count,
            "articlesSortBy": articles_sort_by,
            "articlesSortByAsc": articles_sort_by_asc,
            "dataType": data_type,
            "forceMaxDataTimeWindow": force_max_data_time_window,
            "resultType": result_type
        }
        
        # Add optional parameters
        if ignore_source_group_uri:
            payload["ignoreSourceGroupUri"] = ignore_source_group_uri
        
        try:
            return self._make_request('article/getArticles', payload)
        
        except Exception as e:
            logger.error(f"Failed to search articles for keyword '{keyword}': {str(e)}")
            raise
    
    def get_article_details(self, article_uri: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific article
        
        Args:
            article_uri: Unique article URI
            
        Returns:
            Dictionary containing article details
        """
        if not article_uri:
            raise ValueError("Article URI cannot be empty")
        
        payload = {
            "action": "getArticle",
            "articleUri": article_uri,
            "resultType": "info"
        }
        
        try:
            return self._make_request('article/getArticle', payload)
        
        except Exception as e:
            logger.error(f"Failed to get article details for URI '{article_uri}': {str(e)}")
            raise
    
    def search_articles_with_custom_payload(self, custom_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search for articles using a custom payload
        
        Args:
            custom_payload: Custom request payload (apiKey will be added automatically)
            
        Returns:
            Dictionary containing search results
        """
        try:
            return self._make_request('article/getArticles', custom_payload)
        
        except Exception as e:
            logger.error(f"Failed to search articles with custom payload: {str(e)}")
            raise
    
    def close(self):
        """Close the session"""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Example usage
if __name__ == "__main__":
    # Initialize connector (replace with your actual API key)
    api_key = "your-newsapi-key-here"
    
    try:
        with NewsAPIConnector(api_key) as connector:
            # Search for articles with default parameters
            results = connector.search_articles(
                keyword="Tesla Inc",
                articles_count=10,
                articles_sort_by="date",
                ignore_source_group_uri="paywall/paywalled_sources"
            )
            
            print(f"Found {len(results.get('articles', {}).get('results', []))} articles")
            
            # Print article titles and sources
            for article in results.get('articles', {}).get('results', []):
                title = article.get('title', 'No title')
                source = article.get('source', {}).get('title', 'Unknown source')
                date = article.get('dateTime', 'Unknown date')
                print(f"- {title} ({source}) - {date}")
            
            # Example with custom payload matching the documentation
            custom_payload = {
                "action": "getArticles",
                "keyword": "artificial intelligence",
                "sourceLocationUri": [
                    "http://en.wikipedia.org/wiki/United_States",
                    "http://en.wikipedia.org/wiki/Canada",
                    "http://en.wikipedia.org/wiki/United_Kingdom"
                ],
                "ignoreSourceGroupUri": "paywall/paywalled_sources",
                "articlesPage": 1,
                "articlesCount": 5,
                "articlesSortBy": "date",
                "articlesSortByAsc": False,
                "dataType": ["news", "pr"],
                "forceMaxDataTimeWindow": 31,
                "resultType": "articles"
            }
            
            custom_results = connector.search_articles_with_custom_payload(custom_payload)
            print(f"\nCustom search found {len(custom_results.get('articles', {}).get('results', []))} articles")
                
    except Exception as e:
        print(f"Error: {e}")