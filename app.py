from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from datetime import datetime, timedelta
from sqlalchemy import or_
from collections import defaultdict
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "dev-secret")
db_url = os.environ.get("DATABASE_URL")

if db_url:
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
else:
    db_url = "sqlite:///quiz.db"

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'



START_TIME = datetime(2026, 3, 22, 6, 0, 0)      # ВРЕМЯ СТАРТА
END_TIME   = datetime(2026, 3, 27, 23, 59, 0)    # ВРЕМЯ ОКОНЧАНИЯ
REMINDER_TIME = datetime(2026, 3, 23, 8, 0, 0)   # 14 ноября, 17:00
START_TEXT = ' 23 марта, 08:00'




# ---------------- Модели ----------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    block = db.Column(db.String(100), nullable=False)
    text = db.Column(db.String(500), nullable=False)
    correct_answer = db.Column(db.String(200), nullable=True)


class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    text = db.Column(db.String(500))
    link = db.Column(db.Text)

    user = db.relationship('User', backref='answers')
    question = db.relationship('Question', backref='answers')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------------- Маршруты ----------------
with app.app_context():
    db.create_all()

    

@app.route('/')
def index():
    return render_template('main.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form['username']
        user = User.query.filter(
            or_(User.username == identifier, User.email == identifier)
	).first()
        if user and user.password == request.form['password']:
            login_user(user)
            return redirect(url_for('blocks'))
        else:
            flash("Неверный логин или пароль")
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash("Такой логин уже существует")
        elif User.query.filter_by(email=email).first():
            flash("Этот email уже зарегистрирован")
        else:
            user = User(username=username, email=email, password=password)
            db.session.add(user)
            db.session.commit()
            flash("Регистрация успешна! Теперь войдите.")
            return redirect(url_for('login'))
    return render_template('register.html')


@app.route("/dashboard")
@login_required
def dashboard():
    answers = (
        db.session.query(Answer, Question)
        .join(Question, Answer.question_id == Question.id)
        .filter(Answer.user_id == current_user.id)
        .all()
    )
    grouped = defaultdict(list)
    for ans, q in answers:
    	grouped[q.block].append((ans, q))
    	
    return render_template("dashboard.html", grouped_answers=grouped)

@app.route('/edit_answer/<int:answer_id>', methods=['GET', 'POST'])
@login_required
def edit_answer(answer_id):
    answer = Answer.query.get_or_404(answer_id)
    if answer.user_id != current_user.id:
        flash("Вы не можете редактировать чужие ответы.")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        answer.text = request.form['text'][:500]
        answer.link = request.form['link']
        db.session.commit()
        flash("Ответ обновлён.")
        return redirect(url_for('dashboard'))

    return render_template('edit_answer.html', answer=answer)

@app.route("/blocks")
@login_required
def blocks():
    now = datetime.now()

    #До начала чемпионата
    if now < START_TIME:
        flash("Задания будут доступны" + START_TEXT)
        return redirect(url_for('index'))

    #После окончания чемпионата
    if now > END_TIME:
        flash("Чемпионат завершён")
        return redirect(url_for('index'))
    
    # Загружаем все уникальные блоки из базы
    blocks = db.session.query(Question.block).distinct().all()
    blocks = [b[0].strip() for b in blocks if b[0] and b[0].strip()]
    return render_template("blocks.html", blocks=blocks)



@app.route("/block/<block_name>")
@login_required
def show_block(block_name):
    now = datetime.now()
    if now < START_TIME or now > END_TIME:
        flash("Доступ к заданиям ограничен по времени.")
        return redirect(url_for('index'))

    questions = Question.query.filter_by(block=block_name).all()

    user_answers = {
        a.question_id: a
        for a in Answer.query.filter_by(user_id=current_user.id).all()
    }

    return render_template(
        "block.html",
        block=block_name,
        questions=questions,
        user_answers=user_answers
    )

@app.route('/answer/<int:qid>/<block_name>', methods=['POST'])
@login_required
def submit_answer(qid, block_name):
    answer_text = request.form['answer'][:500]
    answer_link = request.form['link']
    existing = Answer.query.filter_by(user_id=current_user.id, question_id=qid).first()
    if existing:
        existing.text = answer_text
        existing.link = answer_link
    else:
        ans = Answer(user_id=current_user.id, question_id=qid, text=answer_text, link=answer_link)
        db.session.add(ans)
    db.session.commit()
    flash("Ответ сохранён")
    return redirect(url_for('show_block', block_name=block_name))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта")
    return redirect(url_for('login'))


@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash("Доступ запрещён")
        return redirect(url_for('dashboard'))
    answers = Answer.query.all()
    return render_template('admin.html', answers=answers)
    

if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
