#!/usr/bin/env python
from flask import Flask, render_template, request, jsonify, make_response, session, redirect, url_for, send_file
from flask_wtf import Form
from wtforms import StringField, SelectField, PasswordField, IntegerField, DateField, RadioField
from wtforms.validators import InputRequired, Email, Length, Regexp
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from pit import * 
from functools import wraps
import pandas as pd
from io import BytesIO
from datetime import datetime

DEBUG = True
app = Flask(__name__)
Bootstrap(app)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = '7d441f27d441f27567d441f2b6176a'

# User data simulation
taxcodes = {}
taxrecords = []

# Decorator for login required
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'taxcode' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Format number with thousand separator
def place_value(number): 
    return ("{:,}".format(number)) 

class PITForm(Form):
    codeorpay = StringField('Mã tổ chức thu nhập')
    nameorpay = StringField('Tên tổ chức trả thu nhập')
    gross = StringField('Thu nhập hàng tháng (lương, các khoản phụ cấp, làm ngoài giờ...)', validators=[InputRequired()], default=0)
    contract = StringField('Lương hợp đồng (căn cứ đóng bảo hiểm)', validators=[InputRequired()], default=0)
    dependant = StringField('Số người phụ thuộc', validators=[InputRequired()], default=0)
    region = SelectField(
        'Chọn vùng',
        choices = [
            ('1', 'Vùng 1 Hà Nội, Quảng Ninh, Đà Nẵng, Tp.HCM, Bình Dương, Đồng Nai, Vũng Tàu'), 
            ('2', 'Vùng 2 Hải Phòng, Vĩnh Phúc, Thái Nguyên, Khánh Hoà, Bình Phước, Tây Ninh, Long An, An Giang, Cần Thơ, Cà Mau.'), 
            ('3', 'Vùng 3 Hà Tây, Bắc Ninh, Hải Dương, Hưng Yên, Huế, Bình Định, Gia Lai, Đắc Lắc, Lâm Đồng, Ninh Thuận, Bình Thuận, ĐồngTháp, Tiền Giang, Vĩnh Long, Bến Tre, Kiên Giang, Hậu Giang, Sóc Trăng, Bạc Liêu'), 
            ('4', 'Vùng 4 các tỉnh còn lại.')]
    )

class LoginForm(FlaskForm):
    taxcode = StringField('Mã số thuế', validators=[InputRequired(), Length(max=10)])
    password = PasswordField('Mật khẩu', validators=[InputRequired(), Length(min=8, max=80)])

class RegisterForm(FlaskForm):
    taxcode = StringField('Mã số thuế', validators=[InputRequired(), Length(max=10)])
    username = StringField('Họ tên', validators=[InputRequired(), Length(min=1, max=80)])
    password = PasswordField('Mật khẩu', validators=[InputRequired(), Length(min=8, max=80)])
    email = StringField('Email', validators=[
        InputRequired(message="Vui lòng nhập email"), 
        Email(message="Email không hợp lệ"), 
        Length(max=50, message="Email không được quá 50 ký tự")
    ])
    birth_date = DateField('Ngày sinh (date/month/year)', validators=[InputRequired(message="Vui lòng nhập ngày sinh")])
    gender = RadioField('Giới tính', choices=[('male', 'Nam'), ('female', 'Nữ')], validators=[InputRequired(message="Vui lòng chọn giới tính")])
    document_type = SelectField('Loại giấy tờ', choices=[('cmnd', 'Chứng minh thư nhân dân'), ('cccd', 'Căn cước công dân'), ('hc', 'Hộ chiếu')], validators=[InputRequired(message="Vui lòng chọn loại giấy tờ")])
    document_number = StringField('Số giấy tờ', validators=[
        InputRequired(message="Vui lòng nhập số giấy tờ"), 
        Length(max=12, message="Số giấy tờ không được quá 12 chữ số"),
        Regexp('^[0-9]*$', message="Số giấy tờ chỉ được chứa các chữ số")
    ])
    phone_number = StringField('Số điện thoại', validators=[
        InputRequired(message="Vui lòng nhập số điện thoại"), 
        Length(max=10, message="Số điện thoại không được quá 10 chữ số"),
        Regexp('^[0-9]*$', message="Số điện thoại chỉ được chứa các chữ số")
    ])

