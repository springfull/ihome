# coding:utf-8
from celery import Celery
from ihome.tasks import config

# 定义celery对象
celery_app = Celery('ihome')
celery_app.config_from_object(config)

# celery_app.autodiscover_tasks(['ihome.tasks.sms'])
celery_app.autodiscover_tasks(["ihome.tasks.sms"])


