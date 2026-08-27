// Vercel Serverless Function: Multi-Provider Voice & Brain Cascade Failover
// Zero-dependency, ultra-fast execution for Vercel Edge/Node runtime

export const config = {
  maxDuration: 15,
};

const LOCAL_ABBR = {
  'tks': 'cảm ơn', 'thx': 'cảm ơn', 'cam on': 'cảm ơn',
  'ko': 'không', 'k': 'không', 'hok': 'không', 'khum': 'không',
  'dc': 'được', 'đc': 'được', 'dk': 'được',
  'bt': 'biết', 'bít': 'biết',
  'ng': 'người', 'ngta': 'người ta',
  'j': 'gì', 'gi': 'gì',
  'vs': 'với', 'w': 'với',
  'h': 'giờ', 'mn': 'mọi người',
  'a': 'anh', 'e': 'em', 'c': 'chị'
};

function localNormalize(text) {
  let res = text;
  // Currency
  res = res.replace(/(\d+)\s*(?:k|K)\b/g, '$1 nghìn đồng');
  res = res.replace(/(\d+)\s*(?:tr|TR|củ)\b/g, '$1 triệu đồng');
  res = res.replace(/(\d+)\s*(?:đ|vnd|VND|đồng)\b/g, '$1 đồng');
  // Dates DD/MM/YYYY
  res = res.replace(/(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})/g, 'ngày $1 tháng $2 năm $3');
  res = res.replace(/(\d{1,2})[\/\-](\d{1,2})/g, 'ngày $1 tháng $2');
  // Abbreviations
  const words = res.split(/\s+/);
  const cleanWords = words.map(w => {
    const clean = w.replace(/[^\w\s]/gi, '').toLowerCase();
    if (LOCAL_ABBR[clean]) {
      const punct = w.replace(/[\w\s]/gi, '');
      return LOCAL_ABBR[clean] + punct;
    }
    return w;
  });
  return cleanWords.join(' ');
}

// 1. Brain Cascade (Gemini -> Groq -> Nvidia NIM -> Local)
async function normalizeBrainCascade(text, customKeys = {}) {
  const geminiKey = customKeys.gemini || process.env.GEMINI_API_KEY;
  const groqKey = customKeys.groq || process.env.GROQ_API_KEY;
  const nvidiaKey = customKeys.nvidia || process.env.NVIDIA_NIM_API_KEY;

  // Tier 1: Gemini
  if (geminiKey) {
    try {
      const prompt = `Ban la bo nao chuan hoa van ban tieng Viet cho he thong giong noi TTS. Chuyen toan bo so, ngay thang, viet tat, tieng long sang chu tieng Viet tron vanh ro chu. Chi tra ve duy nhat cau da chuan hoa.\nCau: "${text}"`;
      const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${geminiKey}`;
      const resp = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents: [{ parts: [{ text: prompt }] }],
          generationConfig: { temperature: 0.2, maxOutputTokens: 250 }
        })
      });
      if (resp.ok) {
        const data = await resp.json();
        const norm = data.candidates?.[0]?.content?.parts?.[0]?.text?.trim();
        if (norm) return { text: norm.replace(/^"|"$/g, ''), provider: 'Gemini 2.0 Flash (Tier 1)' };
      }
    } catch (e) {
      console.warn('Gemini failover:', e.message);
    }
  }

  // Tier 2: Groq Llama 3.3
  if (groqKey) {
    try {
      const resp = await fetch('https://api.groq.com/openai/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${groqKey}`
        },
        body: JSON.stringify({
          model: 'llama-3.3-70b-versatile',
          messages: [
            { role: 'system', content: 'Chuan hoa so, ngay thang, tu viet tat sang chu tieng Viet cho TTS. Chi tra ve cau ket qua duy nhat.' },
            { role: 'user', content: text }
          ],
          temperature: 0.2,
          max_tokens: 250
        })
      });
      if (resp.ok) {
        const data = await resp.json();
        const norm = data.choices?.[0]?.message?.content?.trim();
        if (norm) return { text: norm.replace(/^"|"$/g, ''), provider: 'Groq Llama 3.3 (Tier 2)' };
      }
    } catch (e) {
      console.warn('Groq failover:', e.message);
    }
  }

  // Tier 3: Nvidia NIM
  if (nvidiaKey) {
    try {
      const resp = await fetch('https://integrate.api.nvidia.com/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${nvidiaKey}`
        },
        body: JSON.stringify({
          model: 'meta/llama-3.3-70b-instruct',
          messages: [
            { role: 'system', content: 'Chuan hoa so, ngay thang, viet tat tieng Viet cho TTS.' },
            { role: 'user', content: text }
          ],
          temperature: 0.2,
          max_tokens: 250
        })
      });
      if (resp.ok) {
        const data = await resp.json();
        const norm = data.choices?.[0]?.message?.content?.trim();
        if (norm) return { text: norm.replace(/^"|"$/g, ''), provider: 'NVIDIA NIM (Tier 3)' };
      }
    } catch (e) {
      console.warn('Nvidia failover:', e.message);
    }
  }

  // Tier 4: Local Regex
  return { text: localNormalize(text), provider: 'Local Rule Engine (Tier 4 - Offline)' };
}

