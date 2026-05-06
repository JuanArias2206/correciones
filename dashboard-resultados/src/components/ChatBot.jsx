import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  kpis, sustancias, intencionalidad, sexo, sustanciasPorIntencionalidad,
  sustanciaSexo, productosTodos, conteoCategorias, productosPorCategoria,
  productosBlacklist, baseCompleta
} from '../data/data';

const DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/chat/completions';

/* ─── ÍNDICES ───────────────────────────────────────────────────── */
const productosPorCat = {};
productosTodos.forEach(p => {
  if (!productosPorCat[p.categoria]) productosPorCat[p.categoria] = [];
  productosPorCat[p.categoria].push(p);
});
Object.keys(productosPorCat).forEach(cat => {
  productosPorCat[cat].sort((a, b) => b.conteo - a.conteo);
});

const prodCatSexo = {};
baseCompleta.forEach(r => {
  const cat = r.grupos_sustancia_final;
  const prod = r.nom_pro;
  const s = r.sexo;
  if (!cat || cat === 'nan' || !prod || prod === 'nan' || !s) return;
  const key = `${cat}|${s}`;
  if (!prodCatSexo[key]) prodCatSexo[key] = {};
  prodCatSexo[key][prod] = (prodCatSexo[key][prod] || 0) + 1;
});

const prodCatIntenc = {};
baseCompleta.forEach(r => {
  const cat = r.grupos_sustancia_final;
  const prod = r.nom_pro;
  const i = r.intencionalidad;
  if (!cat || cat === 'nan' || !prod || prod === 'nan' || !i) return;
  const key = `${cat}|${i}`;
  if (!prodCatIntenc[key]) prodCatIntenc[key] = {};
  prodCatIntenc[key][prod] = (prodCatIntenc[key][prod] || 0) + 1;
});

const catIntenc = {};
baseCompleta.forEach(r => {
  const cat = r.grupos_sustancia_final;
  const i = r.intencionalidad;
  if (!cat || cat === 'nan' || !i) return;
  if (!catIntenc[cat]) catIntenc[cat] = { intencional: 0, no_intencional: 0 };
  if (i === 'intencional') catIntenc[cat].intencional++;
  else if (i === 'no_intencional') catIntenc[cat].no_intencional++;
});

const catTotals = {};
baseCompleta.forEach(r => {
  const cat = r.grupos_sustancia_final;
  if (!cat || cat === 'nan') return;
  catTotals[cat] = (catTotals[cat] || 0) + 1;
});

const catSexo = {};
baseCompleta.forEach(r => {
  const cat = r.grupos_sustancia_final;
  const s = r.sexo;
  if (!cat || cat === 'nan' || !s) return;
  if (!catSexo[cat]) catSexo[cat] = { F: 0, M: 0 };
  if (s === 'F') catSexo[cat].F++;
  else if (s === 'M') catSexo[cat].M++;
});

const topFromMap = (map, n = 20) =>
  Object.entries(map).sort((a, b) => b[1] - a[1]).slice(0, n)
    .map(([prod, count]) => `${prod}: ${count}`).join(', ');

const normalizeAccents = (str) =>
  str.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();

const matchCategory = (cat, query) => {
  const q = normalizeAccents(query);
  const c = normalizeAccents(cat);
  if (q.includes(c)) return true;
  return c.split('_').some(w => w.length > 2 && q.includes(w));
};

