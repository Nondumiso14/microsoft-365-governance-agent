import os
from dotenv import load_dotenv

load_dotenv()
class Settings: 
    AZURE_CLIENT_ID: str = os.getenv("AZURE_CLIENT_ID", "")
    AZURE_CLIENT_SECRET: str = os.getenv("AZURE_CLIENT_SECRET", "")
    AZURE_TENANT_ID: str = os.getenv("AZURE_TENANT_ID", "")
    AZURE_REDIRECT_URI: str = os.getenv("AZURE_REDIRECT_URI", "")
    GRAPH_API_ENDPOINT: str = os.getenv("GRAPH_API_ENDPOINT", "https://graph.microsoft.com/v1.0")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Anthropic / Claude
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY" , "")
    CLAUDE_ORCHESTRATOR_MODEL: str = os.getenv(
        "CLAUDE_ORCHESTRATOR_MODEL", "claude-sonnet-4-6"
    )
    
    CLAUDE_FAST_MODEL : str = os.getenv(
          "CLAUDE_FAST_MODEL", "claude-haiku-4-5-20251001"
    )

    # PostgreSQL
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:yourpassword@localhost:5432/m365_governance"
    )

    # App
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

settings=Settings()
