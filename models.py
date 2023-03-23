from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Host(Base):
    __tablename__ = 'host'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    cpu_data: Mapped["CpuData"] = relationship(back_populates="host")
    ip: Mapped[str] = mapped_column()


class CpuData(Base):
    __tablename__ = 'cpu_data'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    host_id: Mapped[int] = mapped_column(ForeignKey('host.id'), nullable=False)
    host: Mapped["Host"] = relationship(back_populates="cpu_data")
    cpu_util: Mapped[int] = mapped_column()
    timestamp: Mapped[int] = mapped_column(nullable=False)
