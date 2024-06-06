from TAX import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(60), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    # topics = db.relationship('Topic', backref='userdetail', lazy=True)
    def __repr__(self):
        return f"User('{self.id}', '{self.username}', '{self.email}', '{self.password}')"