# coding: utf-8

import logging
from contextvars import ContextVar
from contextlib import asynccontextmanager
from sys import stderr
import typing as t
from uuid import uuid4 as uuid
from traceback import format_exc

from loguru import logger as l
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from uvicorn import run

from cloudflare_error_page import render  # pyright: ignore[reportMissingImports]
from config import c
import utils as u

VERSION = '2025.12.10'
reqid: ContextVar[str] = ContextVar('landing_reqid', default='not-in-request')

# region init


@asynccontextmanager
async def lifespan(app: FastAPI):
    # init logger
    l.remove()

    # 定义日志格式，包含 reqid
    def log_format(record):
        reqid = record['extra'].get('reqid', 'fallback-logid')
        return '<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <yellow>' + reqid + '</yellow> | <cyan>{name}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>\n'

    l.add(
        stderr,
        level=c.log.level,
        format=log_format,
        backtrace=True,
        diagnose=True
    )

    if c.log.file:
        l.add(
            c.log.file,
            level=c.log.file_level or c.log.level,
            format=log_format,
            colorize=False,
            rotation=c.log.rotation,
            retention=c.log.retention,
            enqueue=True
        )
    l.configure(extra={'reqid': 'not-in-request'})
    l.info('SiiWay Landing Page')
    l.info(f'Version: {VERSION}')
    l.info(f'GitHub: https://github.com/siiway/landing')
    l.info(f'Licensed under MIT License.')
    yield

app = FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan
)

@app.middleware('http')
async def log_requests(request: Request, call_next: t.Callable):
    request_id = str(uuid())
    token = reqid.set(request_id)
    with l.contextualize(reqid=request_id):
        if request.client:
            ip = f'[{request.client.host}]' if ':' in request.client.host else request.client.host
            port = request.client.port
        else:
            ip = 'unknown-ip'
            port = 0
        # rev_ip = request.headers.get('CF-Connecting-IP') or request.headers.get('X-Forwarded-For')
        # {f" ({rev_ip})" if rev_ip else ""}
        l.info(f'Incoming request: {ip}:{port} - {request.method} {request.url.path}')
        try:
            p = u.perf_counter()
            resp: Response = await call_next(request)
            l.info(f'Outgoing response: {resp.status_code} ({p()}ms)')
            return resp
        except Exception as e:
            l.error(f'Server error: {e} ({p()}ms)\n{format_exc()}')
            resp = Response(f'Internal Server Error ({request_id})', 500)
        finally:
            resp.headers['X-Landing-Version'] = VERSION
            resp.headers['X-Landing-Request-Id'] = request_id
            reqid.reset(token)
            return resp


class InterceptHandler(logging.Handler):
    def emit(self, record):
        logger_opt = l.opt(depth=6, exception=record.exc_info)
        logger_opt.log(record.levelname, record.getMessage())


logging.getLogger('uvicorn').handlers.clear()
logging.getLogger('uvicorn.access').handlers.clear()
logging.getLogger('uvicorn.error').handlers.clear()
logging.getLogger().handlers = [InterceptHandler()]
logging.getLogger().setLevel(c.log.level)
logging.getLogger('watchfiles').level = logging.WARNING

# endregion init

# region route

@app.get('/favicon.ico')
async def favicon():
    return RedirectResponse('https://icons.siiway.org/siiway/icon.svg', 301)

def check_domain(host: str, domains: list[str]) -> bool:
    host = host.lower()
    return any(host == d.lower() or host.endswith('.' + d.lower()) for d in domains)

@app.get('/{path:path}')
async def handle_request(
    path: str,
    req: Request
):
    host = req.headers.get('Host', c.landing_domain)
    cf_ray = req.headers.get('CF-Ray', 'No Ray ID')
    cf_connecting_ip = req.headers.get('CF-Connecting-IP', '0.0.0.0')
    show_more_info = not check_domain(host, c.domains)
    l.info(f'Render page: Host: {host}, Show more info: {show_more_info}, RayID: {cf_ray}, Connecting: {cf_connecting_ip}')
    page = render({
        "html_title": f"{host} | 404: Site doesn't exist",
        "title": "Site Not Found",
        "error_code": "404",
        "more_information": {
            "hidden": show_more_info,
            "text": "siiway.org",
            "link": "https://siiway.org",
            "for": ""
        },
        "browser_status": {
            "status": "ok",
            "location": "",
            "name": "",
            "status_text": ""
        },
        "cloudflare_status": {
            "status": "ok",
            "location": "",
            "name": "",
            "status_text": ""
        },
        "host_status": {
            "status": "error",
            "location": "",
            "name": "",
            "status_text": "Not Found"
        },
        "error_source": "host",
        "what_happened": "The site you requested is not exist.",
        "what_can_i_do": "Please check if you spelled it wrongly.",
        "perf_sec_by": {
            "text": f"SiiWay Landing Page - v{VERSION}",
            "link": "https://github.com/siiway/landing"
        },
        "ray_id": cf_ray,
        "client_ip": cf_connecting_ip
    })
    return HTMLResponse(
        page,
        status_code=404,
        headers={
            'X-Robots-Tag': 'noindex,nofollow,nostore'
        }
    )


# endregion route

# region main

if __name__ == '__main__':
    l.info(f'Starting server: {f"[{c.host}]" if ":" in c.host else c.host}:{c.port} with {c.workers} workers')
    run('main:app', host=c.host, port=c.port, workers=c.workers)
    print()
    l.info('Bye.')

# endregion main
