# LICENSE CHECKLIST — LAPQUE PERSONAL VIETNAMESE TTS

Trước khi đưa một thành phần vào hệ thống, ghi nhận chi tiết:

---

### 1. F5-TTS (Upstream)
- **Repository:** https://github.com/SWivid/F5-TTS
- **Code License:** MIT License (Tự do sử dụng, sửa đổi, nhúng trong ứng dụng).
- **Pretrained Weights / Checkpoint License:** CC-BY-NC 4.0 (Phi thương mại, do huấn luyện trên bộ dữ liệu Emilia).
- **Phạm vi áp dụng:** Phù hợp hoàn hảo cho Personal Non-Commercial TTS Studio.
- **Checked date:** 2026-08-24.

---

### 2. F5-TTS Vietnamese Community (psilabvnorg & hipleonas)
- **Repository:** https://github.com/psilabvnorg/F5-TTS-Vietnamese & https://github.com/hipleonas/f5-tts
- **Code License:** MIT License.
- **Model Checkpoints:** Cần kiểm tra license của từng HuggingFace repo cụ thể trước khi tải.
- **Checked date:** 2026-08-24.

---

### 3. GPT-SoVITS (Upstream)
- **Repository:** https://github.com/RVC-Boss/GPT-SoVITS
- **Code License:** MIT License.
- **Pretrained Weights License:** Tuân theo license phát hành của từng phiên bản release (V1/V2).
- **Phạm vi áp dụng:** Đối chứng benchmark zero-shot & few-shot tiếng Việt.
- **Checked date:** 2026-08-24.

---

### 4. OpenVoice (MyShell)
- **Repository:** https://github.com/myshell-ai/OpenVoice
- **Code License:** MIT License (V1 & V2).
- **Model License:** MIT License.
- **Lưu ý:** Native support cho EN, ES, FR, ZH, JP, KR; chỉ dùng làm reference benchmark phụ nếu cần kiểm soát tone color / prosody.
- **Checked date:** 2026-08-24.

---

**Quy tắc:** Tuyệt đối không nhúng trọng số mô hình (weights/checkpoints) vào git repository. License code và license checkpoint được quản lý và đánh giá độc lập.