// 2. Voice Cascade (ElevenLabs -> Fish Audio -> Edge/Fallback)
async function synthesizeVoiceCascade(text, customKeys = {}, voiceGender = 'male') {
  const elevenKey = customKeys.elevenlabs || process.env.ELEVENLABS_API_KEY;
  const fishKey = customKeys.fish_audio || process.env.FISH_AUDIO_API_KEY;

  // Tier 1: ElevenLabs (King of Quality)
  if (elevenKey) {
    try {
      const voiceId = customKeys.eleven_voice_id || process.env.ELEVENLABS_VOICE_ID || '21m00Tcm4TlvDq8ikWAM';
      const resp = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${voiceId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'xi-api-key': elevenKey,
          'Accept': 'audio/mpeg'
        },
        body: JSON.stringify({
          text: text,
          model_id: 'eleven_multilingual_v2',
          voice_settings: { stability: 0.5, similarity_boost: 0.8 }
        })
      });
      if (resp.ok) {
        const audioBuffer = await resp.arrayBuffer();
        return { buffer: Buffer.from(audioBuffer), format: 'mp3', provider: 'ElevenLabs API (Tier 1 - Vua Chất Lượng)' };
      }
    } catch (e) {
      console.warn('ElevenLabs failover:', e.message);
    }
  }

  // Tier 2: Fish Audio (Fish Speech)
  if (fishKey) {
    try {
      const refId = customKeys.fish_ref_id || process.env.FISH_AUDIO_REF_ID || 'default';
      const resp = await fetch('https://api.fish.audio/v1/tts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${fishKey}`,
          'Accept': 'audio/mpeg'
        },
        body: JSON.stringify({
          text: text,
          reference_id: refId,
          format: 'mp3',
          mp3_bitrate: 128
        })
      });
      if (resp.ok) {
        const audioBuffer = await resp.arrayBuffer();
        return { buffer: Buffer.from(audioBuffer), format: 'mp3', provider: 'Fish Audio API (Tier 2 - Fish Speech)' };
      }
    } catch (e) {
      console.warn('Fish Audio failover:', e.message);
    }
  }

  // Tier 4 Fallback
  return null;
}

export default async function handler(req, res) {
  // CORS Headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    return res.status(200).json({ ok: true });
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const t0 = Date.now();
  try {
    const { text, style_id = 'neutral', voice_gender = 'male', custom_keys = {} } = req.body || {};

    if (!text || !text.trim()) {
      return res.status(400).json({ error: 'Văn bản không được để trống' });
    }

    // Step 1: Normalize via Brain Cascade
    const brainResult = await normalizeBrainCascade(text.trim(), custom_keys);

    // Step 2: Synthesize via Voice Cascade
    const voiceResult = await synthesizeVoiceCascade(brainResult.text, custom_keys, voice_gender);

    const elapsed = ((Date.now() - t0) / 1000).toFixed(2);

    if (voiceResult && voiceResult.buffer) {
      res.setHeader('Content-Type', 'audio/mpeg');
      res.setHeader('X-Brain-Provider', brainResult.provider);
      res.setHeader('X-Voice-Provider', voiceResult.provider);
      res.setHeader('X-Elapsed-Time', `${elapsed}s`);
      return res.status(200).send(voiceResult.buffer);
    } else {
      return res.status(200).json({
        status: 'success',
        normalized_text: brainResult.text,
        brain_provider: brainResult.provider,
        voice_provider: 'Edge-TTS Local/Client Fallback',
        elapsed_seconds: parseFloat(elapsed),
        message: 'Văn bản đã được chuẩn hóa qua Brain Cascade. Sẵn sàng phát âm.'
      });
    }
  } catch (err) {
    console.error('Serverless synthesize error:', err);
    return res.status(500).json({ error: err.message || 'Lỗi xử lý máy chủ' });
  }
}
