import json
import time
import datetime
import pymysql
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)


def get_product_info(unpack_info) -> dict:
    print(unpack_info)
    camera_id, makeup_id, ps_id, meeting_time, phone_number, package, \
        camera_status, makeup_status, ps_status = unpack_info.split('+')[:-1]
    product_info = {
        '预约摄影师编号': int(camera_id),
        '预约化妆师编号': int(makeup_id),
        '预约后期师编号': int(ps_id),
        '预约拍摄时间': meeting_time,
        '预约顾客联系方式': phone_number,
        '选择套餐类型': package,
        '摄影师接单状态': int(camera_status),
        '化妆师接单状态': int(makeup_status),
        '后期师接单状态': int(ps_status)
    }
    return product_info


@app.route("/imax", methods=['GET', 'POST'])  # 系统进入的巨幕画面
def imax():
    if request.method == 'GET':
        return render_template('entrance.html')


@app.route("/sign/up", methods=["GET", "POST"])
def sign_up():
    if request.method == "GET":
        return render_template('sign_up.html', user_info = '请输入您的用户名')

    """ 获取用户输入的request信息 """
    user_name = request.form.get('name')
    """ 0表示男性 1表示女性 """
    if request.form.get('gender0'):
        gender = '男'
    else:
        gender = '女'
    year = request.form.get('year')
    month = request.form.get('month')
    day = request.form.get('day')
    password = request.form.get('psd')
    phone = request.form.get('phone')
    email = request.form.get('email')

    sql = f"insert into 客户 " \
          f"(用户名, 密码, 性别, 出生日期, 电话号码, 邮箱) " \
          f"values('{user_name}', '{password}', '{gender}', '{year}-{month}-{day}', '{phone}', '{email}')"
    try:
        print(f"'{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 尝试插入数据 {sql}'")
        CURSOR.execute(sql)  # 执行插入语句
        CONN.commit()  # 提交数据
        print('插入成功......')
        return redirect(url_for('login_in'), code = 301)  # 不要使用重定向，url_for里面要用函数名而不是url名
    except Exception as e:
        print(e)
        CONN.rollback()  # 发生错误则回滚

    return render_template('sign_up.html', user_info = '该用户名已被注册')


@app.route("/login/in", methods=["GET", "POST"])  # 登陆界面
def login_in():
    if request.method == "GET":
        return render_template('login_in.html', reforce = "请输入您的用户名")

    user_name = request.form.get('user_name')
    password = request.form.get('password')
    sql = f"select 客户编号, 密码 from 客户 where 用户名='{user_name}'"
    CURSOR.execute(sql)  # 执行语句
    fetch_data = CURSOR.fetchall()
    if len(fetch_data) > 0:  # 能查询到对应用户
        user_number = fetch_data[0][0]  # 获取查询的用户编号
        true_password = fetch_data[0][1]  # 获取查询的用户密码
        if true_password == password:  # 用户存在且密码输入正确则进入系统主界面
            return redirect(url_for('main', user_number = user_number), code = 301)
        else:
            return render_template('login_in.html', reforce = '您输入的用户名或密码有误，请重新输入')
    else:
        return render_template('login_in.html', reforce = '该用户不存在')


@app.route('/main/user', methods = ['GET', 'POST'])
def main_user():
    print(f"'{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 进入用户界面通过{request.method}'")
    user_number = request.args['user_number']
    sql = f"select * from 客户 where 客户编号={user_number}"  # 获取用户的信息
    CURSOR.execute(sql)
    fetch_data = CURSOR.fetchall()
    print(f'这里是查询到的用户信息: {fetch_data}')
    user_name = fetch_data[0][1]
    real_name = fetch_data[0][4]
    gender = fetch_data[0][5]
    birth_date = fetch_data[0][6]
    if birth_date == '' or birth_date == '--':
        birth_date = '待完善'
    phone_number = fetch_data[0][3]
    wechat_number = fetch_data[0][7]
    email = fetch_data[0][8]
    if request.method == 'GET':
        return render_template('main_user.html', user_number = user_number, user_name = user_name,
                               real_name = real_name, gender = gender, birth_date = birth_date,
                               phone_number = phone_number, wechat_number = wechat_number, email = email)


@app.route("/main", methods=['GET', "POST"])
def main():
    print(f"'{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 进入主界面通过{request.method}'")
    user_number = request.args['user_number']  # 通过get请求获取用户ID
    return render_template('main.html', user_number = user_number)


