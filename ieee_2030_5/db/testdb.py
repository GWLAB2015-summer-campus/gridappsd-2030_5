from conn import get_db_session
from tables import ResponseTable, ApplianceLoadReductionColumns

def test():
    session = get_db_session()
    response = ResponseTable(
        href = "/",
        endDeviceLFDI = "testedev",
        status = 1,
        subject = "testsubject",
    )
    session.add(response)
    response = ResponseTable(
        href = "/a",
        endDeviceLFDI = "testedev",
        status = 1,
        subject = "testsubject",
        appliance_load_reduction = ApplianceLoadReductionColumns(
            type = 1
        )
    )
    session.add(response)
    session.commit()

if __name__ == '__main__':
    test()
