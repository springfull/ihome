# coding:utf-8
import redis
class Config(object):

    SECRET_KEY= 'asdasfas'
    # mysql数据库
    SQLALCHEMY_DATABASE_URI = 'mysql://myuser:123456@127.0.0.1:3306/ihome_01'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_ECHO = True
    # redis数据库

    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379




    # flask-session
    SESSION_TYPE = 'redis'
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST,port=REDIS_PORT)
    SESSION_USE_SIGNER = True
    PERMANENT_SESSION_LIFETIME = 86400

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    pass


CONFIG_MAP = {'develop':DevelopmentConfig,
              'product':ProductionConfig}