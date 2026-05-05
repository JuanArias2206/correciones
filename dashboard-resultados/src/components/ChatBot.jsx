import React, { useState, useRef, useEffect } from 'react';
import {
  kpis, sustancias, intencionalidad, sexo, sustanciasPorIntencionalidad,
  sustanciaSexo, productosTodos, conteoCategorias, productosPorCategoria,
  productosBlacklist, baseCompleta
} from '../data/data';

const DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/chat/completions';

// ─── ÍNDICE: productos por categoría ──────────────────────────────────────
const productosPorCat = {};
productosTodos.forEach(p => {
  if (!productosPorCat[p.categoria]) productosPorCat[p.categoria] = [];
  productosPorCat[p.categoria].push(p);
});
Object.keys(productosPorCat).forEach(cat => {
  productosPorCat[cat].sort((a, b) => b.conteo - a.conteo);
});

// ─── ÍNDICE: productos por categoría + sexo (desde baseCompleta) ──────────
const prodCatSexo = {}; // { "cat|F": { "producto": count } }
baseCompleta.forEach(r => {
  const cat = r.grupos_sustancia_final;
  const prod = r.nom_pro;
  const s = r.sexo;
  if (!cat || cat === 'nan' || !prod || prod === 'nan' || !s) return;
  const key = `${cat}|${s}`;
  if (!prodCatSexo[key]) prodCatSexo[key] = {};
  prodCatSexo[key][prod] = (prodCatSexo[key][prod] || 0) + 1;
});

// ─── ÍNDICE: productos por categoría + intencionalidad ────────────────────
const prodCatIntenc = {}; // { "cat|intencional": { "producto": count } }
baseCompleta.forEach(r => {
  const cat = r.grupos_sustancia_final;
  const prod = r.nom_pro;
  const i = r.intencionalidad;
  if (!cat || cat === 'nan' || !prod || prod === 'nan' || !i) return;
  const key = `${cat}|${i}`;
  if (!prodCatIntenc[key]) prodCatIntenc[key] = {};
  prodCatIntenc[key][prod] = (prodCatIntenc[key][prod] || 0) + 1;
});

// Helper: obtener top N productos de un mapa { prod: count }
const topFromMap = (map, n = 20) => {
  return Object.entries(map)
    .sort((a, b) => b[1] - a[1])
    .slice(0, n)
    .map(([prod, count]) => `${prod}: ${count}`)
    .join(', ');
};

// Helper: match de categoría flexible (por palabra)
const matchCategory = (cat, query) => {
  const q = query.toLowerCase();
  const c = cat.toLowerCase();
  if (q.includes(c)) return true;
  // Separar por guiones bajos
  const words = c.split('_');
  return words.some(w => w.length > 2 && q.includes(w));
};

