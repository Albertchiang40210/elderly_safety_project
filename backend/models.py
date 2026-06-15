from datetime import datetime
from typing import List, Optional
from sqlalchemy import ForeignKey, String, Integer, DateTime, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# 建立 Base 類別
class Base(DeclarativeBase):
    pass

class Elder(Base):
    """長者/居民基本資料表"""
    __tablename__ = "elders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="長者姓名")
    room_number: Mapped[str] = mapped_column(String(20), nullable=False, comment="房號")
    line_user_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="綁定的 LINE User ID (未來Bot推播用)")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # 關聯設定：一對多
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="elder")


class Camera(Base):
    """CCTV 攝影機設備表"""
    __tablename__ = "cameras"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    location: Mapped[str] = mapped_column(String(100), nullable=False, comment="攝影機架設位置(e.g., 301房)")
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="串流 IP 位址")
    status: Mapped[str] = mapped_column(String(20), default="active", comment="設備狀態: active, inactive")

    # 關聯設定：一對多 (已修正為對應 Alert 類別)
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="camera")


class Alert(Base):
    """跌倒警報事件紀錄表 (核心)"""
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 外鍵關聯
    elder_id: Mapped[int] = mapped_column(Integer, ForeignKey("elders.id"), nullable=False)
    camera_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("cameras.id"), nullable=True)
    
    alert_type: Mapped[str] = mapped_column(String(30), default="fall", comment="警報類型: fall, SOS等")
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="觸發時間時間")
    status: Mapped[str] = mapped_column(String(20), default="未處理", comment="狀態: 未處理, 已處理")
    
    # 擴充欄位：儲存 AI 觸發當下的關鍵影格路徑
    snapshot_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="AI骨架截圖路徑")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="護理人員處理備註")

    # 反向關聯設定
    elder: Mapped["Elder"] = relationship("Elder", back_populates="alerts")
    camera: Mapped[Optional["Camera"]] = relationship("Camera", back_populates="alerts")