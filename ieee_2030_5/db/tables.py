import datetime
import logging

from sqlalchemy import Integer, String, DateTime, ForeignKey, select, func
from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column, composite, relationship
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.ext.declarative import declared_attr
from dataclasses import dataclass, field
from typing import Optional, List
import ieee_2030_5.models as m
import ieee_2030_5.hrefs as hrefs

_log = logging.getLogger(__name__)

class Base(DeclarativeBase):
    def to_model(self):
        raise "Not Implemented"

    def add(self):
        from ieee_2030_5.db.conn import get_db_session
        try:
            with get_db_session() as session:
                session.add(self)
                session.commit()
        except Exception as e:
            _log.error(f"Faild to Insert in DB Table={self.__name__} Data={self}")
            _log.error(e)
            raise e

    @classmethod
    def get_one(cls, where=None):
        from ieee_2030_5.db.conn import get_db_session
        try:
            with get_db_session() as session:
                query = select(cls)

                if where is not None:
                    query = query.where(where)

                return session.execute(query).scalar_one()
        except Exception as e:
            _log.error(f"Faild to Select in DB Table={cls.__name__}, id={id}")
            _log.error(e)
            raise e   

    @classmethod
    def get_by_id(cls, id):
        return cls.get_one(where = cls.id == id)

    @classmethod
    def get_all(cls, start=0, limit=-1, where=None, order_by=None):
        from ieee_2030_5.db.conn import get_db_session
        try:
            with get_db_session() as session:
                query = select(func.count('*')).select_from(cls)

                if where is not None:
                    query = query.where(where)

                all_cnt = session.execute(query).scalar()

                query = select(cls)

                if where is not None:
                    query = query.where(where)

                if order_by is not None:
                    query = query.order_by(
                        *order_by
                    )
                
                if limit > -1:
                    query = query.limit(limit)

                selected_list = session.execute(
                                    query.offset(start)
                                ).scalars().all()
                return all_cnt, selected_list
        except Exception as e:
            _log.error(f"Faild to Select in DB Table={cls.__name__}, id={id}")
            _log.error(e)
            raise e

# ----- Response Table -----

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
    @dataclass
    class ApplianceLoadReductionColumns:
        type: Optional[int] = None

    applianceLoadReduction: Mapped[ApplianceLoadReductionColumns] = composite(
        mapped_column("alr_type")
    )


    @dataclass
    class AppliedTargetReductionColumns:
        type: Optional[int] = None
        value: Optional[int] = None

    appliedTargetTeduction: Mapped[AppliedTargetReductionColumns] = composite(
        mapped_column("atr_type"), mapped_column("atr_value")
    )


    @dataclass
    class DutyCycleColumns:
        normal_value: Optional[int] = None

    dutyCycle: Mapped[DutyCycleColumns] = composite(
        mapped_column("dc_normal_value")
    )


    @dataclass
    class OffsetColumns:
        cooling_offset: Optional[int] = None
        heating_offset: Optional[int] = None
        load_adjustment_percentage_offset: Optional[int] = None

    offset: Mapped[OffsetColumns] = composite(
        mapped_column("cooling_offset"), mapped_column("heating_offset"), 
        mapped_column("load_adjustment_percentage_offset")
    )

    override_duration: Mapped[Optional[int]]


    @dataclass
    class SetPointColumns:
        cooling_setpoint: Optional[int] = None
        heating_setpoint: Optional[int] = None

    setPoint: Mapped[SetPointColumns] = composite(
        mapped_column("cooling_setpoint"),
        mapped_column("heating_setpoint")
    )

# ---------------

def get_column_name_of_class(prefix, C):
    return [
        f"{prefix}_{k}"
        for k, v in C.__dict__.items()
        if ( not k.startswith("_") ) and ( not callable(v) )
    ]

# ----- DERControll -----

