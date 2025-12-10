# coding: utf-8
# Configs

import typing as t

from pydantic import BaseModel, field_validator, PositiveInt
from yaml import safe_load

# Logging


class LogModel(BaseModel):
    '''
    日志配置 Model
    '''

    level: t.Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] = 'INFO'
    '''
    日志等级
    - DEBUG
    - INFO
    - WARNING
    - ERROR
    - CRITICAL
    '''

    file: str | None = 'logs/{time:YYYY-MM-DD}.log'
    '''
    日志文件保存格式 (for Loguru)
    - 设置为 None 以禁用
    '''

    file_level: t.Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] | None = 'INFO'
    '''
    单独设置日志文件中的日志等级, 如设置为 None 则使用 level 设置
    - DEBUG
    - INFO
    - WARNING
    - ERROR
    - CRITICAL
    '''

    rotation: str | int = '1 days'
    '''
    配置 Loguru 的 rotation (轮转周期) 设置
    '''

    retention: str | int = '3 days'
    '''
    配置 Loguru 的 retention (轮转保留) 设置
    '''

    @field_validator('level', 'file_level', mode='before')
    def normalize_level(cls, v):
        if v is None:
            return v
        if not isinstance(v, str):
            raise ValueError(f'Invaild log level: {v}')
        upper = v.strip().upper()
        valid = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if upper not in valid:
            raise ValueError(f'Invaild log level: {v}')
        return upper

# Server


class ConfigModel(BaseModel):
    log: LogModel = LogModel()

    host: str = '0.0.0.0'
    '''
    服务监听地址 (仅在直接启动 main.py 时有效)
    '''

    port: PositiveInt = 9456
    '''
    服务监听端口 (仅在直接启动 main.py 时有效)
    '''

    workers: PositiveInt = 2
    '''
    服务 Worker 数 (仅在直接启动 main.py 时有效)
    '''

    domains: list[str] = []
    '''
    官方域名列表
    '''

    landing_domain: str = 'landing.siiway.top'
    '''
    Host fallback
    '''


config_dict = {}

try:
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config_dict = safe_load(f)
except:
    pass

c = ConfigModel.model_validate(config_dict)
