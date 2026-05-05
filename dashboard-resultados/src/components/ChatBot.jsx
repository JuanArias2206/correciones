import React, { useState, useRef, useEffect } from 'react';
import {
  kpis, sustancias, intencionalidad, sexo, sustanciasPorIntencionalidad,
  sustanciaSexo, productosTodos, conteoCategorias, productosPorCategoria,
  productosBlacklist
} from '../data/data';

const DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/chat/completions';

// ─── DATOS LOCALES: índices para búsqueda rápida ───────────────────────────
const ALL_DATA = {
  kpis, sustancias, intencionalidad, sexo,
  sustanciasPorIntencionalidad, sustanciaSexo,
  productosTodos, conteoCategorias, productosPorCategoria,
  productosBlacklist
};

// Mapa de categorías → productos (completo, no solo top 5)
const productosPorCat = {};
productosTodos.forEach(p => {
  if (!productosPorCat[p.categoria]) productosPorCat[p.categoria] = [];
  productosPorCat[p.categoria].push(p);
});
// Pre-ordenar cada categoría por conteo descendente
Object.keys(productosPorCat).forEach(cat => {
  productosPorCat[cat].sort((a, b) => b.conteo - a.conteo);
});

// Set de todas las palabras clave conocidas (categorías + productos + sustancias)
const keywords = new Set();
sustancias.forEach(s => keywords.add(s.sustancia.toLowerCase()));
productosTodos.forEach(p => {
  keywords.add(p.producto.toLowerCase());
  keywords.add(p.categoria.toLowerCase());
});
sexo.forEach(s => keywords.add(s.sexo.toLowerCase()));
intencionalidad.forEach(i => keywords.add(i.intencionalidad.toLowerCase()));

// ─── BÚSQUEDA LOCAL INTELIGENTE ────────────────────────────────────────────
const searchLocalData = (userQuery) => {
  const query = userQuery.toLowerCase();
  const results = [];

  // 1. Buscar categorías mencionadas
  const categoriasMencionadas = [...new Set(productosTodos.map(p => p.categoria))]
    .filter(cat => query.includes(cat.toLowerCase()) || query.includes(cat.replace(/_/g, ' ').toLowerCase()));

  // 2. Buscar productos específicos mencionados
  const productosMencionados = productosTodos.filter(p =>
    query.includes(p.producto.toLowerCase())
  );

  // 3. Si menciona alguna categoría, incluir sus productos top 20
  categoriasMencionadas.forEach(cat => {
    const prods = productosPorCat[cat] || [];
    const totalCat = prods.reduce((sum, p) => sum + (p.conteo || 0), 0);
    const top20 = prods.slice(0, 20).map(p => `${p.producto}: ${p.conteo}`).join(', ');
    results.push(`CATEGORÍA "${cat}" (${prods.length} productos únicos, ${totalCat} registros totales):
Top 20: ${top20}`);
  });

  // 4. Si pregunta por sexo
  if (query.includes('sexo') || query.includes('femenino') || query.includes('masculino') || query.includes('hombre') || query.includes('mujer') || query.includes('f ') || query.includes('m ')) {
    const sexoData = sustanciaSexo.map(s =>
      `${s.sustancia}: F=${s.F}, M=${s.M} (total=${Number(s.F)+Number(s.M)})`
    ).join('\n');
    results.push('DATOS COMPLETOS SUSTANCIA × SEXO:\n' + sexoData);
  }

  // 5. Si pregunta por intencionalidad
  if (query.includes('intencional') || query.includes('accidental') || query.includes('voluntario') || query.includes('deliberado')) {
    const intData = sustanciasPorIntencionalidad.map(s =>
      `${s.sustancia}: total=${s.total}, intencional=${s.intencional} (${s.porcentaje_intencional}%), no_intencional=${s.no_intencional} (${s.porcentaje_no_intencional}%)`
    ).join('\n');
    results.push('DATOS COMPLETOS SUSTANCIA × INTENCIONALIDAD:\n' + intData);
  }

  // 6. Si pregunta por productos específicos mencionados (con contexto)
  productosMencionados.forEach(p => {
    results.push(`PRODUCTO "${p.producto}": categoría=${p.categoria}, conteo=${p.conteo}, método=${p.metodo_clasificacion}`);
  });

  // 7. Si pregunta por blacklist
  if (query.includes('blacklist') || query.includes('filtrado') || query.includes('bloqueado')) {
    const blData = productosBlacklist.slice(0, 20).map(b =>
      `${b.nombre_producto}: ${b.razon} (frecuencia: ${b.frecuencia})`
    ).join('\n');
    results.push('PRODUCTOS EN BLACKLIST (top 20):\n' + blData);
  }

  // 8. Si pregunta por top/ranking
  if (query.includes('top') || query.includes('ranking') || query.includes('más usad') || query.includes('mas usad') || query.includes('mas frecuente') || query.includes('más frecuente') || query.includes('primer') || query.includes('segundo') || query.includes('tercer')) {
    const topGlobal = productosTodos
      .sort((a, b) => b.conteo - a.conteo)
      .slice(0, 30)
      .map(p => `${p.producto} (${p.categoria}): ${p.conteo}`)
      .join('\n');
    results.push('TOP 30 PRODUCTOS GLOBALES:\n' + topGlobal);
  }

  // 9. Si pregunta por conteo general
  if (query.includes('total') || query.includes('cuántos') || query.includes('cuantos') || query.includes('resumen') || query.includes('general')) {
    results.push(`RESUMEN GENERAL:
- Total registros: ${kpis.total_registros}
- Intencionales: ${kpis.intencional} (${kpis.pct_intencional}%)
- No intencionales: ${kpis.no_intencional} (${kpis.pct_no_intencional}%)
- Femenino: ${kpis.sexo_f} registros
- Masculino: ${kpis.sexo_m} registros
- Categorías: ${kpis.categorias_detectadas}
- Top sustancias: ${sustancias.slice(0,5).map(s=>s.sustancia+':'+s.numero_registros).join(', ')}`);
  }

  // 10. Siempre incluir KPIs base + top sustancias para contexto mínimo
  const baseContext = `KPIs: ${kpis.total_registros} registros, ${kpis.intencional} intencionales, ${kpis.no_intencional} no intencionales, F=${kpis.sexo_f}, M=${kpis.sexo_m}.
Top sustancias: ${sustancias.slice(0,5).map(s=>`${s.sustancia}:${s.numero_registros}`).join(', ')}.
Categorías: ${conteoCategorias.map(c=>`${c.categoria}:${c.conteo}`).join(', ')}.`;

  return baseContext + '\n\n' + results.join('\n\n');
};

