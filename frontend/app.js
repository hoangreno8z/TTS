/**
 * LAPQUE Personal Vietnamese TTS Studio - Frontend Client Logic
 */

document.addEventListener("DOMContentLoaded", () => {
  // Support dynamic Backend URL when deployed on Vercel
  const savedBackendUrl = localStorage.getItem("lapque_custom_backend_url");
  const isVercel = window.location.origin.includes("vercel.app");
  const API_BASE = savedBackendUrl || (isVercel ? "http://127.0.0.1:8000" : window.location.origin);

  // DOM Elements
  const textInput = document.getElementById("textInput");
  const charCount = document.getElementById("charCount");
  const wordCountText = document.getElementById("wordCountText");
  const btnGenerate = document.getElementById("btnGenerate");
  const btnGenerateText = document.getElementById("btnGenerateText");
  const progressBox = document.getElementById("progressBox");
  const progressStatus = document.getElementById("progressStatus");
  const progressBar = document.getElementById("progressBar");
  const progressTimer = document.getElementById("progressTimer");
  const healthBadge = document.getElementById("healthBadge");
  const healthText = document.getElementById("healthText");

  const audioPlayer = document.getElementById("audioPlayer");
  const resultBadge = document.getElementById("resultBadge");
  const resChars = document.getElementById("resChars");
  const resChunks = document.getElementById("resChunks");
  const resStyle = document.getElementById("resStyle");
  const resTime = document.getElementById("resTime");
  const btnDownloadWav = document.getElementById("btnDownloadWav");
  const btnDeleteOutput = document.getElementById("btnDeleteOutput");

  const voiceUpload = document.getElementById("voiceUpload");
  const voiceAnalysisResult = document.getElementById("voiceAnalysisResult");
  const anFilename = document.getElementById("anFilename");
  const anDuration = document.getElementById("anDuration");
  const anSr = document.getElementById("anSr");
  const anChannels = document.getElementById("anChannels");
  const anVAD = document.getElementById("anVAD");
  const anRecommendation = document.getElementById("anRecommendation");

  const stylesContainer = document.getElementById("stylesContainer");
  const btnOpenAddStyle = document.getElementById("btnOpenAddStyle");
  const btnCloseAddStyle = document.getElementById("btnCloseAddStyle");
  const addStyleForm = document.getElementById("addStyleForm");
  const btnSaveNewStyle = document.getElementById("btnSaveNewStyle");

  let activeStyle = "neutral";
  let currentAudioFile = null;
  let timerInterval = null;

  // 1. Check System Health & Fetch Styles
  async function checkHealthAndLoadStyles() {
    try {
      const res = await fetch(`${API_BASE}/health`);
      if (res.ok) {
        const data = await res.json();
        healthText.textContent = `Online • ${data.selected_engine.toUpperCase()}`;
        healthBadge.className = "flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
      } else {
        throw new Error("Offline");
      }
    } catch (e) {
      healthText.textContent = "Chưa kết nối Backend";
      healthBadge.className = "flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20";
    }

    loadStyles();
  }

  async function loadStyles() {
    try {
      const res = await fetch(`${API_BASE}/styles`);
      if (res.ok) {
        const styles = await res.json();
        renderStyles(styles);
      }
    } catch (e) {
      console.error("Could not load styles:", e);
    }
  }

  function renderStyles(styles) {
    stylesContainer.innerHTML = "";
    styles.forEach((st) => {
      const isActive = st.style_id === activeStyle;
      const btn = document.createElement("button");
      btn.type = "button";
      btn.setAttribute("data-style", st.style_id);
      btn.className = `style-card text-left p-4 rounded-xl border transition relative ${
        isActive
          ? "border-indigo-500/40 bg-indigo-500/10 active"
          : "border-slate-800 bg-slate-900/50 hover:border-slate-700"
      }`;

      let icon = "fa-microphone-lines";
      if (st.style_id === "serious") icon = "fa-landmark";
      if (st.style_id === "storytelling") icon = "fa-book-open-reader";
      if (st.style_id.includes("lali")) icon = "fa-wand-magic-sparkles";

      btn.innerHTML = `
        <div class="flex items-center justify-between mb-1">
          <span class="font-semibold text-sm ${isActive ? 'text-indigo-300' : 'text-slate-300'} flex items-center gap-1.5 truncate">
            <i class="fa-solid ${icon} text-xs"></i> ${st.name}
          </span>
          <span class="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 ${isActive ? 'bg-indigo-500/20 text-indigo-300' : 'text-slate-400'} font-mono">${st.speed}x</span>
        </div>
        <p class="text-xs text-slate-400 line-clamp-2">${st.description}</p>
      `;

      btn.addEventListener("click", () => {
        activeStyle = st.style_id;
        document.querySelectorAll(".style-card").forEach(b => {
          b.classList.remove("border-indigo-500/40", "bg-indigo-500/10", "active");
          b.classList.add("border-slate-800", "bg-slate-900/50");
        });
        btn.classList.remove("border-slate-800", "bg-slate-900/50");
        btn.classList.add("border-indigo-500/40", "bg-indigo-500/10", "active");
        
        const badge = document.getElementById("targetStyleBadge");
        if (badge) badge.textContent = `Gắn cho: ${activeStyle}`;
      });

      stylesContainer.appendChild(btn);
    });
  }

  checkHealthAndLoadStyles();

  // 2. Custom Style Toggle & Creation with Multiple MP3 Files
  btnOpenAddStyle.addEventListener("click", () => {
    addStyleForm.classList.toggle("hidden");
  });
  btnCloseAddStyle.addEventListener("click", () => {
    addStyleForm.classList.add("hidden");
  });

  const btnSaveNewStyleText = document.getElementById("btnSaveNewStyleText");
  const newStyleFiles = document.getElementById("newStyleFiles");

  btnSaveNewStyle.addEventListener("click", async () => {
    const sid = document.getElementById("newStyleId").value.trim().toLowerCase().replace(/\s+/g, "_");
    const sname = document.getElementById("newStyleName").value.trim();
    const sdesc = document.getElementById("newStyleDesc").value.trim();

    if (!sid || !sname) {
      alert("Vui lòng nhập đầy đủ Mã Style và Tên hiển thị!");
      return;
    }

    const files = newStyleFiles ? newStyleFiles.files : [];
    if (btnSaveNewStyleText) btnSaveNewStyleText.textContent = "Đang bóc tách phổ Fourier & tạo Style...";
    btnSaveNewStyle.disabled = true;

    try {
      if (files.length > 0) {
        const formData = new FormData();
        formData.append("style_id", sid);
        formData.append("style_name", sname);
        formData.append("description", sdesc);
        for (let i = 0; i < files.length; i++) {
          formData.append("files", files[i]);
        }

        const res = await fetch(`${API_BASE}/styles/upload-samples`, {
          method: "POST",
          body: formData
        });

        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || "Không thể bóc tách phổ");
        }

        const data = await res.json();
        alert(`🎉 ${data.message}\nĐã trích xuất ${data.profile.spectral_envelope_bins} dải tần Fourier và ${data.profile.faiss_timbre_vectors} vector âm sắc!`);
      } else {
        const res = await fetch(`${API_BASE}/styles`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            style_id: sid,
            name: sname,
            description: sdesc,
            speed: 1.0
          })
        });
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || "Không thể lưu style");
        }
      }

      activeStyle = sid;
      addStyleForm.classList.add("hidden");
      document.getElementById("newStyleId").value = "";
      document.getElementById("newStyleName").value = "";
      document.getElementById("newStyleDesc").value = "";
      if (newStyleFiles) newStyleFiles.value = "";
      await loadStyles();
      const badge = document.getElementById("targetStyleBadge");
      if (badge) badge.textContent = `Gắn cho: ${activeStyle}`;

    } catch (e) {
      alert(`Lỗi: ${e.message}`);
    } finally {
      if (btnSaveNewStyleText) btnSaveNewStyleText.textContent = "Bóc Tách Phổ Fourier & Tạo Style";
      btnSaveNewStyle.disabled = false;
    }
  });

  // 3. Character & Word Counter
  textInput.addEventListener("input", () => {
    const len = textInput.value.length;
    charCount.textContent = len.toLocaleString("vi-VN");
    
    const words = textInput.value.trim() ? textInput.value.trim().split(/\s+/).length : 0;
    const sentences = textInput.value.trim() ? textInput.value.split(/[\.\?!]+/).filter(Boolean).length : 0;
    wordCountText.textContent = `${words} từ • ~${sentences} câu`;

    if (len > 4500) {
      charCount.className = "font-bold text-amber-400";
    } else {
      charCount.className = "font-bold text-slate-200";
    }
  });

  // 4. Sample Text Buttons
  document.getElementById("btnSample1").addEventListener("click", () => {
    textInput.value = "Theo báo cáo mới nhất ngày 24/08/2026, PGS.TS Nguyễn Văn A tại TP.HCM đã công bố dự án công nghệ chuyển đổi văn bản tiếng Việt thành giọng nói tự nhiên với chi phí 0 đồng. Dự án giúp tăng trưởng 18.5% hiệu suất sản xuất nội dung số.";
    textInput.dispatchEvent(new Event("input"));
  });

  document.getElementById("btnSample2").addEventListener("click", () => {
    textInput.value = "Mùa thu Hà Nội luôn mang một vẻ đẹp dịu dàng và trầm mặc rất riêng. Khi những cơn gió heo may đầu mùa thổi qua từng góc phố cổ, mùi hoa sữa thoang thoảng quyện trong không gian se lạnh khiến lòng người bâng khuâng khó tả. Những hàng cây cơm nguội vàng soi bóng xuống mặt nước Hồ Gươm phẳng lặng, tạo nên bức tranh thiên nhiên tuyệt mỹ khó quên.";
    textInput.dispatchEvent(new Event("input"));
  });

  document.getElementById("btnClear").addEventListener("click", () => {
    textInput.value = "";
    textInput.dispatchEvent(new Event("input"));
  });

  let selectedGender = "male";
  let selectedCoreMode = "neural";
  const btnVoiceMale = document.getElementById("btnVoiceMale");
  const btnVoiceFemale = document.getElementById("btnVoiceFemale");
  const btnCoreNeural = document.getElementById("btnCoreNeural");
  const btnCoreParametric = document.getElementById("btnCoreParametric");
  const colabGpuUrl = document.getElementById("colabGpuUrl");

  if (btnCoreNeural && btnCoreParametric) {
    btnCoreNeural.addEventListener("click", () => {
      selectedCoreMode = "neural";
      btnCoreNeural.className = "px-2.5 py-1 rounded bg-indigo-600 text-white font-medium text-[11px] shadow-sm";
      btnCoreParametric.className = "px-2.5 py-1 rounded bg-slate-800 text-slate-400 font-medium text-[11px]";
    });
    btnCoreParametric.addEventListener("click", () => {
      selectedCoreMode = "parametric";
      btnCoreParametric.className = "px-2.5 py-1 rounded bg-indigo-600 text-white font-medium text-[11px] shadow-sm";
      btnCoreNeural.className = "px-2.5 py-1 rounded bg-slate-800 text-slate-400 font-medium text-[11px]";
    });
  }

  if (btnVoiceMale && btnVoiceFemale) {
    btnVoiceMale.addEventListener("click", () => {
      selectedGender = "male";
      btnVoiceMale.className = "px-2 py-0.5 rounded bg-indigo-600 text-white font-medium";
      btnVoiceFemale.className = "px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-medium";
    });
    btnVoiceFemale.addEventListener("click", () => {
      selectedGender = "female";
      btnVoiceFemale.className = "px-2 py-0.5 rounded bg-indigo-600 text-white font-medium";
      btnVoiceMale.className = "px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-medium";
    });
  }

  // 5. Synthesis Action
  btnGenerate.addEventListener("click", async () => {
    const text = textInput.value.trim();
    if (!text) {
      alert("Vui lòng nhập văn bản tiếng Việt trước khi tổng hợp!");
      return;
    }

    btnGenerate.disabled = true;
    btnGenerateText.textContent = "Đang Xử Lý...";
    progressBox.classList.remove("hidden");
    progressBar.style.width = "20%";
    progressStatus.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Đang chuẩn hóa văn bản tiếng Việt...';

    let startTime = Date.now();
    timerInterval = setInterval(() => {
      const sec = ((Date.now() - startTime) / 1000).toFixed(1);
      progressTimer.textContent = `${sec}s`;
    }, 100);

    try {
      setTimeout(() => {
        progressBar.style.width = "50%";
        progressStatus.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Đang phân đoạn & biến đổi sóng âm V7...';
      }, 400);

      const gpuUrl = colabGpuUrl ? colabGpuUrl.value.trim() : "";
      const response = await fetch(`${API_BASE}/tts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: text,
          style_id: activeStyle,
          voice_gender: selectedGender,
          core_mode: selectedCoreMode,
          gpu_server_url: gpuUrl || undefined
        })
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Không thể tổng hợp âm thanh.");
      }

      progressBar.style.width = "90%";
      progressStatus.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Đang ghép nối master audio WAV...';

      const data = await response.json();

      progressBar.style.width = "100%";
      progressStatus.innerHTML = '<i class="fa-solid fa-check text-emerald-400"></i> Hoàn thành!';

      currentAudioFile = data.audio_file;
      audioPlayer.src = `${API_BASE}/outputs/${data.audio_file}`;
      audioPlayer.play().catch(() => {});

      resChars.textContent = data.total_characters.toLocaleString("vi-VN");
      resChunks.textContent = data.total_chunks;
      resStyle.textContent = data.style;
      resTime.textContent = `${data.elapsed_seconds}s`;
      resultBadge.textContent = "Thành công";
      resultBadge.className = "text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 font-mono";

      btnDownloadWav.href = `${API_BASE}/outputs/${data.audio_file}`;
      btnDownloadWav.classList.remove("opacity-50", "pointer-events-none");
      btnDeleteOutput.classList.remove("opacity-50", "pointer-events-none");

    } catch (err) {
      alert(`Lỗi: ${err.message}`);
      progressStatus.innerHTML = `<i class="fa-solid fa-triangle-exclamation text-rose-400"></i> ${err.message}`;
    } finally {
      clearInterval(timerInterval);
      btnGenerate.disabled = false;
      btnGenerateText.textContent = "Tổng Hợp Giọng Nói";
      setTimeout(() => {
        progressBox.classList.add("hidden");
      }, 3000);
    }
  });

  // 6. Delete Output Action
  btnDeleteOutput.addEventListener("click", async () => {
    if (!currentAudioFile) return;
    if (!confirm("Bạn có chắc chắn muốn xóa file âm thanh vừa tạo?")) return;

    try {
      const res = await fetch(`${API_BASE}/outputs/${currentAudioFile}`, { method: "DELETE" });
      if (res.ok) {
        audioPlayer.src = "";
        btnDownloadWav.classList.add("opacity-50", "pointer-events-none");
        btnDeleteOutput.classList.add("opacity-50", "pointer-events-none");
        resultBadge.textContent = "Đã xóa";
        resultBadge.className = "text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono";
        currentAudioFile = null;
      }
    } catch (e) {
      alert(`Không thể xóa: ${e.message}`);
    }
  });

  // 7. Voice Reference Upload & Multi-file Fourier Slicing
  const refAudioPlayer = document.getElementById("refAudioPlayer");
  const anF0 = document.getElementById("anF0");
  const anVectors = document.getElementById("anVectors");
  const anFormants = document.getElementById("anFormants");

  voiceUpload.addEventListener("change", async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const formData = new FormData();
    formData.append("style_id", activeStyle);
    for (let i = 0; i < files.length; i++) {
      formData.append("files", files[i]);
    }

    anFilename.innerHTML = `<i class="fa-solid fa-spinner fa-spin text-indigo-400"></i> Đang bóc tách ${files.length} file MP3...`;
    anDuration.textContent = "Đang phân tích phổ...";
    voiceAnalysisResult.classList.remove("hidden");

    try {
      const res = await fetch(`${API_BASE}/styles/upload-samples`, {
        method: "POST",
        body: formData
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Lỗi tải file" }));
        throw new Error(err.detail || "Lỗi tải file");
      }
      const data = await res.json();
      const prof = data.profile;

      anFilename.innerHTML = `<i class="fa-solid fa-circle-check text-emerald-400"></i> ${files.length > 1 ? `${files.length} files (${prof.total_duration_seconds}s)` : files[0].name}`;
      anDuration.textContent = `${prof.total_duration_seconds}s`;

      if (anF0 && prof.f0_statistics) {
        anF0.textContent = `${prof.f0_statistics.f0_mean_hz} Hz (±${prof.f0_statistics.f0_std_hz})`;
      }
      if (anVectors) {
        anVectors.textContent = `${prof.faiss_timbre_vectors.toLocaleString()} vectors`;
      }
      if (anFormants && prof.formants) {
        anFormants.textContent = `F1: ${prof.formants.F1_hz}Hz | F2: ${prof.formants.F2_hz}Hz | F3: ${prof.formants.F3_hz}Hz | F4: ${prof.formants.F4_hz}Hz`;
      }

      anRecommendation.textContent = `✅ Đã bóc tách 2048 dải tần Fourier & lưu vào Style '${activeStyle}'!`;
      anRecommendation.className = "text-emerald-400 font-medium pt-1 text-center";

      if (refAudioPlayer) {
        refAudioPlayer.src = `${API_BASE}/voice_ref/${activeStyle}/reference.wav?t=${Date.now()}`;
        refAudioPlayer.load();
      }

      await loadStyles();
      alert(`🎉 Bóc tách thành công ${files.length} file âm thanh mẫu cho Style '${activeStyle}'!\n- Tổng thời lượng: ${prof.total_duration_seconds}s\n- Dải tần số Fourier: 1025 bins\n- Vector Faiss: ${prof.faiss_timbre_vectors}`);
    } catch (err) {
      anFilename.textContent = "Lỗi bóc tách";
      anDuration.textContent = "Thất bại";
      anRecommendation.textContent = err.message;
      anRecommendation.className = "text-rose-400 font-medium pt-1 text-center";
    }
  });

  // =========================================================================
  // 8. INTERACTIVE MP3 WAVEFORM CUTTER & REAL-TIME AUDIO SLICER
  // =========================================================================
  const cutterModal = document.getElementById("cutterModal");
  const btnOpenCutterHeader = document.getElementById("btnOpenCutterHeader");
  const btnOpenCutterBox = document.getElementById("btnOpenCutterBox");
  const btnCloseCutterModal = document.getElementById("btnCloseCutterModal");
  const cutterUploadArea = document.getElementById("cutterUploadArea");
  const cutterFileInput = document.getElementById("cutterFileInput");
  const cutterUploadText = document.getElementById("cutterUploadText");
  const cutterWaveformSection = document.getElementById("cutterWaveformSection");
  const waveformCanvas = document.getElementById("waveformCanvas");
  const waveformLoading = document.getElementById("waveformLoading");

  const cutterLiveTimeReadout = document.getElementById("cutterLiveTimeReadout");
  const cutterStartBadge = document.getElementById("cutterStartBadge");
  const cutterEndBadge = document.getElementById("cutterEndBadge");
  const cutterDurBadge = document.getElementById("cutterDurBadge");
  const startFormattedDisplay = document.getElementById("startFormattedDisplay");
  const endFormattedDisplay = document.getElementById("endFormattedDisplay");

  const cutterStartInput = document.getElementById("cutterStartInput");
  const cutterEndInput = document.getElementById("cutterEndInput");
  const btnPlayCutterSelection = document.getElementById("btnPlayCutterSelection");
  const btnPlayCutterText = document.getElementById("btnPlayCutterText");
  const playIcon = document.getElementById("playIcon");
  const btnStopCutter = document.getElementById("btnStopCutter");

  const cutterCurrentStyleName = document.getElementById("cutterCurrentStyleName");
  const cutterNewStyleInputs = document.getElementById("cutterNewStyleInputs");
  const btnExecuteSliceAndProfile = document.getElementById("btnExecuteSliceAndProfile");
  const btnExecuteSliceText = document.getElementById("btnExecuteSliceText");

  // Nudge Buttons
  const btnStartMinus1 = document.getElementById("btnStartMinus1");
  const btnStartMinus01 = document.getElementById("btnStartMinus01");
  const btnStartPlus01 = document.getElementById("btnStartPlus01");
  const btnStartPlus1 = document.getElementById("btnStartPlus1");

  const btnEndMinus1 = document.getElementById("btnEndMinus1");
  const btnEndMinus01 = document.getElementById("btnEndMinus01");
  const btnEndPlus01 = document.getElementById("btnEndPlus01");
  const btnEndPlus1 = document.getElementById("btnEndPlus1");

  let cutterAudioBuffer = null;
  let cutterAudioCtx = null;
  let cutterSourceNode = null;
  let cutterRawFile = null;
  let cutterTotalDuration = 0;
  let cutterStartSec = 0.0;
  let cutterEndSec = 10.0;
  let isPlayingSelection = false;
  let animFrameId = null;
  let playbackStartTime = 0;
  let currentPlayheadPos = 0;
  let dragMode = null; // 'start', 'end', 'pan', 'new'

  function openCutter() {
    if (cutterCurrentStyleName) cutterCurrentStyleName.textContent = activeStyle;
    cutterModal.classList.remove("hidden");
    cutterModal.style.display = "flex";
  }

  function closeCutter() {
    stopCutterAudio();
    cutterModal.classList.add("hidden");
    cutterModal.style.display = "none";
  }

  window.openCutterModal = openCutter;

  if (btnOpenCutterHeader) btnOpenCutterHeader.addEventListener("click", openCutter);
  if (btnOpenCutterBox) btnOpenCutterBox.addEventListener("click", openCutter);
  if (btnCloseCutterModal) btnCloseCutterModal.addEventListener("click", closeCutter);

  cutterModal.addEventListener("click", (e) => {
    if (e.target === cutterModal) closeCutter();
  });

  // Radio toggle for destination style
  document.querySelectorAll("input[name='cutterTarget']").forEach((radio) => {
    radio.addEventListener("change", (e) => {
      if (e.target.value === "new") {
        cutterNewStyleInputs.classList.remove("hidden");
      } else {
        cutterNewStyleInputs.classList.add("hidden");
      }
    });
  });

  cutterUploadArea.addEventListener("click", () => cutterFileInput.click());

  cutterFileInput.addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    stopCutterAudio();
    cutterRawFile = file;
    cutterUploadText.textContent = `Đang nạp file: ${file.name}...`;
    if (waveformLoading) waveformLoading.classList.remove("hidden");
    cutterWaveformSection.classList.remove("hidden");

    try {
      if (!cutterAudioCtx) {
        cutterAudioCtx = new (window.AudioContext || window.webkitAudioContext)();
      }
      const arrayBuf = await file.arrayBuffer();
      cutterAudioBuffer = await cutterAudioCtx.decodeAudioData(arrayBuf);
      cutterTotalDuration = cutterAudioBuffer.duration;

      cutterStartSec = 0.0;
      cutterEndSec = Math.min(15.0, cutterTotalDuration);
      currentPlayheadPos = cutterStartSec;

      updateTimeInputs();
      drawWaveform(cutterStartSec);
      cutterUploadText.textContent = `File: ${file.name} (${formatTimeMs(cutterTotalDuration)})`;
    } catch (err) {
      alert(`Không thể đọc file âm thanh này: ${err.message}`);
      cutterWaveformSection.classList.add("hidden");
      cutterUploadText.textContent = "Bấm để chọn file lồng tiếng / MP3 dài cần cắt";
    } finally {
      if (waveformLoading) waveformLoading.classList.add("hidden");
    }
  });

  function formatTimeMs(sec) {
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    const ms = Math.floor((sec % 1) * 1000);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}.${ms.toString().padStart(3, '0')}`;
  }

  function updateTimeInputs() {
    cutterStartInput.value = cutterStartSec.toFixed(1);
    cutterStartInput.max = cutterTotalDuration.toFixed(1);
    cutterEndInput.value = cutterEndSec.toFixed(1);
    cutterEndInput.max = cutterTotalDuration.toFixed(1);

    const dur = Math.max(0, cutterEndSec - cutterStartSec);
    const startFmt = formatTimeMs(cutterStartSec);
    const endFmt = formatTimeMs(cutterEndSec);

    if (cutterStartBadge) cutterStartBadge.textContent = startFmt;
    if (cutterEndBadge) cutterEndBadge.textContent = endFmt;
    if (cutterDurBadge) cutterDurBadge.textContent = `${dur.toFixed(1)}s`;
    if (startFormattedDisplay) startFormattedDisplay.textContent = startFmt;
    if (endFormattedDisplay) endFormattedDisplay.textContent = endFmt;

    if (!isPlayingSelection && cutterLiveTimeReadout) {
      cutterLiveTimeReadout.textContent = formatTimeMs(cutterStartSec);
    }
  }

  // Nudge adjustment helper
  function adjustStart(delta) {
    cutterStartSec = Math.max(0, Math.min(cutterStartSec + delta, cutterEndSec - 0.2));
    updateTimeInputs();
    drawWaveform(cutterStartSec);
  }

  function adjustEnd(delta) {
    cutterEndSec = Math.min(cutterTotalDuration, Math.max(cutterEndSec + delta, cutterStartSec + 0.2));
    updateTimeInputs();
    drawWaveform(cutterStartSec);
  }

  if (btnStartMinus1) btnStartMinus1.addEventListener("click", () => adjustStart(-1.0));
  if (btnStartMinus01) btnStartMinus01.addEventListener("click", () => adjustStart(-0.1));
  if (btnStartPlus01) btnStartPlus01.addEventListener("click", () => adjustStart(0.1));
  if (btnStartPlus1) btnStartPlus1.addEventListener("click", () => adjustStart(1.0));

  if (btnEndMinus1) btnEndMinus1.addEventListener("click", () => adjustEnd(-1.0));
  if (btnEndMinus01) btnEndMinus01.addEventListener("click", () => adjustEnd(-0.1));
  if (btnEndPlus01) btnEndPlus01.addEventListener("click", () => adjustEnd(0.1));
  if (btnEndPlus1) btnEndPlus1.addEventListener("click", () => adjustEnd(1.0));

  cutterStartInput.addEventListener("input", () => {
    cutterStartSec = Math.max(0, Math.min(parseFloat(cutterStartInput.value) || 0, cutterTotalDuration));
    if (cutterStartSec > cutterEndSec) cutterEndSec = Math.min(cutterStartSec + 5, cutterTotalDuration);
    updateTimeInputs();
    drawWaveform(cutterStartSec);
  });

  cutterEndInput.addEventListener("input", () => {
    cutterEndSec = Math.max(0, Math.min(parseFloat(cutterEndInput.value) || 0, cutterTotalDuration));
    if (cutterEndSec < cutterStartSec) cutterStartSec = Math.max(0, cutterEndSec - 5);
    updateTimeInputs();
    drawWaveform(cutterStartSec);
  });

  // Waveform Drawing at High Resolution
  function drawWaveform(playheadSec = null) {
    if (!cutterAudioBuffer) return;
    const canvas = waveformCanvas;
    const ctx = canvas.getContext("2d");
    
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * (window.devicePixelRatio || 1);
    canvas.height = rect.height * (window.devicePixelRatio || 1);

    const width = canvas.width;
    const height = canvas.height;
    const channelData = cutterAudioBuffer.getChannelData(0);
    const totalSamples = channelData.length;

    ctx.clearRect(0, 0, width, height);

    // 1. Draw Waveform Bars
    const barWidth = 2.0 * (window.devicePixelRatio || 1);
    const gap = 1.0 * (window.devicePixelRatio || 1);
    const numBars = Math.floor(width / (barWidth + gap));
    const step = Math.floor(totalSamples / numBars);
    const midY = height / 2;

    const startX = (cutterStartSec / cutterTotalDuration) * width;
    const endX = (cutterEndSec / cutterTotalDuration) * width;

    for (let i = 0; i < numBars; i++) {
      const x = i * (barWidth + gap);
      let maxVal = 0;
      const offset = i * step;
      for (let j = 0; j < step; j += 8) {
        const val = Math.abs(channelData[offset + j] || 0);
        if (val > maxVal) maxVal = val;
      }
      const barHeight = Math.max(2, maxVal * (height * 0.82));

      // Color inside selection vs outside
      if (x >= startX && x <= endX) {
        ctx.fillStyle = "#818cf8"; // indigo-400
      } else {
        ctx.fillStyle = "#334155"; // slate-700
      }
      ctx.fillRect(x, midY - barHeight / 2, barWidth, barHeight);
    }

    // 2. Highlight Selection Window
    ctx.fillStyle = "rgba(99, 102, 241, 0.22)";
    ctx.fillRect(startX, 0, Math.max(2, endX - startX), height);

    // 3. Selection Borders & Big Touch Handles (for mobile comfort)
    ctx.fillStyle = "#6366f1";
    ctx.fillRect(startX - 2, 0, 4, height);
    ctx.fillStyle = "#f43f5e";
    ctx.fillRect(endX - 2, 0, 4, height);

    // Start handle (Green/Indigo)
    ctx.fillStyle = "#a5b4fc";
    ctx.beginPath();
    ctx.arc(startX, 14, 8, 0, Math.PI * 2);
    ctx.fill();

    // End handle (Rose)
    ctx.fillStyle = "#fda4af";
    ctx.beginPath();
    ctx.arc(endX, 14, 8, 0, Math.PI * 2);
    ctx.fill();

    // 4. Live Playhead Indicator Line (Glowing Emerald)
    if (playheadSec !== null && playheadSec >= cutterStartSec && playheadSec <= cutterEndSec) {
      const playheadX = (playheadSec / cutterTotalDuration) * width;
      ctx.fillStyle = "#10b981"; // emerald-500
      ctx.fillRect(playheadX - 1.5, 0, 3, height);

      // Playhead top triangle marker
      ctx.beginPath();
      ctx.moveTo(playheadX - 6, 0);
      ctx.lineTo(playheadX + 6, 0);
      ctx.lineTo(playheadX, 10);
      ctx.closePath();
      ctx.fill();
    }
  }

  // Unified Mouse / Touch Coordinate Helper
  function getCanvasRelativeX(e) {
    const rect = waveformCanvas.getBoundingClientRect();
    const clientX = (e.touches && e.touches.length > 0) ? e.touches[0].clientX : e.clientX;
    const clickRatio = Math.max(0, Math.min((clientX - rect.left) / rect.width, 1.0));
    return clickRatio * cutterTotalDuration;
  }

  function handlePointerDown(e) {
    if (!cutterAudioBuffer) return;
    const clickSec = getCanvasRelativeX(e);
    const rect = waveformCanvas.getBoundingClientRect();
    const thresholdSec = (20 / rect.width) * cutterTotalDuration; // 20px touch tolerance

    if (Math.abs(clickSec - cutterStartSec) < thresholdSec) {
      dragMode = 'start';
    } else if (Math.abs(clickSec - cutterEndSec) < thresholdSec) {
      dragMode = 'end';
    } else if (clickSec > cutterStartSec && clickSec < cutterEndSec) {
      dragMode = 'pan';
    } else {
      dragMode = 'new';
      cutterStartSec = clickSec;
      cutterEndSec = Math.min(cutterStartSec + 5.0, cutterTotalDuration);
    }
    updateTimeInputs();
    drawWaveform(cutterStartSec);
  }

  function handlePointerMove(e) {
    if (!dragMode || !cutterAudioBuffer) return;
    const clickSec = getCanvasRelativeX(e);

    if (dragMode === 'start') {
      cutterStartSec = Math.max(0, Math.min(clickSec, cutterEndSec - 0.2));
    } else if (dragMode === 'end') {
      cutterEndSec = Math.min(cutterTotalDuration, Math.max(clickSec, cutterStartSec + 0.2));
    } else if (dragMode === 'new') {
      cutterEndSec = Math.min(cutterTotalDuration, Math.max(clickSec, cutterStartSec + 0.2));
    }
    updateTimeInputs();
    drawWaveform(cutterStartSec);
  }

  function handlePointerUp() {
    dragMode = null;
  }

  // Mouse & Touch Listeners with touch-action prevention
  waveformCanvas.addEventListener("mousedown", handlePointerDown);
  window.addEventListener("mousemove", handlePointerMove);
  window.addEventListener("mouseup", handlePointerUp);

  waveformCanvas.addEventListener("touchstart", (e) => {
    e.preventDefault();
    handlePointerDown(e);
  }, { passive: false });

  window.addEventListener("touchmove", (e) => {
    if (dragMode) {
      e.preventDefault();
      handlePointerMove(e);
    }
  }, { passive: false });

  window.addEventListener("touchend", handlePointerUp);

  // Play / Stop Selection with STRICT Hard-Stop at cutterEndSec
  function stopCutterAudio() {
    if (animFrameId) {
      cancelAnimationFrame(animFrameId);
      animFrameId = null;
    }
    if (cutterSourceNode) {
      try {
        cutterSourceNode.stop();
        cutterSourceNode.disconnect();
      } catch (e) {}
      cutterSourceNode = null;
    }
    isPlayingSelection = false;
    currentPlayheadPos = cutterStartSec;
    if (btnPlayCutterText) btnPlayCutterText.textContent = "Nghe Thử Đoạn Cắt";
    if (playIcon) playIcon.className = "fa-solid fa-play";
    if (cutterLiveTimeReadout) cutterLiveTimeReadout.textContent = formatTimeMs(cutterStartSec);
    drawWaveform(cutterStartSec);
  }

  btnPlayCutterSelection.addEventListener("click", () => {
    if (!cutterAudioBuffer) return;

    // Toggle Pause/Stop if currently playing
    if (isPlayingSelection) {
      stopCutterAudio();
      return;
    }

    stopCutterAudio();
    isPlayingSelection = true;
    if (btnPlayCutterText) btnPlayCutterText.textContent = "Tạm Dừng";
    if (playIcon) playIcon.className = "fa-solid fa-pause";

    if (cutterAudioCtx.state === 'suspended') {
      cutterAudioCtx.resume();
    }

    const durationToPlay = Math.max(0.1, cutterEndSec - cutterStartSec);
    cutterSourceNode = cutterAudioCtx.createBufferSource();
    cutterSourceNode.buffer = cutterAudioBuffer;
    cutterSourceNode.connect(cutterAudioCtx.destination);

    // Exact Web Audio API boundary start
    cutterSourceNode.start(0, cutterStartSec, durationToPlay);
    playbackStartTime = cutterAudioCtx.currentTime;

    // Real-Time 60 FPS Animation & Clock Counter with STRICT HARD STOP
    function updatePlayhead() {
      if (!isPlayingSelection) return;

      const elapsed = cutterAudioCtx.currentTime - playbackStartTime;
      const currentPos = cutterStartSec + elapsed;

      // STRICT HARD-STOP: If reached or exceeded end marker, STOP IMMEDIATELY!
      if (currentPos >= cutterEndSec) {
        stopCutterAudio();
        return;
      }

      currentPlayheadPos = currentPos;
      if (cutterLiveTimeReadout) {
        cutterLiveTimeReadout.textContent = formatTimeMs(currentPos);
      }
      drawWaveform(currentPos);

      animFrameId = requestAnimationFrame(updatePlayhead);
    }

    animFrameId = requestAnimationFrame(updatePlayhead);

    cutterSourceNode.onended = () => {
      stopCutterAudio();
    };
  });

  btnStopCutter.addEventListener("click", stopCutterAudio);

  // Execute Slicing & Profiling
  btnExecuteSliceAndProfile.addEventListener("click", async () => {
    if (!cutterRawFile) {
      alert("Vui lòng tải lên file âm thanh trước!");
      return;
    }

    const dur = cutterEndSec - cutterStartSec;
    if (dur < 0.5) {
      alert("Đoạn cắt quá ngắn (tối thiểu 0.5 giây).");
      return;
    }

    const targetType = document.querySelector("input[name='cutterTarget']:checked").value;
    let targetStyleId = activeStyle;
    let targetStyleName = "";

    if (targetType === "new") {
      targetStyleId = document.getElementById("cutterNewStyleId").value.trim().toLowerCase().replace(/\s+/g, "_");
      targetStyleName = document.getElementById("cutterNewStyleName").value.trim();
      if (!targetStyleId || !targetStyleName) {
        alert("Vui lòng nhập Mã Style và Tên hiển thị cho Style mới!");
        return;
      }
    }

    btnExecuteSliceAndProfile.disabled = true;
    if (btnExecuteSliceText) btnExecuteSliceText.textContent = "Đang cắt chính xác và bóc tách phổ Fourier...";

    const formData = new FormData();
    formData.append("file", cutterRawFile);
    formData.append("start_sec", cutterStartSec);
    formData.append("end_sec", cutterEndSec);
    formData.append("style_id", targetStyleId);
    if (targetStyleName) formData.append("style_name", targetStyleName);

    try {
      const res = await fetch(`${API_BASE}/audio/slice-and-profile`, {
        method: "POST",
        body: formData
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Lỗi cắt audio" }));
        throw new Error(err.detail || "Lỗi cắt audio");
      }

      const data = await res.json();
      activeStyle = targetStyleId;
      await loadStyles();
      closeCutter();

      alert(`🎉 ${data.message}\n- File cắt: ${data.sliced_file}\n- Formants: F1=${data.profile.formants.F1_hz}Hz, F2=${data.profile.formants.F2_hz}Hz\n- Vector Faiss: ${data.profile.faiss_timbre_vectors}`);

    } catch (e) {
      alert(`Lỗi: ${e.message}`);
    } finally {
      btnExecuteSliceAndProfile.disabled = false;
      if (btnExecuteSliceText) btnExecuteSliceText.textContent = "Cắt & Bóc Tách Phổ Nạp Vào Style Ngay";
    }
  });

  // =========================================================================
  // 9. AI JUDGE & CLOSED-LOOP AUTO-TUNE STUDIO (10 METRICS + SAMPLE SELECT + CONTINUE)
  // =========================================================================
  const autotuneModal = document.getElementById("autotuneModal");
  const btnOpenAutoTuneHeader = document.getElementById("btnOpenAutoTuneHeader");
  const btnCloseAutoTuneModal = document.getElementById("btnCloseAutoTuneModal");
  const atStyleDisplay = document.getElementById("atStyleDisplay");
  const atTestTextInput = document.getElementById("atTestTextInput");
  const atUserInstructionInput = document.getElementById("atUserInstructionInput");
  const atSampleSelect = document.getElementById("atSampleSelect");
  const atMaxRounds = document.getElementById("atMaxRounds");
  const btnRunAutoTune = document.getElementById("btnRunAutoTune");
  const atBtnText = document.getElementById("atBtnText");
  const atPlayIcon = document.getElementById("atPlayIcon");
  const atTotalScoreDisplay = document.getElementById("atTotalScoreDisplay");
  const atVerdictBadge = document.getElementById("atVerdictBadge");
  const atRoundStatusText = document.getElementById("atRoundStatusText");

  // 10 Detailed Metrics Elements
  const atScoreTimbre = document.getElementById("atScoreTimbre");
  const atBarTimbre = document.getElementById("atBarTimbre");
  const atScoreSpecEnv = document.getElementById("atScoreSpecEnv");
  const atBarSpecEnv = document.getElementById("atBarSpecEnv");
  const atScorePitchMean = document.getElementById("atScorePitchMean");
  const atBarPitchMean = document.getElementById("atBarPitchMean");
  const atScorePitchDyn = document.getElementById("atScorePitchDyn");
  const atBarPitchDyn = document.getElementById("atBarPitchDyn");
  const atScoreF1 = document.getElementById("atScoreF1");
  const atBarF1 = document.getElementById("atBarF1");
  const atScoreF2 = document.getElementById("atScoreF2");
  const atBarF2 = document.getElementById("atBarF2");
  const atScoreF3F4 = document.getElementById("atScoreF3F4");
  const atBarF3F4 = document.getElementById("atBarF3F4");
  const atScoreHnr = document.getElementById("atScoreHnr");
  const atBarHnr = document.getElementById("atBarHnr");
  const atScoreAntiCrackle = document.getElementById("atScoreAntiCrackle");
  const atBarAntiCrackle = document.getElementById("atBarAntiCrackle");
  const atScoreEnergyBal = document.getElementById("atScoreEnergyBal");
  const atBarEnergyBal = document.getElementById("atBarEnergyBal");

  const atRoundsList = document.getElementById("atRoundsList");
  const atCritiqueLog = document.getElementById("atCritiqueLog");
  const atAudioPlayer = document.getElementById("atAudioPlayer");
  const btnContinueAutoTune = document.getElementById("btnContinueAutoTune");
  const atContinueIcon = document.getElementById("atContinueIcon");
  const atContinueText = document.getElementById("atContinueText");
  const btnSaveOptimalPreset = document.getElementById("btnSaveOptimalPreset");
  const btnSavePresetText = document.getElementById("btnSavePresetText");
  const atPromptTranslationCard = document.getElementById("atPromptTranslationCard");
  const atPromptTranslationText = document.getElementById("atPromptTranslationText");

  let currentTuneSessionId = null;
  let selectedRoundNumber = null;
  let promptDebounceTimer = null;

  if (atUserInstructionInput) {
    atUserInstructionInput.addEventListener("input", () => {
      clearTimeout(promptDebounceTimer);
      const text = atUserInstructionInput.value.trim();
      if (!text) {
        if (atPromptTranslationCard) atPromptTranslationCard.classList.add("hidden");
        return;
      }
      promptDebounceTimer = setTimeout(async () => {
        try {
          const res = await fetch(`${API_BASE}/autotune/interpret-prompt`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ instruction: text })
          });
          if (res.ok) {
            const data = await res.json();
            if (data.status === "success" && data.compiled) {
              const exp = data.compiled.acoustic_explanation || "";
              if (atPromptTranslationText) atPromptTranslationText.textContent = exp;
              if (atPromptTranslationCard) atPromptTranslationCard.classList.remove("hidden");
            }
          }
        } catch (e) {}
      }, 300);
    });
  }

  async function loadStyleSamples(styleId) {
    if (!atSampleSelect) return;
    try {
      const res = await fetch(`${API_BASE}/voice_samples/${styleId}`);
      if (res.ok) {
        const data = await res.json();
        const samples = data.samples || [];
        atSampleSelect.innerHTML = "";
        if (samples.length === 0) {
          atSampleSelect.innerHTML = `<option value="">Mẫu mặc định (reference.wav)</option>`;
        } else {
          samples.forEach((s) => {
            const opt = document.createElement("option");
            opt.value = s.filename;
            opt.textContent = `${s.source === "voice" ? "⭐ Chuẩn:" : "✂️ Đoạn cắt:"} ${s.filename}`;
            atSampleSelect.appendChild(opt);
          });
        }
      }
    } catch (e) {
      atSampleSelect.innerHTML = `<option value="">Mẫu mặc định (reference.wav)</option>`;
    }
  }

  const btnTrainVoiceIndex = document.getElementById("btnTrainVoiceIndex");
  const btnTrainIndexText = document.getElementById("btnTrainIndexText");
  const iconTrainIndex = document.getElementById("iconTrainIndex");
  const atModelTrainedBadge = document.getElementById("atModelTrainedBadge");

  async function checkTrainingStatus(styleId) {
    if (!atModelTrainedBadge) return;
    try {
      const res = await fetch(`${API_BASE}/trainer/status/${styleId}`);
      if (res.ok) {
        const data = await res.json();
        if (data.has_trained_model) {
          atModelTrainedBadge.classList.remove("hidden");
          const totalSlices = data.meta?.total_slices_indexed || 0;
          atModelTrainedBadge.textContent = `🧠 Model Nơ-ron Đã Lập Chỉ Mục (${totalSlices} mẫu)`;
        } else {
          atModelTrainedBadge.classList.add("hidden");
        }
      }
    } catch (e) {
      atModelTrainedBadge.classList.add("hidden");
    }
  }

  if (btnTrainVoiceIndex) {
    btnTrainVoiceIndex.addEventListener("click", async () => {
      btnTrainVoiceIndex.disabled = true;
      if (btnTrainIndexText) btnTrainIndexText.textContent = "Đang trích xuất & huấn luyện...";
      if (iconTrainIndex) iconTrainIndex.className = "fa-solid fa-spinner fa-spin text-indigo-300";

      try {
        const res = await fetch(`${API_BASE}/trainer/train-index`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ style_id: activeStyle })
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: "Lỗi huấn luyện" }));
          throw new Error(err.detail || "Lỗi huấn luyện");
        }
        const data = await res.json();
        alert(`🎉 Huấn luyện thành công dấu vân tay AI Voice!\n- Đã phân tích: ${data.total_files} file mẫu gốc\n- Đã trích xuất và lập chỉ mục: ${data.total_slices} vector nơ-ron\n- Thời gian: ${data.training_time}s`);
        await checkTrainingStatus(activeStyle);
      } catch (e) {
        alert(`Không thể huấn luyện: ${e.message}`);
      } finally {
        btnTrainVoiceIndex.disabled = false;
        if (btnTrainIndexText) btnTrainIndexText.textContent = "Huấn Luyện AI (Index)";
        if (iconTrainIndex) iconTrainIndex.className = "fa-solid fa-graduation-cap text-indigo-400";
      }
    });
  }

  async function openAutoTuneModal() {
    if (atStyleDisplay) atStyleDisplay.textContent = activeStyle;
    autotuneModal.classList.remove("hidden");
    autotuneModal.style.display = "flex";

    await loadStyleSamples(activeStyle);
    await checkTrainingStatus(activeStyle);

    // Fetch existing optimal preset if available
    try {
      const res = await fetch(`${API_BASE}/autotune/preset/${activeStyle}`);
      if (res.ok) {
        const data = await res.json();
        if (data.status === "success" && data.preset) {
          renderExistingPreset(data.preset);
        }
      }
    } catch (e) {
      console.log("No existing preset found for", activeStyle);
    }
  }

  function closeAutoTuneModal() {
    autotuneModal.classList.add("hidden");
    autotuneModal.style.display = "none";
  }

  window.openAutoTuneModal = openAutoTuneModal;
  if (btnOpenAutoTuneHeader) btnOpenAutoTuneHeader.addEventListener("click", openAutoTuneModal);
  if (btnCloseAutoTuneModal) btnCloseAutoTuneModal.addEventListener("click", closeAutoTuneModal);

  autotuneModal.addEventListener("click", (e) => {
    if (e.target === autotuneModal) closeAutoTuneModal();
  });

  function renderExistingPreset(preset) {
    const score = preset.score || preset.best_score || 0;
    atTotalScoreDisplay.innerHTML = `<span>${score.toFixed(1)}</span><span class="text-lg text-slate-500 font-normal">/100</span>`;
    
    if (score >= 95.0) {
      atVerdictBadge.textContent = "XUẤT SẮC (ĐẠT CHUẨN 100Đ)";
      atVerdictBadge.className = "px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30";
    } else if (score >= 82.0) {
      atVerdictBadge.textContent = "RẤT TỐT (ĐẠT PHÒNG THU)";
      atVerdictBadge.className = "px-3 py-1 rounded-full text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30";
    } else {
      atVerdictBadge.textContent = "CẦN TỐI ƯU THÊM";
      atVerdictBadge.className = "px-3 py-1 rounded-full text-xs font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30";
    }

    atRoundStatusText.textContent = preset.approved_by_user ? "✅ Cấu hình này đã được bạn duyệt & lưu vào hệ thống" : `Đã chấm qua ${preset.total_rounds || 1} vòng`;

    if (preset.final_breakdown) {
      renderBreakdown(preset.final_breakdown);
    }
    if (preset.final_critique) {
      renderCritique(preset.final_critique);
    }
  }

  function renderBreakdown(b) {
    // 1. Timbre
    if (atScoreTimbre) atScoreTimbre.textContent = `${b.timbre_score || 0} / 20.0`;
    if (atBarTimbre) atBarTimbre.style.width = `${((b.timbre_score || 0) / 20.0) * 100}%`;

    // 2. Spec Env
    if (atScoreSpecEnv) atScoreSpecEnv.textContent = `${b.spectral_envelope_score || 0} / 15.0`;
    if (atBarSpecEnv) atBarSpecEnv.style.width = `${((b.spectral_envelope_score || 0) / 15.0) * 100}%`;

    // 3. Pitch Mean
    if (atScorePitchMean) atScorePitchMean.textContent = `${b.pitch_mean_score || b.pitch_score || 0} / 15.0`;
    if (atBarPitchMean) atBarPitchMean.style.width = `${((b.pitch_mean_score || b.pitch_score || 0) / 15.0) * 100}%`;

    // 4. Pitch Dynamics
    if (atScorePitchDyn) atScorePitchDyn.textContent = `${b.pitch_dynamics_score || 8.0} / 10.0`;
    if (atBarPitchDyn) atBarPitchDyn.style.width = `${((b.pitch_dynamics_score || 8.0) / 10.0) * 100}%`;

    // 5. Formant F1
    if (atScoreF1) atScoreF1.textContent = `${b.formant_f1_score || 8.0} / 10.0`;
    if (atBarF1) atBarF1.style.width = `${((b.formant_f1_score || 8.0) / 10.0) * 100}%`;

    // 6. Formant F2
    if (atScoreF2) atScoreF2.textContent = `${b.formant_f2_score || 8.0} / 10.0`;
    if (atBarF2) atBarF2.style.width = `${((b.formant_f2_score || 8.0) / 10.0) * 100}%`;

    // 7. Formant F3-F4
    if (atScoreF3F4) atScoreF3F4.textContent = `${b.formant_f3_f4_score || 4.0} / 5.0`;
    if (atBarF3F4) atBarF3F4.style.width = `${((b.formant_f3_f4_score || 4.0) / 5.0) * 100}%`;

    // 8. HNR Clarity
    if (atScoreHnr) atScoreHnr.textContent = `${b.hnr_clarity_score || b.clarity_score || 0} / 5.0`;
    if (atBarHnr) atBarHnr.style.width = `${((b.hnr_clarity_score || (b.clarity_score ? b.clarity_score/2 : 0)) / 5.0) * 100}%`;

    // 9. Anti Crackle
    if (atScoreAntiCrackle) atScoreAntiCrackle.textContent = `${b.anti_crackle_score || 4.5} / 5.0`;
    if (atBarAntiCrackle) atBarAntiCrackle.style.width = `${((b.anti_crackle_score || 4.5) / 5.0) * 100}%`;

    // 10. Energy Balance
    if (atScoreEnergyBal) atScoreEnergyBal.textContent = `${b.band_balance_score || (b.energy_score ? b.energy_score/2 : 0)} / 5.0`;
    if (atBarEnergyBal) atBarEnergyBal.style.width = `${((b.band_balance_score || (b.energy_score ? b.energy_score/2 : 0)) / 5.0) * 100}%`;
  }

  function renderCritique(notes) {
    if (!atCritiqueLog) return;
    atCritiqueLog.innerHTML = "";
    notes.forEach((n) => {
      const row = document.createElement("div");
      row.className = "flex items-start gap-1.5 p-1.5 rounded bg-slate-900 border border-slate-800 text-[11px]";
      row.innerHTML = `<i class="fa-solid fa-check text-amber-400 mt-0.5 text-[10px]"></i> <span>${n}</span>`;
      atCritiqueLog.appendChild(row);
    });
  }

  function renderRoundsList(history) {
    if (!atRoundsList) return;
    atRoundsList.innerHTML = "";
    history.forEach((h, idx) => {
      const card = document.createElement("button");
      card.type = "button";
      card.className = "w-full text-left p-2 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-amber-500/40 transition flex items-center justify-between group";
      card.innerHTML = `
        <div class="flex items-center gap-2">
          <span class="w-5 h-5 rounded-full bg-amber-500/20 text-amber-300 flex items-center justify-center font-mono font-bold text-[10px]">V${h.round}</span>
          <span class="font-semibold text-slate-200 text-xs">Vòng ${h.round}</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="font-mono font-bold ${h.score >= 90 ? 'text-emerald-400' : h.score >= 75 ? 'text-amber-400' : 'text-rose-400'}">${h.score.toFixed(1)}đ</span>
          <i class="fa-solid fa-play text-slate-500 group-hover:text-amber-400 text-xs"></i>
        </div>
      `;

      card.addEventListener("click", () => {
        selectedRoundNumber = h.round;
        if (atAudioPlayer) {
          atAudioPlayer.src = `${h.audio_url}?t=${Date.now()}`;
          atAudioPlayer.play();
        }
        renderBreakdown(h.breakdown);
        renderCritique(h.critique_notes);

        if (btnSaveOptimalPreset) {
          btnSaveOptimalPreset.disabled = false;
          btnSavePresetText.textContent = `Đồng Ý & Lưu Bộ Lọc Vòng ${h.round} (${h.score.toFixed(1)}đ)`;
        }
      });

      atRoundsList.appendChild(card);
    });
  }

  // Trigger Full AutoTune Run
  btnRunAutoTune.addEventListener("click", async () => {
    btnRunAutoTune.disabled = true;
    if (btnSaveOptimalPreset) btnSaveOptimalPreset.disabled = true;
    if (btnContinueAutoTune) btnContinueAutoTune.disabled = true;
    if (atBtnText) atBtnText.textContent = "BOT Đang Đọc & Giám Khảo Đang Chấm...";
    if (atPlayIcon) atPlayIcon.className = "fa-solid fa-spinner fa-spin";
    atRoundStatusText.textContent = "BOT Học Sinh đang đọc câu kiểm tra & BOT Giám Khảo đang phân tích 10 tiêu chí...";

    const maxRounds = parseInt(atMaxRounds.value) || 5;
    const testText = (atTestTextInput ? atTestTextInput.value : "").trim() || "Xin chào, đây là bài kiểm tra chất giọng lồng tiếng của tôi.";
    const sampleFile = atSampleSelect ? atSampleSelect.value : "";
    const userInstruction = atUserInstructionInput ? atUserInstructionInput.value.trim() : "";

    try {
      const res = await fetch(`${API_BASE}/autotune/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          style_id: activeStyle,
          test_text: testText,
          max_rounds: maxRounds,
          sample_file: sampleFile,
          user_instruction: userInstruction
        })
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Lỗi chạy Auto-tune" }));
        throw new Error(err.detail || "Lỗi chạy Auto-tune");
      }

      const data = await res.json();
      currentTuneSessionId = data.session_id;
      selectedRoundNumber = data.best_round || data.history.length;

      const preset = data.candidate_preset;
      renderExistingPreset(preset);
      renderRoundsList(data.history);

      if (atAudioPlayer && data.history.length > 0) {
        const bestRound = data.history[data.history.length - 1];
        atAudioPlayer.src = `${bestRound.audio_url}?t=${Date.now()}`;
        atAudioPlayer.play();
      }

      if (btnContinueAutoTune) btnContinueAutoTune.disabled = false;
      if (btnSaveOptimalPreset) {
        btnSaveOptimalPreset.disabled = false;
        btnSavePresetText.textContent = `Đồng Ý & Lưu Bộ Lọc Vòng ${data.best_round} (${data.best_score.toFixed(1)}đ)`;
      }

      atRoundStatusText.textContent = `Chấm điểm xong ${data.history.length} vòng! Bạn có thể bấm "Chưa Đạt" để tối ưu tiếp hoặc bấm "Lưu".`;
    } catch (e) {
      alert(`Lỗi: ${e.message}`);
      atRoundStatusText.textContent = `Thất bại: ${e.message}`;
    } finally {
      btnRunAutoTune.disabled = false;
      if (atBtnText) atBtnText.textContent = "Bắt Đầu Chấm Điểm & Tự Học";
      if (atPlayIcon) atPlayIcon.className = "fa-solid fa-play";
    }
  });

  // Continue Tuning Action (Chưa Đạt - Tối Ưu Thêm Vòng)
  if (btnContinueAutoTune) {
    btnContinueAutoTune.addEventListener("click", async () => {
      if (!currentTuneSessionId) {
        alert("Vui lòng bắt đầu chấm điểm trước!");
        return;
      }

      btnContinueAutoTune.disabled = true;
      if (btnSaveOptimalPreset) btnSaveOptimalPreset.disabled = true;
      if (atContinueText) atContinueText.textContent = "Đang tối ưu sâu thêm 5 vòng...";
      if (atContinueIcon) atContinueIcon.className = "fa-solid fa-spinner fa-spin";
      atRoundStatusText.textContent = "Đang tiếp tục các vòng nâng cao dựa trên nhận xét mới của Giám Khảo...";

      const userInstruction = atUserInstructionInput ? atUserInstructionInput.value.trim() : "";

      try {
        const res = await fetch(`${API_BASE}/autotune/continue`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            session_id: currentTuneSessionId,
            additional_rounds: 5,
            user_instruction: userInstruction
          })
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: "Lỗi tiếp tục tối ưu" }));
          throw new Error(err.detail || "Lỗi tiếp tục tối ưu");
        }

        const data = await res.json();
        selectedRoundNumber = data.best_round || data.history.length;

        renderExistingPreset(data.candidate_preset);
        renderRoundsList(data.history);

        if (atAudioPlayer && data.history.length > 0) {
          const bestRound = data.history[data.history.length - 1];
          atAudioPlayer.src = `${bestRound.audio_url}?t=${Date.now()}`;
          atAudioPlayer.play();
        }

        if (btnSaveOptimalPreset) {
          btnSaveOptimalPreset.disabled = false;
          btnSavePresetText.textContent = `Đồng Ý & Lưu Bộ Lọc Vòng ${data.best_round} (${data.best_score.toFixed(1)}đ)`;
        }

        atRoundStatusText.textContent = `Đã tối ưu xong tổng cộng ${data.history.length} vòng! Điểm cao nhất: ${data.best_score.toFixed(1)}đ.`;
      } catch (e) {
        alert(`Lỗi: ${e.message}`);
        atRoundStatusText.textContent = `Thất bại: ${e.message}`;
      } finally {
        btnContinueAutoTune.disabled = false;
        if (atContinueText) atContinueText.textContent = "🔄 Chưa Đạt - Tối Ưu Thêm 5 Vòng";
        if (atContinueIcon) atContinueIcon.className = "fa-solid fa-rotate-right";
      }
    });
  }

  // Explicit Save Preset upon user decision
  if (btnSaveOptimalPreset) {
    btnSaveOptimalPreset.addEventListener("click", async () => {
      if (!currentTuneSessionId) {
        alert("Vui lòng thực hiện chu trình tự học trước khi lưu!");
        return;
      }

      btnSaveOptimalPreset.disabled = true;
      btnSavePresetText.textContent = "Đang lưu cấu hình...";

      try {
        const res = await fetch(`${API_BASE}/autotune/save-preset`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            session_id: currentTuneSessionId,
            style_id: activeStyle,
            round_idx: selectedRoundNumber
          })
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: "Lỗi lưu cấu hình" }));
          throw new Error(err.detail || "Lỗi lưu cấu hình");
        }

        const data = await res.json();
        alert(`🎉 ${data.message}\nCấu hình tối ưu này sẽ được áp dụng cho mọi văn bản bạn đọc sau này!`);
        atRoundStatusText.textContent = "✅ Đã lưu thành công cấu hình tối ưu!";
        btnSavePresetText.textContent = "✅ Đã Lưu Vào Style Này";
      } catch (e) {
        alert(`Không thể lưu: ${e.message}`);
        btnSaveOptimalPreset.disabled = false;
        btnSavePresetText.textContent = "Đồng Ý & Lưu Bộ Lọc Này";
      }
    });
  }

});




