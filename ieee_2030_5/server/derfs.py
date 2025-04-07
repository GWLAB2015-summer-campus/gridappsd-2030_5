from dataclasses import asdict
from typing import Optional
from pprint import pformat

from flask import Response, request
from werkzeug.exceptions import NotFound, InternalServerError, BadRequest

import ieee_2030_5.adapters as adpt
from ieee_2030_5.data.indexer import add_href, get_href
import ieee_2030_5.hrefs as hrefs
import ieee_2030_5.models as m
from ieee_2030_5.server.base_request import RequestOp
from ieee_2030_5.utils import xml_to_dataclass
import ieee_2030_5.db.tables as t

import logging

_log = logging.getLogger(__name__)


class DERRequests(RequestOp):
    """
    Class supporting end devices and any of the subordinate calls to it.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def put(self) -> Response:
        """Allows putting of 2030.5 DER data to the server.
        """
        if not request.path.startswith(hrefs.DEFAULT_DER_ROOT):
            raise ValueError(f"Invalid path for {self.__class__} {request.path}")

        parser = hrefs.HrefParser(request.path)

        clstype = {
            hrefs.DER_SETTINGS: m.DERSettings,
            hrefs.DER_STATUS: m.DERStatus,
            hrefs.DER_CAPABILITY: m.DERCapability,
            hrefs.DER_AVAILABILITY: m.DERAvailability,
            hrefs.DER_PROGRAM: m.DERProgram,
        }

        data = request.get_data(as_text=True)
        data = xml_to_dataclass(data, clstype[parser.at(2)])

        # if request.path.endswith("ders") or request.path.endswith("derg"):
        #     print(f"----------------------DER PUT {request.path} {data}")


        _log.info(f"DER PUT {request.path} {asdict(data)}")
        meta_data = dict(lfdi=self.lfdi, uri=f"{request.path}")
        adpt.ListAdapter.set_single_amd_meta_data(uri=f"{request.path}",
                                                  envelop=meta_data,
                                                  obj=data)
        return self.build_response_from_dataclass(data)

    def get(self) -> Response:

        if not request.path.startswith(hrefs.DEFAULT_DER_ROOT):
            raise ValueError(f"Invalid path for {self.__class__} {request.path}")

        value = adpt.ListAdapter.get_single(request.path)

        if value is None:

            parser = hrefs.HrefParser(request.path)

            subpaths = {
                hrefs.DER_SETTINGS: m.DERSettings(href=request.path),
                hrefs.DER_STATUS: m.DERStatus(href=request.path),
                hrefs.DER_CAPABILITY: m.DERCapability(href=request.path),
                hrefs.DER_AVAILABILITY: m.DERAvailability(href=request.path),
                hrefs.DER_PROGRAM: m.DERProgram(href=request.path),
            }

            if parser.has_index():
                index = parser.at(1)
                subpath = parser.at(2)
                value = subpaths[subpath]

        # pth_split = request.path.split(hrefs.SEP)

        # if len(pth_split) == 1:
        #     # TODO Add arguments
        #     value = adpt.DERAdapter.fetch_list()
        # else:
        #     value = adpt.DERAdapter.fetch_at(int(pth_split[1]))

        return self.build_response_from_dataclass(value)


class DERProgramRequests(RequestOp):
    """
    Class supporting end devices and any of the subordinate calls to it.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def put(self) -> Response:
        if not request.data:
            raise BadRequest()

        parsed = hrefs.HrefParser(request.path)

        try:
            if parsed.count() == 3 and parsed.at(2) == hrefs.DDERC:
                # update Default DER Control
                data: m.DefaultDERControl = xml_to_dataclass(request.data.decode('utf-8'), m.DefaultDERControl)
                if not isinstance(data, m.DefaultDERControl):
                    raise BadRequest()
                
                dderc = t.DefaultDERControlTable.from_model(data, der_program_id=parsed.at(1))
                dderc = dderc.update()
                return Response(status=200)
            else:
                _log.error(f"Invalid path for {self.__class__} {request.path}")
                raise NotFound(f"{request.path}")
        except Exception as e:
            _log.error(e)
            raise InternalServerError()

    def post(self) -> Response:
        if not request.data:
            raise BadRequest()
        

        parsed = hrefs.HrefParser(request.path)

        try:
            if parsed.count() == 1:
                # create DER Program
                data: m.DERProgram = xml_to_dataclass(request.data.decode('utf-8'), m.DERProgram)
                if not isinstance(data, m.DERProgram):
                    raise werkzeug.exceptions.BadRequest()
                
                derProgram = t.DERProgramTable.from_model(data)
                derProgram.add()
                dderc = t.DefaultDERControlTable.get_server_default(derProgram.id)
                dderc.add()

            elif parsed.count() == 3 and parsed.at(2) == hrefs.DERC:
                # create DER Control
                data: m.DERControl = xml_to_dataclass(request.data.decode('utf-8'), m.DERControl)
                if not isinstance(data, m.DERControl):
                    raise werkzeug.exceptions.BadRequest()
   
                derControl = t.DERControlTable.from_model(data, der_program_id=parsed.at(1))
                derControl.add()

            elif parsed.count() == 3 and parsed.at(2) == hrefs.DERCURVE:
                # create DER Curve
                data: m.DERCurve = xml_to_dataclass(request.data.decode('utf-8'), m.DERCurve)
                if not isinstance(data, m.DERCurve):
                    raise werkzeug.exceptions.BadRequest()
                    
                derCurve = t.DERCurveTable.from_model(data, der_program_id=parsed.at(1))
                derCurve.add()

                for cdata in data.CurveData:
                    curveData = t.CurveDataTable.from_model(cdata, der_curve_id=derCurve.id)
                    curveData.add()
            else:
                _log.error(f"Invalid path for {self.__class__} {request.path}")
                raise NotFound(f"{request.path}")

            return Response(status=201)

        except Exception as e:
            _log.error(e)
            raise InternalServerError()


    def get(self) -> Response:

        _log.debug(f"Processing get request for: {request.path} with args: {[x for x in request.args.keys()]}")
        start = int(request.args.get('s', 0))
        after = int(request.args.get('a', 0))
        limit = int(request.args.get('l', 1))

        parsed = hrefs.HrefParser(request.path)

        try:
            if parsed.count() <= 2:
                if not parsed.has_index():
                    # get DER Program List
                    all_cnt, selected_list = t.DERProgramTable.get_all(
                        start = start,
                        limit = limit,
                        order_by=(
                            t.DERProgramTable.primacy,
                            t.DERProgramTable.mrid.desc()
                        )
                    )
                    retval = m.DERProgramList(
                        href = request.path,
                        subscribable = False,
                        all = all_cnt,
                        results = len(selected_list),
                        DERProgram = [derp.to_model() for derp in selected_list]
                    )
                else:
                    # get DER Program by ID
                    retval = t.DERProgramTable.get_by_id(parsed.at(1))
                    if retval is not None:
                        retval = retval.to_model()
            elif parsed.count() == 4:
                if parsed.at(2) == hrefs.DERC:
                    # get DER Control
                    retval = t.DERControlTable.get_one(
                        where = (
                            t.DERControlTable.id == parsed.at(3) and 
                            t.DERControlTable.der_program_id == parsed.at(1)
                        )
                    )
                    if retval is not None:
                        retval = retval.to_model()
                elif parsed.at(2) == hrefs.DERCURVE:
                    # get DER Curve
                    retval = t.DERCurveTable.get_one(
                        where = (
                            t.DERCurveTable.id == parsed.at(3) and 
                            t.DERCurveTable.der_program_id == parsed.at(1)
                        )
                    )
                    if retval is not None:
                        retval = retval.to_model()
                else: retval = None
            elif parsed.at(2) == hrefs.DERC:
                # get DER Control List
                all_cnt, selected_list = t.DERControlTable.get_all(
                    start = start,
                    limit = limit,
                    order_by=(
                        t.DERControlTable.interval_start,
                        t.DERControlTable.creation_time.desc(),
                        t.DERControlTable.mrid.desc()
                    ),
                    where = (
                        t.DERControlTable.der_program_id == parsed.at(1)
                    )
                )
                retval = m.DERControlList(
                    href = request.path,
                    subscribable = False,
                    all = all_cnt,
                    results = len(selected_list),
                    DERControl = [derc.to_model() for derc in selected_list]
                )

            elif parsed.at(2) == hrefs.DDERC:
                # get Default DERC
                retval = t.DefaultDERControlTable.get_by_id(parsed.at(1))
                if retval is not None:
                    retval = retval.to_model()
            elif parsed.at(2) == hrefs.DERCURVE:
                # get DER Curve List
                all_cnt, selected_list = t.DERCurveTable.get_all(
                    start = start,
                    limit = limit,
                    order_by=(
                        t.DERCurveTable.creation_time.desc(),
                        t.DERCurveTable.mrid.desc()
                    ),
                    where = (
                        t.DERCurveTable.der_program_id == parsed.at(1)
                    )
                )
                retval = m.DERCurveList(
                    href = request.path,
                    all = all_cnt,
                    results = len(selected_list),
                    DERCurve = [dc.to_model() for dc in selected_list]
                )
        except Exception as e:
            _log.error(e)
            raise InternalServerError()

        if not retval:
            raise NotFound(f"{request.path}")

        return self.build_response_from_dataclass(retval)
