# BẢO VỆ DỮ LIỆU & QUYỀN SỬ DỤNG GIỌNG MẪU (REFERENCE CONSENT)

---

## 1. NGUYÊN TẮC BẢO MẬT DỮ LIỆU CÁ NHÂN
- Tệp giọng nói mẫu (ví dụ: `Loc-Dinh-Ky.mp3`, preset `Lali5`):
  - Được lưu trữ cục bộ trên máy tính cá nhân người dùng tại `references/` hoặc `data/raw/`.
  - Không bao giờ được commit hoặc đồng bộ công khai lên kho lưu trữ mã nguồn Git.
  - Khi truyền qua Google Colab trong phiên xử lý, dữ liệu nằm trong bộ nhớ RAM/ổ đĩa tạm thời `/content/temp_colab` và tự động bị hủy sau khi phiên làm việc kết thúc.

---

## 2. METADATA QUẢN TRỊ GIỌNG MẪU
Mỗi preset giọng mẫu được quản lý với metadata:
```yaml
speaker:
  id: "lali5"
  name: "Local Reference Voice"
  ownership: "user_owned"
  consent: "confirmed_personal_use"
  source: "local_recording"
  export_policy: "private_only"
```
