import os
from typing import Dict
from mcp import StdioServerParameters
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.db_utils.db_config import DatabaseConfig


class MCPServerConfig:
    """Configuration management for MCP server setup."""
    
    def __init__(self, db_config: DatabaseConfig = None):
        self.db_config = db_config or DatabaseConfig()
        self.database_url = self._build_database_url()
        self.environment = self._setup_environment()
        self.server_params = self._create_server_params()
    
    def _build_database_url(self) -> str:
        """Build PostgreSQL connection URL."""
        return (f"postgresql://{self.db_config.user}:{self.db_config.password}"
                f"@{self.db_config.host}:{self.db_config.port}/{self.db_config.database}")
    
    def _setup_environment(self) -> Dict[str, str]:
        """Setup environment variables for MCP server."""
        mcp_env = os.environ.copy()
        mcp_env.update({
            'DATABASE_URL': self.database_url,
            'POSTGRES_HOST': self.db_config.host,
            'POSTGRES_PORT': str(self.db_config.port),
            'POSTGRES_DB': self.db_config.database,
            'POSTGRES_USER': self.db_config.user,
            'POSTGRES_PASSWORD': self.db_config.password,
        })
        return mcp_env
    
    def _create_server_params(self) -> StdioServerParameters:
        """Create MCP server parameters."""
        return StdioServerParameters(
            command="npx",
            args=["@modelcontextprotocol/server-postgres", self.database_url],
            env=self.environment
        )
    
    @staticmethod
    def handle_mcp_error(error: Exception) -> None:
        """Handle MCP server connection errors."""
        print(f"Error connecting to PostgreSQL MCP server: {error}")
        print("Make sure the @modelcontextprotocol/server-postgres package is installed:")
        print("npm install -g @modelcontextprotocol/server-postgres")