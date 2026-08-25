# RECOVERY PROMPT

Dừng mọi thay đổi.

1. Đọc STATE.md.
2. Xác định commit/trạng thái cuối cùng đã pass.
3. Không refactor.
4. Tái hiện lỗi bằng test tối thiểu.
5. Xác định nguyên nhân.
6. Sửa một nguyên nhân mỗi lần.
7. Chạy regression tests.
8. Báo cáo trước khi chuyển phase.

Nếu lỗi do upstream engine:
- không sửa bừa source upstream;
- ghi rõ version/commit;
- ghi patch riêng nếu cần.
