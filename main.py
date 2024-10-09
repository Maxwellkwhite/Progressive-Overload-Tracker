from flask import Flask, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, PasswordField
from wtforms.validators import DataRequired, Email
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import random
import stripe
import os
import smtplib
import jsonify

APP_NAME = 'ENTER HERE'
stripe.api_key = 'pk_test_51Q87D2HTbTE26Y4DuAB8Up8y2fFfhzM8ZGwLmSaMwLCkLzanKu5QrAxJxqK8MApNSyeGLTgMn2ExcQ0QDSKf66Z5005lRtW3rF'

app = Flask(__name__)
ckeditor = CKEditor(app)
Bootstrap5(app)
# app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')
app.config['SECRET_KEY'] = 'ABSCDE'

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", 'sqlite:///users.db')
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Create a form to register new users
class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired() ])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Sign Me Up!")

# Create a form to login existing users
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Let Me In!")

class ChangePassword(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    new_password = PasswordField("New Password", validators=[DataRequired()])
    submit = SubmitField("Change Password")

class Feedback(FlaskForm):
    feedback = StringField("Feedback", validators=[DataRequired()])
    submit = SubmitField("Provide Feedback")

class CreateSet(FlaskForm):
    name_of_set = StringField("Name of Set", validators=[DataRequired()])
    exercise1 = StringField("Exercise 1", validators=[DataRequired()])
    exercise2 = StringField("Exercise 2")
    exercise3 = StringField("Exercise 3")
    exercise4 = StringField("Exercise 4")
    exercise5 = StringField("Exercise 5")
    exercise6 = StringField("Exercise 6")
    exercise7 = StringField("Exercise 7")
    exercise8 = StringField("Exercise 8")
    submit = SubmitField("Create Set")

class AddExercise(FlaskForm):
    name_of_set = SelectField("Name of Set", validators=[DataRequired()])
    
    def __init__(self, *args, **kwargs):
        super(AddExercise, self).__init__(*args, **kwargs)
        with app.app_context():
            unique_sets = db.session.query(SetList.set_name).distinct().all()
            self.name_of_set.choices = [(set[0], set[0]) for set in unique_sets]
    new_exercise = StringField("Add Exercise", validators=[DataRequired()])
    submit = SubmitField("Add")

#user DB
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))
    premium_level: Mapped[int] = mapped_column(Integer)
    # date_of_signup: Mapped[Date] = mapped_column(Date)
    points: Mapped[int] = mapped_column(Integer)

class SetList(db.Model):
    __tablename__ = "set_lists"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Create Foreign Key, "users.id" the users refers to the tablename of User.
    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    set_name: Mapped[str] = mapped_column(String(250), unique=False, nullable=False)
    exercise: Mapped[int] = mapped_column(Integer, nullable=True)
    weight: Mapped[str] = mapped_column(String(250))
    reps: Mapped[str] = mapped_column(String(250))

with app.app_context():
    db.create_all()

@app.route('/', methods=["GET", "POST"])
def landing_page():
    return render_template("index.html")

@app.route('/workouts', methods=["GET", "POST"])
def workouts():
    form = AddExercise()
    result = db.session.execute(db.select(SetList).where(SetList.user_id == current_user.id))
    user_result = db.session.execute(db.select(User).where(User.id == current_user.id))
    user = user_result.scalar()
    exercises = result.scalars().all()
    return render_template("workouts.html", exercises=exercises, form=form, user=user)