// ─── BÚSQUEDA LOCAL INTELIGENTE ────────────────────────────────────────────
const searchLocalData = (userQuery) => {
  const query = userQuery.toLowerCase();
  const results = [];

  // Determinar si pregunta por sexo
  const asksSexo = query.includes('sexo') || query.includes('femenino') || query.includes('masculino')
    || query.includes('hombre') || query.includes('mujer') || query.includes('mujeres')
    || query.includes('hombres') || /\bf\b/.test(query) || /\bm\b/.test(query);

  // Determinar sexo específico
  const askF = asksSexo && (query.includes('femenino') || query.includes('mujer') || /\bf\b/.test(query));
  const askM = asksSexo && (query.includes('masculino') || query.includes('hombre') || /\bm\b/.test(query));
  const targetSex = askF ? 'F' : (askM ? 'M' : null);

  // Determinar si pregunta por intencionalidad
  const asksIntenc = query.includes('intencional') || query.includes('accidental')
    || query.includes('voluntario') || query.includes('deliberado');
  const askIntenc = asksIntenc && query.includes('intencional');
  const askNoIntenc = asksIntenc && (query.includes('no intencional') || query.includes('accidental'));

  // 1. Buscar categorías mencionadas (flexible)
  const categoriasMencionadas = [...new Set(productosTodos.map(p => p.categoria))]
    .filter(cat => matchCategory(cat, query));

  // 2. Buscar productos específicos mencionados
  const productosMencionados = productosTodos.filter(p =>
    query.includes(p.producto.toLowerCase())
  );

  // 3. Por cada categoría mencionada, incluir top productos
  categoriasMencionadas.forEach(cat => {
    if (targetSex) {
      // Productos filtrados por categoría + sexo desde baseCompleta
      const key = `${cat}|${targetSex}`;
      const map = prodCatSexo[key];
      if (map && Object.keys(map).length > 0) {
        const total = Object.values(map).reduce((a, b) => a + b, 0);
        results.push(`PRODUCTOS EN "${cat}" PARA SEXO ${targetSex === 'F' ? 'FEMENINO' : 'MASCULINO'} (${Object.keys(map).length} productos, ${total} registros):\n${topFromMap(map, 25)}`);
      }
      // También ambos sexos para comparación
      if (askF || !askM) {
        const keyM = `${cat}|M`;
        const mapM = prodCatSexo[keyM];
        if (mapM) results.push(`(Comparación: ${cat} en M: ${Object.values(mapM).reduce((a,b)=>a+b,0)} registros)`);
      }
      if (askM || !askF) {
        const keyF = `${cat}|F`;
        const mapF = prodCatSexo[keyF];
        if (mapF) results.push(`(Comparación: ${cat} en F: ${Object.values(mapF).reduce((a,b)=>a+b,0)} registros)`);
      }
    } else {
      // Productos generales (sin filtrar por sexo)
      const prods = productosPorCat[cat] || [];
      const totalCat = prods.reduce((sum, p) => sum + (p.conteo || 0), 0);
      results.push(`CATEGORÍA "${cat}" (${prods.length} productos únicos, ${totalCat} registros):\nTop 25: ${prods.slice(0, 25).map(p => `${p.producto}: ${p.conteo}`).join(', ')}`);
    }
  });

  // 4. Si pregunta por sexo, incluir datos generales
  if (asksSexo) {
    const sexoData = sustanciaSexo.map(s =>
      `${s.sustancia}: F=${s.F}, M=${s.M} (total=${Number(s.F)+Number(s.M)})`
    ).join('\n');
    results.push('DATOS SUSTANCIA × SEXO:\n' + sexoData);
  }

  // 5. Si pregunta por intencionalidad
  if (asksIntenc) {
    const intData = sustanciasPorIntencionalidad.map(s =>
      `${s.sustancia}: total=${s.total}, intencional=${s.intencional} (${s.porcentaje_intencional}%), no_intencional=${s.no_intencional} (${s.porcentaje_no_intencional}%)`
    ).join('\n');
    results.push('DATOS SUSTANCIA × INTENCIONALIDAD:\n' + intData);
  }

  // 6. Productos específicos mencionados
  productosMencionados.forEach(p => {
    results.push(`PRODUCTO "${p.producto}": categoría=${p.categoria}, conteo=${p.conteo}, método=${p.metodo_clasificacion}`);
  });

  // 7. Blacklist
  if (query.includes('blacklist') || query.includes('filtrado') || query.includes('bloqueado')) {
    const blData = productosBlacklist.slice(0, 20).map(b => `${b.nombre_producto}: ${b.razon} (frecuencia: ${b.frecuencia})`).join('\n');
    results.push('BLACKLIST (top 20):\n' + blData);
  }

  // 8. Top / ranking global
  if (query.includes('top') || query.includes('ranking') || query.includes('más usad') || query.includes('mas usad') || query.includes('mas frecuente') || query.includes('más frecuente') || query.includes('primer') || query.includes('segundo') || query.includes('tercer')) {
    const topGlobal = productosTodos.sort((a, b) => b.conteo - a.conteo).slice(0, 30).map(p => `${p.producto} (${p.categoria}): ${p.conteo}`).join('\n');
    results.push('TOP 30 PRODUCTOS GLOBALES:\n' + topGlobal);
  }

  // 9. Contexto base siempre
  const baseContext = `KPIs: ${kpis.total_registros} registros, ${kpis.intencional} intencionales, ${kpis.no_intencional} no intencionales, F=${kpis.sexo_f}, M=${kpis.sexo_m}.
Top sustancias: ${sustancias.slice(0,5).map(s=>`${s.sustancia}:${s.numero_registros}`).join(', ')}.`;

  return baseContext + '\n\n' + results.join('\n\n');
};

