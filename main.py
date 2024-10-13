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
import datetime




APP_NAME = 'ProgressiveLift'
stripe.api_key = os.environ.get('STRIPE_API')

app = Flask(__name__)
ckeditor = CKEditor(app)
Bootstrap5(app)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')

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
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Sign Me Up!")

# Create a form to login existing users
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Let Me In!")

class ChangePassword(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    new_password = PasswordField("New Password", validators=[DataRequired()])
    submit = SubmitField("Change Password")

class Feedback(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    feedback = StringField("Feedback", validators=[DataRequired()])
    submit = SubmitField("Provide Feedback")

class CreateSet(FlaskForm):
    name_of_set = StringField("Name of Set", validators=[DataRequired()])
    exercise1 = StringField("Exercise 1", validators=[DataRequired()])
    exercise2 = StringField("Exercise 2")
    exercise3 = StringField("Exercise 3")
    exercise4 = StringField("Exercise 4")
    exercise5 = StringField("Exercise 5")
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
    date_of_signup: Mapped[Date] = mapped_column(Date)
    end_date_premium: Mapped[Date] = mapped_column(Date)
    points: Mapped[int] = mapped_column(Integer)
    weekly_points: Mapped[int] = mapped_column(Integer)
    monthly_points: Mapped[int] = mapped_column(Integer)
    daily_points: Mapped[int] = mapped_column(Integer)
    last_weekly_reset: Mapped[Date] = mapped_column(Date)
    last_monthly_reset: Mapped[Date] = mapped_column(Date)
    last_daily_reset: Mapped[Date] = mapped_column(Date)

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
@login_required
def workouts():
    form = AddExercise()
    form2 = CreateSet()
    # Get the current date
    current_date = datetime.date.today()
    
    # Check if the user is logged in and their premium status
    if current_user.end_date_premium < current_date:
        current_user.premium_level = 0
    
    # Reset weekly points if a week has passed
    if (current_date - current_user.last_weekly_reset).days >= 7:
        current_user.weekly_points = 0
        current_user.last_weekly_reset = current_date
    
    # Reset monthly points if a month has passed
    if current_date.month != current_user.last_monthly_reset.month or current_date.year != current_user.last_monthly_reset.year:
        current_user.monthly_points = 0
        current_user.last_monthly_reset = current_date
    
    # Reset daily points if a day has passed
    if current_date > current_user.last_daily_reset:
        current_user.daily_points = 0
        current_user.last_daily_reset = current_date
    
    db.session.commit()

    result = db.session.execute(db.select(SetList).where(SetList.user_id == current_user.id))
    user_result = db.session.execute(db.select(User).where(User.id == current_user.id))
    user = user_result.scalar()
    exercises = result.scalars().all()
    return render_template("workouts.html", exercises=exercises, form=form, user=user, form2=form2)

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
            if new_weight > old_weight and old_weight != 0:
                current_user.points += 1
                current_user.weekly_points += 1
                current_user.monthly_points += 1
                current_user.daily_points += 1
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
                current_user.weekly_points += 1
                current_user.monthly_points += 1
                current_user.daily_points += 1
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

@app.route('/leaderboard', methods =['POST','GET'])
def leaderboard():
    # Set the number of items per page
    per_page = 10
    
    # Get the current page number from the request, defaulting to 1
    page = request.args.get('page', 1, type=int)
    
    # Query users, ordered by points in descending order, with pagination
    users = db.session.execute(db.select(User).order_by(User.points.desc())
                               .offset((page - 1) * per_page).limit(per_page)).scalars()
    
    # Get total number of users for pagination
    total_users = db.session.execute(db.select(db.func.count(User.id))).scalar()
    
    # Convert the result to a list for easier handling in the template
    leaderboard_data = []
    for user in users:
        # Count the total exercises for each user
        total_exercises = db.session.execute(db.select(db.func.count(SetList.id))
                                             .where(SetList.user_id == user.id)).scalar()
        
        # Find the best lift (exercise with the most weight) for each user
        best_lift = db.session.execute(db.select(SetList)
                                       .where(SetList.user_id == user.id)
                                       .order_by(SetList.weight.desc())
                                       .limit(1)).scalar()
        
        best_lift_info = f"{best_lift.exercise} ({best_lift.weight})" if best_lift else "N/A"
        
        leaderboard_data.append({
            'name': user.name,
            'points': user.points,
            'weekly_points': user.weekly_points,
            'monthly_points': user.monthly_points,
            'daily_points': user.daily_points,
            'total_exercises': total_exercises,
            'best_lift': best_lift_info
        })
    
    # Calculate total pages
    total_pages = (total_users + per_page - 1) // per_page
    
    # Calculate next page number
    next_page = page + 1 if page < total_pages else None
    
    return render_template('leaderboard.html', leaderboard=leaderboard_data,
                           page=page, total_pages=total_pages, next_page=next_page)

@app.route('/user', methods =['POST','GET'])
@login_required
def user_page():
    user = current_user
    # Get user's exercises
    exercises = db.session.execute(db.select(SetList).where(SetList.user_id == user.id)).scalars().all()
    
    # Group exercises by set name
    exercise_sets = {}
    for exercise in exercises:
        if exercise.set_name not in exercise_sets:
            exercise_sets[exercise.set_name] = []
        exercise_sets[exercise.set_name].append(exercise)
    
    return render_template('user_page.html', user=user, exercise_sets=exercise_sets)


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
            date_of_signup=datetime.date.today(),
            end_date_premium=datetime.date.today(),
            premium_level=0,
            points = 0,
            weekly_points = 0,
            monthly_points = 0,
            daily_points = 0,
            last_weekly_reset = datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday() + 1),
            last_monthly_reset = datetime.date.today().replace(day=1),
            last_daily_reset = datetime.date.today(),)
        db.session.add(new_user)
        db.session.commit()
        # This line will authenticate the user with Flask-Login
        login_user(new_user)
        return redirect(url_for("price_page"))
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
DOMAIN2 = 'https://progressivelift.com'

