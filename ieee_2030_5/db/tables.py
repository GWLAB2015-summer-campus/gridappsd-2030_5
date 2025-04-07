import datetime
import logging

from sqlalchemy import Integer, String, DateTime, ForeignKey, select, func, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase, backref
from sqlalchemy.orm import Mapped, mapped_column, composite, relationship
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.ext.declarative import declared_attr
from dataclasses import dataclass, field, asdict
from typing import Optional, List
import ieee_2030_5.models as m
import ieee_2030_5.hrefs as hrefs
from ieee_2030_5.types_ import format_time

_log = logging.getLogger(__name__)

class Base(DeclarativeBase):
    def to_model(self):
        raise "Not Implemented"

    def add(self, commit=True):
        from ieee_2030_5.db.conn import get_db_session
        try:
            with get_db_session() as session:
                session.add(self)
                if commit:
                    session.commit()
                else:
                    session.flush()
        except Exception as e:
            _log.error(f"Faild to Insert in DB Data={self}")
            _log.error(e)
            raise e

    def update(self, commit=True):
        from ieee_2030_5.db.conn import get_db_session
        try:
            with get_db_session() as session:
                session.merge(self)
                if commit:
                    session.commit()
                else:
                    session.flush()
        except Exception as e:
            _log.error(f"Faild to Update in DB Data={self}")
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
            _log.error(f"Faild to Select in DB Table={cls.__name__}")
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
        (f"{prefix}_{k}" if prefix is not None else k, type(v))
        for k, v in C.__dict__.items()
        if ( not k.startswith("_") ) and ( not callable(v) )
    ]

# ----- DERControll -----

