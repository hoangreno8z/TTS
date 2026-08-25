import os
import json
import time
import numpy as np
import soundfile as sf
import librosa
from typing import Dict, Any, List, Optional, Callable
from app.audio.acoustic_judge_bot import AcousticJudgeBot
from app.audio.audio_enhancer import AudioEnhancer

class AcousticAutoTuner:
    def __init__(self, project_root: str, target_sr: int = 24000):
        self.project_root = project_root
        self.sr = target_sr
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

    def _generate_base_speech(self, text: str, output_path: str) -> np.ndarray:
        """Generates clean Vietnamese spoken speech from text using edge_tts."""
        import edge_tts
        import asyncio
        
        temp_mp3 = output_path + '.temp.mp3'
        
        async def run_tts():
            comm = edge_tts.Communicate(text, 'vi-VN-NamMinhNeural')
            await comm.save(temp_mp3)

        try:
            asyncio.run(run_tts())
            data, sr = sf.read(temp_mp3)
            if len(data.shape) > 1:
                data = np.mean(data, axis=1)
            if sr != self.sr:
                data = librosa.resample(data.astype(np.float32), orig_sr=sr, target_sr=self.sr)
            return data
        finally:
            if os.path.exists(temp_mp3):
                try:
                    os.remove(temp_mp3)
                except OSError:
                    pass

    def get_style_samples(self, style_id: str) -> List[Dict[str, Any]]:
        """Lists all available sample WAV/MP3 files for this style."""
        clean_style = style_id.lower().strip().replace(' ', '_')
        results = []
        
        # Check data/voice/{style_id}
        voice_dir = os.path.join(self.project_root, 'data', 'voice', clean_style)
        if os.path.exists(voice_dir):
            for f in os.listdir(voice_dir):
                if f.lower().endswith(('.wav', '.mp3')):
                    p = os.path.join(voice_dir, f)
                    results.append({
                        'filename': f,
                        'source': 'voice',
                        'path': p,
                        'size_bytes': os.path.getsize(p)
                    })
        
        # Check data/raw/{style_id}
        raw_dir = os.path.join(self.project_root, 'data', 'raw', clean_style)
        if os.path.exists(raw_dir):
            for f in os.listdir(raw_dir):
                if f.lower().endswith(('.wav', '.mp3')):
                    p = os.path.join(raw_dir, f)
                    if not any(r['filename'] == f for r in results):
                        results.append({
                            'filename': f,
                            'source': 'raw_slices',
                            'path': p,
                            'size_bytes': os.path.getsize(p)
                        })
        return results

    def start_autotune_session(
        self,
        style_id: str,
        test_text: str = "Xin chào, đây là bài kiểm tra chất giọng lồng tiếng của tôi.",
        max_rounds: int = 5,
        sample_file: Optional[str] = None,
        user_instruction: Optional[str] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        clean_style = style_id.lower().strip().replace(' ', '_')
        style_voice_dir = os.path.join(self.project_root, 'data', 'voice', clean_style)
        profile_json_path = os.path.join(style_voice_dir, 'acoustic_profile.json')

        # 1. Select reference audio
        ref_wav_path = os.path.join(style_voice_dir, 'reference.wav')
        if sample_file:
            cand1 = os.path.join(style_voice_dir, sample_file)
            cand2 = os.path.join(self.project_root, 'data', 'raw', clean_style, sample_file)
            if os.path.exists(cand1):
                ref_wav_path = cand1
            elif os.path.exists(cand2):
                ref_wav_path = cand2

        profile_data = {}
        if os.path.exists(profile_json_path):
            try:
                with open(profile_json_path, 'r', encoding='utf-8') as f:
                    profile_data = json.load(f)
            except Exception:
                pass

        judge = AcousticJudgeBot(
            target_audio_path=ref_wav_path if os.path.exists(ref_wav_path) else None,
            profile_dict=profile_data
        )

        tune_out_dir = os.path.join(self.project_root, 'outputs', 'autotune')
        os.makedirs(tune_out_dir, exist_ok=True)
        session_id = f"tune_{clean_style}_{int(time.time())}"

        # 2. Student BOT reads the test text into real Vietnamese speech
        clean_text = (test_text or "Xin chào, đây là bài kiểm tra giọng lồng tiếng.").strip()
        base_speech_path = os.path.join(tune_out_dir, f"{session_id}_base.wav")
        base_audio = self._generate_base_speech(clean_text, base_speech_path)

        # 3. Initial Parameter State
        initial_pitch = profile_data.get('f0_statistics', {}).get('suggested_pitch_shift_semitones', 0.0)
        curr_params = {
            'pitch_shift_semitones': float(np.clip(initial_pitch, -12.0, 12.0)),
            'formant_warp_ratio': 1.0,
            'morph_strength': 0.75,
            'index_rate': 0.85,
            'eq_sub_gain_db': 0.0,
            'eq_mid_gain_db': 0.0,
            'eq_air_gain_db': 0.0,
            'spectral_blend_ratio': 0.40,
            'resonance_q': 1.2,
            'anti_crackle_filter': True
        }

        history = []
        best_score = 0.0
        best_round_idx = 1
        best_params = curr_params.copy()

        session_data = {
            'session_id': session_id,
            'style_id': clean_style,
            'test_text': clean_text,
            'sample_file': sample_file or 'reference.wav',
            'ref_wav_path': ref_wav_path,
            'user_instruction': user_instruction or '',
            'base_speech_path': base_speech_path,
            'status': 'running',
            'current_round': 0,
            'history': [],
            'curr_params': curr_params
        }
        self.active_sessions[session_id] = session_data

        return self._run_optimization_loop(
            session_id=session_id,
            base_audio=base_audio,
            judge=judge,
            start_round=1,
            num_rounds=max_rounds,
            user_instruction=user_instruction,
            progress_callback=progress_callback
        )

    def continue_autotune_session(
        self,
        session_id: str,
        additional_rounds: int = 5,
        user_instruction: Optional[str] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """Resumes optimization for K more rounds from the previous state."""
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Không tìm thấy phiên tự học {session_id}")

        clean_style = session['style_id']
        base_speech_path = session['base_speech_path']
        ref_wav_path = session['ref_wav_path']

        if not os.path.exists(base_speech_path):
            base_audio = self._generate_base_speech(session['test_text'], base_speech_path)
        else:
            base_audio, _ = sf.read(base_speech_path)

        style_voice_dir = os.path.join(self.project_root, 'data', 'voice', clean_style)
        profile_json_path = os.path.join(style_voice_dir, 'acoustic_profile.json')
        profile_data = {}
        if os.path.exists(profile_json_path):
            try:
                with open(profile_json_path, 'r', encoding='utf-8') as f:
                    profile_data = json.load(f)
            except Exception:
                pass

        judge = AcousticJudgeBot(
            target_audio_path=ref_wav_path if os.path.exists(ref_wav_path) else None,
            profile_dict=profile_data
        )

        instruction_to_use = user_instruction if user_instruction is not None else session.get('user_instruction', '')
        session['user_instruction'] = instruction_to_use

        start_round = session.get('current_round', 0) + 1
        return self._run_optimization_loop(
            session_id=session_id,
            base_audio=base_audio,
            judge=judge,
            start_round=start_round,
            num_rounds=additional_rounds,
            user_instruction=instruction_to_use,
            progress_callback=progress_callback
        )

    def _run_optimization_loop(
        self,
        session_id: str,
        base_audio: np.ndarray,
        judge: AcousticJudgeBot,
        start_round: int,
        num_rounds: int,
        user_instruction: Optional[str] = "",
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        session = self.active_sessions[session_id]
        clean_style = session['style_id']
        history = session.get('history', [])
        curr_params = session.get('curr_params', {})
        tune_out_dir = os.path.join(self.project_root, 'outputs', 'autotune')
        ref_wav_path = session.get('ref_wav_path')

        # 1. Semantic Acoustic Compilation from natural language prompt
        compiled_spec = None
        if user_instruction:
            try:
                from app.audio.semantic_acoustic_compiler import get_semantic_compiler
                compiler = get_semantic_compiler()
                compiled_spec = compiler.compile_instruction(user_instruction)
                
                # Apply initial target bias from semantic compilation
                curr_params['pitch_shift_semitones'] += compiled_spec.get('target_pitch_delta_semitones', 0.0) * 0.35
                curr_params['pitch_shift_semitones'] = float(np.clip(curr_params['pitch_shift_semitones'], -12.0, 12.0))
                curr_params['eq_sub_gain_db'] += compiled_spec.get('sub_bass_gain_db', 0.0) * 0.4
                curr_params['eq_air_gain_db'] += compiled_spec.get('air_treble_gain_db', 0.0) * 0.4
            except Exception:
                pass

        ref_spectrum = None
        if ref_wav_path and os.path.exists(ref_wav_path):
            try:
                r_audio, r_sr = sf.read(ref_wav_path)
                if len(r_audio.shape) > 1:
                    r_audio = np.mean(r_audio, axis=1)
                r_stft = np.abs(librosa.stft(r_audio.astype(np.float32), n_fft=1024, hop_length=256))
                ref_spectrum = np.mean(r_stft, axis=1)
            except Exception:
                pass

        best_score = max([h['score'] for h in history], default=0.0)
        best_round_idx = max([h['round'] for h in history if h['score'] == best_score], default=1)
        best_params = curr_params.copy()

        for r_offset in range(num_rounds):
            round_idx = start_round + r_offset

            # Apply candidate filter
            cand_audio = self._apply_acoustic_filter(
                base_audio, self.sr, curr_params, clean_style, ref_spectrum=ref_spectrum
            )
            cand_audio = AudioEnhancer.clean_and_polish_audio(cand_audio, self.sr)

            # Save round audio
            round_audio_file = f"{session_id}_round_{round_idx}.wav"
            round_audio_path = os.path.join(tune_out_dir, round_audio_file)
            sf.write(round_audio_path, cand_audio, self.sr)

            # Judge evaluates
            evaluation = judge.evaluate_audio(cand_audio, self.sr, user_instruction=user_instruction)
            score = evaluation['total_score']

            round_record = {
                'round': round_idx,
                'score': score,
                'breakdown': evaluation['breakdown'],
                'critique_notes': evaluation['critique_notes'],
                'params': curr_params.copy(),
                'audio_url': f"/outputs/autotune/{round_audio_file}",
                'verdict': evaluation['verdict']
            }
            history.append(round_record)
            session['history'] = history
            session['current_round'] = round_idx
            session['curr_params'] = curr_params

            if progress_callback:
                progress_callback(round_record)

            if score > best_score:
                best_score = score
                best_round_idx = round_idx
                best_params = curr_params.copy()

            if score >= 96.0:
                break

            # Adjust parameters based on judge feedback
            deltas = evaluation.get('delta_corrections', {})
            step_size = max(0.35, 1.0 - (round_idx / 20.0))

            curr_params['pitch_shift_semitones'] += deltas.get('pitch_shift_semitones', 0.0) * 0.85 * step_size
            curr_params['pitch_shift_semitones'] = float(np.clip(curr_params['pitch_shift_semitones'], -12.0, 12.0))

            warp_delta = (deltas.get('formant_warp_ratio', 1.0) - 1.0) * 0.6 * step_size
            curr_params['formant_warp_ratio'] += warp_delta
            curr_params['formant_warp_ratio'] = float(np.clip(curr_params['formant_warp_ratio'], 0.70, 1.40))

            curr_params['eq_sub_gain_db'] += deltas.get('eq_sub_gain_db', 0.0) * 0.65 * step_size
            curr_params['eq_sub_gain_db'] = float(np.clip(curr_params['eq_sub_gain_db'], -8.0, 8.0))

            curr_params['eq_air_gain_db'] += deltas.get('eq_air_gain_db', 0.0) * 0.65 * step_size
            curr_params['eq_air_gain_db'] = float(np.clip(curr_params['eq_air_gain_db'], -8.0, 8.0))

            curr_params['spectral_blend_ratio'] = min(0.85, curr_params.get('spectral_blend_ratio', 0.4) + 0.05)
            curr_params['morph_strength'] = min(1.0, curr_params.get('morph_strength', 0.75) + 0.04)
            curr_params['index_rate'] = min(1.0, curr_params.get('index_rate', 0.85) + 0.03)

        candidate_preset = {
            'style_id': clean_style,
            'test_text': session['test_text'],
            'sample_file': session.get('sample_file', 'reference.wav'),
            'best_score': best_score,
            'best_round': best_round_idx,
            'total_rounds': len(history),
            'timestamp': time.time(),
            'optimized_parameters': best_params,
            'final_critique': history[-1]['critique_notes'],
            'final_breakdown': history[-1]['breakdown']
        }

        session['status'] = 'completed'
        session['candidate_preset'] = candidate_preset

        return {
            'session_id': session_id,
            'status': 'success',
            'style_id': clean_style,
            'test_text': session['test_text'],
            'best_score': best_score,
            'best_round': best_round_idx,
            'history': history,
            'candidate_preset': candidate_preset
        }

    def save_optimal_preset(self, session_id: str, style_id: str, round_idx: Optional[int] = None) -> Dict[str, Any]:
        """Explicitly saves the user-approved preset to disk."""
        clean_style = style_id.lower().strip().replace(' ', '_')
        style_voice_dir = os.path.join(self.project_root, 'data', 'voice', clean_style)
        os.makedirs(style_voice_dir, exist_ok=True)

        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Không tìm thấy phiên tự học {session_id}")

        history = session.get('history', [])
        if not history:
            raise ValueError("Không có dữ liệu vòng lặp để lưu")

        target_round = history[-1]
        if round_idx is not None and 1 <= round_idx <= len(history):
            target_round = history[round_idx - 1]

        optimal_preset = {
            'style_id': clean_style,
            'approved_by_user': True,
            'score': target_round['score'],
            'round': target_round['round'],
            'saved_at': time.time(),
            'optimized_parameters': target_round['params'],
            'final_critique': target_round['critique_notes'],
            'final_breakdown': target_round['breakdown']
        }

        preset_file = os.path.join(style_voice_dir, 'optimal_preset.json')
        with open(preset_file, 'w', encoding='utf-8') as f:
            json.dump(optimal_preset, f, indent=2, ensure_ascii=False)

        return {
            'status': 'success',
            'message': f"Đã lưu thành công bộ lọc {clean_style} (Vòng {target_round['round']}: {target_round['score']}đ)!",
            'preset': optimal_preset
        }

    def _apply_acoustic_filter(
        self,
        audio: np.ndarray,
        sr: int,
        params: Dict[str, Any],
        style_id: str,
        ref_spectrum: Optional[np.ndarray] = None
    ) -> np.ndarray:
        pitch_shift = params.get('pitch_shift_semitones', 0.0)
        index_rate = params.get('index_rate', 0.85)

        if abs(pitch_shift) > 0.05:
            shifted = librosa.effects.pitch_shift(audio, sr=sr, n_steps=pitch_shift)
        else:
            shifted = audio.copy()

        try:
            from app.audio.rvc_inference_engine import RVCInferenceEngine
            rvc_engine = RVCInferenceEngine.get_instance()
            if rvc_engine.is_loaded:
                converted = rvc_engine.convert_voice(
                    audio_float=shifted,
                    source_sr=sr,
                    pitch_shift_semitones=pitch_shift,
                    index_rate=index_rate
                )
                if converted is not None and len(converted) > 0:
                    shifted = converted
        except Exception as e:
            print(f"RVC Inference Notice in AutoTuner: {e}")

        # Spectral Envelope Morphing & EQ
        stft = librosa.stft(shifted, n_fft=1024, hop_length=256)
        mag, phase = np.abs(stft), np.angle(stft)
        freqs = librosa.fft_frequencies(sr=sr, n_fft=1024)

        eq_sub = params.get('eq_sub_gain_db', 0.0)
        eq_air = params.get('eq_air_gain_db', 0.0)
        sub_gain = 10.0 ** (eq_sub / 20.0)
        air_gain = 10.0 ** (eq_air / 20.0)

        mag[freqs <= 350, :] *= sub_gain
        mag[freqs >= 6000, :] *= air_gain

        # Direct Spectral Matching with target sample
        if ref_spectrum is not None and len(ref_spectrum) == mag.shape[0]:
            blend = params.get('spectral_blend_ratio', 0.4)
            curr_mean_spec = np.mean(mag, axis=1, keepdims=True) + 1e-6
            target_profile = ref_spectrum[:, np.newaxis]
            gain_curve = (target_profile / curr_mean_spec) ** blend
            gain_curve = np.clip(gain_curve, 0.25, 4.0)
            mag = mag * gain_curve

        shifted = librosa.istft(mag * np.exp(1j * phase), hop_length=256)
        return shifted

auto_tuner = None
def get_auto_tuner(project_root: str):
    global auto_tuner
    if auto_tuner is None:
        auto_tuner = AcousticAutoTuner(project_root)
    return auto_tuner
