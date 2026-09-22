from pathlib import Path
import re
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator, ValidationError
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .settings import ROOT, Settings
from .index import get_chunks, public_source, search, status
from .cloud import Cloud, CloudError

Language = Literal['en', 'zh-TW']


class Turn(BaseModel):
    role: Literal['user', 'assistant']
    content: str = Field(max_length=12000)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    language: Language = 'en'
    history: list[Turn] = Field(default_factory=list, max_length=12)

    @field_validator('question')
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError('Question is empty')
        return value.strip()


class Section(BaseModel):
    kind: Literal['evidence', 'analogy', 'background', 'limitation']
    text: str = Field(min_length=1, max_length=10000)
    citations: list[str] = Field(max_length=12)


class TranslationRequest(BaseModel):
    language: Language
    sections: list[Section] = Field(min_length=1, max_length=16)


def validate_sections(raw, sources):
    try:
        if not isinstance(raw, list) or not 1 <= len(raw) <= 16:
            raise ValueError()
        sections = [Section.model_validate(section).model_dump() for section in raw]
        allowed = {source['id'] for source in sources}
        for section in sections:
            if (set(section['citations']) - allowed or
                    (section['kind'] == 'evidence' and not section['citations'])):
                raise CloudError('citation_error')
        return sections
    except (ValidationError, TypeError, ValueError):
        raise CloudError('provider_format') from None


def limitation(text):
    return [{'kind': 'limitation', 'text': text, 'citations': []}]


SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'Referrer-Policy': 'no-referrer',
    'Cache-Control': 'no-store',
    'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'self'; frame-src 'self'; frame-ancestors 'self'; base-uri 'none'; form-action 'self'",
}


def create_app(settings=None, cloud=None):
    settings = settings or Settings.load()
    cloud = cloud or Cloud(settings)
    app = FastAPI(title='Orbit Satellite Learning', docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=['127.0.0.1', 'localhost'])

    @app.middleware('http')
    async def local_only(request: Request, call_next):
        if request.method == 'POST':
            origin = request.headers.get('origin')
            if origin is not None:
                if origin != 'http://' + request.headers.get('host', ''):
                    return JSONResponse({'detail': {'code': 'cross_origin'}}, status_code=403, headers=SECURITY_HEADERS)
            if request.headers.get('sec-fetch-site') == 'cross-site':
                return JSONResponse({'detail': {'code': 'cross_origin'}}, status_code=403, headers=SECURITY_HEADERS)
            # Read bounded bodies even when no Content-Length is supplied.
            size, body = 0, []
            async for chunk in request.stream():
                size += len(chunk)
                if size > 180000:
                    return JSONResponse({'detail': {'code': 'request_too_large'}}, status_code=413, headers=SECURITY_HEADERS)
                body.append(chunk)
            request._body = b''.join(body)
        response = await call_next(request)
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value
        return response

    @app.exception_handler(CloudError)
    async def cloud_error(request, exc):
        return JSONResponse({'detail': {'code': exc.code}}, status_code=503 if exc.code in {'missing_key', 'missing_prompt'} else 502, headers=SECURITY_HEADERS)

    @app.get('/')
    def home():
        return FileResponse(ROOT / 'static' / 'index.html')

    @app.get('/api/status')
    def app_status():
        return status(settings)

    @app.get('/static/app.js')
    def javascript():
        # Windows registry MIME associations can incorrectly classify .js as text/plain.
        return FileResponse(ROOT / 'static' / 'app.js', media_type='application/javascript')

    @app.get('/document')
    def document():
        if not settings.pdf.is_file():
            raise HTTPException(404, detail={'code': 'missing_document'})
        return FileResponse(settings.pdf, media_type='application/pdf',
                            headers={'Content-Disposition': 'inline; filename="MSS-Reference-Architecture-v2.pdf"'})

    @app.post('/api/chat')
    def chat(payload: ChatRequest):
        info = status(settings)
        if not info['chunks']:
            raise HTTPException(503, detail={'code': 'missing_index'})
        # Resolve short follow-ups using recent user questions, not assistant instructions.
        short_followup = (len(payload.question) < 150 and bool(
            re.search(r'\b(it|its|they|them|that|those|these)\b|^(tell me more|why[?？.! ]*$|explain more)', payload.question, re.I)
            or re.search(r'^(再說|再解釋|多說|詳細說|為什麼[？?。！!]*$)|它|這個|這些|那個', payload.question)))
        query = payload.question
        if short_followup:
            previous = [turn.content for turn in payload.history if turn.role == 'user'][-2:]
            if previous:
                query += '\n' + '\n'.join(previous)
        vector, retrieval_warning = None, None
        if settings.api_key and settings.embeddings_enabled and info['embedded_chunks']:
            try:
                vector = cloud.embed([query])[0]
            except CloudError:
                retrieval_warning = 'keyword_fallback'
        sources = search(settings, query, vector=vector)
        if not sources:
            text = ('目前找不到足以回答這個問題的文件段落。請改用衛星相關術語，或選擇學習主題。' if payload.language == 'zh-TW' else
                    'I could not find document passages that support an answer. Try a satellite term or choose a learning topic.')
            return {'mode': 'no_evidence', 'sections': limitation(text), 'sources': [], 'retrieval': 'keyword', 'warning': retrieval_warning}
        if not settings.api_key:
            text = ('尚未設定所選 AI 服務的 API 金鑰。目前顯示的是文件搜尋結果，而非 AI 解答。你可以閱讀右側的英文原文，或開啟引用頁面。啟用 AI 後即可取得中文說明。' if payload.language == 'zh-TW' else
                    'The selected AI provider API is not connected yet. These are document search results, not an AI answer. Read the original excerpts in Sources or open their PDF pages. Connect AI to receive explanations.')
            return {'mode': 'search', 'sections': limitation(text), 'sources': sources, 'retrieval': 'keyword', 'warning': None}
        raw = cloud.answer(payload.question, payload.language, [turn.model_dump() for turn in payload.history], sources)
        sections = validate_sections(raw, sources)
        return {'mode': 'answer', 'sections': sections, 'sources': sources,
                'retrieval': 'hybrid' if vector is not None else 'keyword', 'warning': retrieval_warning}

    @app.post('/api/translate')
    def translate(payload: TranslationRequest):
        original = [section.model_dump() for section in payload.sections]
        ids = {chunk_id for section in original for chunk_id in section['citations']}
        sources = [public_source(chunk) for chunk in get_chunks(settings, ids)]
        validate_sections(original, sources)
        translated = validate_sections(cloud.translate(original, payload.language), sources)
        if len(original) != len(translated) or any(a['kind'] != b['kind'] or a['citations'] != b['citations'] for a, b in zip(original, translated)):
            raise CloudError('citation_error')
        return {'sections': translated, 'sources': sources}

    app.mount('/static', StaticFiles(directory=ROOT / 'static', check_dir=False), name='static')
    return app
