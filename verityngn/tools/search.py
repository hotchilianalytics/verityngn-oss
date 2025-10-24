import logging
from typing import Dict, Any, List
from langchain_community.utilities import GoogleSearchAPIWrapper
from langchain_community.tools.google_search import GoogleSearchRun

class SearchTool:
    """Tool for performing web searches."""
    
    def __init__(self, api_key: str, cse_id: str):
        """
        Initialize the search tool.
        
        Args:
            api_key (str): Google Search API key
            cse_id (str): Custom Search Engine ID
        """
        self.api_key = api_key
        self.cse_id = cse_id
        self.logger = logging.getLogger(__name__)
        
        # Initialize the search wrapper
        self.search_wrapper = GoogleSearchAPIWrapper(
            google_api_key=api_key,
            google_cse_id=cse_id
        )
        
        # Initialize the search tool
        self.search_tool = GoogleSearchRun(
            api_wrapper=self.search_wrapper
        )
    
    def search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Perform a web search.
        
        Args:
            query (str): Search query
            num_results (int): Number of results to return
            
        Returns:
            List[Dict[str, Any]]: Search results
        """
        try:
            # Set the number of results
            self.search_wrapper.k = num_results
            
            # Perform the search
            results = self.search_wrapper.results(query, num_results)
            
            # Format the results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "title": result.get("title", ""),
                    "link": result.get("link", ""),
                    "snippet": result.get("snippet", "")
                })
            
            self.logger.info(f"Search for '{query}' returned {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Error performing search: {e}")
            return []
    
    def run_search(self, query: str) -> str:
        """
        Run a search and return the results as a string.
        
        Args:
            query (str): Search query
            
        Returns:
            str: Search results as a string
        """
        try:
            # Run the search tool
            result = self.search_tool.run(query)
            self.logger.info(f"Search for '{query}' completed")
            return result
            
        except Exception as e:
            self.logger.error(f"Error running search: {e}")
            return f"Error performing search: {str(e)}" 