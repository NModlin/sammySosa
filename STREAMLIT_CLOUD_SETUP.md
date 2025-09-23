# Streamlit Cloud Setup Guide

## Database Configuration for Streamlit Cloud

To run this application on Streamlit Cloud, you need to configure database secrets.

### Step 1: Set up a PostgreSQL Database

You can use any cloud PostgreSQL provider:
- **Supabase** (Free tier available): https://supabase.com
- **Neon** (Free tier available): https://neon.tech
- **Railway** (Free tier available): https://railway.app
- **Heroku Postgres** (Paid): https://www.heroku.com/postgres
- **AWS RDS** (Paid): https://aws.amazon.com/rds/

### Step 2: Configure Streamlit Secrets

1. Go to your Streamlit Cloud app dashboard
2. Click on your app
3. Click on "Settings" (gear icon)
4. Go to the "Secrets" tab
5. Add the following configuration:

```toml
# Database Configuration
[database]
host = "your-database-host.com"
port = "5432"
database = "sam_contracts"
username = "your-username"
password = "your-password"

# API Keys
SAM_API_KEY = "your-sam-api-key-here"
SLACK_WEBHOOK_URL = "your-slack-webhook-url-here"

# Optional Configuration
API_KEY_EXPIRATION_DATE = "2025-12-21"
```

### Step 3: Database Setup

The application will automatically create the required tables when it first connects to your database.

### Step 4: Get SAM.gov API Key

1. Go to https://sam.gov/data-services
2. Register for an account
3. Request an API key
4. Add the key to your Streamlit secrets

### Demo Mode

If you don't want to set up a database immediately, the application will offer a "Demo Mode" that shows sample data without database functionality.

## Local Development

For local development, use Docker:

```bash
docker compose up -d
```

This will start both the application and PostgreSQL database locally.

## Environment Variables

You can also use environment variables instead of Streamlit secrets:

- `GOVCON_DB_URL`: Full PostgreSQL connection string
- `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_PORT`: Individual database parameters
- `SAM_API_KEY`: Your SAM.gov API key
- `SLACK_WEBHOOK_URL`: Your Slack webhook URL

## Troubleshooting

### Database Connection Issues

1. **Check your database credentials** in the secrets configuration
2. **Verify database accessibility** - make sure your database allows connections from Streamlit Cloud
3. **Check database name** - ensure the database exists
4. **Use Demo Mode** if you just want to see the interface

### API Issues

1. **SAM.gov API Key** - Make sure your API key is valid and not expired
2. **Rate Limits** - SAM.gov has rate limits, so don't run the scraper too frequently

### Performance

- The application uses caching to improve performance
- Database queries are optimized with proper indexing
- Large datasets may take time to load initially
