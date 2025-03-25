from datetime import datetime, timedelta
from flask import Response
import zoneinfo
import tzlocal

from ieee_2030_5.server.base_request import RequestOp
import ieee_2030_5.models as m
from ieee_2030_5.types_ import TimeOffsetType, format_time


class TimeRequest(RequestOp):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get(self) -> Response:
        now_utc = datetime.utcnow().replace(tzinfo=zoneinfo.ZoneInfo('UTC'))
        
        local_tz = zoneinfo.ZoneInfo(tzlocal.get_localzone().zone)

        now_local = datetime.now().replace(tzinfo=local_tz)

        start_dst_utc, end_dst_utc = [
            datetime.now().astimezone(local_tz).replace(tzinfo=zoneinfo.ZoneInfo('UTC'))
            for _ in range(2)
        ]

        utc_offset = local_tz.utcoffset(start_dst_utc - timedelta(days=1))
        dst_offset = local_tz.utcoffset(start_dst_utc + timedelta(days=1)) - utc_offset
        local_but_utc = datetime.now().replace(tzinfo=zoneinfo.ZoneInfo('UTC'))

        tm = m.Time(currentTime=format_time(now_utc),
                    dstEndTime=format_time(end_dst_utc.replace(tzinfo=zoneinfo.ZoneInfo('UTC'))),
                    dstOffset=TimeOffsetType(int(dst_offset.total_seconds())),
                    localTime=format_time(local_but_utc),
                    quality=None,
                    tzOffset=TimeOffsetType(utc_offset.total_seconds()))

        return self.build_response_from_dataclass(tm)