@app.route('/main/appointment', methods=['GET', 'POST'])
def main_appointment():
    print(f"'{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 进入预约界面通过{request.method}'")
    user_number = request.args['user_number']
    sql = f"select * from 工作人员"
    CURSOR.execute(sql)
    employee_list = CURSOR.fetchall()
    camera_dict_list = []
    makeup_dict_list = []
    ps_dict_list = []
    for query in employee_list:
        if query[2] == '摄影部':
            camera_dict_list.append({'id': query[0], 'name': query[1]})
        if query[2] == '化妆部':
            makeup_dict_list.append({'id': query[0], 'name': query[1]})
        if query[2] == '后期部':
            ps_dict_list.append({'id': query[0], 'name': query[1]})
    begin_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 截取时间戳
    begin_time_day, begin_time_hms = begin_time.split()
    hour, minute, sec = begin_time_hms.split(':')
    choose_time_min = begin_time_day + 'T' + hour + ':' + minute  # 实时更新预约时间下限
    if request.method == 'GET':
        return render_template('main_appointment.html', user_number = user_number, camera_dict_list = camera_dict_list,
                               makeup_dict_list = makeup_dict_list, ps_dict_list = ps_dict_list,
                               choose_time_min = choose_time_min)
    print(request.form)
    camera_id = request.form.get('cameraman')  # 获取预约摄影师的编号
    if camera_id == 'rand':
        sql_camera = f"select 员工编号 from 工作人员 where 所属部门='摄影部'"
        CURSOR.execute(sql_camera)
        fetch_data = CURSOR.fetchall()
        camera_id = fetch_data[0][0]
    makeup_id = request.form.get('makeup')
    if makeup_id == 'rand':
        sql_makeup = f"select 员工编号 from 工作人员 where 所属部门='化妆部'"
        CURSOR.execute(sql_makeup)
        fetch_data = CURSOR.fetchall()
        makeup_id = fetch_data[0][0]
    ps_id = request.form.get('ps')
    if ps_id == 'rand':
        sql_ps = f"select 员工编号 from 工作人员 where 所属部门='后期部'"
        CURSOR.execute(sql_ps)
        fetch_data = CURSOR.fetchall()
        ps_id = fetch_data[0][0]
    meeting_time = request.form.get('meeting-time').replace('T', ' ')
    phone_number = request.form.get('phone_number')
    if request.form.get('packageA'):
        package = '套餐A'
    elif request.form.get('packageB'):
        package = '套餐B'
    else:
        package = '套餐C'
    product_info = {
        '预约摄影师编号': int(camera_id),
        '预约化妆师编号': int(makeup_id),
        '预约后期师编号': int(ps_id),
        '预约拍摄时间': meeting_time,
        '预约顾客联系方式': phone_number,
        '选择套餐类型': package,
        '摄影师接单状态': 0,
        '化妆师接单状态': 0,
        '后期师接单状态': 0
    }
    product_info_values = ''.join(str(value) + '+' for value in product_info.values())
    order_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    order_status = '已预约，等待接单'
    message = request.form.get('message')
    sql_insert_order = f"insert into 订单 (下单客户编号, 商品信息, 订单状态, 下单时间, 附属信息) " \
                 f"values ('{user_number}', '{product_info_values}', '{order_status}', '{order_time}', '{message}')"
    try:
        print(f"'{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 尝试插入数据 {sql_insert_order}'")
        CURSOR.execute(sql_insert_order)  # 执行插入语句
        CONN.commit()  # 提交数据
        print('插入成功......')
    except Exception as e:
        print(e)
        CONN.rollback()  # 发生错误则回滚

    return render_template('main.html', user_number = user_number)