/* ─── BÚSQUEDA LOCAL ─────────────────────────────────────────────── */
const searchLocalData = (userQuery) => {
  const query = userQuery.toLowerCase();
  const results = [];

  const categoriasMencionadas = [...new Set(productosTodos.map(p => p.categoria))]
    .filter(cat => matchCategory(cat, query));

  const asksCompare = query.includes('compar') || query.includes('vs') || query.includes('versus')
    || query.includes('contra') || query.includes('diferencia');

  const asksSexo = query.includes('sexo') || query.includes('femenino') || query.includes('masculino')
    || query.includes('hombre') || query.includes('mujer') || query.includes('mujeres')
    || query.includes('hombres') || /\bf\b/.test(query) || /\bm\b/.test(query)
    || (asksCompare && categoriasMencionadas.length >= 2);
  const askF = asksSexo && (query.includes('femenino') || query.includes('mujer') || /\bf\b/.test(query));
  const askM = asksSexo && (query.includes('masculino') || query.includes('hombre') || /\bm\b/.test(query));
  const targetSex = askF ? 'F' : (askM ? 'M' : null);

  const asksIntenc = query.includes('intencional') || query.includes('accidental')
    || query.includes('voluntario') || query.includes('deliberado')
    || (asksCompare && categoriasMencionadas.length >= 2);

  const productosMencionados = productosTodos.filter(p =>
    query.includes(p.producto.toLowerCase())
  );

  categoriasMencionadas.forEach(cat => {
    if (targetSex) {
      const key = `${cat}|${targetSex}`;
      const map = prodCatSexo[key];
      if (map && Object.keys(map).length > 0) {
        const total = Object.values(map).reduce((a, b) => a + b, 0);
        results.push(`PRODUCTOS EN "${cat}" PARA SEXO ${targetSex === 'F' ? 'FEMENINO' : 'MASCULINO'} (${Object.keys(map).length} productos, ${total} registros):\n${topFromMap(map, 25)}`);
      }
      const opposite = targetSex === 'F' ? 'M' : 'F';
      const mapOpp = prodCatSexo[`${cat}|${opposite}`];
      if (mapOpp) results.push(`(Comparación: ${cat} en ${opposite}: ${Object.values(mapOpp).reduce((a,b)=>a+b,0)} registros)`);
    } else {
      const prods = productosPorCat[cat] || [];
      const totalCat = prods.reduce((sum, p) => sum + (p.conteo || 0), 0);
      results.push(`CATEGORÍA "${cat}" (${prods.length} productos únicos, ${totalCat} registros):\nTop 25: ${prods.slice(0, 25).map(p => `${p.producto}: ${p.conteo}`).join(', ')}`);
    }
    if (asksIntenc && catIntenc[cat]) {
      const d = catIntenc[cat];
      const total = d.intencional + d.no_intencional;
      const pctI = total ? ((d.intencional / total) * 100).toFixed(1) : 0;
      const pctNI = total ? ((d.no_intencional / total) * 100).toFixed(1) : 0;
      results.push(`INTENCIONALIDAD EN "${cat}": Intencional=${d.intencional.toLocaleString('es-CO')} (${pctI}%), No Intencional=${d.no_intencional.toLocaleString('es-CO')} (${pctNI}%), Total=${total.toLocaleString('es-CO')}`);
    }
    if (asksSexo && !targetSex && catSexo[cat]) {
      const sx = catSexo[cat];
      const sxTotal = sx.F + sx.M;
      const pctF = sxTotal ? ((sx.F / sxTotal) * 100).toFixed(1) : 0;
      const pctM = sxTotal ? ((sx.M / sxTotal) * 100).toFixed(1) : 0;
      results.push(`SEXO EN "${cat}": Femenino=${sx.F.toLocaleString('es-CO')} (${pctF}%), Masculino=${sx.M.toLocaleString('es-CO')} (${pctM}%), Total=${sxTotal.toLocaleString('es-CO')}`);
    }
  });

  if (asksSexo) {
    const sexoData = sustanciaSexo.map(s =>
      `${s.sustancia}: F=${s.F}, M=${s.M} (total=${Number(s.F)+Number(s.M)})`
    ).join('\n');
    results.push('DATOS SUSTANCIA × SEXO:\n' + sexoData);
  }

  if (asksCompare && categoriasMencionadas.length >= 2) {
    const compBlocks = categoriasMencionadas
      .filter(cat => catIntenc[cat])
      .map(cat => {
        const d = catIntenc[cat];
        const total = d.intencional + d.no_intencional;
        const pctI = total ? ((d.intencional / total) * 100).toFixed(1) : 0;
        const pctNI = total ? ((d.no_intencional / total) * 100).toFixed(1) : 0;
        const totalAll = catTotals[cat] || 0;
        const sx = catSexo[cat] || { F: 0, M: 0 };
        const sxTotal = sx.F + sx.M;
        const pctF = sxTotal ? ((sx.F / sxTotal) * 100).toFixed(1) : 0;
        const pctM = sxTotal ? ((sx.M / sxTotal) * 100).toFixed(1) : 0;
        return `COMPARACIÓN "${cat}": Total=${totalAll.toLocaleString('es-CO')} | Intencional=${d.intencional.toLocaleString('es-CO')} (${pctI}%) | No Intencional=${d.no_intencional.toLocaleString('es-CO')} (${pctNI}%) | Femenino=${sx.F.toLocaleString('es-CO')} (${pctF}%) | Masculino=${sx.M.toLocaleString('es-CO')} (${pctM}%)`;
      });
    if (compBlocks.length >= 2) results.push(compBlocks.join('\n'));
  }

  if (asksIntenc) {
    const intData = sustanciasPorIntencionalidad.map(s =>
      `${s.sustancia}: total=${s.total}, intencional=${s.intencional} (${s.porcentaje_intencional}%), no_intencional=${s.no_intencional} (${s.porcentaje_no_intencional}%)`
    ).join('\n');
    results.push('DATOS SUSTANCIA × INTENCIONALIDAD:\n' + intData);

    if (categoriasMencionadas.length >= 2) {
      const compData = categoriasMencionadas
        .filter(cat => catIntenc[cat])
        .map(cat => {
          const d = catIntenc[cat];
          const total = d.intencional + d.no_intencional;
          const pctI = total ? ((d.intencional / total) * 100).toFixed(1) : 0;
          const pctNI = total ? ((d.no_intencional / total) * 100).toFixed(1) : 0;
          return `${cat}: Intencional=${d.intencional.toLocaleString('es-CO')} (${pctI}%), No Intencional=${d.no_intencional.toLocaleString('es-CO')} (${pctNI}%), Total=${total.toLocaleString('es-CO')}`;
        }).join('\n');
      if (compData) results.push('COMPARACIÓN INTENCIONALIDAD ENTRE CATEGORÍAS:\n' + compData);
    }
  }

  productosMencionados.forEach(p => {
    results.push(`PRODUCTO "${p.producto}": categoría=${p.categoria}, conteo=${p.conteo}, método=${p.metodo_clasificacion}`);
  });

  if (query.includes('blacklist') || query.includes('filtrado') || query.includes('bloqueado')) {
    const blData = productosBlacklist.slice(0, 20).map(b => `${b.nombre_producto}: ${b.razon} (frecuencia: ${b.frecuencia})`).join('\n');
    results.push('BLACKLIST (top 20):\n' + blData);
  }

  if (query.includes('top') || query.includes('ranking') || query.includes('más usad') || query.includes('mas usad')
    || query.includes('mas frecuente') || query.includes('más frecuente')
    || query.includes('primer') || query.includes('segundo') || query.includes('tercer')) {
    const topGlobal = [...productosTodos].sort((a, b) => b.conteo - a.conteo).slice(0, 30)
      .map(p => `${p.producto} (${p.categoria}): ${p.conteo}`).join('\n');
    results.push('TOP 30 PRODUCTOS GLOBALES:\n' + topGlobal);
  }

  const baseContext = `KPIs: ${kpis.total_registros} registros, ${kpis.intencional} intencionales, ${kpis.no_intencional} no intencionales, F=${kpis.sexo_f}, M=${kpis.sexo_m}.
Top sustancias: ${sustancias.slice(0,5).map(s=>`${s.sustancia}:${s.numero_registros}`).join(', ')}.
Intencionalidad global: ${kpis.pct_intencional}% intencional, ${kpis.pct_no_intencional}% no intencional.`;

  return baseContext + '\n\n' + results.join('\n\n');
};

