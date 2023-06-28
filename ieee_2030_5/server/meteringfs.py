"""
This module handles MirrorUsagePoint and UsagePoint constructs for a server.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

from flask import Response, request
from werkzeug.exceptions import BadRequest

import ieee_2030_5.adapters as adpt
import ieee_2030_5.hrefs as hrefs
import ieee_2030_5.models as m
from ieee_2030_5.data.indexer import get_href
from ieee_2030_5.server.base_request import RequestOp
from ieee_2030_5.server.uuid_handler import UUIDHandler
from ieee_2030_5.utils import dataclass_to_xml, xml_to_dataclass

# Metering Function Set Guidelines
# 10.11.3 Application guidelines/behavior
# A Metering Mirror function set server SHALL NOT advertise support for mirroring unless it has the
# resources available to host at least one additional mirror. The server must have room for at least one
# instance of each of the resources possible under a Usage Point.
# The following rules apply to creating and maintaining Metering Mirrors.
#
# a) To create a new Metering Mirror the client SHALL POST to the server’s MirrorUsagePointList
#    (e.g., /mup) for the mirrored usage point.
#   1) This POST SHALL contain at least the information through the definition of
#       MirrorMeterReadings and ReadingType including the MirrorUsagePoint mRID and
#       MirrorMeterReading mRIDs.
# 
#   2) The POST MAY also contain MirrorReadingSets and Readings.
# 
#   3) If the mRID of the MirrorUsagePoint is unique (does not match a MirrorUsagePoint.mRID of
#       an existing MirrorUsagePoint) the response SHALL be response code 201 (Created), the
#       MirrorUsagePoint URI SHALL be included in the Location header.
# 
#   4) If the mRID of the MirrorUsagePoint matches an existing MirrorUsagePoint, the new data
#       SHALL be written over the existing MirrorUsagePoint (and associated UsagePoint) and the
#       response code SHALL be 204 (No Content), the MirrorUsagePoint URI SHALL be included
#       in the Location header. If the MirrorUsagePoint contains MirrorMeterReadings, then the
#       guidance of Rule h) and Rule i) are to be applied.
#
# b) When the Metering Mirror function set server receives a POST it SHALL copy the received data,
#    including mRIDs, into the normal metering structure to its Metering UsagePoint structure (e.g.,
#    /upt), and it SHALL allocate enough resources to manage the mirror and its data.
#
# c) A GET of the resource (MirrorUsagePoint) identified in the response to the initial POST SHALL
#    return a resource with only the first level elements (i.e., sub-elements and collections are not
#    included).
#
# d) To POST new data to an existing MirrorUsagePoint, the Metering client SHALL POST a
#    MirrorMeterReading or MirrorMeterReadingList containing MirrorReadingSets and/or Readings to
#    the resource identified in the Metering server’s response to the POST that created the resource (e.g.,
#    /mup/3).
#
# e) The Metering Mirror server SHOULD only accept POSTs to a given MirrorUsagePoint from the
#    client that created the mirror.
#
# f) If a POST to the MirrorUsagePoint is of a MirrorMeterReading, then a successful response SHALL
#    contain a Location header indicating the URI of the MeterReading resource under the associated
#    UsagePoint (e.g., /upt/2/mr/3).
#
# g) If a POST to the MirrorUsagePoint is of a MirrorMeterReadingList, then a successful response
#    SHALL contain a Location header indicating the URI of the MeterReadingList under the associated
#    UsagePoint (e.g., /upt/2/mr).
#
# h) In a POST to the MirrorUsagePoint, the mRID attribute of the MirrorMeterReading(s) SHALL be
#    used by the Metering Mirror server to associate the data in a POST with the MeterReading in the
#    associated UsagePoint.
# 
#   1) In a POST to the MirrorUsagePoint, if the mRID attribute matches a previous
#       MirrorMeterReading, then each of the contained MirrorReadingSets SHALL be handled as
#       required by Rule i) below. The contents of the MirrorMeterReading SHALL overwrite the
#       data in the associated MeterReading.
#
#   2) In a POST to the MirrorUsagePoint, if the mRID does not match a previous
#       MirrorMeterReading and it contains a ReadingType, then a new MeterReading SHALL be
#       created under the associated UsagePoint with the new data.
#
#   3) In a POST to the MirrorUsagePoint, if the mRID does not match a previous
#       MirrorMeterReading and there is not a ReadingType, then the request SHALL be rejected
#       with a response code 400 (Bad Request).
#
# i) In a POST to the MirrorUsagePoint, where the request is not rejected, the new data SHALL be
#           applied to the related UsagePoint resource structure according to the following:
# 
#   1) If a MirrorReadingSet is received with a duplicate mRID of an existing ReadingSet, and it is
#      targeted within the same resource hierarchy, then the new data SHALL replace the existing
#      data of the identified ReadingSet.
#
#   2) If a MirrorReadingSet is received with a unique mRID, then the new data SHALL be added to
#      the identified ReadingSetList.

# j) If a client POSTs more data than the Metering Mirror server is willing to accept, the server SHALL
#    respond with a response code of 413 (Request Entity Too Large).
#
# k) The Metering Mirror server MAY decide when to remove data from the related UsagePoint
#    resource structure.
#
# l) When a MirrorUsagePoint is deleted, the associated UsagePoint SHALL also be deleted.
#    A Metering Mirror function set server MAY implement a timeout mechanism on a mirror. If a Metering
#    Mirror function set server does not receive any POSTs from a Metering Mirror function set client for more
#    than a specified time, the server MAY remove the MirrorUsagePoint resource and its related UsagePoint
#    resource. The recommended timeout is 72 hours.


class Error(Exception):
    pass


@dataclass
class ResponseStatus:
    location: str
    status: str


class UsagePointRequest(RequestOp):
    
    def get(self) -> Response:
        pth_info = request.environ['PATH_INFO']
        try:
            upt = adpt.MirrorUsagePointAdapter.fetch_usage_point_by_href(pth_info)
        except StopIteration:
            return Response(status=404, response="Not Found")
        return self.build_response_from_dataclass(upt)


class MirrorUsagePointRequest(RequestOp):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get(self) -> Response:
        mup_href = hrefs.MirrorUsagePointHref.parse(request.path)
        
        start = int(request.args.get("s", 0))
        limit = int(request.args.get("l", 1))
        after = int(request.args.get("a", 0))
        
        mup = adpt.MirrorUsagePointAdapter.fetch_all(m.MirrorUsagePointList(href=mup_href.as_href(), pollRate=adpt.BaseAdapter.server_config().usage_point_post_rate))

        #if mup_href.mirror_usage_point_index == hrefs.NO_INDEX:
        #    mup = adpt.MirrorUsagePointAdapter.fetch_all(m.MirrorUsagePointList, start=start, after=after limit=limit)
        
        return self.build_response_from_dataclass(mup)
            
        try:

            if mup_href.mirror_usage_point_index == hrefs.NO_INDEX:
                mup = adpt.MirrorUsagePointAdapter.fetch_mirror_usage_point_list(pth_info)
            else:
                mup = adpt.MirrorUsagePointAdapter.fetch_mirror_usage_by_href(pth_info)
                
            return self.build_response_from_dataclass(mup)
        except StopIteration:
            if pth_info == hrefs.mirror_usage_point_href():
                mupl = adpt.MirrorUsagePointAdapter.fetch_mirror_usage_point_list()
                
                
            return Response("Not Found", status=404)
    
    def add_update_usage_point(self, mup: m.MirrorUsagePoint):
        
        try:
            index = adpt.UsagePointAdapter.fetch_by_mrid(mup.mRID)
        except KeyError:
            index = None
        
        upt = m.UsagePoint(mRID=mup.mRID, 
                           description=mup.description,
                           deviceLFDI=mup.deviceLFDI,
                           version=mup.version,
                           serviceCategoryKind=mup.serviceCategoryKind,
                           status=mup.status)
        mup_href = hrefs.MirrorUsagePointHref.parse(mup.href)
        upt_href = hrefs.UsagePointHref(usage_point_index=mup_href.mirror_usage_point_index)
        upt.href = upt_href.as_href()
        upt_href.include_mr = True        
        upt.MeterReadingListLink = m.MeterReadingListLink(href=upt_href.as_href())
        if index:            
            upt = adpt.UsagePointAdapter.replace(upt, index)
        else:
            adpt.UsagePointAdapter.add(upt)
        
    def add_update_meter_reading(self, mup: m.MirrorUsagePoint, mmr: m.MirrorMeterReading):
        
        m.MeterReading(mRID=mmr.mRID,
                       description=mmr.description,
                       version=mmr.version,
                       )
        
        

    def post(self) -> Response:
        xml = request.data.decode('utf-8')
        data = xml_to_dataclass(request.data.decode('utf-8'))
        data_type = type(data)
        if data_type not in (m.MirrorUsagePoint, m.MirrorReadingSet, m.MirrorMeterReading):
            raise BadRequest()

        pth_info = request.path
        pths = pth_info.split(hrefs.SEP)
        if len(pths) == 1 and data_type is not m.MirrorUsagePoint:
            # Check to make sure not a new mrid
            raise BadRequest("Must post MirrorUsagePoint to top level only")

        mup_href = hrefs.MirrorUsagePointHref.parse(request.path)
        # Creating a new mup
        if data_type == m.MirrorUsagePoint:
            before = adpt.MirrorUsagePointAdapter.size()
            adpt.MirrorUsagePointAdapter.add(item=data)
            self.add_update_usage_point(data)
            after = adpt.MirrorUsagePointAdapter.size()
            
            if before == after:
                result = [204, data.href]
            else:
                result = [201, data.href]
            
            #result = adpt.MirrorUsagePointAdapter.create(mup=data)
        elif data_type == m.MirrorMeterReading:
            # Create a reading or "subtype"
            mup = adpt.MirrorUsagePointAdapter.fetch(mup_href.mirror_usage_point_index)
            
            before = adpt.MirrorUsagePointAdapter.size_children(mup, "mr") 
            try:
                child_index = adpt.MirrorUsagePointAdapter.fetch_child_index_by_mrid(mup, "mr", data.mRID)
            except KeyError:
                child_index = None
            
            if child_index is None:
                adpt.MirrorUsagePointAdapter.add_replace_child(mup, "mr", data)
                
            else:
                adpt.MirrorUsagePointAdapter.replace_child(mup, "mr", child_index, data)
            
            self.add_update_meter_reading(mup, data)
            after = adpt.MirrorUsagePointAdapter.size_children(mup, "mr")
            
            if before == after:
                result = [204, data.href]
            else:
                result = [201, data.href]
                
            #adpt.MirrorUsagePointAdapter.add_replace_child(mup, )
            #adpt.MirrorUsagePointAdapter.add_container(m.MirrorReadingSet, mup)
            #result = adpt.MirrorUsagePointAdapter.add_replace_child(mup, )
            #result = adpt.MirrorUsagePointAdapter.create_reading(href=pth_info, data=data)
        else:
            raise BadRequest("Must post MirrorUsagePoint or MirrorReadingSet onlyonly")
        result = ResponseStatus(status=result[0], location = result[1])

        if isinstance(result, Error):
            return Response(result.args[1], status=500)
        # Note response to the post is different due to added endpoint.
        
        return Response(headers={'Location': result.location}, status=result.status if isinstance(result.status, int) else result.status.value)
