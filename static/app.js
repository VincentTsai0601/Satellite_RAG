'use strict';
const $ = selector => document.querySelector(selector);
const state = {language:'en',messages:[],sources:[],busy:false,info:null,selectedTopic:-1};
const copy = {
  en: {
    skip:'Skip to question',brandCaption:'SATELLITE LEARNING SPACE',newChat:'New conversation',learningPath:'YOUR LEARNING PATH',smallSteps:'Big systems. Small steps.',sidebarNote:'Start with the basics. Follow your curiosity.',local:'Running on your PC',workspace:'Satellite study',personal:'Personal workspace',tutor:'Your satellite tutor',checking:'Connecting…',eyebrow:'A LITTLE CURIOSITY GOES A LONG WAY',headline:'Understand the\nnetwork above.',intro:'Explore how satellites connect our world. Ask a question, start with a topic, and learn one concept at a time.',grounded:'Grounded in MSS Reference Architecture v2.0',tryQuestion:'A GOOD PLACE TO START',learningNote:'No background needed. Every acronym gets an explanation.',thinking:'Finding supporting passages…',searchAvailable:'Document search is ready. Connect AI for explanations.',connectAI:'Connect AI ↗',questionLabel:'Your question',placeholder:'Ask anything about satellite systems…',enterHint:'Enter to send · Shift + Enter for a new line',verifyNote:'Learn with sources. Check the original page for technical detail.',sources:'Sources',reference:'REFERENCE / 02',coverTitle:'Mobile satellite\nsystems.',coverSub:'The architecture behind\na connected world.',documentTitle:'MSS Reference Architecture',documentOrg:'Mobile Satellite Services Association',pages:'pages',originalPDF:'Original PDF',openReference:'Open reference document',evidenceTitle:'See where it comes from.',evidenceText:'Relevant passages appear here when you ask a question. Every citation takes you back to the original page.',privacy:'Your document and index stay on this PC. Connected AI receives relevant text.',setupEyebrow:'ONE-TIME SETUP',setupTitle:'Connect your learning assistant.',setupIntro:'Document search works now. AI explanations and translation need an API key.',setupOne:'In the app folder, copy .env.example to .env.',setupTwo:'Set AI_PROVIDER to openai or gemini, then add the matching key in .env. Save it locally; never paste it here.',setupThree:'Restart with Start.cmd. Run Enable-AI.cmd only for OpenAI semantic embeddings.',setupDisclosure:'Questions send your message, recent context, and matching passages to the selected provider. Translation sends the selected answer. API usage is billed separately.',refreshStatus:'Check connection',close:'Close',send:'Send question',you:'You',orbit:'Orbit',searchMode:'DOCUMENT SEARCH',hybridMode:'AI + HYBRID SEARCH',keywordMode:'AI + KEYWORD SEARCH',offline:'SERVER UNAVAILABLE',evidence:'From the document',analogy:'Illustrative analogy',background:'Additional background',limitation:'A note about this answer',sourceNote:'Retrieved passages from the original English document. A matching passage is evidence to inspect, not a guarantee that every claim is correct.',originalExcerpt:'ORIGINAL ENGLISH EXCERPT',fullPassage:'Read full passage',page:'p.',figureWarning:'Figure detail may be missing from extracted text. Inspect the original page.',tableWarning:'Table layout is flattened. Check headers, units, and footnotes in the PDF.',sparseWarning:'Very little text could be extracted from this page.',unitWarning:'The source has inconsistent EIRP units (dBW/dBm) in the table and its note.',viewSources:'View sources',translateChinese:'Translate to Chinese',translateEnglish:'Translate to English',showOriginal:'Show original',translated:'Translated explanation',translating:'Translating…',fallback:'Semantic search was unavailable; these sources use keyword search.',refreshReady:'API key detected. You can close this window and ask a question.',refreshMissing:'No API key detected. Save .env and restart Start.cmd before checking again.',error:'The request could not be completed. Try again.',network:'Cannot reach the local server. Start the app and try again.',missing_prompt:'The tutor instructions are missing or unreadable. Restore prompts/tutor.md and try again.',missing_key:'AI is not connected. Open Connect AI for setup instructions.',missing_index:'The document index is missing. Run Setup.cmd to build it.',missing_document:'The PDF is missing from the app’s data folder. See README.md.',provider_auth:'The AI provider rejected the API key. Check your local .env file and restart.',provider_limit:'The AI provider reported a usage or rate limit. Check your API billing or try again later.',provider_timeout:'The AI provider took too long to respond. Please try again.',provider_error:'The AI provider could not complete this request. Check your connection and configured model.',provider_format:'The AI response could not be read safely. Please try again.',citation_error:'The answer’s source references could not be verified, so the answer was withheld. Please try again.',cross_origin:'This request must come from the local website.',request_too_large:'This message is too long. Start a new conversation or shorten it.',validation:'Please enter a shorter question and try again.',
    topics:[['Satellite orbits','LEO, MEO & GEO'],['The system, end to end','Space, ground & users'],['Inside the payload','Transparent & regenerative'],['Joining mobile networks','5G & non-terrestrial networks'],['Making it all work','Resources & services']],
    topicQuestions:['Explain LEO, MEO, and GEO orbits for a beginner.','Explain the space, ground, and user segments of a satellite system for a beginner.','What is the difference between transparent and regenerative satellite payloads?','How does a satellite system connect with 5G mobile networks?','How does resource management coordinate satellite beams and user services?'],
    suggestions:['What makes LEO different from GEO?','How does my phone connect to a satellite?','What does a satellite gateway do?','What is a regenerative payload?']
  },
  'zh-TW': {
    skip:'跳至問題輸入欄',brandCaption:'衛星系統學習空間',newChat:'開啟新對話',learningPath:'你的學習路徑',smallSteps:'龐大的系統，一步步理解。',sidebarNote:'從基礎開始，跟隨你的好奇心。',local:'在你的電腦上執行',workspace:'衛星系統學習',personal:'個人工作空間',tutor:'你的衛星學習助手',checking:'連線中…',eyebrow:'從一個小問題，開啟探索',headline:'理解天空中的\n通訊網路。',intro:'探索衛星如何連結世界。提出問題、選擇主題，一次掌握一個概念。',grounded:'以 MSS 參考架構第 2.0 版為學習依據',tryQuestion:'從這些問題開始',learningNote:'不需要相關背景，每個縮寫都會獲得說明。',thinking:'正在尋找相關文件段落…',searchAvailable:'文件搜尋已就緒。連接 AI 即可取得說明。',connectAI:'連接 AI ↗',questionLabel:'你的問題',placeholder:'想了解衛星系統的什麼呢？',enterHint:'按 Enter 傳送 · Shift + Enter 換行',verifyNote:'根據來源學習，技術細節請查閱原始頁面。',sources:'參考來源',reference:'參考文件 / 02',coverTitle:'行動衛星\n通訊系統。',coverSub:'理解連結世界的\n系統架構。',documentTitle:'MSS 參考架構',documentOrg:'行動衛星服務協會',pages:'頁',originalPDF:'原始 PDF',openReference:'開啟參考文件',evidenceTitle:'了解每個解答的依據。',evidenceText:'提出問題後，相關段落會出現在這裡。每個引用都能帶你回到原始文件頁面。',privacy:'文件與索引保留在本機。連接 AI 後會傳送相關文字。',setupEyebrow:'首次設定',setupTitle:'連接你的學習助手。',setupIntro:'目前已可搜尋文件。AI 說明與翻譯需要 API 金鑰。',setupOne:'在應用程式資料夾中，將 .env.example 複製為 .env。',setupTwo:'將 AI_PROVIDER 設為 openai 或 gemini，再在 .env 填入對應金鑰。請勿將金鑰貼到這裡。',setupThree:'使用 Start.cmd 重新啟動；只有使用 OpenAI 語意嵌入時才執行 Enable-AI.cmd。',setupDisclosure:'提問時會將你的訊息、近期對話與相關段落傳送至所選服務。翻譯時會傳送選取的解答。API 費用另計。',refreshStatus:'檢查連線',close:'關閉',send:'傳送問題',you:'你',orbit:'學習助手',searchMode:'文件搜尋',hybridMode:'AI ＋ 混合搜尋',keywordMode:'AI ＋ 關鍵字搜尋',offline:'伺服器未連線',evidence:'文件依據',analogy:'輔助理解的比喻',background:'補充背景',limitation:'解答限制與提醒',sourceNote:'以下是原始英文文件中的相關段落。請核對原文；檢索到段落不代表每項說明都一定正確。',originalExcerpt:'英文原文段落',fullPassage:'閱讀完整段落',page:'頁',figureWarning:'擷取文字可能缺少圖中細節，請查看原始頁面。',tableWarning:'表格已轉為文字，請在 PDF 中核對欄位、單位與註腳。',sparseWarning:'這一頁可擷取的文字很少。',unitWarning:'原文件的表格與註腳使用了不一致的 EIRP 單位（dBW/dBm）。',viewSources:'查看來源',translateChinese:'翻譯為中文',translateEnglish:'翻譯為英文',showOriginal:'顯示原始解答',translated:'翻譯後的說明',translating:'翻譯中…',fallback:'語意搜尋暫時無法使用，目前顯示關鍵字搜尋結果。',refreshReady:'已偵測到 API 金鑰。關閉視窗後即可提問。',refreshMissing:'尚未偵測到 API 金鑰。儲存 .env 並重新啟動 Start.cmd 後再試。',error:'無法完成這次請求，請稍後再試。',network:'無法連接本機伺服器，請啟動應用程式後再試。',missing_key:'尚未連接 AI，請開啟「連接 AI」查看設定步驟。',missing_index:'找不到文件索引，請執行 Setup.cmd。',missing_document:'應用程式的 data 資料夾中找不到 PDF，請參考 README.md。',provider_auth:'AI 服務拒絕了這個 API 金鑰，請檢查本機 .env 並重新啟動。',provider_limit:'AI 服務已達使用量或請求頻率限制，請檢查 API 帳單或稍後再試。',provider_timeout:'AI 服務回應逾時，請再試一次。',provider_error:'AI 服務無法完成請求，請檢查網路連線及設定的模型。',provider_format:'無法安全讀取 AI 回應，請再試一次。',citation_error:'無法驗證解答的來源引用，因此未顯示該解答。請再試一次。',cross_origin:'請從本機網站送出請求。',request_too_large:'訊息過長，請縮短內容或開啟新對話。',validation:'請縮短問題後再試。',
    missing_prompt:'教學指引遺失或無法讀取。請還原 prompts/tutor.md 後再試一次。',
    topics:[['衛星軌道','低軌、中軌與地球同步軌道'],['從頭到尾認識系統','太空、地面與使用者'],['衛星酬載內部','透明式與再生式'],['連結行動網路','5G 與非地面網路'],['讓系統協同運作','資源管理與服務']],
    topicQuestions:['請為初學者解釋低地球軌道、中地球軌道與地球同步軌道。','請為初學者解釋衛星系統的太空段、地面段與使用者段。','透明式與再生式衛星酬載有什麼差別？','衛星系統如何與 5G 行動網路連接？','資源管理如何協調衛星波束與使用者服務？'],
    suggestions:['低地球軌道與地球同步軌道有何不同？','手機如何與衛星連線？','衛星閘道站有什麼功能？','什麼是再生式酬載？']
  }
};
const t = key => copy[state.language][key] || copy.en[key] || copy[state.language].error;
function node(tag, className, text){const el=document.createElement(tag); if(className)el.className=className; if(text!==undefined)el.textContent=text;return el;}
function multiline(el,text){el.replaceChildren();text.split('\n').forEach((line,i)=>{if(i)el.append(document.createElement('br'));el.append(document.createTextNode(line));});}
function pageLabel(page){return state.language==='en' ? `p. ${page}` : `第 ${page} 頁`;}

