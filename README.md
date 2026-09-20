# Orbit - Satellite Learning

A personal website for learning satellite systems from **MSS Reference Architecture Version 2.0**. English is the default; the top-right switch changes the interface and future replies to Mandarin in Traditional Chinese. The supplied PDF stays in its original English.

## Open the website

1. On this PC, double-click **Start.cmd**. The environment and local document index have already been prepared.
2. Open **http://127.0.0.1:8765** if your browser does not open automatically.
3. Ask a question or choose a learning topic. The right panel shows original passages with links to their PDF pages.

Keep the launch window open. Press **Ctrl+C** in that window to stop the app. If a server is already running, Start.cmd simply opens it; close its original server window before restarting after configuration changes. There are no accounts and no public deployment.

If you move the project to another PC, or its Python runtime changes, recreate the virtual environment using **Setup.cmd**. It installs the locked Python dependencies and rebuilds the index. Python 3.12+ and an internet connection for installation are required. Copy the source folder without `.venv` when moving it; virtual environments are not portable.

## Enable AI explanations and translation

Without an API key, the application is deliberately **document search only**. It does not generate answers or pretend that excerpts are an AI response. Chinese search uses a small satellite-term dictionary in this mode; unfamiliar Chinese phrasing may need English technical terms.

1. Copy **.env.example** to **.env** in this folder. Ensure Windows has not appended `.txt`.
2. Edit `.env` locally and set `OPENAI_API_KEY=your-real-key`. Do not paste your key into chat or a browser field. Obtain a key from your OpenAI API account; API billing is separate from using this Codex conversation.
3. Double-click **Enable-AI.cmd**. It sends the extracted passages to OpenAI and stores embeddings in the local SQLite index. Completed batches are cached, so retrying resumes incomplete work.
4. Stop and restart the app with **Start.cmd**. The status badge reports AI + hybrid search when all chunks have embeddings for the configured model.

An API key without embeddings still permits AI answers over local keyword retrieval. Changing `EMBEDDING_MODEL` requires running Enable-AI.cmd again. Changing `CHAT_MODEL` requires restarting. Defaults are `gpt-4.1-mini` and `text-embedding-3-small`.

No key was available during initial development. The shipped index contains real extracted text and keyword search data, with no fabricated vectors. See **VERIFICATION.md** for what was tested and what still requires credentials.

## Learn step by step

1. **Orbits:** What are LEO, MEO, and GEO? (PDF pp. 15-17.)
2. **System segments:** How do users, satellites, and ground equipment connect? (pp. 18, 21-41.)
3. **Payloads:** How do transparent and regenerative architectures differ? (pp. 18-25.)
4. **Mobile networks:** Where do radio access and core networks fit? (pp. 22-35, 65-75.)
5. **Coordination and services:** How are beams and resources managed? How do NR and NB-IoT share infrastructure? (pp. 36-39, 46-64, 76-91.)

Ask follow-up questions, inspect the sources, and use **Translate to Chinese / Translate to English** on individual AI answers. The original answer and its citations are preserved. Switching interface language does not rewrite old messages. Conversations live only in browser memory and disappear on reload or **New conversation**.

## How RAG works here

`PDF → page/section passages → local keyword + vector index → relevant passages → tutor → cited explanation`

RAG means retrieval-augmented generation. This application does not retrain the model. It selects document passages at question time and asks the model to explain them. Explanations distinguish document facts, analogies, extra background, and limitations. Citations are validated against the retrieved chunk IDs before the server returns an answer. That verifies provenance, not whether every natural-language claim is correct; inspect cited passages for technical decisions.

Text extraction can miss diagram arrows, embedded labels, formulas, and table alignment. Figure and table passages carry warnings. Figure 43 on page 80 is mostly visual. Page 39's EIRP row and footnote use inconsistent dBW/dBm units; do not silently resolve this ambiguity. The app links to the original PDF for inspection and does not claim to understand unextracted diagram details.

The PDF is a versioned reference, not a live source for the latest standard or deployment status. The app has no browsing tools. Instructions inside source text are treated as untrusted document content.

## Data and costs

- **Local:** original PDF, extracted text, section/page metadata, keyword index, cached vectors, runtime prompt, and credentials in `.env`.
- **Sent to OpenAI:** extracted text during optional embedding; question and bounded recent context plus selected passages for answers; selected answer text for translation. API requests use `store:false` for generated responses. Provider handling still follows your API account's policies; this is not an offline or zero-retention guarantee.
- **Never in browser assets:** your API key. The app does not save chat transcripts or call web search.
- **Billing:** embedding, answer, and translation requests use your separately billed API account. No automatic paid embedding job runs at server startup.

## Files and commands

