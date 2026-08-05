import logging
import typing as t
from contextlib import asynccontextmanager
from contextvars import ContextVar
from sys import stderr
from traceback import format_exc
from uuid import uuid4 as uuid

from cloudflare_error_page import render
from fastapi import FastAPI, Request, Response
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
)
from loguru import logger as l
from uvicorn import run

import utils as u
from config import c

VERSION = "2026.8.5"
reqid: ContextVar[str] = ContextVar("landing_reqid", default="not-in-request")

# region init


@asynccontextmanager
async def lifespan(app: FastAPI):
    # init logger
    l.remove()

    # log format
    def log_format(record):
        reqid = record["extra"].get("reqid", "fallback-logid")
        return (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <yellow>"
            + reqid
            + "</yellow> | <cyan>{name}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>\n"
        )

    l.add(stderr, level=c.log.level, format=log_format, backtrace=True, diagnose=True)

    if c.log.file:
        l.add(
            c.log.file,
            level=c.log.file_level or c.log.level,
            format=log_format,
            colorize=False,
            rotation=c.log.rotation,
            retention=c.log.retention,
            enqueue=True,
        )
    l.configure(extra={"reqid": "not-in-request"})
    l.info("SiiWay Landing Page")
    l.info(f"Version: {VERSION}")
    l.info("GitHub: https://github.com/siiway/landing")
    l.info("Licensed under MIT License.")
    l.debug("Worker init done.")
    yield


app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)


@app.middleware("http")
async def log_requests(request: Request, call_next: t.Callable):
    request_id = str(uuid())
    token = reqid.set(request_id)
    with l.contextualize(reqid=request_id):
        if request.client:
            ip = (
                f"[{request.client.host}]"
                if ":" in request.client.host
                else request.client.host
            )
            port = request.client.port
        else:
            ip = "unknown-ip"
            port = 0
        # rev_ip = request.headers.get('CF-Connecting-IP') or request.headers.get('X-Forwarded-For')
        # {f" ({rev_ip})" if rev_ip else ""}
        l.info(f"Incoming request: {ip}:{port} - {request.method} {request.url.path}")
        try:
            p = u.perf_counter()
            resp: Response = await call_next(request)
            l.info(f"Outgoing response: {resp.status_code} ({p()}ms)")
            return resp
        except Exception as e:  # ruff: ignore[BLE001]
            l.error(f"Server error: {e} ({p()}ms)\n{format_exc()}")
            resp = Response(f"Internal Server Error ({request_id})", 500)
        resp.headers["X-Landing-Version"] = VERSION
        resp.headers["X-Landing-Request-Id"] = request_id
        reqid.reset(token)
        return resp


class InterceptHandler(logging.Handler):
    def emit(self, record):
        logger_opt = l.opt(depth=6, exception=record.exc_info)
        logger_opt.log(record.levelname, record.getMessage())


logging.getLogger("uvicorn").handlers.clear()
logging.getLogger("uvicorn.access").handlers.clear()
logging.getLogger("uvicorn.error").handlers.clear()
logging.getLogger().handlers = [InterceptHandler()]
logging.getLogger().setLevel(c.log.level)
logging.getLogger("watchfiles").level = logging.WARNING

# endregion init

# region route


@app.get("/favicon.ico")
async def favicon():
    return RedirectResponse("https://icons.siiway.org/siiway/icon.svg", 301)


# prepare plain response
plain_resp = PlainTextResponse(
    "Site Not Found", status_code=404, headers={"X-Robots-Tag": "None"}
)


@app.get("/{path:path}")
async def handle_request(path: str, req: Request):
    ua = req.headers.get("User-Agent")
    if not ua:
        l.debug("No UA, response plain text")
        return plain_resp
    for m in c.automated_exclude:
        if m in req.url.path:
            l.debug(f"Automated path {m!r} matched, response plain text")
            return plain_resp

    host = req.headers.get("Host")
    cf_ray = req.headers.get("CF-Ray")
    cf_connecting_ip = req.headers.get("CF-Connecting-IP")
    origin_ip = req.client.host or None  # ty: ignore[unresolved-attribute]
    show_more_info = not u.check_domain(host or c.landing_domain, c.domains)

    is_browser = u.test_ua(ua)
    l.debug(
        f"Render page: Host: {host!r}, Show more info: {show_more_info!r}, RayID: {cf_ray!r}, Connecting: {cf_connecting_ip!r}, Origin: {origin_ip!r}, User-Agent: {ua!r} (browser: {is_browser})"
    )
    if is_browser:
        page = render(
            {
                "html_title": f"{host or c.landing_domain} | 404: Site doesn't exist",
                "title": "Site Not Found",
                "error_code": "404",
                "more_information": {
                    "hidden": show_more_info,
                    "text": "siiway.org",
                    "link": "https://siiway.org",
                },
                "browser_status": {
                    "status": "ok",
                    "location": "",
                    "name": "",
                    "status_text": "",
                },
                "cloudflare_status": {
                    "status": "ok",
                    "location": "Global",
                    "name": "",
                    "status_text": "",
                },
                "host_status": {
                    "status": "error",
                    "location": "",
                    "name": "",
                    "status_text": "Not Found",
                },
                "error_source": "host",
                "what_happened": "The site you requested is not exist.",
                "what_can_i_do": "Please check if you spelled it wrongly.",
                "perf_sec_by": {
                    "text": f"SiiWay Landing Page - v{VERSION}",
                    "link": "https://github.com/siiway/landing",
                },
                "ray_id": cf_ray or "No Ray ID",
                "client_ip": cf_connecting_ip or origin_ip or "0.0.0.0",
            }
        )
        page = u.replace_error_icon(page)
        return HTMLResponse(page, status_code=404, headers={"X-Robots-Tag": "none"})
    else:
        ret: dict[str, t.Any] = {
            "status_code": 404,
            "error": "Site doesn't exist",
            "host": host,
            "ray_id": cf_ray,
            "client_ip": cf_connecting_ip,
            "version": VERSION,
            "source": "https://github.com/siiway/landing",
        }
        if show_more_info:
            ret.update({"more_info": "https://siiway.org"})
        return JSONResponse(ret, status_code=404, headers={"X-Robots-Tag": "none"})


# endregion route

# region main

if __name__ == "__main__":
    l.info(
        f"Starting server: {f'[{c.host}]' if ':' in c.host else c.host}:{c.port} with {c.workers} workers"
    )
    run("main:app", host=c.host, port=c.port, workers=c.workers)
    print()
    l.info("Bye.")

# endregion main