@dataclass
class DERControlBaseColumns:
    op_mod_connect: Mapped[bool]
    op_mod_energize: Mapped[bool]

    @dataclass
    class PowerFactorWithExcitationColumns:
        displacement: Optional[int] = None
        excitation: Optional[int] = None
        multiplier: Optional[int] = None
        
    @declared_attr
    def opModFixedPFAbsorbW(self) -> Mapped[PowerFactorWithExcitationColumns]:
        return composite(*[
                    mapped_column(cn) 
                    for cn in get_column_name_of_class("op_mod_fixed_pf_absorbw", self.PowerFactorWithExcitationColumns)
                ])

    @declared_attr
    def opModFixedPFInjectW(self) -> Mapped[PowerFactorWithExcitationColumns]:
        return composite(*[
                    mapped_column(cn) 
                    for cn in get_column_name_of_class("op_mod_fixed_pf_injectw", self.PowerFactorWithExcitationColumns)
                ])



    @dataclass
    class FixedVarColumns:
        reftype: Optional[int] = None
        value: Optional[int] = None

    @declared_attr
    def opModFixedVar(self) -> Mapped[FixedVarColumns]:
        return composite(*[
                    mapped_column(cn) 
                    for cn in get_column_name_of_class("op_mod_fixed_var", self.FixedVarColumns)
                ])

    op_mod_fixed_w: Mapped[int]

    op_mod_max_lim_w: Mapped[int]

    ramp_tms: Mapped[int]


    @dataclass
    class FreqDroopColumns:
        dbof: Optional[int] = None
        dbuf: Optional[int] = None
        kof: Optional[int] = None
        kuf: Optional[int] = None
        open_loop_tms: Optional[int] = None

    @declared_attr
    def opModFreqDroop(self) -> Mapped[FreqDroopColumns]:
        return composite(*[
                    mapped_column(cn) 
                    for cn in get_column_name_of_class("op_mod_freq_droop", self.FreqDroopColumns)
                ])

    op_mod_freq_watt: Mapped[str] = mapped_column(String(50))
    
    op_mod_hfrt_may_trip: Mapped[str] = mapped_column(String(50))
    op_mod_hfrt_must_trip: Mapped[str] = mapped_column(String(50))
    
    op_mod_hvrt_may_trip: Mapped[str] = mapped_column(String(50))
    op_mod_hvrt_momentary_cessation: Mapped[str] = mapped_column(String(50))
    op_mod_hvrt_must_trip: Mapped[str] = mapped_column(String(50))

    op_mod_lfrt_may_trip: Mapped[str] = mapped_column(String(50))
    op_mod_lfrt_must_trip: Mapped[str] = mapped_column(String(50))

    op_mod_lvrt_may_trip: Mapped[str] = mapped_column(String(50))
    op_mod_lvrt_momentary_cessation: Mapped[str] = mapped_column(String(50))
    op_mod_lvrt_must_trip: Mapped[str] = mapped_column(String(50))


    @dataclass
    class ReactivePowerColumns:
        multiplier: Optional[int] = None
        value: Optional[int] = None

    @declared_attr
    def opModTargetVar(self) -> Mapped[ReactivePowerColumns]:
        return composite(*[
                    mapped_column(cn) 
                    for cn in get_column_name_of_class("op_mod_target_var", self.ReactivePowerColumns)
                ])
    

    @dataclass
    class ActivePowerColumns:
        multiplier: Optional[int] = None
        value: Optional[int] = None

    @declared_attr
    def opModTargetW(self) -> Mapped[ActivePowerColumns]:
        return composite(*[
                    mapped_column(cn) 
                    for cn in get_column_name_of_class("op_mod_target_w", self.ActivePowerColumns)
                ])

    op_mod_volt_var: Mapped[str] = mapped_column(String(50))
    op_mod_volt_watt: Mapped[str] = mapped_column(String(50))
    op_mod_watt_pf: Mapped[str] = mapped_column(String(50))
    op_mod_watt_var: Mapped[str] = mapped_column(String(50))

