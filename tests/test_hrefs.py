import pytest
import ieee_2030_5.hrefs as hrefs
from ieee_2030_5.hrefs import NO_INDEX

def test_simple_href():
    href = hrefs.SimpleHref.parse("/dc_1", hrefs.DEFAULT_CURVE_ROOT)
    assert 1 == href.index 
    with pytest.raises(NotImplementedError):
        str(href)
    with pytest.raises(NotImplementedError):
        href.url()

def test_curve_href():
    href = hrefs.CurveHref.parse("/dc_1")
    assert 1 == href.index
    assert "/dc_1" == href.url()
    assert "/dc_1" == str(href)
    

def test_upt_href():
    href = hrefs.UsagePointHref.parse("/upt")
    assert href.usage_point_index == NO_INDEX
    assert href.meter_reading_list_index == NO_INDEX
    assert href.meter_reading_index == NO_INDEX
    assert href.reading_set_index == NO_INDEX
    assert href.reading_index == NO_INDEX
    assert href.include_mr == False
    
    href = hrefs.UsagePointHref.parse(hrefs.SEP.join(["/upt", "0"]))
    
    assert href.usage_point_index == 0
    assert href.meter_reading_list_index == NO_INDEX
    assert href.meter_reading_index == NO_INDEX
    assert href.reading_set_index == NO_INDEX
    assert href.reading_index == NO_INDEX
    assert href.include_mr == False
    
    href = hrefs.UsagePointHref.parse(hrefs.SEP.join(["/upt", "0", "mr"]))
    
    assert href.usage_point_index == 0
    
    assert href.include_mr == True
    assert href.meter_reading_list_index == NO_INDEX
    assert href.meter_reading_index == NO_INDEX
    assert href.reading_set_index == NO_INDEX
    assert href.reading_index == NO_INDEX

def test_mup_href():
    href = hrefs.MirrorUsagePointHref.parse("/mup")
    assert href.mirror_usage_point_index == NO_INDEX
    assert href.meter_reading_list_index == NO_INDEX
    assert href.meter_reading_index == NO_INDEX
    assert href.reading_set_index == NO_INDEX
    assert href.reading_index == NO_INDEX
    assert href.include_mr == False
    
    href = hrefs.MirrorUsagePointHref.parse("/mup_0")
    
    assert href.mirror_usage_point_index == 0
    assert href.meter_reading_list_index == NO_INDEX
    assert href.meter_reading_index == NO_INDEX
    assert href.reading_set_index == NO_INDEX
    assert href.reading_index == NO_INDEX
    assert href.include_mr == False
    
    href = hrefs.MirrorUsagePointHref.parse("/mup_0_mr")
    
    assert href.mirror_usage_point_index == 0
    
    assert href.include_mr == True
    assert href.meter_reading_list_index == NO_INDEX
    assert href.meter_reading_index == NO_INDEX
    assert href.reading_set_index == NO_INDEX
    assert href.reading_index == NO_INDEX
    

def test_edev_href():
        
    href = hrefs.EdevHref.parse("/edev")
    
    assert href.edev_der_subtype is hrefs.DERSubType.None_Available
    assert href.edev_subtype is hrefs.EDevSubType.None_Available
    assert hrefs.NO_INDEX == href.edev_index
    assert hrefs.NO_INDEX == href.edev_subtype_index

    href = hrefs.EdevHref.parse(f"/edev_0")
    
    assert href.edev_der_subtype is hrefs.DERSubType.None_Available
    assert href.edev_subtype is hrefs.EDevSubType.None_Available
    assert 0 == href.edev_index
    assert hrefs.NO_INDEX == href.edev_subtype_index
    
    href = hrefs.EdevHref.parse(f"/edev_0_der")
    
    assert href.edev_der_subtype is hrefs.DERSubType.None_Available
    assert href.edev_subtype is hrefs.EDevSubType.DER
    assert 0 == href.edev_index
    assert hrefs.NO_INDEX == href.edev_subtype_index
    
    href = hrefs.EdevHref.parse(f"/edev_0_der_0")
    
    assert href.edev_der_subtype is hrefs.DERSubType.None_Available
    assert href.edev_subtype is hrefs.EDevSubType.DER
    assert 0 == href.edev_index
    assert 0 == href.edev_subtype_index
    
    href = hrefs.EdevHref.parse(f"/edev_0_der_0_dera")
    
    assert href.edev_der_subtype is hrefs.DERSubType.Availability
    assert href.edev_subtype is hrefs.EDevSubType.DER
    assert 0 == href.edev_index
    assert 0 == href.edev_subtype_index
    
    href = hrefs.EdevHref.parse(f"/edev_0_der_0_dera")
    
    assert href.edev_der_subtype is hrefs.DERSubType.Availability
    assert href.edev_subtype is hrefs.EDevSubType.DER
    assert 0 == href.edev_index
    assert 0 == href.edev_subtype_index
    
    href = hrefs.EdevHref.parse(f"/edev_0_der_0_derg")
    
    assert href.edev_der_subtype is hrefs.DERSubType.Settings
    assert href.edev_subtype is hrefs.EDevSubType.DER
    assert 0 == href.edev_index
    assert 0 == href.edev_subtype_index
    
    href = hrefs.EdevHref.parse(f"/edev_0_der_0_dstat")
    
    assert href.edev_der_subtype is hrefs.DERSubType.Status
    assert href.edev_subtype is hrefs.EDevSubType.DER
    assert 0 == href.edev_index
    assert 0 == href.edev_subtype_index
    
