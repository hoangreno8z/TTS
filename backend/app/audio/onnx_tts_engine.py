import os
import sys
import time
import numpy as np
import soundfile as sf

curr_dir = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(curr_dir, "..", "..", ".."))
if not os.path.exists(os.path.join(PROJECT_ROOT, "models")):
    PROJECT_ROOT = os.path.abspath(os.path.join(curr_dir, "..", ".."))

class ONNXTTSBackend:
    _instance = None

    def __init__(self):
        self.sessions = {}
        self.init_models()

    def init_models(self):
        try:
            import onnxruntime as ort
            models_dir = os.path.join(PROJECT_ROOT, "models", "onnx")
            if os.path.exists(models_dir):
                for f in os.listdir(models_dir):
                    if f.endswith(".onnx"):
                        model_id = f.replace(".onnx", "")
                        model_path = os.path.join(models_dir, f)
                        try:
                            sess = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
                            self.sessions[model_id] = sess
                            print(f"[ONNXTTSBackend] Loaded ONNX model: {model_id} ({os.path.getsize(model_path)} bytes)")
                        except Exception as load_err:
                            print(f"[ONNXTTSBackend] Notice loading {f}: {load_err}")
        except Exception as e:
            print(f"[ONNXTTSBackend] Init notice: {e}")

    def synthesize(self, text: str, style_id: str, output_wav_path: str) -> bool:
        clean_sid = style_id.lower().strip().replace(" ", "_")
        sess = self.sessions.get(clean_sid)
        if sess is None:
            return False

        try:
            # Simple character/phoneme token mapping
            tokens = [min(254, max(1, ord(c) % 250 + 1)) for c in text.strip()]
            if not tokens:
                tokens = [1, 2, 3]
            tokens_arr = np.array([tokens], dtype=np.int64)

            input_name = sess.get_inputs()[0].name
            outputs = sess.run(None, {input_name: tokens_arr})

            # Check output waveform
            if len(outputs) >= 2:
                wav_out = outputs[1] # (1, 1, samples)
            else:
                wav_out = outputs[0]

            wav_data = np.squeeze(wav_out).astype(np.float32)
            if np.max(np.abs(wav_data)) > 0:
                wav_data = wav_data / (np.max(np.abs(wav_data)) + 1e-6) * 0.95

            sf.write(output_wav_path, wav_data, 22050)
            return True
        except Exception as e:
            print(f"[ONNXTTSBackend] Synthesis notice: {e}")
            return False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ONNXTTSBackend()
        return cls._instance
