from flask import render_template, redirect, url_for, request, flash
from TAX import app, db, bcrypt
from TAX.models import User
from TAX.pit import PersonalMonthlyIncome
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField
from wtforms.validators import InputRequired
from datetime import datetime, timedelta
from flask import jsonify

def place_value(number):
    return ("{:,}".format(number))

class PITForm(FlaskForm):
    gross = StringField('Thu nhập hàng tháng (lương, các khoản phụ cấp, làm ngoài giờ...)', validators=[InputRequired()], default=0)
    contract = StringField('Lương hợp đồng (căn cứ đóng bảo hiểm)', validators=[InputRequired()], default=0)
    dependant = StringField('Số người phụ thuộc', validators=[InputRequired()], default=0)
    region = SelectField(
        'Chọn vùng',
        choices=[
            ('1', 'Vùng 1 Hà Nội, Quảng Ninh, Đà Nẵng, Tp.HCM, Bình Dương, Đồng Nai, Vũng Tàu'),
            ('2', 'Vùng 2 Hải Phòng, Vĩnh Phúc, Thái Nguyên, Khánh Hoà, Bình Phước, Tây Ninh, Long An, An Giang, Cần Thơ, Cà Mau.'),
            ('3', 'Vùng 3 Hà Tây, Bắc Ninh, Hải Dương, Hưng Yên, Huế, Bình Định, Gia Lai, Đắc Lắc, Lâm Đồng, Ninh Thuận, Bình Thuận, ĐồngTháp, Tiền Giang, Vĩnh Long, Bến Tre, Kiên Giang, Hậu Giang, Sóc Trăng, Bạc Liêu'),
            ('4', 'Vùng 4 các tỉnh còn lại.')
        ]
    )

# @app.route('/', methods=['GET', 'POST'])
# @app.route('/index', methods=['GET', 'POST'])
# def index():
#     form = PITForm()
#     if request.method == 'GET':
#         return render_template('index.html', form=form)

#     elif request.method == 'POST' and form.validate_on_submit():
#         gross = int(form.gross.data)
#         contract = int(form.contract.data)
#         dependant = int(form.dependant.data)
#         region = int(form.region.data)

#         income = PersonalMonthlyIncome(gross, contract, dependant, region)
#         data = [
#             {'Name': 'Thu nhập trong tháng (lương, phụ cấp, ...)', 'Value': place_value(income.gross)},
#             {'Name': 'Lương hợp đồng (căn cứ tính bảo hiểm)', 'Value': place_value(income.contract)},
#             {'Name': 'Mức lương tối thiểu theo vùng', 'Value': place_value(income.minimum_salary())},
#             {'Name': 'Mức tối đa đóng BHXH (8%), BHYT (1.5%)', 'Value': place_value(income.insurance_based_calculation())},
#             {'Name': 'Mức tối đa đóng BHTN (1%)', 'Value': place_value(income.unemployment_based_calculation())},
#             {'Name': 'Bảo hiểm xã hội', 'Value': place_value(income.social_insurance())},
#             {'Name': 'Bảo hiểm y tế', 'Value': place_value(income.health_insurance())},
#             {'Name': 'Bảo hiểm thất nghiệp', 'Value': place_value(income.unemployment())},
#             {'Name': 'Giảm trừ cá nhân', 'Value': place_value(income.personal_deduction())},
#             {'Name': 'Giảm trừ người phụ thuộc', 'Value': place_value(income.dependant_deduction())},
#             {'Name': 'Thu nhập chịu thuế', 'Value': place_value(income.taxable_income())},
#             {'Name': 'Thuế thu nhập cá nhân', 'Value': place_value(income.personal_income_tax())},
#             {'Name': 'Tiền lương thực nhận (net income)', 'Value': place_value(income.net_income())}
#         ]

#         return render_template('index.html', data=data, form=form)

@app.route('/')
@app.route('/home',methods=["GET", "POST"])
def home():  
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            next_page = request.args.get('next')
            # if(not user.topics):
            #     topic = Topic(user_id = user.id)
            #     db.session.add(topic)
            #     db.session.commit()
            return redirect(url_for('admin', user=user.id)) if user.role == 'admin' else redirect(url_for('tax', user=user.id))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('home.html')

# @app.route('/login', methods=["GET", "POST"])
# def login():
    
#     return render_template('login.html')
    
@app.route('/sigup', methods=["GET", "POST"])
def sigup():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Account already exists', 'warning')
        elif password != confirm_password:
            flash('Password does not match', 'warning')
        else:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            user = User(username=username, email=email, password=hashed_password)
            db.session.add(user)
            db.session.commit()
            flash('Your account has been created! You are now able to log in', 'success')
            return redirect(url_for('home'))
    return render_template('sigup.html')