import os
import requests
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from db import get_db

app = FastAPI()

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

class BookingRequest(BaseModel):
    service_id: str
    service_name: str
    price: int
    date: str
    time: str
    client_name: str
    client_phone: str

@app.get("/api/slots")
def get_slots(date: str = Query(..., regex=r"^\d{4}-\d{2}-\d{2}$")):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT time FROM bookings WHERE date = ? AND status != 'cancelled'", 
            (date,)
        )
        rows = cursor.fetchall()
        taken = [r["time"] for r in rows]
    return {"taken": taken}

@app.post("/api/book")
def create_booking(req: BookingRequest):
    if len(req.client_name.strip()) < 2:
        raise HTTPException(status_code=400, detail="Имя слишком короткое")
    if len(req.client_phone.strip()) < 6:
        raise HTTPException(status_code=400, detail="Неверный формат телефона")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM bookings WHERE date = ? AND time = ? AND status != 'cancelled'",
            (req.date, req.time)
        )
        if cursor.fetchone():
            raise HTTPException(status_code=409, detail="Этот слот уже занят")

        cursor.execute('''
            INSERT INTO bookings (service_id, service_name, price, date, time, client_name, client_phone)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (req.service_id, req.service_name, req.price, req.date, req.time, req.client_name, req.client_phone))
        conn.commit()
        booking_id = cursor.lastrowid

    if BOT_TOKEN and CHAT_ID:
        msg = (
            f"📌 <b>Новая заявка на запись!</b>\n\n"
            f"<b>Услуга:</b> {req.service_name}\n"
            f"<b>Дата и время:</b> {req.date} в {req.time}\n"
            f"<b>Клиент:</b> {req.client_name}\n"
            f"<b>Телефон:</b> {req.client_phone}\n\n"
            f"<b>Стоимость:</b> {req.price:,} ₸".replace(',', ' ')
        )
        try:
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"},
                timeout=5
            )
        except Exception as e:
            print(f"Ошибка отправки Telegram: {e}")

    return {"ok": True, "booking_id": booking_id}