@app.route('/create-set', methods=["GET", "POST"])
def create_set():
    form=CreateSet()
    if form.validate_on_submit():
        if form.exercise1.data:
            new_exercise = SetList(
                user_id=current_user.id,
                set_name=form.name_of_set.data,
                exercise=form.exercise1.data,
                weight=0,
                reps=0)
            db.session.add(new_exercise)
            db.session.commit()
        if form.exercise2.data:
            new_exercise = SetList(
                user_id=current_user.id,
                set_name=form.name_of_set.data,
                exercise=form.exercise2.data,
                weight=0,
                reps=0)
            db.session.add(new_exercise)
            db.session.commit()
        if form.exercise3.data:
            new_exercise = SetList(
                user_id=current_user.id,
                set_name=form.name_of_set.data,
                exercise=form.exercise3.data,
                weight=0,
                reps=0)
            db.session.add(new_exercise)
            db.session.commit()
        if form.exercise4.data:
            new_exercise = SetList(
                user_id=current_user.id,
                set_name=form.name_of_set.data,
                exercise=form.exercise4.data,
                weight=0,
                reps=0)
            db.session.add(new_exercise)
            db.session.commit()
        if form.exercise5.data:
            new_exercise = SetList(
                user_id=current_user.id,
                set_name=form.name_of_set.data,
                exercise=form.exercise5.data,
                weight=0,
                reps=0)
            db.session.add(new_exercise)
            db.session.commit()
        if form.exercise6.data:
            new_exercise = SetList(
                user_id=current_user.id,
                set_name=form.name_of_set.data,
                exercise=form.exercise6.data,
                weight=0,
                reps=0)
            db.session.add(new_exercise)
            db.session.commit()
        if form.exercise7.data:
            new_exercise = SetList(
                user_id=current_user.id,
                set_name=form.name_of_set.data,
                exercise=form.exercise7.data,
                weight=0,
                reps=0)
            db.session.add(new_exercise)
            db.session.commit()
        if form.exercise8.data:
            new_exercise = SetList(
                user_id=current_user.id,
                set_name=form.name_of_set.data,
                exercise=form.exercise8.data,
                weight=0,
                reps=0)
            db.session.add(new_exercise)
            db.session.commit()
        g_user = current_user.get_id()
        return redirect(url_for("workouts"))
    return render_template("create_sets.html", form=form)

@app.route("/weight_update/<int:id>", methods =["GET", "POST"])
def weight_update(id):
    if request.method == "POST":
        with app.app_context():
            completed_update = db.session.execute(db.select(SetList).where(SetList.id == id)).scalar()
            old_weight = float(completed_update.weight)
            new_weight = float(request.form.get("weight"))
            if new_weight > old_weight:
                current_user.points += 1
            completed_update.weight = new_weight
            db.session.commit()
        return redirect(url_for('workouts'))
    
@app.route("/reps_update/<int:id>", methods =["GET", "POST"])
def reps_update(id):
    if request.method == "POST":
        with app.app_context():
            completed_update = db.session.execute(db.select(SetList).where(SetList.id == id)).scalar()
            old_reps = int(completed_update.reps)
            new_reps = int(request.form.get("reps"))
            if new_reps > old_reps:
                current_user.points += 1
            completed_update.reps = new_reps
            db.session.commit()
        return redirect(url_for('workouts'))
    
@app.route("/delete/<int:id>", methods =['POST','GET'])
def delete_exercise(id):
    if request.method == "POST":
        exercise_to_delete = db.get_or_404(SetList, id)
        db.session.delete(exercise_to_delete)
        db.session.commit()
        return redirect(url_for('workouts'))
    
@app.route("/add_exercise", methods =['POST','GET'])
def add_exercise():
    form = AddExercise()
    if form.validate_on_submit():
        new_exercise = SetList(
            user_id=current_user.id,
            set_name=request.form.get('name_of_set'),
            exercise=request.form.get('new_exercise'),
            weight=0,
            reps=0)
        db.session.add(new_exercise)
        db.session.commit()
        return redirect(url_for('workouts'))

@app.route('/leaderboard/<int:page>', methods =['POST','GET'])
def leaderboard(page):
    # Set the number of items per page
    per_page = 10
    
    # Query users, ordered by points in descending order, with pagination
    users = db.session.execute(db.select(User).order_by(User.points.desc())
                               .offset((page - 1) * per_page).limit(per_page)).scalars()
    
    # Get total number of users for pagination
    total_users = db.session.execute(db.select(db.func.count(User.id))).scalar()
    
    # Convert the result to a list for easier handling in the template
    leaderboard_data = [
        {'name': user.name, 'points': user.points}
        for user in users
    ]
    
    # Calculate total pages
    total_pages = (total_users + per_page - 1) // per_page
    
    return render_template('leaderboard.html', leaderboard=leaderboard_data,
                           page=page, total_pages=total_pages)

@app.route('/user/<int:user_id>')
@login_required
def user_page(user_id):
    user = db.get_or_404(User, user_id)
    
    # Get user's exercises
    exercises = db.session.execute(db.select(SetList).where(SetList.user_id == user_id)).scalars().all()
    
    # Group exercises by set name
    exercise_sets = {}
    for exercise in exercises:
        if exercise.set_name not in exercise_sets:
            exercise_sets[exercise.set_name] = []
        exercise_sets[exercise.set_name].append(exercise)
    
    return render_template('user_page.html', user=user, exercise_sets=exercise_sets)