// ─── FORMATO MARKDOWN BÁSICO ─────────────────────────────────────
const formatMarkdown = (text) => {
  // Escapar HTML primero para seguridad
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // **negrita**
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

  // Saltos de línea dobles → párrafos
  const paragraphs = html.split('\n\n');
  html = paragraphs.map(p => {
    // Detectar listas numeradas
    const lines = p.split('\n');
    const isNumberedList = lines.every(l => /^\d+\.\s/.test(l.trim()) || l.trim() === '');
    const isBulletList = lines.every(l => /^[-•]\s/.test(l.trim()) || l.trim() === '');

    if (isNumberedList && lines.length > 1) {
      const items = lines
        .filter(l => /^\d+\.\s/.test(l.trim()))
        .map(l => `<li>${l.replace(/^\d+\.\s/, '')}</li>`)
        .join('');
      return `<ol>${items}</ol>`;
    }

    if (isBulletList && lines.length > 1) {
      const items = lines
        .filter(l => /^[-•]\s/.test(l.trim()))
        .map(l => `<li>${l.replace(/^[-•]\s/, '')}</li>`)
        .join('');
      return `<ul>${items}</ul>`;
    }

    // Si una línea empieza con número + punto, envolver en span
    return lines.map(l => {
      if (/^\d+\.\s/.test(l.trim())) {
        return `<span class="chat-numbered">${l}</span>`;
      }
      return l;
    }).join('<br/>');
  }).join('</p><p>');

  return `<p>${html}</p>`;
};
const buildSystemPrompt = () => {
  return `Eres un asistente experto en análisis epidemiológico y toxicológico de sustancias. Trabajas con datos reales del sistema SIVIGILA de notificación obligatoria en Colombia.

Tus capacidades:
- Analizar y comparar datos de clasificación de sustancias, productos, sexo e intencionalidad.
- Dar rankings, conteos, porcentajes y comparaciones precisas.

Reglas de estilo y formato:
1. Usa SOLO los datos del contexto. NUNCA inventes cifras.
2. Responde en español, de forma concisa pero completa.
3. IMPORTANTE: Para listas numeradas usa el formato "1. item" (número + punto + espacio).
4. Para texto destacado usa **negrita** con doble asterisco.
5. Separa párrafos con doble salto de línea.
6. Incluye cifras exactas con formato legible (ej: 27,006 en vez de 27006).
7. Si puedes dar un ranking, hazlo en lista numerada.`;
};