@dataclass
class DERControlBaseColumns:
    op_mod_connect: Mapped[Optional[bool]] = mapped_column(default=None)
    op_mod_energize: Mapped[Optional[bool]] = mapped_column(default=None)

    @dataclass
    class PowerFactorWithExcitationColumns:
        displacement: Optional[int] = None
        excitation: Optional[int] = None
        multiplier: Optional[int] = None
        
    @declared_attr
    def opModFixedPFAbsorbW(self) -> Mapped[PowerFactorWithExcitationColumns]:
        return composite(*[
                    mapped_column(cn) 
                    for cn, _ in get_column_name_of_class("op_mod_fixed_pf_absorbw", self.PowerFactorWithExcitationColumns)
                ])

    @declared_attr
    def opModFixedPFInjectW(self) -> Mapped[PowerFactorWithExcitationColumns]:
        return composite(*[
                    mapped_column(cn) 
                    for cn, _ in get_column_name_of_class("op_mod_fixed_pf_injectw", self.PowerFactorWithExcitationColumns)
                ])



    @dataclass
    class FixedVarColumns:
        reftype: Optional[int] = None
        value: Optional[int] = None

    @declared_attr
    def opModFixedVar(self) -> Mapped[FixedVarColumns]:
        return composite(*[
                    mapped_column(cn) 
                    for cn, _ in get_column_name_of_class("op_mod_fixed_var", self.FixedVarColumns)
                ])

    op_mod_fixed_w: Mapped[Optional[int]] = mapped_column(default=None)

    op_mod_max_lim_w: Mapped[Optional[int]] = mapped_column(default=None)

    ramp_tms: Mapped[Optional[int]] = mapped_column(default=None)


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
                    for cn, _ in get_column_name_of_class("op_mod_freq_droop", self.FreqDroopColumns)
                ])

    op_mod_freq_watt: Mapped[Optional[str]] = mapped_column(String(50))
    
    op_mod_hfrt_may_trip: Mapped[Optional[str]] = mapped_column(String(50))
    op_mod_hfrt_must_trip: Mapped[Optional[str]] = mapped_column(String(50))
    
    op_mod_hvrt_may_trip: Mapped[Optional[str]] = mapped_column(String(50))
    op_mod_hvrt_momentary_cessation: Mapped[Optional[str]] = mapped_column(String(50))
    op_mod_hvrt_must_trip: Mapped[Optional[str]] = mapped_column(String(50))

    op_mod_lfrt_may_trip: Mapped[Optional[str]] = mapped_column(String(50))
    op_mod_lfrt_must_trip: Mapped[Optional[str]] = mapped_column(String(50))

    op_mod_lvrt_may_trip: Mapped[Optional[str]] = mapped_column(String(50))
    op_mod_lvrt_momentary_cessation: Mapped[Optional[str]] = mapped_column(String(50))
    op_mod_lvrt_must_trip: Mapped[Optional[str]] = mapped_column(String(50))


    @dataclass
    class ReactivePowerColumns:
        multiplier: Optional[int] = None
        value: Optional[int] = None

    @declared_attr
    def opModTargetVar(self) -> Mapped[ReactivePowerColumns]:
        return composite(*[
                    mapped_column(cn) 
                    for cn, _ in get_column_name_of_class("op_mod_target_var", self.ReactivePowerColumns)
                ])
    

    @dataclass
    class ActivePowerColumns:
        multiplier: Optional[int] = None
        value: Optional[int] = None

    @declared_attr
    def opModTargetW(self) -> Mapped[ActivePowerColumns]:
        return composite(*[
                    mapped_column(cn) 
                    for cn, _ in get_column_name_of_class("op_mod_target_w", self.ActivePowerColumns)
                ])

    op_mod_volt_var: Mapped[Optional[str]] = mapped_column(String(50))
    op_mod_volt_watt: Mapped[Optional[str]] = mapped_column(String(50))
    op_mod_watt_pf: Mapped[Optional[str]] = mapped_column(String(50))
    op_mod_watt_var: Mapped[Optional[str]] = mapped_column(String(50))

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)

    def der_control_base_to_model(self):
        return m.DERControlBase(
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
                refType = self.opModFixedVar.reftype,
                value = self.opModFixedVar.value
            ),
            opModFixedW = self.op_mod_fixed_w,
            opModMaxLimW = self.op_mod_max_lim_w,
            rampTms = self.ramp_tms,
            opModFreqDroop = m.FreqDroopType(
                dBOF = self.opModFreqDroop.dbof,
                dBUF = self.opModFreqDroop.dbuf,
                kOF = self.opModFreqDroop.kof,
                kUF = self.opModFreqDroop.kuf,
                openLoopTms = self.opModFreqDroop.open_loop_tms
            ),
            opModFreqWatt = self.op_mod_freq_watt,
            opModHFRTMayTrip = self.op_mod_hfrt_may_trip,
            opModHFRTMustTrip = self.op_mod_hfrt_must_trip,
            opModHVRTMayTrip = self.op_mod_hvrt_may_trip,
            opModHVRTMomentaryCessation = self.op_mod_hvrt_momentary_cessation,
            opModHVRTMustTrip = self.op_mod_hvrt_must_trip,
            opModLFRTMayTrip = self.op_mod_lfrt_may_trip,
            opModLFRTMustTrip = self.op_mod_lfrt_must_trip,
            opModLVRTMayTrip = self.op_mod_lvrt_may_trip,
            opModLVRTMomentaryCessation = self.op_mod_lvrt_momentary_cessation,
            opModLVRTMustTrip = self.op_mod_lvrt_must_trip,
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
        )
    
    @classmethod
    def from_model(cls, der_control_base: m.DERControlBase):
        init_c = cls(
            op_mod_connect = der_control_base.opModConnect,
            op_mod_energize = der_control_base.opModEnergize,
            opModFixedPFAbsorbW = cls.PowerFactorWithExcitationColumns(
                displacement = der_control_base.opModFixedPFAbsorbW.displacement,
                excitation = der_control_base.opModFixedPFAbsorbW.excitation,
                multiplier = der_control_base.opModFixedPFAbsorbW.multiplier
            ) if der_control_base.opModFixedPFAbsorbW is not None else None,
            opModFixedPFInjectW = cls.PowerFactorWithExcitationColumns(
                displacement = der_control_base.opModFixedPFInjectW.displacement,
                excitation = der_control_base.opModFixedPFInjectW.excitation,
                multiplier = der_control_base.opModFixedPFInjectW.multiplier
            ) if der_control_base.opModFixedPFInjectW is not None else None,
            opModFixedVar = cls.FixedVarColumns(
                reftype = der_control_base.opModFixedVar.refType,
                value = der_control_base.opModFixedVar.value
            ) if der_control_base.opModFixedVar is not None else None,
            op_mod_fixed_w = der_control_base.opModFixedW,
            op_mod_max_lim_w = der_control_base.opModMaxLimW,
            ramp_tms = der_control_base.rampTms,
            opModFreqDroop = cls.FreqDroopColumns(
                dbof = der_control_base.opModFreqDroop.dBOF,
                dbuf = der_control_base.opModFreqDroop.dBUF,
                kof = der_control_base.opModFreqDroop.kOF,
                kuf = der_control_base.opModFreqDroop.kUF,
                open_loop_tms = der_control_base.opModFreqDroop.openLoopTms
            ) if der_control_base.opModFreqDroop is not None else None,
            op_mod_freq_watt = der_control_base.opModFreqWatt,
            op_mod_hfrt_may_trip = der_control_base.opModHFRTMayTrip,
            op_mod_hfrt_must_trip = der_control_base.opModHFRTMustTrip,
            op_mod_hvrt_may_trip = der_control_base.opModHVRTMayTrip,
            op_mod_hvrt_momentary_cessation = der_control_base.opModHVRTMomentaryCessation,
            op_mod_hvrt_must_trip = der_control_base.opModHVRTMustTrip,
            op_mod_lfrt_may_trip = der_control_base.opModLFRTMayTrip,
            op_mod_lfrt_must_trip = der_control_base.opModLFRTMustTrip,
            op_mod_lvrt_may_trip = der_control_base.opModLVRTMayTrip,
            op_mod_lvrt_momentary_cessation = der_control_base.opModLVRTMomentaryCessation,
            op_mod_lvrt_must_trip = der_control_base.opModLVRTMustTrip,
            opModTargetVar = cls.ReactivePowerColumns(
                multiplier = der_control_base.opModTargetVar.multiplier,
                value = der_control_base.opModTargetVar.value
            ) if der_control_base.opModTargetVar is not None else None,
            opModTargetW = cls.ActivePowerColumns(
                multiplier = der_control_base.opModTargetW.multiplier,
                value = der_control_base.opModTargetW.value
            ) if der_control_base.opModTargetW is not None else None,
            op_mod_volt_var = der_control_base.opModVoltVar,
            op_mod_volt_watt = der_control_base.opModVoltWatt,
            op_mod_watt_pf = der_control_base.opModWattPF,
            op_mod_watt_var = der_control_base.opModWattVar
        )
        return init_c

