from typing import Union
from ieee_2030_5.data.indexer import add_href
import ieee_2030_5.hrefs as hrefs
import ieee_2030_5.models as m
from ieee_2030_5.adapters import Adapter
from ieee_2030_5.config import ReturnValue
import logging
_log = logging.getLogger(__name__)

DERCurveAdapter = Adapter[m.DERCurve](hrefs.curve_href(), generic_type=m.DERCurve)

DERControlAdapter = Adapter[m.DERControl]("/derc", generic_type=m.DERControl)
DERCurveAdapter = Adapter[m.DERCurve](hrefs.curve_href(), generic_type=m.DERCurve)
DERProgramAdapter = Adapter[m.DERProgram](hrefs.der_program_href(), generic_type=m.DERProgram)
FunctionSetAssignmentsAdapter = Adapter[m.FunctionSetAssignments](url_prefix="/fsa", generic_type=m.FunctionSetAssignments)

EndDeviceAdapter = Adapter[m.EndDevice](hrefs.get_enddevice_href(), generic_type=m.EndDevice)
DeviceCapabilityAdapter = Adapter[m.DeviceCapability]("/dcap", generic_type=m.DeviceCapability)
# Generally the href will only be in the context of an end device.
RegistrationAdapter = Adapter[m.Registration](url_prefix="/reg", generic_type=m.Registration)
DERAdapter = Adapter[m.DER](url_prefix="/der", generic_type=m.DER)
MirrorUsagePointAdapter = Adapter[m.MirrorUsagePoint](url_prefix="/mup", generic_type=m.MirrorUsagePoint)
MirrorMeterReadingAdapter = Adapter[m.MirrorMeterReading](url_prefix="/mr", generic_type=m.MirrorMeterReading)
MirrorReadingSetAdapter = Adapter[m.MirrorReadingSet](url_prefix="/rs", generic_type=m.MirrorReadingSet)
UsagePointAdapter = Adapter[m.UsagePoint](url_prefix="/upt", generic_type=m.UsagePoint)


def create_mirror_meter_reading(mup_href: str, mr: Union[m.MirrorMeterReading, m.MirrorMeterReadingList]) -> ReturnValue:
    upt_href = hrefs.UsagePointHref()
    upt_index = int(mup_href.split(hrefs.SEP)[-1])
    
    was_updated = False
    was_success = True
    try:
        found_mirror_reading = MirrorMeterReadingAdapter.fetch_by_mrid(mr.mRID)
        was_updated = True
        mr_index = int(found_mirror_reading.href.split(hrefs.SEP)[-1])
    except KeyError:
        mr.href = upt_href.meterreading(upt_index, MirrorMeterReadingAdapter.size())
        found_mirror_reading = MirrorMeterReadingAdapter.add(mr)
        mr_index = int(mr.href.split(hrefs.SEP)[-1])
    
    if isinstance(mr, m.MirrorMeterReadingList):
        raise NotImplemented()
            
        
    elif isinstance(mr, m.MirrorMeterReading):        
        for rs_index, rs in enumerate(found_mirror_reading.MirrorReadingSet):
            try:
                found_rs = MirrorReadingSetAdapter.fetch_by_mrid(rs.mRID)
                was_updated = True
            except KeyError:
                found_rs = None
            
            if not found_rs:
                rs.href = upt_href.readingset(upt_index, mr_index, rs_index)
                found_rs = MirrorReadingSetAdapter.add(rs)
            else:               
                found_rs.description = rs.description
                found_rs.timePeriod = rs.timePeriod
                found_rs.version = rs.version
                
            for r_index, r in enumerate(rs.Reading):
                r.href = upt_href.readingsetreading(upt_index, mr_index, rs_index, r_index)
                
    return ReturnValue(was_success, found_mirror_reading, was_updated)
    


