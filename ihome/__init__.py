# coding:utf-8
from flask import Flask
from config import CONFIG_MAP
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_wtf import CSRFProtect
import redis
import logging
from logging.handlers import RotatingFileHandler
from ihome.utils.commons import ReConverter

# 设置日志信息
# 等级，格式，文件，启用
logging.basicConfig(level=logging.INFO)
file_log_handler = RotatingFileHandler('logs/log',maxBytes=1024*1024*100,backupCount=10)
formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
file_log_handler.setFormatter(formatter)
logging.getLogger().addHandler(file_log_handler)


db = SQLAlchemy()
redis_store = None
def create_app(config_name):
    app = Flask(__name__)
    config_class = CONFIG_MAP.get(config_name)
    app.config.from_object(config_class)
    db.init_app(app)

    global redis_store
    redis_store = redis.StrictRedis(host=config_class.REDIS_HOST,port=config_class.REDIS_PORT)

    Session(app)
    CSRFProtect(app)
    app.url_map.converters["re"] = ReConverter

    # 注册蓝图
    from ihome import api_1_0
    app.register_blueprint(api_1_0.api,url_prefix='/api/v1.0')
    from ihome import web_html
    app.register_blueprint(web_html.html)
    return app
