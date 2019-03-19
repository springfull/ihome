# coding:utf-8
from . import api
from .. import redis_store, db
from flask import request, jsonify, current_app, session
from ihome.utils.response_code import RET
import re
from ..models import User
from sqlalchemy.exc import IntegrityError
from ihome import constants


@api.route('/users', methods=['POST'])
def register():
    """
    请求格式json 方式post
    手机号 短信验证码 密码
    :return: json
    """
    req_dict = request.get_json()
    mobile = req_dict.get('mobile')
    sms_code = req_dict.get('sms_code')
    password = req_dict.get('password')
    password2 = req_dict.get('password2')

    # 校验参数
    if not all([mobile, sms_code, password, password2]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')
    # 判断手机格式
    if not re.match(r'1[3-8]\d{9}', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg='号码格式错误')

    if password2 != password:
        return jsonify(errno=RET.PARAMERR, errmsg='两次密码不一致')

    # 从redis中取出验证码
    try:
        real_sms_code = redis_store.get('sms_code_%s' % mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='验证码异常')

    # 判断验证码是否过期

    if real_sms_code is None:
        return jsonify(errno=RET.NODATA, errmsg='验证码过期')

    try:
        redis_store.delete('sms_code_%s' % mobile)
    except Exception as e:
        current_app.logger.error(e)

    # 判断用户填写验证码的正确性
    if real_sms_code != sms_code:
        return jsonify(errno=RET.DATAERR, errmsg='验证码错误')

    # 保存到数据库中
    user = User(name=mobile, mobile=mobile)
    user.password = password

    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAEXIST, errmsg='手机号已存在')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据库异常")

    session['name'] = mobile
    session['mobile'] = mobile
    session['user_id'] = user.id

    return jsonify(errno=RET.OK, errmsg='注册成功')


@api.route('/sessions', methods=['POST'])
def login():
    """
    数据格式json
    手机号，
    密码，
    验证码

    :return:
    """
    res_dict = request.get_json()
    mobile = res_dict.get('mobile')
    password = res_dict.get('password')

    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')

    if not re.match(r'1[3-8]\d{9}', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg='号码格式错误')

    # 判断次数是否超过限制
    user_ip = request.remote_addr
    try:
        access_num = redis_store.get('access_num_%s' % user_ip)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if access_num is not None and int(access_num) >= constants.LOGIN_ERROR_MAX_TIMES:
            return jsonify(errno=RET.REQERR, errmsg="错误次数过多，请稍后重试")

    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取用户信息失败")

    if user is None or not user.check_password(password):
        try:
            redis_store.incr('access_num_%s' % user_ip)
            redis_store.expire("access_num_%s" % user_ip, constants.LOGIN_ERROR_FORBID_TIME)
        except Exception as e:
            current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="用户名或密码错误")

    session['name'] = user.name
    session['mobile'] = user.mobile
    session['user_id'] = user.id
    return jsonify(errno=RET.OK, errmsg="登录成功")


@api.route('/session', methods=['GET'])
def check_login():
    name = session.get('name')
    if name is not None:
        return jsonify(errno=RET.OK, errmsg='true', data={'name': name})
    else:
        return jsonify(errno=RET.SESSIONERR, errmsg="false")


@api.route('/session', methods=['DELETE'])
def logout():
    csrf_token = session.get('csrf_token')
    session.clear()
    session['csrf_token'] = csrf_token
    return jsonify(errno=RET.OK, errmsg="OK")