/* ─── MARKDOWN RENDERER ──────────────────────────────────────────── */
const formatMarkdown = (text) => {
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

  const paragraphs = html.split('\n\n');
  html = paragraphs.map(p => {
    const lines = p.split('\n');
    const isNumbered = lines.every(l => /^\d+\.\s/.test(l.trim()) || l.trim() === '');
    const isBullet   = lines.every(l => /^[-•]\s/.test(l.trim()) || l.trim() === '');

    if (isNumbered && lines.length > 1) {
      const items = lines.filter(l => /^\d+\.\s/.test(l.trim()))
        .map(l => `<li>${l.replace(/^\d+\.\s/, '')}</li>`).join('');
      return `<ol>${items}</ol>`;
    }
    if (isBullet && lines.length > 1) {
      const items = lines.filter(l => /^[-•]\s/.test(l.trim()))
        .map(l => `<li>${l.replace(/^[-•]\s/, '')}</li>`).join('');
      return `<ul>${items}</ul>`;
    }
    return lines.map(l =>
      /^\d+\.\s/.test(l.trim()) ? `<span class="chat-numbered">${l}</span>` : l
    ).join('<br/>');
  }).join('</p><p>');

  return `<p>${html}</p>`;
};

/* ─── SYSTEM PROMPT ──────────────────────────────────────────────── */
const buildSystemPrompt = () =>
  `Eres un asistente experto en análisis epidemiológico y toxicológico de sustancias. Trabajas con datos reales del sistema SIVIGILA de notificación obligatoria en Colombia.

Tus capacidades:
- Analizar y comparar datos de clasificación de sustancias, productos, sexo e intencionalidad.
- Dar rankings, conteos, porcentajes y comparaciones precisas.

Reglas de estilo y formato:
1. Usa SOLO los datos del contexto. NUNCA inventes cifras.
2. Responde en español, de forma concisa pero completa.
3. Para listas numeradas usa el formato "1. item" (número + punto + espacio).
4. Para texto destacado usa **negrita** con doble asterisco.
5. Separa párrafos con doble salto de línea.
6. Incluye cifras exactas con formato legible (ej: 27,006 en vez de 27006).
7. Si puedes dar un ranking, hazlo en lista numerada.`;

