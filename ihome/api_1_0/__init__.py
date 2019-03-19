# coding:utf-8
from flask import Blueprint

api = Blueprint('api_1_0', __name__)

from . import vertify_code, passport, profile, pay, orders, houses
