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

    @classmethod
    def load(cls):
        load_dotenv(ROOT / '.env', override=False)
        key = os.getenv('OPENAI_API_KEY', '').strip()
        if key in {'your-key-here', 'sk-your-key-here'}:
            key = ''
        return cls(api_key=key,
                   chat_model=os.getenv('CHAT_MODEL', 'gpt-4.1-mini').strip(),
                   embedding_model=os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small').strip())