// ─── SYSTEM PROMPT BASE ────────────────────────────────────────────────────
const buildSystemPrompt = () => {
  return `Eres un asistente experto en análisis epidemiológico y toxicológico de sustancias. Trabajas con datos reales del sistema SIVIGILA de notificación obligatoria en Colombia.

Tus capacidades:
- Analizar y comparar datos de clasificación de sustancias, productos, sexo e intencionalidad.
- Responder con precisión basándote en los datos que se te proporcionan.
- Dar rankings, conteos, porcentajes y comparaciones.
- Interpretar patrones epidemiológicos.

Reglas:
1. Usa SOLO los datos que aparecen en el contexto del mensaje del usuario. NUNCA inventes cifras ni productos.
2. Si la información para responder no está en el contexto proporcionado, dilo claramente.
3. Responde SIEMPRE en español, de forma concisa pero completa.
4. Usa formato de lista cuando enumeres varios items.
5. Incluye cifras exactas (conteos) cuando estén disponibles.
6. Puedes calcular porcentajes, diferencias y proporciones con los datos dados.`;
};

// ─── COMPONENTE ────────────────────────────────────────────────────────────
const ChatBot = () => {
  const [isOpen, setIsOpen] = useState(false);
  const getInitialApiKey = () => {
    const envKey = import.meta.env?.VITE_DEEPSEEK_API_KEY;
    if (envKey) return envKey;
    const localKey = localStorage.getItem('deepseek_api_key');
    if (localKey) return localKey;
    return sessionStorage.getItem('deepseek_api_key') || '';
  };

  const [apiKey, setApiKey] = useState(getInitialApiKey);
  const [showConfig, setShowConfig] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'assistant', content: '¡Hola! Soy tu asistente de análisis para los datos de clasificación de sustancias. Puedo consultar todas las categorías, productos, sexo e intencionalidad en tiempo real.\n\nPrueba preguntarme cosas como:\n• "¿Cuál es el producto más usado en medicamentos_no_SPA?"\n• "Compara cocaína vs alcohol por sexo"\n• "Top 10 productos más frecuentes"\n• "¿Qué diferencia hay entre intencional y no intencional en opioides?"' }
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
                background: msg.role === 'user' ? '#2563eb' : 'white',
                color: msg.role === 'user' ? 'white' : '#1f2937',
                padding: '0.75rem 1rem',
                borderRadius: msg.role === 'user' ? '1rem 1rem 0.25rem 1rem' : '1rem 1rem 1rem 0.25rem',
                fontSize: '0.875rem', lineHeight: 1.6,
                boxShadow: '0 1px 2px rgba(0,0,0,0.08)',
                whiteSpace: 'pre-wrap', wordBreak: 'break-word',
              }}>
                {msg.content}
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
