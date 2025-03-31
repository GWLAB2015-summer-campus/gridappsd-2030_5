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
            adpt.ListAdapter.append_and_increment_href(request.path, data)
            return Response(status=201)
        else:
            raise werkzeug.exceptions.NotFound()

    def get(self) -> Response:
        start = int(request.args.get("s", 0))
        limit = int(request.args.get("l", 1))
        after = int(request.args.get("a", 0))

        rsps_href = hrefs.ResponseHref.parse(request.path)

        if rsps_href.has_subtitle():
            if rsps_href.has_subindex():
                retval = adpt.ListAdapter.get(rsps_href.list_url(), rsps_href.rsps_subindex)
            else:
                retval = adpt.ListAdapter.get_resource_list(request.path, start, after, limit)
            return self.build_response_from_dataclass(retval)
        else:
            raise werkzeug.exceptions.NotFound()
