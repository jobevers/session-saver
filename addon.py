import pathlib
import pickle
import uuid
from datetime import datetime

from mitmproxy import http
from typing_extensions import TypedDict

import helpers


Flow = TypedDict(
    "Flow", {"response": http.Response, "request": http.Request, "timestamp": str}
)


def response(flow: http.HTTPFlow) -> None:
    # use uuid1 so that the outputs are sorted by time
    uid = str(uuid.uuid1())
    now = helpers.utcnow()
    data: Flow = {
        "response": flow.response,
        "request": flow.request,
        "timestamp": now.isoformat(),
    }
    p = pathlib.Path("http-data", now.strftime("%Y%m%d"))
    p.mkdir(exist_ok=True, parents=True)
    with p.joinpath(f"{uid}.pkl").open("wb") as fout:
        pickle.dump(data, fout)