function setLanguage(language){
  state.language=language;document.documentElement.lang=language;
  document.title=language==='en'?'Orbit · Satellite Learning':'Orbit · 衛星系統學習';
  document.querySelectorAll('[data-i18n]').forEach(el=>multiline(el,t(el.dataset.i18n)));
  $('#lang-en').classList.toggle('active',language==='en');$('#lang-en').setAttribute('aria-pressed',String(language==='en'));
  $('#lang-zh').classList.toggle('active',language==='zh-TW');$('#lang-zh').setAttribute('aria-pressed',String(language==='zh-TW'));
  $('#question').placeholder=t('placeholder');$('#send').setAttribute('aria-label',t('send'));
  $('.dialog-close').setAttribute('aria-label',t('close'));$('#topics').setAttribute('aria-label',t('learningPath'));
  $('.language-switch').setAttribute('aria-label',language==='en'?'Language':'語言');
  $('#refresh-result').textContent='';
  renderTopics();renderSuggestions();renderMessages();renderSources();renderStatus();
}
function renderTopics(){
  $('#topics').replaceChildren();
  copy[state.language].topics.forEach(([name,sub],i)=>{
    const button=node('button','topic'+(i===state.selectedTopic?' active':''));
    const info=node('span'); info.append(node('span','topic-name',name),node('span','topic-sub',sub));
    button.append(node('span','topic-number',String(i+1).padStart(2,'0')),info);
    button.disabled=state.busy;button.addEventListener('click',()=>{state.selectedTopic=i;submitQuestion(copy[state.language].topicQuestions[i]);});$('#topics').append(button);
  });
}
function renderSuggestions(){
  $('#suggestions').replaceChildren();
  copy[state.language].suggestions.forEach((question,i)=>{
    const button=node('button','suggestion'); const top=node('span','suggestion-top');
    top.setAttribute('aria-hidden','true');top.append(node('span','',['◎','⌁','⌘','◇'][i]),node('span','','↗'));
    button.append(top,node('span','suggestion-question',question));button.disabled=state.busy;
    button.addEventListener('click',()=>submitQuestion(question));$('#suggestions').append(button);
  });
}
function renderStatus(){
  const info=state.info;
  $('#mode-badge').textContent=info ? t(info.api_configured?(info.embedded_chunks===info.chunks && info.chunks?'hybridMode':'keywordMode'):'searchMode') : t('checking');
  $('#setup-strip').hidden=!info || info.api_configured;
  if(info)$('#document-pages').textContent=String(info.pages||97);
}
async function refreshStatus(){
  try{const response=await fetch('/api/status');if(!response.ok)throw Error();state.info=await response.json();renderStatus();return true;}
  catch{$('#mode-badge').textContent=t('offline');return false;}
}
function renderSources(){
  const has=state.sources.length>0;$('#source-default').hidden=has;$('#source-results').hidden=!has;
  $('#source-count').textContent=has?String(state.sources.length).padStart(2,'0'):'01';
  $('#source-results').replaceChildren();if(!has)return;
  $('#source-results').append(node('p','source-results-note',t('sourceNote')));
  for(const source of state.sources){
    const card=node('article','source-card');card.dataset.sourceId=source.id;
    const top=node('div','source-card-top');top.append(node('span','',`MSS · v${source.version}`));
    const link=node('a','page-link',pageLabel(source.page)+' ↗');link.href=`/document#page=${Number(source.page)}`;link.target='_blank';link.rel='noopener';top.append(link);
    card.append(top,node('h3','',source.section),node('div','original-label',t('originalExcerpt')));
    const excerpt=node('div','source-excerpt',source.text.length>300?source.text.slice(0,300)+'…':source.text);excerpt.lang='en';card.append(excerpt);
    if(source.text.length>300){const details=node('details');details.append(node('summary','',t('fullPassage')));const full=node('div','source-excerpt',source.text);full.lang='en';details.append(full);card.append(details);}
    const warningKeys={figure:'figureWarning',table:'tableWarning',sparse_text:'sparseWarning',unit_conflict:'unitWarning'};
    for(const warning of (source.warning||'').split(',')){if(warningKeys[warning])card.append(node('p','source-warning',t(warningKeys[warning])));}
    $('#source-results').append(card);
  }
}
function showSources(message,id){
  state.sources=message.sources||[];renderSources();
  document.querySelectorAll('.source-card.highlight').forEach(el=>el.classList.remove('highlight'));
  if(id){const card=[...document.querySelectorAll('.source-card')].find(el=>el.dataset.sourceId===id);if(card){card.classList.add('highlight');card.scrollIntoView({block:'nearest',behavior:'smooth'});}}
  else if(innerWidth<=950)$('#source-heading').scrollIntoView({block:'start',behavior:'smooth'});
}
function renderMessages(){
  $('#welcome').hidden=state.messages.length>0;$('#messages').replaceChildren();
  state.messages.forEach(message=>{
    const article=node('article','message '+message.role);article.lang=message.displayLanguage||message.language;
    const heading=node('div','message-heading');const avatar=node('span','avatar',message.role==='user'?'↗':'◎');avatar.setAttribute('aria-hidden','true');heading.append(avatar,node('span','',t(message.role==='user'?'you':'orbit')));article.append(heading);
    if(message.role==='user'){article.append(node('div','message-content',message.content));}
    else if(message.error){article.append(node('div','error-text',t(message.error)));}
    else{
      for(const section of (message.displaySections||message.sections)){
        const block=node('section','message-section '+section.kind);block.append(node('div','section-label',t(section.kind)),node('div','section-text',section.text));
        const renderedIds=new Set();
        for(const id of section.citations){if(renderedIds.has(id))continue;renderedIds.add(id);const source=message.sources.find(item=>item.id===id);if(!source)continue;const cite=node('button','citation',pageLabel(source.page));cite.addEventListener('click',()=>showSources(message,id));block.append(cite);}
        article.append(block);
      }
      if(message.warning)article.append(node('div','source-warning',t('fallback')));
      const actions=node('div','message-actions');
      if(message.sources.length){const sources=node('button','',t('viewSources')+` (${message.sources.length})`);sources.addEventListener('click',()=>showSources(message));actions.append(sources);}
      if(message.mode==='answer'){
        const translated=!!message.displaySections;
        const button=node('button','',message.translating?t('translating'):translated?t('showOriginal'):t(message.language==='en'?'translateChinese':'translateEnglish'));
        button.disabled=state.busy||!!message.translating;
        button.addEventListener('click',()=>translateMessage(message));actions.append(button);
        if(translated)actions.append(node('span','translation-tag',t('translated')));
      }
      article.append(actions);
      if(message.translationError)article.append(node('div','error-text',t(message.translationError)));
    }
    $('#messages').append(article);
  });
}
async function api(route,body){
  let response;
  try{response=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:AbortSignal.timeout(150000)});}
  catch{throw {code:'network'};}
  let data;try{data=await response.json();}catch{throw {code:'error'};}
  if(!response.ok)throw {code:typeof data.detail?.code==='string'?data.detail.code:response.status===422?'validation':'error'};
  return data;
}
function scrollChat(){requestAnimationFrame(()=>{const scroller=$('#chat-scroll');if(innerWidth>950)scroller.scrollTop=scroller.scrollHeight;else $('#thinking').hidden?$('#messages').lastElementChild?.scrollIntoView({block:'nearest'}):$('#thinking').scrollIntoView({block:'nearest'});});}
function setBusy(busy){state.busy=busy;$('#send').disabled=busy;$('#new-chat').disabled=busy;$('#thinking').hidden=!busy;renderTopics();renderSuggestions();}
async function submitQuestion(question){
  question=question.trim();if(!question||state.busy)return;
  const language=state.language;
  const history=state.messages.filter(m=>!m.error&&(m.role==='user'||m.mode==='answer')).slice(-10).map(m=>({role:m.role,content:m.role==='user'?m.content:m.sections.map(s=>s.text).join('\n').slice(0,12000)}));
  state.messages.push({role:'user',content:question,language});$('#question').value='';setBusy(true);renderMessages();scrollChat();
  try{const result=await api('/api/chat',{question,language,history});state.messages.push({role:'assistant',language,...result});state.sources=result.sources;}
  catch(error){state.messages.push({role:'assistant',language,error:error.code||'error'});}
  finally{setBusy(false);renderMessages();renderSources();scrollChat();$('#question').focus({preventScroll:true});}
}
async function translateMessage(message){
  if(message.displaySections){delete message.displaySections;delete message.displayLanguage;renderMessages();return;}
  if(message.translating||state.busy)return;
  const language=message.language==='en'?'zh-TW':'en';message.translating=true;delete message.translationError;renderMessages();
  try{const result=await api('/api/translate',{language,sections:message.sections});message.displaySections=result.sections;message.displayLanguage=language;}
  catch(error){message.translationError=error.code||'error';}
  finally{message.translating=false;renderMessages();}
}
$('#lang-en').addEventListener('click',()=>setLanguage('en'));$('#lang-zh').addEventListener('click',()=>setLanguage('zh-TW'));
$('#chat-form').addEventListener('submit',event=>{event.preventDefault();submitQuestion($('#question').value);});
$('#question').addEventListener('keydown',event=>{if(event.key==='Enter'&&!event.shiftKey&&!event.isComposing){event.preventDefault();submitQuestion(event.target.value);}});
$('#new-chat').addEventListener('click',()=>{if(state.busy)return;state.messages=[];state.sources=[];state.selectedTopic=-1;renderMessages();renderSources();renderTopics();$('#question').focus();});
$('#setup-button').addEventListener('click',()=>$('#setup-dialog').showModal());
$('#refresh-status').addEventListener('click',async()=>{const ok=await refreshStatus();$('#refresh-result').textContent=ok?t(state.info.api_configured?'refreshReady':'refreshMissing'):t('network');});
setLanguage('en');refreshStatus();