def create_mirror_usage_point(mup: m.MirrorUsagePoint) -> ReturnValue:
    """Creates a MirrorUsagePoint and associated UsagePoint and adds them to their adapters."""
    
    # assert mup.href is None, "Cannot create a new mirror usage point with an href set already."
    found_with_mrid = None
    if MirrorUsagePointAdapter.size() > 0:    
        try:
            found_with_mrid = MirrorUsagePointAdapter.fetch_by_mrid(mup.mRID)
        except KeyError:
            ...
    
    
    if not found_with_mrid:
        # After this call the href is populated with the mup
        mup = MirrorUsagePointAdapter.add(mup)
        usage_point_index = int(mup.href.split(hrefs.SEP)[-1])
        
        upt_href = hrefs.UsagePointHref()
        
        meter_reading_list = m.MeterReadingList(href=upt_href.meterreading_list(usage_point_index))
                        
        for index, mirror_reading in enumerate(mup.MirrorMeterReading):
            if mirror_reading.ReadingType is None:
                return ReturnValue(False, "Invalid Reading Type")
            if not mirror_reading.href:
                mirror_reading.href = upt_href.meterreading(usage_point_index, index)
            reading = m.MeterReading(upt_href.meterreading(usage_point_index, index))
            reading.mRID = mirror_reading.mRID
            reading.description = mirror_reading.description
            
            
            if mirror_reading.Reading is not None:
                # These links are going to be handled by the add_href / get_href functions.
                reading.ReadingLink = m.ReadingLink(upt_href.reading(index))
                add_href(upt_href.reading(index), mirror_reading.Reading)
                
            reading.ReadingTypeLink = m.ReadingTypeLink(upt_href.readingtype(usage_point_index, index))
            add_href(upt_href.readingtype(usage_point_index, index), mirror_reading.ReadingType)
                        
            meter_reading_list.MeterReading.append(reading)
        
        upt = UsagePointAdapter.add(m.UsagePoint(href=upt_href,
                                           description=mup.description,
                                           deviceLFDI=mup.deviceLFDI,
                                           serviceCategoryKind=mup.serviceCategoryKind,
                                           mRID=mup.mRID,
                                           roleFlags=mup.roleFlags,
                                           status=mup.status,
                                           MeterReadingListLink=m.MeterReadingListLink(meter_reading_list.href)))
        _log.debug(f"Storing meter_reading_list {meter_reading_list.href}")
        add_href(meter_reading_list.href, meter_reading_list)
        update = False
    else:
        # TODO Update all properties with new items from mup
        mup.href = found_with_mrid.href
        found_with_mrid.description = mup.description
        found_with_mrid.deviceLFDI = mup.deviceLFDI
        found_with_mrid.serviceCategoryKind = mup.serviceCategoryKind
        found_with_mrid.mRID = mup.mRID
        found_with_mrid.roleFlags = mup.roleFlags
        found_with_mrid.status = mup.status
        update = True
    
    return ReturnValue(True, mup, update)
    
        
    
    
    
    # def create(self, mup: m.MirrorUsagePoint) -> Tuple[ReturnCode, str]:
    #     """Creates a MirrorUsagePoint and its associated usage point
        
    #     This method creates all of the sub elements of the usage point and
    #     mirror usage points as well.
    #     """
        
    #     before = len(self.__upt_container__)
    #     upt = self.__upt_container__.create_or_replace(mup)
    #     after = len(self.__upt_container__)
    #     if after > before:
    #         # TODO: Don't hard code here.
    #         mup.href = upt.href.replace('upt', 'mup')
    #         mup.postRate = BaseAdapter.server_config().usage_point_post_rate
    #         self.__mirror_usage_points__.append(mup)
    #         return ReturnCode.CREATED.value, mup.href
    #     else:
    #         for i, o in enumerate(self.__mirror_usage_points__):
    #             if o.mRID == mup.mRID:
    #                 mup.href = o.href
    #                 self.__mirror_usage_points__[i] = mup
    #                 break
    #         return ReturnCode.NO_CONTENT.value, mup.href