@app.route('/index')
@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    form = PITForm()
    global taxrecords

    if request.method == 'GET':
        return render_template('index.html', form=form)

    elif request.method == 'POST':
        codeorpay = request.form.get('codeorpay')
        nameorpay = request.form.get('nameorpay')
        gross = int(request.form['gross'])
        contract = int(request.form['contract'])
        dependant = int(request.form['dependant'])
        region = int(request.form['region'])

        income = PersonalMonthlyIncome(gross,contract,dependant,region)
        #return str(income.personal_income_tax()), 200

        data = [
            {'Name':'Thu nhập trong tháng (lương, phụ cấp, ...)', 'Value':place_value(income.gross)},
            {'Name':'Lương hợp đồng (căn cứ tính bảo hiểm)', 'Value':place_value(income.contract)},
            {'Name':'Mức lương tối thiểu theo vùng', 'Value':place_value(income.minimum_salary())},
            {'Name':'Mức tối đa đóng BHXH (8%), BHYT (1.5%)', 'Value':place_value(income.insurance_based_calculation())},
            {'Name':'Mức tối đa đóng BHTN (1%)', 'Value':place_value(income.unemployment_based_calculation())},
            {'Name':'Bảo hiểm xã hội', 'Value':place_value(income.social_insurance())},
            {'Name':'Bảo hiểm y tế', 'Value':place_value(income.health_insurance())},
            {'Name':'Bảo hiểm thất nghiệp', 'Value':place_value(income.unemployment())},
            {'Name':'Giảm trừ cá nhân', 'Value':place_value(income.personal_deduction())},
            {'Name':'Giảm trừ người phụ thuộc', 'Value':place_value(income.dependant_deduction())},
            {'Name':'Thu nhập chịu thuế', 'Value':place_value(income.taxable_income())},
            {'Name':'Thuế thu nhập cá nhân', 'Value':place_value(income.personal_income_tax())},
            {'Name':'Tiền lương thực nhận (net income)', 'Value':place_value(income.net_income())}
        ]
        if 'submit_tax' in request.form:
            record = {
                'codeorpay': request.form['codeorpay'],
                'nameorpay': request.form['nameorpay'],
                'gross': place_value(income.gross),
                'contract': place_value(income.contract),
                'dependant': request.form['dependant'],
                'region': request.form['region'],
                'social_insurance': place_value(income.social_insurance()),
                'health_insurance': place_value(income.health_insurance()),
                'unemployment': place_value(income.unemployment()),
                'dependant_deduction': place_value(income.dependant_deduction()),
                'taxable_income': place_value(income.taxable_income()),
                'personal_income_tax': place_value(income.personal_income_tax()),
                'net_income': place_value(income.net_income())
            }
            taxrecords.append(record)

        return render_template('index.html', data=data, form=form, taxrecords=taxrecords)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if request.method == 'GET':
        return render_template('login.html', form=form)

    elif request.method == 'POST':
        taxcode = request.form.get('taxcode')
        password = request.form.get('password')

        if taxcode in taxcodes and taxcodes[taxcode]['password'] == password:
            session['taxcode'] = taxcode
            return redirect(url_for('index'))

        return '<h1>Invalid taxcode or password</h1>'

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if request.method == 'GET':
        return render_template('register.html', form=form)

    elif request.method == 'POST':
        taxcode = request.form.get('taxcode')
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        birth_date = request.form.get('birth_date')
        gender = request.form.get('gender')
        document_type = request.form.get('document_type')
        document_number = request.form.get('document_number')
        phone_number = request.form.get('phone_number')

        if taxcode not in taxcodes:
            taxcodes[taxcode] = {
                'username': username,
                'password': password,
                'email': email,
                'birth_date': birth_date,
                'gender': gender,
                'document_type': document_type,
                'document_number': document_number,
                'phone_number': phone_number
            }
            return redirect(url_for('login'))

        return '<h1>Mã số thuế đã tồn tại</h1>'

    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    session.pop('taxcode', None)
    return redirect(url_for('login'))

@app.route('/thongke')
@login_required
def thongke():
    global taxrecords
    return render_template('thongke.html', taxrecords=taxrecords)

@app.route('/download_excel')
@login_required
def download_excel():
    global taxrecords
    df = pd.DataFrame(taxrecords)
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Thống kê thuế', index=False)
    writer.close()
    output.seek(0)
    today = datetime.today().strftime('%Y-%m-%d')
    return send_file(output, download_name=f'Thong_ke_thue_{today}.xlsx', as_attachment=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