@dataclass
class DERControlTable(DERControlBaseColumns, Base):
    __tablename__ = "der_control"
    __allow_unmapped__ = True
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    der_program_id: Mapped[int] = mapped_column(ForeignKey("der_program.id"), primary_key=True)
    derProgram = relationship("DERProgramTable", foreign_keys="[DERControlTable.der_program_id]", back_populates="derControls")

    activate: Mapped[bool] = mapped_column(default=False)
    device_category: Mapped[str] = mapped_column(String(20))
    randomize_duration: Mapped[int]
    randomize_start: Mapped[int]
    creation_time: Mapped[int]

    @dataclass
    class EventStatusColumns:
        current_status: Mapped[int]
        date_time: Mapped[Datetime]
        potentially_superseded: Mapped[bool]
        potentially_superseded_time: Mapped[int]
        reason: Mapped[str] = mapped_column(String(192))

    eventStatus: Mapped[EventStatusColumns] = composite(
        *[
            mapped_column(f"event_status_{cn}")
            for cn in get_column_name_of_class(EventStatusColumns)
        ]
    )

    @dataclass
    class DateTimeIntervalColumns:
        duration: Mapped[int]
        start: Mapped[int]
    
    interval: Mapped[DateTimeIntervalColumns] = composite(
        *[
            mapped_column(f"interval_{cn}")
            for cn in get_column_name_of_class(DateTimeIntervalColumns)
        ]
    )

    description: Mapped[str] = mapped_column(String(32))
    mrid: Mapped[str] = mapped_column(String(50))
    version: Mapped[int]
    subscribable: Mapped[int]
    reply_to: Mapped[str] = mapped_column(String(50))
    response_required: Mapped[str] = mapped_column(String(20))

    def to_model(self):
        return m.DERControl(
            DERControlBase = m.DERControlBase(
                opModConnect = self.op_mod_connect,
                opModEnergize = self.op_mod_energize,
                opModFixedPFAbsorbW = m.PowerFactorWithExcitation(
                    displacement = self.opModFixedPFAbsorbW.displacement,
                    excitation = self.opModFixedPFAbsorbW.excitation,
                    multiplier = self.opModFixedPFAbsorbW.multiplier
                ),
                opModFixedPFInjectW = m.PowerFactorWithExcitation(
                    displacement = self.opModFixedPFInjectW.displacement,
                    excitation = self.opModFixedPFInjectW.excitation,
                    multiplier = self.opModFixedPFInjectW.multiplier
                ),
                opModFixedVar = m.FixedVar(
                    refType = self.opModFixedVar.refType
                    value = self.opModFixedVar.value
                ),
                opModFixedW = self.op_mod_fixed_w,
                opModMaxLimW = self.op_mod_max_lim_w,
                rampTms = self.ramp_tms
                opModFreqDroop = m.FreqDroop(
                    dbof = self.opModFreqDroop.dbof,
                    dbuf = self.opModFreqDroop.dbuf,
                    kof = self.opModFreqDroop.kof,
                    kuf = self.opModFreqDroop.kuf,
                    openLoopTms = self.opModFreqDroop.open_loop_tms
                ),
                opModFreqWatt = self.op_mod_freq_watt
                opModHFRTMayTrip = self.op_mod_hfrt_may_trip
                opModHFRTMustTrip = self.op_mod_hfrt_must_trip
                opModHVRTMayTrip = self.op_mod_hvrt_may_trip
                opModHVRTMomentaryCessation = self.op_mod_hvrt_momentary_cessation
                opModHVRTMustTrip = self.op_mod_hvrt_must_trip
                opModLFRTMayTrip = self.op_mod_lfrt_may_trip
                opModLFRTMustTrip = self.op_mod_lfrt_must_trip
                opModLVRTMayTrip = self.op_mod_lvrt_may_trip
                opModLVRTMomentaryCessation = self.op_mod_lvrt_momentary_cessation
                opModLVRTMustTrip = self.op_mod_lvrt_must_trip
                opModTargetVar = m.ReactivePower(
                    multiplier = self.opModTargetVar.multiplier,
                    value = self.opModTargetVar.value
                ),
                opModTargetW = m.ActivePower(
                    multiplier = self.opModTargetW.multiplier,
                    value = self.opModTargetW.value
                ),
                opModVoltVar = self.op_mod_volt_var,
                opModVoltWatt = self.op_mod_volt_watt,
                opModWattPF = self.op_mod_watt_pf,
                opModWattVar = self.op_mod_watt_var
            ),
            deviceCategory = self.device_category,
            randomizeDuration = self.randomize_duration,
            randomizeStart = self.randomize_start,
            creationTime = self.creation_time,
            EventStatus = m.EventStatus(
                currentStatus = self.eventStatus.current_status,
                dateTime = self.eventStatus.date_time,
                potentiallySuperseded = self.eventStatus.potentially_superseded,
                potentiallySupersededTime = self.eventStatus.potentially_superseded_time,
                reason = self.eventStatus.reason
            ),
            interval = m.DateTimeInterval(
                duration = self.interval.duration,
                start = self.interval.start
            ),
            mRID = self.mrid,
            description = self.description,
            version = self.version,
            subscribable = self.subscribable,
            replyTo = self.reply_to,
            responseRequired = self.response_required,
            href = hrefs.SEP.join([
                hrefs.DEFAULT_DERP_ROOT, 
                str(self.der_program_id),
                "derc",
                str(self.id)
            ])
        )

