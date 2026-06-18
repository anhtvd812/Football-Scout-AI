# Football Scout AI — Frontend (Hoàng)

Giao diện web React cho hệ thống Trinh sát & Định giá cầu thủ bóng đá.

## Chạy dự án

```bash
cd FE
npm install
npm run dev
```

Mở http://localhost:5173

## Tính năng

- **Dashboard**: Bộ lọc nâng cao, lưới thẻ cầu thủ, badge Undervalued/Overvalued
- **Chi tiết cầu thủ**: Modal + Radar Chart overlay so sánh với siêu sao
- **Chatbot AI**: Floating widget, quick replies, rich messages với Mini Player Cards
- **Loading & Toast**: Skeleton, spinner, thông báo lỗi

## Kết nối API (Hưng)

Tạo file `.env`:

```env
VITE_API_URL=http://localhost:8000/api
VITE_USE_MOCK=false
```

### Endpoints mong đợi

| Method | Path | Mô tả |
|--------|------|--------|
| GET | `/players?search=&position=&league=&min_age=&max_age=&max_budget=` | Danh sách cầu thủ |
| GET | `/players/:id` | Chi tiết cầu thủ |
| POST | `/chat/query` `{ "message": "..." }` | Chatbot → JSON response |

Response mẫu chat/valuation:

```json
{
  "reply": "Tìm thấy 2 cầu thủ tương đồng...",
  "similar_players": [
    { "name": "Alex Scott", "similarity_score": 0.89, "price": 15000000 }
  ]
}
```

Khi `VITE_USE_MOCK=true` (mặc định), app dùng mock data để demo không cần backend.

## Tech stack

- React 19 + TypeScript + Vite
- Tailwind CSS v4
- SVG Radar Chart (không phụ thuộc thư viện chart nặng)
