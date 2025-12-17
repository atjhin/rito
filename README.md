# Rito — League of Legends Story Generator

A web application that generates dynamic stories featuring League of Legends champions using LangGraph and multiple AI models (Grok-4, Gemini, GPT).

## Project Structure

```
rito/
├── src/                      # Main application source code
│   ├── __init__.py
│   ├── app.py                # Flask app factory
│   ├── routes.py             # API routes
│   ├── config/               # Configuration modules
│   │   ├── __init__.py
│   │   ├── settings.py       # Paths & environment config
│   │   └── llm.py            # LLM model configurations
│   ├── agents/               # LangGraph agents
│   │   ├── __init__.py
│   │   ├── base.py           # Base Agent class
│   │   ├── champion.py       # Champion roleplay agent
│   │   ├── event_creator.py  # Story event generator
│   │   ├── novel_writer.py   # Narrative writer
│   │   ├── role_assigner.py  # Turn-based role assignment
│   │   ├── summarizer.py     # Conversation summarizer
│   │   └── factory.py        # AgentFactory
│   ├── core/                 # Core business logic
│   │   ├── __init__.py
│   │   ├── story_teller.py   # Main LangGraph orchestrator
│   │   ├── logger.py         # Checkpoint logging to S3
│   │   └── lore.py           # Champion lore utilities
│   ├── schemas/              # Data models & types
│   │   ├── __init__.py
│   │   ├── state.py          # AgentState TypedDict
│   │   ├── agent_config.py   # Agent configuration dataclasses
│   │   ├── story_config.py   # StoryTellerItem
│   │   └── roles.py          # Champion & system roles
│   ├── services/             # External service integrations
│   │   ├── __init__.py
│   │   └── s3.py             # AWS S3 operations
│   └── logs/                 # Runtime logs directory
├── static/                   # Frontend static files
│   ├── css/
│   │   └── styles.css
│   └── js/
│       └── app.js
├── templates/                # Jinja2 HTML templates
│   └── index.html
├── data/                     # Static data files
│   └── champions.txt         # Champion list with temperature settings
├── scripts/                  # Utility scripts
│   └── data_extraction/      # Data scraping utilities
├── run.py                    # Application entry point
├── requirements.txt          # Python dependencies
├── Dockerfile               # Container configuration
└── README.md
```

## Features

- **Multi-Agent Story Generation**: Uses LangGraph to orchestrate multiple AI agents for collaborative storytelling
- **Champion Roleplay**: Each League of Legends champion is represented by an AI agent with personality and lore
- **Event-Driven Narrative**: Automatic story event generation with pacing control
- **Novel-Quality Output**: Final stories are polished by a dedicated writer agent
- **Multiple AI Providers**: Supports Google Gemini, OpenAI GPT, and xAI Grok models

## Prerequisites

- Python 3.11+
- AWS S3 credentials (for champion lore storage)
- API keys for LLM providers:
  - `GOOGLE_API_KEY` - Google Gemini
  - `OPENAI_API_KEY` - OpenAI GPT (optional)
  - `XAI_API_KEY` - xAI Grok

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/rito.git
cd rito
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your API keys:
```env
GOOGLE_API_KEY=your_google_api_key
OPENAI_API_KEY=your_openai_api_key
XAI_API_KEY=your_xai_api_key
S3_ACCESS_KEY=your_s3_access_key
S3_SECRET_KEY=your_s3_secret_key
S3_REGION=your_s3_region
S3_BUCKET=your_s3_bucket
```

## Running the Application

### Development
```bash
python run.py
```

The application will be available at `http://localhost:5000`

### Docker
```bash
docker build -t rito .
docker run -p 5000:5000 --env-file .env rito
```

## API Endpoints

- `GET /` - Main web interface
- `POST /submit-data` - Generate a story with provided champions and scenario

### Request Format
```json
{
  "story": "Twisted Fate and Zed meet at a coffee shop",
  "characters": [
    {
      "name": "Twisted Fate",
      "personality": "charming",
      "models": ["Grok-4"]
    },
    {
      "name": "Zed",
      "personality": "mysterious",
      "models": ["Grok-4"]
    }
  ]
}
```

## Architecture

The story generation pipeline uses LangGraph with the following flow:

1. **EventCreatorBot** - Generates story events based on the scenario
2. **RoleAssignerBot** - Determines which champion speaks next
3. **Champion Agents** - Roleplay as their respective champions
4. **SummarizerBot** - Compresses conversation history
5. **NovelWriterBot** - Transforms the script into polished prose

## License

MIT License