`AGENTS.md` guides coding agents. `prompts/tutor.md` is the actual tutor prompt, read by the server. `data/mss-reference-v2.pdf` is an unchanged copy of your source; `data/index.sqlite` and `data/extraction-report.json` hold the index and page coverage.

In PowerShell, from this folder:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m satellite.ingest --check
.\.venv\Scripts\python.exe -m satellite.ingest         # local rebuild; preserves unchanged embeddings
.\.venv\Scripts\python.exe -m satellite.ingest --embed # paid cloud embedding; key required
node --check static/app.js
```

Browser checks: install Playwright in a separate development environment, then run `node tests/browser-smoke.cjs` while the app is running. `PLAYWRIGHT_MODULE` can point to an existing Playwright installation. The test uses Microsoft Edge headless, tests real local retrieval, and substitutes only AI responses for translation UI checks. It never claims those fixtures are live model output.

Local endpoints: `GET /api/status`, `POST /api/chat` (`question`, `language`, `history`), `POST /api/translate` (`sections`, `language`), and `GET /document`. No endpoint accepts arbitrary document paths or URLs. Chat returns sections with validated citation IDs and page-bearing source objects. Requests are bounded; cross-origin POSTs and non-local hostnames are rejected.

## Troubleshooting

- **No AI answer:** open **Connect AI** and follow the instructions above. Do not enter the key in the question box.
- **Wrong or rejected key:** edit the local `.env`, check your API account, then stop and restart.
- **Rate/quota limit:** check API billing and provider limits. The application does not silently retry paid requests.
- **Cannot connect:** run Start.cmd, keep its server window open, and use the exact localhost address above. If port 8765 belongs to a different program, close that program or change both the launcher and test URL deliberately.
- **Missing PDF:** put the original document at `data/mss-reference-v2.pdf`, then run Setup.cmd. You can also run `powershell -File Setup.ps1 -SourcePdf "C:\path\reference.pdf"` when this file is absent.
- **Index is incomplete:** run the local indexing command. For semantic search, rerun Enable-AI.cmd after checking the key; completed batches remain cached.
- **Empty sources:** try the English acronym or select a topic. The assistant should admit missing evidence rather than invent an answer.

---

# 中文快速入門

這是一個在你的 Windows 電腦上執行的個人衛星學習網站，以 **MSS 參考架構第 2.0 版**為主要來源。

## 開始使用

1. 按兩下 **Start.cmd**，開啟 **http://127.0.0.1:8765**。
2. 右上角選擇 **繁體中文**。介面與後續解答將使用中文，原有訊息保持不變。
3. 選擇學習主題或直接提問。右側會顯示英文原文，點選頁碼即可查看 PDF。
4. 保持啟動視窗開啟；在該視窗按 **Ctrl+C** 可停止網站。重新整理或「開啟新對話」會清除本次對話。

## 啟用 AI

目前未設定 API 金鑰時，網站只提供真實的文件搜尋，不會假裝產生 AI 解答。

1. 將 **.env.example** 複製為 **.env**，注意副檔名不要變成 `.txt`。
2. 在文字編輯器中，於 `OPENAI_API_KEY=` 後填入你自己的 OpenAI API 金鑰。不要將金鑰貼到聊天或網頁欄位。
3. 執行 **Enable-AI.cmd** 建立語意索引，再停止並重新執行 **Start.cmd**。
4. 即可取得中文說明，並個別翻譯解答；來源引用會保留。

建立語意索引會將文件段落傳送至 OpenAI。提問會傳送問題、近期對話與相關段落；翻譯會傳送選取的解答。**API 費用另計**。原始 PDF、索引與金鑰保留在本機，瀏覽器不會取得金鑰。

## 建議學習順序

衛星軌道 → 太空段、地面段與使用者段 → 透明式與再生式酬載 → 行動網路整合 → 資源管理與服務。

初學者可問：「低地球軌道是什麼？」「衛星閘道站有什麼功能？」「再生式酬載與透明式酬載有何不同？」尚未啟用語意搜尋時，中文搜尋使用有限的術語對照表；找不到段落時可改用英文縮寫。

圖表擷取可能不完整，尤其是第 80 頁的圖 43。請核對原始頁面。第 39 頁的 EIRP 單位在表格與註腳中不一致，助手應指出疑義，不應擅自修正。引用驗證確保來源編號有效，並不保證每句自然語言說明都完全正確。

移至另一台電腦時，複製專案但不要沿用 `.venv`，改執行 **Setup.cmd** 重建環境。需要 Python 3.12 以上與安裝套件時的網路連線。開發指引見 **AGENTS.md**，實際教學規則見 **prompts/tutor.md**，測試紀錄見 **VERIFICATION.md**。