@app.route('/main/order', methods=['GET', 'POST'])
def main_order():
    print(f"'{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 进入个人订单界面通过{request.method}'")
    user_number = request.args['user_number']
    sql = f"select 订单号, 商品信息, 订单状态 from 订单 where 下单客户编号 = {user_number}"
    CURSOR.execute(sql)
    fetch_data = CURSOR.fetchall()
    main_order_dict = []
    for line in fetch_data:
        product_info_dict = get_product_info(line[1])
        camera_id = product_info_dict['预约摄影师编号']
        makeup_id = product_info_dict['预约化妆师编号']
        ps_id = product_info_dict['预约后期师编号']
        appoint_time = product_info_dict['预约拍摄时间']
        package_type = product_info_dict['选择套餐类型']

        sql_camera = f"select 姓名 from 工作人员 where 员工编号={camera_id}"
        CURSOR.execute(sql_camera)
        fetch_data = CURSOR.fetchall()
        camera_name = fetch_data[0][0]

        sql_makeup = f"select 姓名 from 工作人员 where 员工编号={makeup_id}"
        CURSOR.execute(sql_makeup)
        fetch_data = CURSOR.fetchall()
        makeup_name = fetch_data[0][0]

        sql_ps = f"select 姓名 from 工作人员 where 员工编号={ps_id}"
        CURSOR.execute(sql_ps)
        fetch_data = CURSOR.fetchall()
        ps_name = fetch_data[0][0]

        main_order_dict.append({
            'appointment_idx': line[0],
            'camera_name': camera_name,
            'makeup_name': makeup_name,
            'ps_name': ps_name,
            'appoint_time': appoint_time,
            'order_status': line[2],
            'package_type': package_type
        })

    return render_template('main_order.html', user_number = user_number, main_order_dict = main_order_dict,
                           button_name1 = '取消订单', button_name2 = '催单')


@app.route('/main/info', methods = ['GET', 'POST'])
def main_info():
    print(f"'{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 进入个人消息界面通过{request.method}'")
    user_number = request.args['user_number']
    return render_template('main_info.html', user_number = user_number)


@app.route('/main/change', methods = ['GET', 'POST'])
def main_change():
    print(f"'{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 进入修改个人信息界面通过{request.method}'")
    user_number = request.args['user_number']
    sql = f"select * from 客户 where 客户编号='{user_number}'"
    CURSOR.execute(sql)
    fetch_data = CURSOR.fetchall()
    user_name = fetch_data[0][1]
    real_name = fetch_data[0][4]
    birth_date = fetch_data[0][6]
    phone_number = fetch_data[0][3]
    wechat_number = fetch_data[0][7]
    email = fetch_data[0][8]
    if request.method == 'GET':
        return render_template('main_change.html', user_number = user_number, user_name = user_name,
                               real_name = real_name, birth_date = birth_date, phone_number = phone_number,
                               wechat_number = wechat_number, email = email)
    print(request.form)
    new_user_name = request.form.get('user_name')
    new_real_name = request.form.get('real_name')
    if request.form.get('gender0'):
        new_gender = '男'
    else:
        new_gender = '女'
    new_birth_date = request.form.get('birth_date')
    if (not new_birth_date) or new_birth_date == '--':
        new_birth_date = '待完善'
    new_phone_number = request.form.get('phone_number')
    new_wechat_number = request.form.get('wechat_number')
    new_email = request.form.get('email')
    sql_change = f"update 客户 set " \
                 f"用户名 = '{new_user_name}', " \
                 f"真实姓名 = '{new_real_name}', " \
                 f"性别 = '{new_gender}', " \
                 f"出生日期 = '{new_birth_date}', " \
                 f"电话号码 = '{new_phone_number}', " \
                 f"微信号 = '{new_wechat_number}', " \
                 f"邮箱 = '{new_email}' " \
                 f"where 客户编号 = {user_number}"
    CURSOR.execute(sql_change)
    CONN.commit()  # 不提交无法在数据库内部进行修改
    return redirect(url_for('main_user', user_number = user_number), code = 301)


@app.route('/main/delete', methods = ['GET', 'POST'])
def main_delete():
    print(f"'{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 进入删除链接通过{request.method}'")
    print(request.args)
    user_number = request.args['user_number']
    appointment_idx = request.args['appointment_idx']
    sql_delete = f"delete from 订单 where 订单号='{appointment_idx}'"
    print(f'执行删除语句 - {sql_delete}')
    try:
        CURSOR.execute(sql_delete)
        CONN.commit()
        print('删除成功......')
    except Exception as e:
        print(e)
        CONN.rollback()
    return redirect(url_for('main_order', user_number = user_number), code = 301)


