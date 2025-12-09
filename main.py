# coding: utf-8

import logging
from contextvars import ContextVar
from contextlib import asynccontextmanager
from sys import stderr
import typing as t

from loguru import logger as l
from fastapi import FastAPI, Header

from cloudflare_error_page import render  # pyright: ignore[reportMissingImports]
import config as c

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


@app.route('/{path:path}')
async def handle_request(
    path: str,
    host: t.Annotated[str | None, Header()] = None,
    cf_ray: t.Annotated[str | None, Header()] = None,
    cf_connecting_ip: t.Annotated[str | None, Header()] = None
):
    host = host if host else 'landing.siiway.org'
    cf_ray = cf_ray if cf_ray else 'No Ray ID'
    cf_connecting_ip = cf_connecting_ip if cf_connecting_ip else '0.0.0.0'
    page = render({
        "html_title": f"{host} | 404: Site doesn't exist",
        "title": "Not Found",
        "error_code": "404",
        "more_information": {
            "hidden": False,
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
            "status_text": "Not Exist"
        },
        "error_source": "host",
        "what_happened": "The site you requested is not exist.",
        "what_can_i_do": "Please check if you spelled it wrongly.",
        "perf_sec_by": {
            "text": "SiiWay Landing Page",
            "link": "https://github.com/siiway/landing"
        },
        "ray_id": cf_ray,
        "client_ip": cf_connecting_ip
    })


# endregion route

# region main

# if __name__ == '__main__':
#     l.info(f'Starting server: {f"[{c.host}]" if ":" in c.host else c.host}:{c.port} with {c.workers} workers')
#     run('main:app', host=c.host, port=c.port, workers=c.workers)
#     print()
#     l.info('Bye.')

# TODO

# endregion main