/* ─── SUGGESTION CHIPS ───────────────────────────────────────────── */
const SUGGESTIONS = [
  '¿Cuál es el producto más frecuente en medicamentos_no_SPA?',
  'Compara alcohol_etanol entre hombres y mujeres',
  'Compara cocaína vs alcohol por intencionalidad',
  '¿Qué productos se encuentran en tranquilizantes?',
  'Resumen general del dataset',
];

/* ─── TYPING DOTS ────────────────────────────────────────────────── */
const TypingDots = () => (
  <div className="chatbot-typing">
    <span/><span/><span/>
  </div>
);

/* ─── COPY BUTTON ────────────────────────────────────────────────── */
const CopyBtn = ({ text }) => {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    });
  };
  return (
    <button className="chatbot-copy-btn" onClick={copy} title="Copiar">
      {copied ? '✓' : '⧉'}
    </button>
  );
};

/* ─── MAIN COMPONENT ─────────────────────────────────────────────── */
const ChatBot = () => {
  const [isOpen, setIsOpen] = useState(false);

  const getInitialApiKey = () => {
    const envKey = import.meta.env?.VITE_DEEPSEEK_API_KEY;
    if (envKey) return envKey;
    return localStorage.getItem('deepseek_api_key') || sessionStorage.getItem('deepseek_api_key') || '';
  };

  const [apiKey,      setApiKey]      = useState(getInitialApiKey);
  const [showConfig,  setShowConfig]  = useState(false);
  const [messages,    setMessages]    = useState([
    { role: 'assistant', content: '¡Hola! Soy tu asistente de análisis epidemiológico.\n\nPregúntame sobre las **sustancias**, **productos**, **distribución por sexo** o **intencionalidad** — o usa una sugerencia rápida abajo.' }
  ]);
  const [input,       setInput]       = useState('');
  const [streaming,   setStreaming]   = useState(false);
  const messagesEndRef = useRef(null);
  const textareaRef    = useRef(null);
  const abortRef       = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  /* Auto-resize textarea */
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 100) + 'px';
  }, [input]);

  const hasApiKey = Boolean(apiKey.trim());

  const saveApiKey = () => {
    if (apiKey.trim()) {
      localStorage.setItem('deepseek_api_key', apiKey.trim());
      sessionStorage.setItem('deepseek_api_key', apiKey.trim());
      setShowConfig(false);
    }
  };

  const clearChat = () => {
    setMessages([
      { role: 'assistant', content: '¡Hola! Soy tu asistente de análisis epidemiológico.\n\nPregúntame sobre las **sustancias**, **productos**, **distribución por sexo** o **intencionalidad** — o usa una sugerencia rápida abajo.' }
    ]);
  };

  const handleSend = useCallback(async (overrideText) => {
    const userQuery = (overrideText || input).trim();
    if (!userQuery || streaming) return;
    if (!hasApiKey) { setShowConfig(true); return; }

    setMessages(prev => [...prev, { role: 'user', content: userQuery }]);
    setInput('');
    setStreaming(true);

    const localData = searchLocalData(userQuery);
    const enrichedUserMsg = `Pregunta del usuario: "${userQuery}"

DATOS RELEVANTES ENCONTRADOS EN LA BASE LOCAL (usa estos datos para responder):
${localData}

Responde la pregunta del usuario basándote en los datos anteriores. Sé preciso con las cifras.`;

    // Add empty assistant message that will be filled via streaming
    setMessages(prev => [...prev, { role: 'assistant', content: '' }]);

    try {
      const controller = new AbortController();
      abortRef.current = controller;

      const response = await fetch(DEEPSEEK_API_URL, {
        method: 'POST',
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiKey}`,
        },
        body: JSON.stringify({
          model: 'deepseek-chat',
          messages: [
            { role: 'system', content: buildSystemPrompt() },
            { role: 'user', content: enrichedUserMsg }
          ],
          temperature: 0.2,
          max_tokens: 2000,
          stream: true,
        }),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.error?.message || `Error HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullText = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n').filter(l => l.startsWith('data: '));
        for (const line of lines) {
          const raw = line.slice(6);
          if (raw === '[DONE]') break;
          try {
            const parsed = JSON.parse(raw);
            const delta = parsed.choices?.[0]?.delta?.content || '';
            fullText += delta;
            setMessages(prev => {
              const updated = [...prev];
              updated[updated.length - 1] = { role: 'assistant', content: fullText };
              return updated;
            });
          } catch { /* ignore parse errors in SSE stream */ }
        }
      }
    } catch (err) {
      if (err.name === 'AbortError') return;
      setMessages(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = { role: 'assistant', content: `❌ Error: ${err.message}` };
        return updated;
      });
    } finally {
      setStreaming(false);
      abortRef.current = null;
    }
  }, [input, streaming, hasApiKey, apiKey]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  const stopStreaming = () => {
    abortRef.current?.abort();
    setStreaming(false);
  };

  return (
    <>
      {/* ── FAB BUTTON ── */}
      <button
        className={`chatbot-fab ${isOpen ? 'chatbot-fab--open' : ''}`}
        onClick={() => setIsOpen(o => !o)}
        title="Asistente de Análisis"
      >
        <span className="chatbot-fab-icon">{isOpen ? '✕' : '💬'}</span>
        {!isOpen && <span className="chatbot-fab-label">Asistente</span>}
      </button>

      {/* ── WINDOW ── */}
      {isOpen && (
        <div className="chatbot-window">

          {/* Header */}
          <div className="chatbot-header">
            <div className="chatbot-header-left">
              <div className="chatbot-avatar">AI</div>
              <div>
                <div className="chatbot-header-title">Asistente de Análisis</div>
                <div className="chatbot-header-sub">
                  <span className={`chatbot-status-dot ${streaming ? 'chatbot-status-dot--active' : ''}`}/>
                  {streaming ? 'Generando respuesta...' : 'DeepSeek · SIVIGILA'}
                </div>
              </div>
            </div>
            <div className="chatbot-header-actions">
              <button className="chatbot-icon-btn" onClick={clearChat} title="Limpiar conversación">🗑</button>
              <button className="chatbot-icon-btn" onClick={() => setShowConfig(v => !v)} title="Configurar API Key">⚙</button>
            </div>
          </div>

          {/* Config panel */}
          {showConfig && (
            <div className="chatbot-config">
              <div className="chatbot-config-label">API Key de DeepSeek</div>
              <input
                type="password" placeholder="sk-..."
                value={apiKey}
                onChange={e => setApiKey(e.target.value)}
                className="chatbot-config-input"
              />
              <div className="chatbot-config-row">
                <button className="chatbot-config-btn chatbot-config-btn--primary" onClick={saveApiKey}>Guardar</button>
                <button className="chatbot-config-btn chatbot-config-btn--secondary" onClick={() => setShowConfig(false)}>Cancelar</button>
              </div>
              {hasApiKey && <div className="chatbot-key-ok">✓ Key activa</div>}
            </div>
          )}

          {/* Messages */}
          <div className="chatbot-messages">
            {messages.map((msg, idx) => (
              <div key={idx} className={`chatbot-msg chatbot-msg--${msg.role}`}>
                {msg.role === 'assistant' && (
                  <div className="chatbot-msg-avatar">AI</div>
                )}
                <div className="chatbot-bubble-wrap">
                  <div className={`chatbot-bubble chatbot-bubble--${msg.role}`}>
                    {msg.role === 'assistant' ? (
                      <>
                        {msg.content ? (
                          <div
                            className="chat-message-content"
                            dangerouslySetInnerHTML={{ __html: formatMarkdown(msg.content) }}
                          />
                        ) : (
                          <TypingDots />
                        )}
                      </>
                    ) : (
                      <span style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</span>
                    )}
                  </div>
                  {msg.role === 'assistant' && msg.content && (
                    <CopyBtn text={msg.content} />
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Suggestion chips */}
          {messages.length <= 2 && !streaming && (
            <div className="chatbot-suggestions">
              {SUGGESTIONS.map((s, i) => (
                <button key={i} className="chatbot-suggestion-chip" onClick={() => handleSend(s)}>
                  {s}
                </button>
              ))}
            </div>
          )}

          {/* Input area */}
          <div className="chatbot-input-area">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={hasApiKey ? 'Pregunta sobre los datos... (Enter para enviar)' : 'Configura tu API Key (⚙)'}
              disabled={!hasApiKey}
              rows={1}
              className="chatbot-textarea"
            />
            {streaming ? (
              <button className="chatbot-send-btn chatbot-send-btn--stop" onClick={stopStreaming} title="Detener">■</button>
            ) : (
              <button
                className={`chatbot-send-btn ${(!input.trim() || !hasApiKey) ? 'chatbot-send-btn--disabled' : ''}`}
                onClick={() => handleSend()}
                disabled={!input.trim() || !hasApiKey}
              >
                ↑
              </button>
            )}
          </div>
        </div>
      )}
    </>
  );
};

export default ChatBot;
