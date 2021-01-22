from typing import Optional

from fastapi import FastAPI

from IEEE2030_5 import IEEE2030_5_ENDPOINTS
import uvicorn

app = FastAPI()


def mycallback():
    return {"woot": "there it is!"}


def load_endpoints(app):
    for d, endpoint in IEEE2030_5_ENDPOINTS.items():
        # TODO modify endpoint.callback to be an actual function
        # This is probably not done here but in the IEEE2030_5_ENDPOINTS module.
        app.add_api_route(endpoint.url, mycallback)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}


if __name__ == "__main__":
    load_endpoints(app)
    app.openapi()
    uvicorn.run(app, host="0.0.0.0", port=8000)
