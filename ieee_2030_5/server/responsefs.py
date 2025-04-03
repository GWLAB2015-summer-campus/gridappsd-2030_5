import logging
from datetime import datetime

import zoneinfo
import werkzeug.exceptions
from flask import Response, request

import ieee_2030_5.adapters as adpt
import ieee_2030_5.hrefs as hrefs
import ieee_2030_5.models as m
from ieee_2030_5.server.base_request import RequestOp
from ieee_2030_5.types_ import format_time
from ieee_2030_5.utils import dataclass_to_xml, xml_to_dataclass

from ieee_2030_5.db.conn import get_db_session
import ieee_2030_5.db.tables as t
from sqlalchemy import select, func

_log = logging.getLogger(__name__)

class RspsRequests(RequestOp):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def post(self, path = None) -> Response:
        if not request.data:
            raise werkzeug.exceptions.BadRequest()
        
        rsps_href = hrefs.ResponseHref.parse(request.path)

        if rsps_href.has_subtitle() and not rsps_href.has_subindex():
            data: m.Response = xml_to_dataclass(request.data.decode('utf-8'), m.Response)
            if not isinstance(data, m.Response):
                raise werkzeug.exceptions.BadRequest()
            
            if not data.createdDateTime:
                data.createdDateTime = format_time(datetime.utcnow().replace(tzinfo=zoneinfo.ZoneInfo('UTC')))

            try:
                with get_db_session() as session:
                    response_row = t.ResponseTable(
                        list_link_id = rsps_href.rsps_index,
                        end_device_lfdi = data.endDeviceLFDI,
                        status = data.status,
                        subject = data.subject,
                        create_data_time = datetime.utcfromtimestamp(data.createdDateTime)
                    )
                    session.add(response_row)
                    session.commit()
            except Exception as e:
                _log.error(f"Faild to Insert in DB : {data}")
                _log.error(e)
                raise werkzeug.exceptions.InternalServerError()

            return Response(status=201)
        else:
            raise werkzeug.exceptions.NotFound()

    def get(self) -> Response:
        start = int(request.args.get("s", 0))
        limit = int(request.args.get("l", 1))
        after = int(request.args.get("a", 0))

        rsps_href = hrefs.ResponseHref.parse(request.path)

        if rsps_href.has_subtitle():
            try:
                with get_db_session() as session:
                    if rsps_href.has_subindex():
                        selected = session.execute(
                                          select(t.ResponseTable).
                                          filter_by(id=rsps_href.subindex)
                                      ).scalar_one()
                        retval = m.Response(
                                href = rsps_href.make_full_url(selected.id),
                                createdDateTime = format_time(selected.create_data_time.strftime("%Y%m%d%H%M%S")),
                                endDeviceLFDI = selected.end_device_lfdi,
                                status = selected.status,
                                subject = selected.subject
                            )
                    else:
                        all_cnt = session.execute(
                            select(func.count('*'))
                            .select_from(t.ResponseTable).
                            filter_by(list_link_id=rsps_href.rsps_index)
                        ).scalar()
                        selected_list = session.execute(
                                          select(t.ResponseTable).
                                          filter_by(list_link_id=rsps_href.rsps_index).
                                          order_by(
                                            t.ResponseTable.create_data_time.desc(),
                                            t.ResponseTable.end_device_lfdi).
                                          limit(limit).
                                          offset(start)
                                        ).scalars().all()
                        retval = m.ResponseList(
                            href = rsps_href.list_url(),
                            subscribable = False,
                            all = all_cnt,
                            results = len(selected_list),
                            Response = [
                            m.Response(
                                href = rsps_href.make_full_url(r.id),
                                createdDateTime = r.create_data_time.strftime("%Y%m%d%H%M%S"),
                                endDeviceLFDI = r.end_device_lfdi,
                                status = r.status,
                                subject = r.subject
                            ) for r in selected_list
                        ])
                    return self.build_response_from_dataclass(retval)
            except Exception as e:
                _log.error(f"Faild to Select in DB")
                _log.error(e)
                raise werkzeug.exceptions.InternalServerError()
        else:
            raise werkzeug.exceptions.NotFound()
