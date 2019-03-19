# coding:utf-8
from . import api
from ihome.utils.captcha.captcha import captcha
from ihome import redis_store
from ihome import constants
from ihome.utils.response_code import RET
from flask import current_app, jsonify, make_response, request
from ..models import User
import random
from ihome.tasks.sms.tasks import send_sms


# 获取图片验证码
@api.route('/image_codes/<image_code_id>')
def get_image_code(image_code_id):
    """
    获取图片验证码
    :param image_code_id:图片验证码编号
    :return:正常 验证码图片，异常 返回json
    """
    # 义务逻辑处理
    # 生成验证码图片
    name, text, image_data = captcha.generate_captcha()
    # 将验证码真实值保存到redis中，并设置有效期

    try:
        redis_store.setex('image_code_%s' % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(error=RET.DBERR, errmsg='保存图片验证码失败')

    resp = make_response(image_data)
    resp.headers['Content_Type'] = "image/jpg"
    return resp


# 获取短信验证码
# api/v1.0/sms_codes/<mobile>?image_code=xxxx&iamge_code_id=xxxx
@api.route('/sms_codes/<re(r"1[34578]\d{9}"):mobile>')
def get_sms_code(mobile):
    """
    获取短信验证码参数
    :param mobile: 
    :return: 
    """
    image_code = request.args.get('image_code')
    image_code_id = request.args.get('image_code_id')

    if not all([image_code, image_code_id]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')

    # 业务逻辑处理
    # 从redis中读取验证码
    try:
        real_image_code = redis_store.get('image_code_%s' % image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="redis数据库异常")

    # 判断验证码是否过期
    if real_image_code is None:
        return jsonify(errno=RET.NODATA, errmsg="图片验证码失效")

    try:
        redis_store.delete('image_code_%s' % image_code_id)
    except Exception as e:
        current_app.logger.error(e)

    if real_image_code.lower() != image_code.lower():
        return jsonify(errno=RET.DATAERR, errmsg="图片验证码错误")

    # 判断用户是否频繁操作
    try:
        send_flag = redis_store.get('send_sms_code_%s' % mobile)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if send_flag is not None:
            return jsonify(errno=RET.REQERR, errmsg="请求过于频繁，请60秒后重试")

    # 判断手机号是否存在
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
    else:
        if user is not None:
            return jsonify(errno=RET.DATAEXIST, errmsg="手机号已存在")

    # 如果手机号不存在则生成短信验证码
    sms_code = '%06d' % random.randint(0, 999999)

    # 保存真实的验证码
    try:

        redis_store.setex('sms_code_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        redis_store.setex('send_sms_code_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存短信验证码异常")

    # 使用celery异步发送短信
    send_sms.delay(mobile, [sms_code, int(constants.SMS_CODE_REDIS_EXPIRES / 60)], 1)

    return jsonify(errno=RET.OK, errmsg='发送成功')
