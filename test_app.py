import pytest
from selenium import webdriver
from pit import PersonalMonthlyIncome
from main import app


class TestPersonalIncomeTax:

    @pytest.fixture(scope="module")
    def client(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  # Run the browser headless
        driver = webdriver.Chrome(options=options)
        yield app.test_client()
        driver.quit()

    def test_register(self, client):
        response = client.post('/register', data={
            'taxcode': '1234567890',
            'username': 'John Doe',
            'password': 'securepassword',
            'email': 'john@example.com',
            'birth_date': '1990-01-01',
            'gender': 'male',
            'document_type': 'cmnd',
            'document_number': '123456789123',
            'phone_number': '1234567890'
        }, follow_redirects=True)
        assert b'Redirecting...' in response.data

    def test_login(self, client):
        response = client.post('/login', data={
            'taxcode': '1234567890',
            'password': 'securepassword'
        }, follow_redirects=True)
        assert b'index' in response.data

    def test_logout(self, client):
        response = client.get('/logout', follow_redirects=True)
        assert b'login' in response.data

    def test_minimum_salary(self):
        income = PersonalMonthlyIncome(gross=0, contract=0, dependant=0, region=1)
        assert income.minimum_salary() == 4680000

    def test_insurance_based_calculation(self):
        income = PersonalMonthlyIncome(gross=0, contract=2000000, dependant=0, region=1)
        assert income.insurance_based_calculation() == 3600000

    def test_unemployment_based_calculation(self):
        income = PersonalMonthlyIncome(gross=0, contract=2000000, dependant=0, region=1)
        assert income.unemployment_based_calculation() == 3600000

    def test_social_insurance(self):
        income = PersonalMonthlyIncome(gross=0, contract=2000000, dependant=0, region=1)
        assert income.social_insurance() == 288000

    def test_health_insurance(self):
        income = PersonalMonthlyIncome(gross=0, contract=2000000, dependant=0, region=1)
        assert income.health_insurance() == 54000

    def test_unemployment(self):
        income = PersonalMonthlyIncome(gross=0, contract=2000000, dependant=0, region=1)
        assert income.unemployment() == 36400

    def test_personal_deduction(self):
        income = PersonalMonthlyIncome(gross=0, contract=0, dependant=0, region=1)
        assert income.personal_deduction() == 11000000

    def test_dependant_deduction(self):
        income = PersonalMonthlyIncome(gross=0, contract=0, dependant=2, region=1)
        assert income.dependant_deduction() == 7200000

    def test_taxable_income(self):
        income = PersonalMonthlyIncome(gross=3000000, contract=2000000, dependant=0, region=1)
        assert income.taxable_income() == 2465000

    def test_personal_income_tax(self):
        income = PersonalMonthlyIncome(gross=3000000, contract=2000000, dependant=0, region=1)
        assert income.personal_income_tax() == 34500

    def test_net_income(self):
        income = PersonalMonthlyIncome(gross=3000000, contract=2000000, dependant=0, region=1)
        assert income.net_income() == 2980500
