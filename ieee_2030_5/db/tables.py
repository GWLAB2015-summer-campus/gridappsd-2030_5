import datetime

from sqlalchemy import Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column, composite
from sqlalchemy.schema import UniqueConstraint
from dataclasses import dataclass
from typing import Optional

class Base(DeclarativeBase):
    pass

@dataclass
class ApplianceLoadReductionColumns:
    type: Optional[int] = None

@dataclass
class AppliedTargetReductionColumns:
    type: Optional[int] = None
    value: Optional[int] = None


@dataclass
class DutyCycleColumns:
    normal_value: Optional[int] = None

@dataclass
class OffsetColumns:
    cooling_offset: Optional[int] = None
    heating_offset: Optional[int] = None
    load_adjustment_percentage_offset: Optional[int] = None

@dataclass
class SetPointColumns:
    cooling_setpoint: Optional[int] = None
    heating_setpoint: Optional[int] = None

@dataclass
class ResponseTable(Base):
    __tablename__ = "response"
    __allow_unmapped__ = True

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    list_link_id: Mapped[int] = mapped_column(primary_key=True)
    create_data_time: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
        
    )
    end_device_lfdi: Mapped[str] = mapped_column(String(40))
    status: Mapped[int]
    subject : Mapped[str] = mapped_column(String(40))

    # DrResponse
    applianceLoadReduction: Mapped[ApplianceLoadReductionColumns] = composite(
        mapped_column("alr_type")
    )
    appliedTargetTeduction: Mapped[AppliedTargetReductionColumns] = composite(
        mapped_column("atr_type"), mapped_column("atr_value")
    )
    dutyCycle: Mapped[DutyCycleColumns] = composite(
        mapped_column("dc_normal_value")
    )
    offset: Mapped[OffsetColumns] = composite(
        mapped_column("cooling_offset"), mapped_column("heating_offset"), 
        mapped_column("load_adjustment_percentage_offset")
    )
    override_duration: Mapped[Optional[int]]
    setPoint: Mapped[SetPointColumns] = composite(
        mapped_column("cooling_setpoint"),
        mapped_column("heating_setpoint")
    )