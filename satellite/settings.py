from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Settings:
    root: Path = ROOT
    pdf: Path = ROOT / 'data' / 'mss-reference-v2.pdf'
    db: Path = ROOT / 'data' / 'index.sqlite'
    api_key: str = ''
    chat_model: str = 'gpt-4.1-mini'
    embedding_model: str = 'text-embedding-3-small'
    ai_provider: str = 'openai'

    @property
    def embeddings_enabled(self):
        return self.ai_provider == 'openai'

    @classmethod
    def load(cls):
        load_dotenv(ROOT / '.env', override=False)
        provider = os.getenv('AI_PROVIDER', 'openai').strip().lower()
        if provider not in {'openai', 'gemini'}:
            raise ValueError('AI_PROVIDER must be openai or gemini')
        key = os.getenv('GEMINI_API_KEY' if provider == 'gemini' else 'OPENAI_API_KEY', '').strip()
        if key in {'your-key-here', 'sk-your-key-here'}:
            key = ''
        return cls(api_key=key, ai_provider=provider,
                   chat_model=(os.getenv('GEMINI_MODEL', 'gemini-2.5-flash') if provider == 'gemini'
                               else os.getenv('CHAT_MODEL', 'gpt-4.1-mini')).strip(),
                   embedding_model=os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small').strip())
