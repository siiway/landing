# coding: utf-8

import logging
from contextvars import ContextVar

from loguru import logger as l
from fastapi import FastAPI

from 

VERSION = '2025.12.10'
reqid: ContextVar[str] = ContextVar('landing_reqid', default='not-in-request')

app = FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)