@dataclass
class DERControlTable(DERControlBaseColumns, Base):
    __tablename__ = "der_control"
    __allow_unmapped__ = True
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    der_program_id: Mapped[int] = mapped_column(ForeignKey("der_program.id"), primary_key=True)
    derProgram = relationship("DERProgramTable", foreign_keys="[DERControlTable.der_program_id]", back_populates="derControls")

    activate: Mapped[bool] = mapped_column(default=False)
    device_category: Mapped[Optional[str]] = mapped_column(String(20))
    randomize_duration: Mapped[Optional[int]] = mapped_column(default=None)
    randomize_start: Mapped[Optional[int]] = mapped_column(default=None)
    creation_time: Mapped[Optional[int]] = mapped_column(default=None)

    @dataclass
    class EventStatusColumns:
        current_status: Optional[int] = None
        potentially_superseded: Optional[bool] = None
        potentially_superseded_time: Optional[int] = None
        reason: str = ""
        date_time: datetime.datetime = datetime.datetime.now()

    eventStatus: Mapped[EventStatusColumns] = composite(
        *[
            mapped_column(cn, String(192), default="") if type_ == str
            else ( mapped_column(cn, DateTime(timezone=True), server_default=func.now()) if type_ == datetime.datetime
            else mapped_column(cn) )
            for cn, type_ in get_column_name_of_class("event_status", EventStatusColumns)
        ]
    )

    @dataclass
    class DateTimeIntervalColumns:
        duration: Optional[int] = None
        start: Optional[int] = None
    
    interval: Mapped[DateTimeIntervalColumns] = composite(
        *[
            mapped_column(cn, BigInteger)
            for cn, _ in get_column_name_of_class("interval", DateTimeIntervalColumns)
        ]
    )

    description: Mapped[Optional[str]] = mapped_column(String(32))
    mrid: Mapped[Optional[str]] = mapped_column(String(50))
    version: Mapped[Optional[int]] = mapped_column(default=None)
    subscribable: Mapped[bool] = mapped_column(default=False)
    reply_to: Mapped[Optional[str]] = mapped_column(String(50))
    response_required: Mapped[Optional[str]] = mapped_column(String(20))

    def to_model(self):
        return m.DERControl(
            DERControlBase = self.der_control_base_to_model(),
            deviceCategory = self.device_category,
            randomizeDuration = self.randomize_duration,
            randomizeStart = self.randomize_start,
            creationTime = self.creation_time,
            EventStatus = m.EventStatus(
                currentStatus = self.eventStatus.current_status,
                dateTime = int(self.eventStatus.date_time.timestamp()),
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
    
    @classmethod
    def from_model(cls, der_control: m.DERControl, der_program_id: int):
        return cls(
            **asdict(DERControlBaseColumns.from_model(der_control.DERControlBase)),
            der_program_id = der_program_id,
            activate = False,
            device_category = der_control.deviceCategory,
            randomize_duration = der_control.randomizeDuration,
            randomize_start = der_control.randomizeStart,
            creation_time = der_control.creationTime,
            eventStatus = cls.EventStatusColumns(
                current_status = der_control.EventStatus.currentStatus,
                date_time = datetime.datetime.fromtimestamp(der_control.EventStatus.dateTime),
                potentially_superseded = der_control.EventStatus.potentiallySuperseded,
                potentially_superseded_time = der_control.EventStatus.potentiallySupersededTime,
                reason = der_control.EventStatus.reason
            ),
            interval = cls.DateTimeIntervalColumns(
                duration = der_control.interval.duration,
                start = der_control.interval.start
            ),
            mrid = der_control.mRID,
            description = der_control.description,
            version = der_control.version,
            subscribable = der_control.subscribable,
            reply_to = der_control.replyTo,
            response_required = der_control.responseRequired
        )

@dataclass
class DefaultDERControlTable(DERControlBaseColumns, Base):
    __tablename__ = "default_der_control"
    __allow_unmapped__ = True
    id: Mapped[int] = mapped_column(ForeignKey("der_program.id"), primary_key=True)
    derProgram = relationship("DERProgramTable", backref=backref("defaultDERControl", uselist=False))

    set_es_delay: Mapped[Optional[int]] = mapped_column(default=None)
    set_es_high_freq: Mapped[Optional[int]] = mapped_column(default=None)
    set_es_high_volt: Mapped[Optional[int]] = mapped_column(default=None)
    set_es_low_freq: Mapped[Optional[int]] = mapped_column(default=None)
    set_es_low_volt: Mapped[Optional[int]] = mapped_column(default=None)
    set_es_ramp_tms: Mapped[Optional[int]] = mapped_column(default=None)
    set_es_random_delay: Mapped[Optional[int]] = mapped_column(default=None)
    set_grad_w: Mapped[Optional[int]] = mapped_column(default=None)
    set_soft_grad_w: Mapped[Optional[int]] = mapped_column(default=None)

    def to_model(self):
        return m.DefaultDERControl(
            DERControlBase = self.der_control_base_to_model(),
            setESDelay = self.set_es_delay,
            setESHighFreq = self.set_es_high_freq,
            setESHighVolt = self.set_es_high_volt,
            setESLowFreq = self.set_es_low_freq,
            setESLowVolt = self.set_es_low_volt,
            setESRampTms = self.set_es_ramp_tms,
            setESRandomDelay = self.set_es_random_delay,
            setGradW = self.set_grad_w,
            setSoftGradW = self.set_soft_grad_w,
        )

    server_default = None

    @classmethod
    def set_server_default(cls, default: m.DefaultDERControl):
        cls.server_default = default

    @classmethod
    def get_server_default(cls, der_program_id: int):
        return cls.from_model(cls.server_default, der_program_id)

    @classmethod
    def from_model(cls, dderc_model: m.DefaultDERControl, der_program_id: int):
        return cls(
            **asdict(DERControlBaseColumns.from_model(dderc_model.DERControlBase)),
            id = der_program_id,
            set_es_delay = dderc_model.setESDelay,
            set_es_high_freq = dderc_model.setESHighFreq,
            set_es_high_volt = dderc_model.setESHighVolt,
            set_es_low_freq = dderc_model.setESLowFreq,
            set_es_low_volt = dderc_model.setESLowVolt,
            set_es_ramp_tms = dderc_model.setESRampTms,
            set_es_random_delay = dderc_model.setESRandomDelay,
            set_grad_w = dderc_model.setGradW,
            set_soft_grad_w = dderc_model.setSoftGradW
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
    excitation: Mapped[Optional[bool]] = mapped_column(default=None)
    xvalue: Mapped[Optional[int]] = mapped_column(default=None)
    yvalue: Mapped[Optional[int]] = mapped_column(default=None)

    def to_model(self):
        return m.CurveData(
            excitation = self.excitation,
            xvalue = self.xvalue,
            yvalue = self.yvalue
        )

    @classmethod
    def from_model(cls, curve_data: m.CurveData, der_curve_id: int):
        return cls(
            der_curve_id = der_curve_id,
            excitation = curve_data.excitation,
            xvalue = curve_data.xvalue,
            yvalue = curve_data.yvalue
        )

@dataclass
class DERCurveTable(Base):
    __tablename__ = "der_curve"
    __allow_unmapped__ = True
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    description: Mapped[str] = mapped_column(String(32), default="")
    mrid: Mapped[str] = mapped_column(String(50), default="")
    version: Mapped[int] = mapped_column(Integer, default=0)
    autonomous_vref_enable: Mapped[Optional[bool]] = mapped_column(Integer, default=None)
    autonomous_vref_time_constant: Mapped[Optional[int]] = mapped_column(Integer, default=None)
    creation_time: Mapped[Optional[int]] = mapped_column(Integer, default=None)
    curve_data = relationship("CurveDataTable", back_populates="derCurve", lazy="selectin")
    curve_type: Mapped[Optional[int]] = mapped_column(Integer, default=None)
    open_loop_tms: Mapped[Optional[int]] = mapped_column(Integer, default=None)
    ramp_dec_tms: Mapped[Optional[int]] = mapped_column(Integer, default=None)
    ramp_inc_tms: Mapped[Optional[int]] = mapped_column(Integer, default=None)
    ramp_pt1_tms: Mapped[Optional[int]] = mapped_column(Integer, default=None)
    vref: Mapped[Optional[int]] = mapped_column(Integer, default=None)
    x_multiplier: Mapped[Optional[int]] = mapped_column(Integer, default=None)
    y_multiplier: Mapped[Optional[int]] = mapped_column(Integer, default=None)
    y_ref_type: Mapped[Optional[int]] = mapped_column(Integer, default=None)

    der_program_id: Mapped[int] = mapped_column(ForeignKey("der_program.id"), primary_key=True)
    derProgram = relationship("DERProgramTable", back_populates="derCurves")

    def to_model(self):
        return m.DERCurve(
            description = self.description,
            mRID = self.mrid,
            version = self.version,
            autonomousVRefEnable = self.autonomous_vref_enable,
            autonomousVRefTimeConstant = self.autonomous_vref_time_constant,
            creationTime = self.creation_time,
            CurveData = [
                data.to_model() for data in self.curve_data
            ],
            curveType = self.curve_type,
            openLoopTms = self.open_loop_tms,
            rampDecTms = self.ramp_dec_tms,
            rampIncTms = self.ramp_inc_tms,
            rampPT1Tms = self.ramp_pt1_tms,
            vRef = self.vref,
            xMultiplier = self.x_multiplier,
            yMultiplier = self.y_multiplier,
            yRefType = self.y_ref_type
        )
    
    @classmethod
    def from_model(cls, der_curve: m.DERCurve, der_program_id: int):
        return cls(
            description = der_curve.description,
            mrid = der_curve.mRID,
            version = der_curve.version,
            autonomous_vref_enable = der_curve.autonomousVRefEnable,
            autonomous_vref_time_constant = der_curve.autonomousVRefTimeConstant,
            creation_time = der_curve.creationTime,
            curve_type = der_curve.curveType,
            open_loop_tms = der_curve.openLoopTms,
            ramp_dec_tms = der_curve.rampDecTms,
            ramp_inc_tms = der_curve.rampIncTms,
            ramp_pt1_tms = der_curve.rampPT1Tms,
            vref = der_curve.vRef,
            x_multiplier = der_curve.xMultiplier,
            y_multiplier = der_curve.yMultiplier,
            y_ref_type = der_curve.yRefType,
            der_program_id = der_program_id
        )

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

    derControls = relationship("DERControlTable", 
                                back_populates="derProgram",
                                foreign_keys="[DERControlTable.der_program_id]"
                            )
    derCurves = relationship("DERCurveTable", back_populates="derProgram")

    def to_model(self):
        return m.DERProgram(
                href = hrefs.SEP.join([
                    hrefs.DEFAULT_DERP_ROOT,
                    str(self.id)
                ]),
                primacy = self.primacy,
                mRID = self.mrid,
                description = self.description,
                version = self.version,
                # ActiveDERControlListLink = m.ActiveDERControlListLink(
                #     href = hrefs.DERProgramHref(self.id).active_control_href,
                # ),
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
    
    @classmethod
    def from_model(cls, der_program: m.DERProgram):
        return cls(
            primacy = der_program.primacy,
            description = der_program.description,
            mrid = der_program.mRID,
            version = der_program.version
        )

# ---------------

tableClass = [
    ResponseTable,
    DERProgramTable,
    DERControlTable,
    DERCurveTable,
    CurveDataTable,
    DefaultDERControlTable
]