@app.route('/payment_page', methods=["GET", "POST"])
def payment_page():
    return render_template('price_page.html')

@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():

        # Check if user email is already present in the database.
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        if user:
            # User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password,
            premium_level=0,
            points = 0
        )
        db.session.add(new_user)
        db.session.commit()
        # This line will authenticate the user with Flask-Login
        login_user(new_user)
        return redirect(url_for("payment_page"))
    return render_template("register.html", form=form, current_user=current_user)

@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        password = form.password.data
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        # Note, email in db is unique so will only have one result.
        user = result.scalar()
        # Email doesn't exist
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        # Password incorrect
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('workouts'))

    return render_template("login.html", form=form, current_user=current_user)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('landing_page'))

#for test of Stripe
YOUR_DOMAIN = 'http://127.0.0.1:5002'
#for live of Stripe
DOMAIN2 = 'https://bingebuddy.us'

@app.route('/create-checkout-session', methods=['POST', 'GET'])
def create_checkout_session():
    try:
        # stripe.Coupon.create(
        # id="free-test",
        # percent_off=100,
        # )
        # stripe.PromotionCode.create(
        # coupon="free-test",
        # code="FREETEST",
        # )
        checkout_session = stripe.checkout.Session.create(
            line_items=[{
                'price_data': {
                'currency': 'usd',
                'product_data': {
                'name': 'Movie Access',},
                'unit_amount': 299,},
                'quantity': 1,}],
            mode='payment',
            allow_promotion_codes = True,
            success_url=YOUR_DOMAIN + '/success',
            cancel_url=YOUR_DOMAIN + '/cancel',)
    except Exception as e:
        return str(e)
    return redirect(checkout_session.url, code=303)

@app.route('/cancel', methods=['POST', 'GET'])
def cancel_session():
    return redirect(url_for('INSERT HERE'))

@app.route('/success', methods=['POST', 'GET'])
def success_session():
    with app.app_context():
        g_user = current_user.get_id()
        completed_update = db.session.execute(db.select(User).where(User.id == g_user)).scalar()
        completed_update.premium_level = 1
        db.session.commit()
    return redirect(url_for('INSERT HERE'))

@app.route('/privacy-policy', methods=['POST', 'GET'])
def privacy_policy():
    return render_template("privacy_policy.html")

@app.route('/terms-and-conditions', methods=['POST', 'GET'])
def terms_and_conditions():
    return render_template("terms_and_conditions.html")

@app.route('/change-password', methods=["GET", "POST"])
def change_password():
    form = ChangePassword()
    g_user = current_user.get_id()
    if form.validate_on_submit():
        password = form.password.data
        new_password = form.new_password.data
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        # Note, email in db is unique so will only have one result.
        user = result.scalar()
        # Email doesn't exist
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('change_password'))
        # Password incorrect
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('change_password'))
        else:
            completed_update = db.session.execute(db.select(User).where(User.id == g_user)).scalar()
            completed_update.password = generate_password_hash(
                    new_password,
                    method='pbkdf2:sha256',
                    salt_length=8)
            db.session.commit()
            flash('Password Changed')
            return redirect(url_for('change_password'))

    return render_template("change_password.html", form=form, current_user=current_user)

@app.route('/feedback', methods=['POST', 'GET'])
def feedback():
    form=Feedback()
    if form.validate_on_submit():
        feedback = form.feedback.data
        my_email = os.environ.get('FROM_EMAIL')
        password = os.environ.get('EMAIL_PASS')
        connection = smtplib.SMTP("smtp.gmail.com", 587)
        connection.starttls()
        connection.login(user=my_email, password=password)
        connection.sendmail(from_addr=my_email, 
                            to_addrs=os.environ.get('TO_EMAIL'), 
                            msg=f"Subject:Feedback from {APP_NAME}!\n\nFeedback: {feedback}",
                            )
        connection.close()
        flash('Feedback received! Thank you for taking the time to help.')
    return render_template("feedback.html", form=form)



if __name__ == "__main__":
    app.run(debug=True, port=5002)