@app.route('/employee/login', methods = ['GET', 'POST'])
def employee_login():
    if request.method == 'GET':
        return render_template('employee_login.html', reforce = '请输入您的员工编号')

    employee_id = request.form.get('user_name')
    password = request.form.get('password')
    sql = f"select 登录密码 from 工作人员 where 员工编号='{employee_id}'"
    CURSOR.execute(sql)
    fetch_data = CURSOR.fetchall()
    if len(fetch_data) > 0:
        true_password = fetch_data[0][0]
        if str(password) == str(true_password):  # 此处我们选择将员工编号视作为员工密码
            return redirect(url_for('employee_main', employee_id = employee_id), code = 301)
        else:
            return render_template('employee_login.html', reforce = '您输入的员工编号或密码有误，请重新输入')
    else:
        return render_template('employee_login.html', reforce = '该员工不存在')


@app.route('/employee/main', methods = ['GET', 'POST'])
def employee_main():
    print(f"'{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 进入员工主界面通过{request.method}'")
    employee_id = request.args['employee_id']  # 通过get请求获取用户ID
    return render_template('employee_main.html', employee_id = employee_id)


@app.route('/employee/page', methods = ['GET', 'POST'])
def employee_page():
    print(f"'{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 进入员工个人信息页面通过{request.method}'")
    employee_id = request.args['employee_id']  # 通过get请求获取用户ID
    sql = f"select * from 工作人员 where 员工编号={employee_id}"
    CURSOR.execute(sql)
    fetch_data = CURSOR.fetchall()
    print(f'这里是查询到的员工信息: {fetch_data}')
    employee_name = fetch_data[0][1]
    employee_department = fetch_data[0][2]
    employee_phone = fetch_data[0][3]
    employee_wechat = fetch_data[0][4]
    employee_bank = fetch_data[0][5]
    employee_entry = fetch_data[0][6]
    return render_template(
        'employee_page.html', employee_id = employee_id, employee_name = employee_name,
        employee_department = employee_department, employee_phone = employee_phone,
        employee_wechat = employee_wechat, employee_bank = employee_bank, employee_entry = employee_entry
    )


@app.route('/employee/order', methods = ['GET', 'POST'])
def employee_order():
    department_map = {
        '摄影部': '预约摄影师编号',
        '化妆部': '预约化妆师编号',
        '后期部': '预约后期师编号'
    }
    print(f"'{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 进入员工消息界面通过{request.method}'")
    employee_id = request.args['employee_id']  # 通过get请求获取ID
    sql_employee_depart = f"select 所属部门 from 工作人员 where 员工编号={employee_id}"
    CURSOR.execute(sql_employee_depart)
    fetch_data = CURSOR.fetchall()
    employee_department = fetch_data[0][0]

    sql = f"select * from 订单"
    CURSOR.execute(sql)
    fetch_data = CURSOR.fetchall()
    info_list = []
    for line_info in fetch_data:
        product_dict = get_product_info(line_info[2])
        if int(employee_id) == int(product_dict[department_map[employee_department]]):
            if line_info[3] == '已预约，等待接单':
                info_list.append({
                    'meeting_time': product_dict["预约拍摄时间"],
                    'user_phone': product_dict['预约顾客联系方式'],
                    'package': product_dict['选择套餐类型'],
                    'order_status': line_info[3],
                    'button_name1': '接单',
                    'button_name2': '拒绝'
                })
            else:
                info_list.append({
                    'meeting_time': product_dict["预约拍摄时间"],
                    'user_phone': product_dict['预约顾客联系方式'],
                    'package': product_dict['选择套餐类型'],
                    'order_status': line_info[3],
                    'button_name1': '结单',
                    'button_name2': '拒绝'
                })
        print(info_list)
    return render_template('employee_order.html', employee_id = employee_id, info_list = info_list)


@app.route('/employee/info', methods = ['GET', 'POST'])
def employee_info():
    print(f"'{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 进入员工信息中心界面通过{request.method}'")
    employee_id = request.args['employee_id']  # 通过get请求获取用户ID
    return render_template('employee_info.html', employee_id = employee_id)


@app.route('/employee/equipment', methods = ['GET', 'POST'])
def employee_equipment():
    print(f"'{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 进入设备借还界面通过{request.method}'")
    employee_id = request.args['employee_id']  # 通过get请求获取用户ID
    return render_template('employee_equipment.html', employee_id = employee_id)


if __name__ == '__main__':
    HOST = 'localhost'
    USER = 'root'
    PASSWORD = 'zjszjs'
    DB = '数据库大作业'
    CHARSET = 'utf8'
    CONN = pymysql.connect(
        host = HOST,
        user = USER,
        password = PASSWORD,
        db = DB,
        charset = CHARSET
    )
    CURSOR = CONN.cursor()
    app.run()