# ---------------

# ----- DERCurve -----

@dataclass
class CurveDataTable(Base):
    __tablename__ = "curve_data"
    __allow_unmapped__ = True
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    der_curve_id: Mapped[int] = mapped_column(ForeignKey("der_curve.id"), primary_key=True)
    derCurve = relationship("DERCurveTable", back_populates="curve_data")
    excitation: Mapped[bool]
    xvalue: Mapped[int]
    yvalue: Mapped[int]

@dataclass
class DERCurveTable(Base):
    __tablename__ = "der_curve"
    __allow_unmapped__ = True
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    description: Mapped[str] = mapped_column(String(32))
    mrid: Mapped[str] = mapped_column(String(50))
    version: Mapped[int]
    autonomous_vref_enable: Mapped[bool]
    autonomous_vref_time_constant: Mapped[int]
    creation_time: Mapped[int]
    curve_data = relationship("CurveDataTable", back_populates="derCurve")
    curve_type: Mapped[int]
    open_loop_tms: Mapped[int]
    ramp_dec_tms: Mapped[int]
    ramp_inc_tms: Mapped[int]
    ramp_pt1_tms: Mapped[int]
    vref: Mapped[int]
    x_multiplier: Mapped[int]
    y_multiplier: Mapped[int]
    y_ref_type: Mapped[int]

    der_program_id: Mapped[int] = mapped_column(ForeignKey("der_program.id"), primary_key=True)
    derProgram = relationship("DERProgramTable", back_populates="derCurves")

# ----- DERProgram -----

@dataclass
class DERProgramTable(Base):
    __tablename__ = "der_program"
    __allow_unmapped__ = True
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    primacy: Mapped[int]
    description: Mapped[str] = mapped_column(String(32))
    mrid: Mapped[str] = mapped_column(String(50))
    version: Mapped[int]

    default_der_controll_id: Mapped[int] = mapped_column(ForeignKey("der_control.id"), nullable=True)
    defaultDer  = relationship("DERControlTable", 
                                foreign_keys="[DERProgramTable.default_der_controll_id]"
                            )

    derControls = relationship("DERControlTable", 
                                back_populates="derProgram",
                                foreign_keys="[DERControlTable.der_program_id]"
                            )
    derCurves = relationship("DERCurveTable", back_populates="derProgram")

    def to_model(self):
        return m.DERProgram(
                href = hrefs.SEP.join([
                    hrefs.DEFAULT_DERP_ROOT,
                    self.id
                ])
                primacy = self.primacy,
                mRID = self.mrid,
                description = self.description,
                version = self.version,
                ActiveDERControlListLink = m.ActiveDERControlListLink(
                    href = hrefs.DERProgramHref(self.id).active_control_href,
                ),
                DefaultDERControlLink = m.DefaultDERControlLink(
                    href = hrefs.DERProgramHref(self.id).default_control_href,
                ),
                DERControlListLink = m.DERControlListLink(
                    href = hrefs.DERProgramHref(self.id).der_control_list_href,
                ),
                DERCurveListLink = m.DERCurveListLink(
                    href = hrefs.DERProgramHref(self.id).der_curve_list_href,
                )
            )

# ---------------

tableClass = [
    ResponseTable,
    DERProgramTable,
    DERControlTable,
    DERCurveTable
]