@app.route('/price_page', methods=["GET", "POST"])
def price_page():
    return render_template('price_page.html')

@app.route('/create-checkout-session', methods=['POST', 'GET'])
def create_checkout_session():
    plan = request.args.get('plan')
    try:
        stripe.Coupon.create(
        id="free-test",
        percent_off=100,
        )
        stripe.PromotionCode.create(
        coupon="free-test",
        code="FREETEST",
        )
        if plan == 'year':
            price = 1999  # $19.99
            product_name = 'Yearly Access'
        elif plan == 'life':
            price = 2999  # $29.99
            product_name = 'Lifetime Access'
        else:
            return "Invalid plan selected", 400

        checkout_session = stripe.checkout.Session.create(
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': product_name,
                    },
                    'unit_amount': price,
                },
                'quantity': 1,
            }],
            mode='payment',
            allow_promotion_codes=True,
            success_url=DOMAIN2 + f'/success?plan={plan}',
            cancel_url=DOMAIN2 + '/cancel',
        )
    except Exception as e:
        return str(e)
    return redirect(checkout_session.url, code=303)

@app.route('/cancel', methods=['POST', 'GET'])
def cancel_session():
    return redirect(url_for('price_page'))

@app.route('/success', methods=['POST', 'GET'])
def success_session():
    with app.app_context():
        g_user = current_user.get_id()
        completed_update = db.session.execute(db.select(User).where(User.id == g_user)).scalar()
        completed_update.premium_level = 1
        
        # Get the plan from the success URL
        plan = request.args.get('plan')
        current_date = datetime.date.today()
        
        if plan == 'year':
            completed_update.end_date_premium = current_date + datetime.timedelta(days=365)
        elif plan == 'life':
            completed_update.end_date_premium = datetime.date(9999, 12, 31)  # Set to a far future date for lifetime access
        
        db.session.commit()
    return redirect(url_for('workouts'))

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


@app.route('/get_user_points', methods=['GET'])
@login_required
def get_user_points():
    user = current_user
    return {
        'total_points': user.points,
    }


if __name__ == "__main__":
    app.run(debug=True, port=5002)
