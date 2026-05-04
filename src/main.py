# coding: utf-8

import logging
from contextvars import ContextVar
from contextlib import asynccontextmanager
from sys import stdout
import typing as t
from uuid import uuid4 as uuid

from fastapi import FastAPI, Request, Response
from fastapi.responses import RedirectResponse

from cloudflare_error_page import render
from config import c
import utils as u

# region init

VERSION = "2026.5.3"
reqid: ContextVar[str] = ContextVar("landing_reqid", default="not-in-request")

# Setup basic logging
logger = logging.getLogger("landing")
logger.setLevel(c.log.level)
handler = logging.StreamHandler(stdout)
handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(handler)
logger.propagate = False

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

# endregion init

# region route


@app.get("/favicon.ico")
async def favicon(req: Request):
    request_id = str(uuid())
    cf_connecting_ip = req.headers.get("CF-Connecting-IP")
    cf_ray = req.headers.get("CF-Ray")
    ip = cf_connecting_ip or "unknown-ip"

    p = u.perf_counter()
    resp = RedirectResponse("https://icons.siiway.org/siiway/icon.svg", 301)
    resp.headers["X-Landing-Version"] = VERSION
    resp.headers["X-Landing-Request-Id"] = request_id

    logger.info(
        f"[{request_id}] {ip} - {req.method} {req.url.path} -> {resp.status_code} ({p()}ms) (RayID: {cf_ray})"
    )
    return resp


@app.get("/{path:path}")
async def handle_request(path: str, req: Request):
    request_id = str(uuid())
    cf_connecting_ip = req.headers.get("CF-Connecting-IP")
    cf_ray = req.headers.get("CF-Ray")
    ip = cf_connecting_ip or "unknown-ip"

    p = u.perf_counter()
    try:
        host = req.headers.get("Host")
        show_more_info = not u.check_domain(host or c.landing_domain, c.domains)
        ua = req.headers.get("User-Agent")
        is_browser = u.test_ua(ua) if ua else True

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
                    "client_ip": cf_connecting_ip or "0.0.0.0",
                }
            )
            page = u.replace_error_icon(page)
            resp = Response(
                content=page,
                status_code=404,
                media_type="text/html",
                headers={"X-Robots-Tag": "none"},
            )
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
            resp = ret

        # Add headers and log in one place
        if isinstance(resp, Response):
            resp.headers["X-Landing-Version"] = VERSION
            resp.headers["X-Landing-Request-Id"] = request_id

        logger.info(
            f"[{request_id}] {ip} - {req.method} {req.url.path} -> {getattr(resp, 'status_code', 200)} ({p()}ms) (RayID: {cf_ray})"
        )
        return resp

    except Exception as e:
        logger.exception(f"[{request_id}] Error: {e}")
        resp = Response(f"Internal Server Error ({request_id})", 500)
        resp.headers["X-Landing-Version"] = VERSION
        resp.headers["X-Landing-Request-Id"] = request_id
        logger.info(
            f"[{request_id}] {ip} - {req.method} {req.url.path} -> 500 ({p()}ms) (RayID: {cf_ray})"
        )
        return resp