// ─── COMPONENTE ────────────────────────────────────────────────────────────
const ChatBot = () => {
  const [isOpen, setIsOpen] = useState(false);
  const DEFAULT_API_KEY = 'sk-90b9c21e412447b188162cab53fad814';

  const getInitialApiKey = () => {
    const envKey = import.meta.env?.VITE_DEEPSEEK_API_KEY;
    if (envKey) return envKey;
    const localKey = localStorage.getItem('deepseek_api_key');
    if (localKey) return localKey;
    const sessionKey = sessionStorage.getItem('deepseek_api_key');
    if (sessionKey) return sessionKey;
    return DEFAULT_API_KEY;
  };

  const [apiKey, setApiKey] = useState(getInitialApiKey);
  const [showConfig, setShowConfig] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'assistant', content: '¡Hola! Soy tu asistente de análisis. Pregúntame cualquier cosa sobre los datos de clasificación de sustancias.\n\n**Ejemplos de lo que puedo hacer:**\n\n1. ¿Cuál es el producto más usado en medicamentos_no_SPA?\n2. Compara cocaína vs alcohol por sexo\n3. Top 10 productos más frecuentes\n4. ¿Qué diferencia hay entre intencional y no intencional en opioides?' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    if (!apiKey.trim()) {
      setShowConfig(true);
      return;
    }

    const userQuery = input.trim();
    setMessages(prev => [...prev, { role: 'user', content: userQuery }]);
    setInput('');
    setLoading(true);

    // ─── BÚSQUEDA LOCAL: encontrar datos relevantes ──────────────────────
    const localData = searchLocalData(userQuery);

    // ─── Construir el mensaje del usuario con contexto enriquecido ───────
    const enrichedUserMsg = `Pregunta del usuario: "${userQuery}"

DATOS RELEVANTES ENCONTRADOS EN LA BASE LOCAL (usa estos datos para responder):
${localData}

Responde la pregunta del usuario basándote en los datos anteriores. Sé preciso con las cifras.`;

    try {
      const response = await fetch(DEEPSEEK_API_URL, {
        method: 'POST',
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
          stream: false,
        }),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.error?.message || `Error HTTP ${response.status}`);
      }

      const data = await response.json();
      const assistantContent = data.choices?.[0]?.message?.content || 'No se recibió respuesta.';
      setMessages(prev => [...prev, { role: 'assistant', content: assistantContent }]);
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `❌ Error: ${error.message}`
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const saveApiKey = () => {
    if (apiKey.trim()) {
      localStorage.setItem('deepseek_api_key', apiKey.trim());
      sessionStorage.setItem('deepseek_api_key', apiKey.trim());
      setShowConfig(false);
    }
  };

  const hasApiKey = Boolean(apiKey.trim());

  return (
    <>
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          position: 'fixed', bottom: '1.5rem', right: '1.5rem', zIndex: 100,
          width: '56px', height: '56px', borderRadius: '50%',
          background: 'linear-gradient(135deg, #1e3a5f, #2563eb)',
          color: 'white', border: 'none',
          boxShadow: '0 4px 14px rgba(0,0,0,0.25)',
          cursor: 'pointer', fontSize: '1.5rem',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          transition: 'transform 0.2s',
        }}
        title="Asistente de Análisis"
      >
        {isOpen ? '✕' : '💬'}
      </button>

      {isOpen && (
        <div style={{
          position: 'fixed', bottom: '5rem', right: '1.5rem', zIndex: 100,
          width: '420px', maxWidth: 'calc(100vw - 2rem)',
          height: '560px', maxHeight: 'calc(100vh - 7rem)',
          background: 'white', borderRadius: '1rem',
          boxShadow: '0 10px 40px rgba(0,0,0,0.2)',
          display: 'flex', flexDirection: 'column', overflow: 'hidden',
          border: '1px solid #e5e7eb',
        }}>
          <div style={{
            padding: '0.875rem 1rem',
            background: 'linear-gradient(135deg, #1e3a5f, #2563eb)',
            color: 'white', display: 'flex',
            justifyContent: 'space-between', alignItems: 'center',
          }}>
            <div>
              <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>Asistente de Análisis</div>
              <div style={{ fontSize: '0.75rem', opacity: 0.85 }}>DeepSeek · Datos locales enriquecidos</div>
            </div>
            <button
              onClick={() => setShowConfig(!showConfig)}
              title="Configurar API Key"
              style={{
                background: 'transparent', border: 'none',
                color: 'rgba(255,255,255,0.7)', fontSize: '0.85rem',
                cursor: 'pointer', padding: '0.25rem',
              }}
            >
              ⚙
            </button>
          </div>

          {showConfig && (
            <div style={{ padding: '0.75rem 1rem', background: '#f9fafb', borderBottom: '1px solid #e5e7eb' }}>
              <div style={{ fontSize: '0.8rem', color: '#374151', marginBottom: '0.5rem', fontWeight: 600 }}>
                API Key de DeepSeek
              </div>
              <input
                type="password" placeholder="sk-..."
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                style={{ width: '100%', padding: '0.5rem', borderRadius: '0.375rem', border: '1px solid #d1d5db', fontSize: '0.85rem', marginBottom: '0.5rem' }}
              />
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button onClick={saveApiKey} style={{ flex: 1, padding: '0.4rem', background: '#2563eb', color: 'white', border: 'none', borderRadius: '0.375rem', fontSize: '0.8rem', cursor: 'pointer' }}>
                  Guardar
                </button>
                <button onClick={() => setShowConfig(false)} style={{ flex: 1, padding: '0.4rem', background: '#e5e7eb', color: '#374151', border: 'none', borderRadius: '0.375rem', fontSize: '0.8rem', cursor: 'pointer' }}>
                  Cancelar
                </button>
              </div>
              {hasApiKey && <div style={{ fontSize: '0.7rem', color: '#10b981', marginTop: '0.3rem', fontWeight: 600 }}>Key activa</div>}
            </div>
          )}

          <div style={{
            flex: 1, overflowY: 'auto', padding: '1rem',
            display: 'flex', flexDirection: 'column', gap: '0.75rem',
            background: '#f9fafb',
          }}>
            {messages.map((msg, idx) => (
              <div key={idx} style={{
                alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                maxWidth: '90%',
                background: msg.role === 'user' ? 'linear-gradient(135deg, #6366f1, #4f46e5)' : '#ffffff',
                color: msg.role === 'user' ? 'white' : '#1f2937',
                padding: '0.75rem 1.1rem',
                borderRadius: msg.role === 'user' ? '1.1rem 1.1rem 0.3rem 1.1rem' : '1.1rem 1.1rem 1.1rem 0.3rem',
                fontSize: '0.875rem', lineHeight: 1.65,
                boxShadow: '0 1px 3px rgba(0,0,0,0.07)',
                wordBreak: 'break-word',
              }}>
                {msg.role === 'assistant' ? (
                  <div
                    className="chat-message-content"
                    dangerouslySetInnerHTML={{ __html: formatMarkdown(msg.content) }}
                  />
                ) : (
                  <span style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</span>
                )}
              </div>
            ))}
            {loading && (
              <div style={{ alignSelf: 'flex-start', background: 'white', padding: '0.75rem 1rem', borderRadius: '1rem 1rem 1rem 0.25rem', fontSize: '0.875rem', color: '#6b7280', boxShadow: '0 1px 2px rgba(0,0,0,0.08)' }}>
                🔍 Buscando datos relevantes...
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div style={{ padding: '0.75rem 1rem', borderTop: '1px solid #e5e7eb', background: 'white', display: 'flex', gap: '0.5rem' }}>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={hasApiKey ? 'Pregunta sobre los datos...' : 'Configura tu API Key (⚙)'}
              disabled={!hasApiKey || loading}
              rows={1}
              style={{
                flex: 1, padding: '0.6rem 0.75rem', borderRadius: '0.5rem',
                border: '1px solid #d1d5db', fontSize: '0.875rem',
                resize: 'none', outline: 'none', fontFamily: 'inherit',
                minHeight: '40px', maxHeight: '100px',
              }}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || !hasApiKey || loading}
              style={{
                padding: '0 1rem',
                background: (!input.trim() || !hasApiKey || loading) ? '#d1d5db' : '#2563eb',
                color: 'white', border: 'none', borderRadius: '0.5rem',
                fontSize: '0.875rem', fontWeight: 600,
                cursor: (!input.trim() || !hasApiKey || loading) ? 'not-allowed' : 'pointer',
                whiteSpace: 'nowrap',
              }}
            >
              Enviar
            </button>
          </div>
        </div>
      )}
    </>
  );
};

export default ChatBot;
