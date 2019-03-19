# coding:utf-8
from . import api
from flask import request, current_app, jsonify,g
from ihome.utils.response_code import RET
from ihome.utils.commons import login_required


@api.route('/users/avatar', methods=['POST'])
@login_required
def set_user_avatar():
    """
    设置用户头像
    :return:
    """
    user_id = g.user_id
    image_file = request.files.get('avatar')
    if image_file is None:
        return jsonify(errno=RET.PARAMERR, errmsg="未上传图片")
    image_data = image_file.read()

    # 调用第三方服务七牛上传