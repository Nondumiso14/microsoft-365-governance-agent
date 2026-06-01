import os 
from dotenv import load_dotenv

load_dotenv()

class Settings:

    # Microsoft Azure / MSAL 
    # Azure App Registration
    # Azure Portal → App registrations → your app → Overview

    # What it is: your app's unique ID in Azure
    # Where to find it: Azure Portal → App registrations → Application (client) ID
    AZURE_CLIENT_ID: str = os.getenv("AZURE_CLIENT_ID", "")

    # What it is: your app's password — like a PIN for your app
    # Where to find it: Azure Portal → Certificates & secrets → Client secrets
    # IMPORTANT: copy it immediately after creating — you cannot see it again
    AZURE_CLIENT_SECRET: str = os.getenv("AZURE_CLIENT_SECRET", "")

    # What it is: your company's Microsoft 365 ID
    # Where to find it: Azure Portal → App registrations → Directory (tenant) ID
    AZURE_TENANT_ID: str = os.getenv("AZURE_TENANT_ID", "")

    # What it is: where Microsoft sends the user back after login
    # Must match EXACTLY what you registered in Azure Portal
    AZURE_REDIRECT_URI: str = os.getenv("AZURE_REDIRECT_URI", "")

    # What it is: the base URL for all Microsoft Graph calls
    # v1.0 is the stable production version — always use this
    GRAPH_API_ENDPOINT: str = os.getenv("GRAPH_API_ENDPOINT", "https://graph.microsoft.com/v1.0")


    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # What it is: your key to access Claude's API
    # Where to get it: console.anthropic.com → API Keys
    ANTHROPIC_API_KEY : str = os.getenv("ANTHROPIC_API_KEY", "")

     # What it is: the Claude model used for deep reasoning
    # Used by: policy_agents.py, orchestrator.py
    # Why Sonnet: smarter model for complex governance decisions
    CLAUDE_ORCHESTRATION_MODEL: str = os.getenv("CLAUDE_FAST_MODEL", "claude-haiku-4-5-20251001")

    #DATABASE_URL PostgreSQL
    #PostgreSQL Database
     # What it is: the connection string for your PostgreSQL database
    # Format: postgresql://username:password@host:port/database_name
    # Your pgAdmin credentials go here
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    #APP
    # Values: "development" or "production"
    # Controls: SQL logging, debug endpoints like /dev/reset
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Values: DEBUG, INFO, WARNING, ERROR
    # NOTE: INFO is the right level for development
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# Single shared instance
# Import THIS — never instantiate Settings() in other files
settings = Settings()