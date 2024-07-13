from flask import Flask, render_template, url_for, request, redirect, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import re, os
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_required, current_user, login_user, logout_user
from form import LoginForm, FurtherInfo, BookFilter, RatingBook, CheckDiscount, RegistryForm
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_wtf.csrf import CSRFProtect
import telebot
import pickle
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


basedir = os.path.abspath(os.path.dirname(__file__))

#csrf = CSRFProtect()
app = Flask(__name__)
app.config['SECRET_KEY'] = 'a really really really really long secret key'
#csrf.init_app(app)

app.config['SQLALCHEMY_DATABASE_URI'] = \
    'sqlite:///' + os.path.join(basedir, 'database.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# load model from pickle file
with open('book_recomend_model.pkl', 'rb') as file:  
    model = pickle.load(file)
df = pd.read_pickle('df.pkl')

df_User_Based = pd.read_pickle('df_User_Based.pkl')
users_pivot = pd.read_pickle('users_pivot_User_Based.pkl')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

print("Login: username user(id) for example user2 the password for all accaounts is pass123. The admin user is user5.")

@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(user_id)


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(160), nullable=False)
    name = db.Column(db.String(255))
    surname = db.Column(db.String(255))
    famname = db.Column(db.String(255))
    phone_number = db.Column(db.String(10))
    location = db.Column(db.String(255))
    age = db.Column(db.Integer)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


Zakaz_Books_table = db.Table(
    "zakaz_books",
    db.Model.metadata,
    db.Column("id", db.Integer, primary_key=True),
    db.Column("book", db.String(13), db.ForeignKey('books.id_book'), nullable=False),
    db.Column("zakaz", db.Integer, db.ForeignKey('zakaz.id_zakaz'), nullable=False),
)

class Books(db.Model):
    __tablename__ = 'books'
    id_book = db.Column(db.String(13), primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    #language = db.Column(db.String(64), nullable=False)
    #genre = db.Column(db.String(64), nullable=False)
    #country = db.Column(db.String(64), nullable=False)
    year = db.Column(db.Integer)
    publisher = db.Column(db.String(255), nullable=False)
    image_S = db.Column(db.String(255), nullable=False)
    image_M = db.Column(db.String(255), nullable=False)
    image_L = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '<{}>'.format(self.title)


class Promocode(db.Model):
    __tablename__ = 'promocode'
    id_promocode = db.Column(db.Integer, primary_key=True)
    promocode = db.Column(db.String(10), nullable=False)
    discount = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '<Promocode: {}, {}>'.format(self.promocode, self.discount)


class Zakaz(db.Model):
    __tablename__ = 'zakaz'
    id_zakaz = db.Column(db.Integer, primary_key=True)
    id_client = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    time_zakaz = db.Column(db.DateTime, default=datetime.utcnow)
    id_promocode_used = db.Column(db.Integer, db.ForeignKey('promocode.id_promocode'))
    books = db.relationship("Books", secondary=Zakaz_Books_table, backref="zakazy")

    def __repr__(self):
        return '<Zakaz #{}>'.format(self.id_zakaz)


# class Card(db.Model):
#     __tablename__ = 'card'
#     id_card = db.Column(db.Integer, primary_key=True)
#     id_zakazi = db.Column(db.Integer, db.ForeignKey('zakaz.id_zakaz'), nullable=False)
#     id_books = db.Column(db.Integer, db.ForeignKey('books.id_book'), nullable=False)
#     quantity_wanted = db.Column(db.Integer, nullable=False)
#     time_card = db.Column(db.DateTime, default=datetime.utcnow)
#
#     def __repr__(self):
#         return '<Card #{}>'.format(self.id)


class Rating(db.Model):
    __tablename__ = 'rating'
    id_rating = db.Column(db.Integer, primary_key=True)
    id_book_to_rate = db.Column(db.String(13), db.ForeignKey('books.id_book'), nullable=False)
    id_client_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.TEXT)
    time_rating = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Rating {}/10 id {}>'.format(self.rating, self.id_book_to_rate)


@app.route('/')
def hello_world():
    flag_btn = current_user.is_authenticated
    new_books = []
    new_books.append(Books.query.get('1552041778'))
    new_books.append(Books.query.get('1879384493'))
    new_books.append(Books.query.get('0812523873'))
    new_books.append(Books.query.get('0449005615'))
    print(new_books)
    return render_template("index.html", flag_btn=flag_btn, new_books=new_books)


@app.route('/about')
def about_us():
    flag_btn = current_user.is_authenticated
    return render_template("about_us.html", flag_btn=flag_btn)


@app.route('/shelves', methods=['POST', 'GET'])
def shelves():
    form = BookFilter()
    flag_btn = current_user.is_authenticated
    books_available = Books.query
    if form.validate_on_submit():

        # lang = {"Русский": form.russian.data, "Английский": form.english.data, "Японский": form.japanese.data}
        # fil1 = [k for k, v in lang.items() if v == True]
        # if len(fil1) > 0:
        #     books_available = books_available.filter(Books.language.in_(fil1))

        # genre = {"Научпоп": form.scipop.data, "Кулинария": form.cookbook.data, "Рассказы": form.stories.data,
        #          "Повесть": form.narrative.data, "Роман": form.novel.data, "Эссе": form.essay.data}
        # fil2 = [k for k, v in genre.items() if v == True]
        # if len(fil2) > 0:
        #     books_available = books_available.filter(Books.genre.in_(fil2))

        # country = {"Япония": form.japan.data, "Китай": form.china.data, "Корея": form.korea.data,
        #            "Вьетнам": form.vietnam.data}
        # fil3 = [k for k, v in country.items() if v == True]
        # if len(fil3) > 0:
        #     books_available = books_available.filter(Books.country.in_(fil3))

        if form.sort.data == '2':
            books_available = books_available.order_by(Books.price)
        elif form.sort.data == '1':
            books_available = books_available.order_by(Books.price.desc())
        else:
            books_available = books_available.order_by(Books.id_book)

    #books_available = books_available.limit(52).all()

    page = request.args.get('page', 1, type=int)
    books_available = Books.query.paginate(page=page, per_page=52)

    return render_template("shelves.html", form=form, flag_btn=flag_btn, books=books_available)

#function to return recommended books - this will be tested
def get_recommends(title = ""):
    try:
        book = df.loc[title]
    except KeyError as e:
        print('The given book', e, 'does not exist')
        return

    distance, indice = model.kneighbors([book.values], n_neighbors=6)

    recommended_books = pd.DataFrame({
        'title'   : df.iloc[indice[0]].index.values,
        'distance': distance[0]
        }) \
        .sort_values(by='distance', ascending=False) \
        .head(4).values

    return recommended_books

@app.route('/shelves/<string:id>', methods=['POST', 'GET'])
def book_detail(id):
    flag_btn = current_user.is_authenticated
    curr_book = Books.query.get(id)
    form = False
    if current_user.is_authenticated and not db.session.query(db.exists().where(Rating.id_client_by == current_user.id).where(Rating.id_book_to_rate == id)).scalar():       
        form = RatingBook()
        if form.validate_on_submit():
            if form.comment.data is None:
                rate_obj = Rating(id_book_to_rate=id, id_client_by=current_user.id, rating=form.rating.data)
                print(rate_obj)
            else:
                rate_obj = Rating(id_book_to_rate=id, id_client_by=current_user.id, rating=form.rating.data, comment=form.comment.data)
            db.session.add(rate_obj)
            db.session.commit()
            print(rate_obj)
            return redirect(request.url)
        #print(form.errors)
    try:
        # evaluate model 
        books = get_recommends(curr_book.title) #0446672211
        print(books)
        if books.all():
            #print(type(books))
            #print(books)
            recommended_books = []
            for i in range(4):
                recommended_books.append(Books.query.get(db.session.execute(db.select(Books.id_book).filter_by(title=books[i][0])).first()[0]))
            print(recommended_books)
        return render_template("book.html", flag_btn=flag_btn, book=curr_book, form=form, recommended_books=recommended_books)
    except:
        print('no_recomendations')    
        return render_template("book.html", flag_btn=flag_btn, book=curr_book, form=form)



@app.route('/shelves/<string:id>/add')
@login_required
def add(id):
    if str(id) in session:
        session[str(id)] = session.get(str(id)) + 1
    else:
        session[str(id)] = 1
    return redirect(url_for('book_detail', id=id))


@app.route('/review') #Рецензии
def review():
    flag_btn = current_user.is_authenticated
    rec = Rating.query.filter(Rating.comment.isnot("")).order_by(Rating.time_rating.desc()).limit(50).all()
    id_bs = []
    auth = []
    pic = []
    for r in rec:
        title = Books.query.get(r.id_book_to_rate).title
        id_bs.append(title)
        author = User.query.get(r.id_client_by).username
        auth.append(author)
        picture = Books.query.get(r.id_book_to_rate).image_L
        pic.append(picture)
    sz = len(rec)

    return render_template("review.html", flag_btn=flag_btn, rec=rec, book=id_bs, auth=auth, sz=sz, pic=pic)


def users_choice(id):
    users_fav=df_User_Based[df_User_Based["id_client_by"]==id].sort_values(["rating"],ascending=False)[0:4]
    return users_fav

def user_based(df_User_Based,id):
    if id not in df_User_Based["id_client_by"].values:
        print("❌ User NOT FOUND ❌")
        
        
    else:
        index=np.where(users_pivot.index==id)[0][0]
        similarity=cosine_similarity(users_pivot)
        similar_users=list(enumerate(similarity[index]))
        similar_users = sorted(similar_users,key = lambda x:x[1],reverse=True)[0:5]
    
        user_rec=[]
    
        for i in similar_users:
                data=df_User_Based[df_User_Based["id_client_by"]==users_pivot.index[i[0]]]
                user_rec.extend(list(data.drop_duplicates("id_client_by")["id_client_by"].values))
        
    return user_rec

#to recommend books for a user based on the books rated by a list of similar users,
#while ensuring that the recommended books are not already rated by the target user.
#The function filters and sorts the books by rating and then selects the top 5 recommendations.
def common(df_User_Based,user,user_id):
    x=df_User_Based[df_User_Based["id_client_by"]==user_id]
    recommend_books=[]
    user=list(user)
    for i in user:
        y=df_User_Based[(df_User_Based["id_client_by"]==i)]
        books=y.loc[~y["title"].isin(x["title"]),:]
        books=books.sort_values(["rating"],ascending=False)[0:5]
        # recommend_books.extend(books["title"].values)
        recommend_books.extend(books["id_books"].values)
    return recommend_books[0:5]

@app.route('/recommendations')
def recommendations():
    flag_btn = current_user.is_authenticated
    print('user.id: ',current_user.id)
    try:
        user_id=current_user.id
        user_choice_df=pd.DataFrame(users_choice(current_user.id))
        user_favorite=users_choice(user_id)

        fav_books = []
        for i in range(4):
            fav_books.append(Books.query.get(pd.DataFrame(users_choice(user_id))["id_books"].values[i]))
        print('fav_books: ', fav_books)
        
        user_based_rec=user_based(df_User_Based,user_id)
        books_for_user=common(df_User_Based,user_based_rec,user_id)
        
        recommended_books = []
        for i in range(4):
            recommended_books.append(Books.query.get(books_for_user[i]))
        print('recommended_books: ', recommended_books)
    except:
        fav_books=False
        recommended_books=False
        print('no_recomendations')    

    return render_template("recommendations.html", flag_btn=flag_btn, fav_books=fav_books, recommended_books=recommended_books)

    return render_template("recommendations.html", flag_btn=flag_btn, rec=rec, book=id_bs, auth=auth, sz=sz, pic=pic)
    return render_template("index.html", flag_btn=flag_btn, new_books=new_books)



regex = '^[a-zA-Z0-9.!#$%&’*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$'
def check(email):
    if re.search(regex, email):
        return True
    else:
        return False


@app.route('/signin', methods=['POST', 'GET'])
def sign():
    form = RegistryForm()
    error = None
    if current_user.is_authenticated:
        return redirect(url_for('account'))
    if form.validate_on_submit():
        if db.session.query(User).filter(User.username == form.username.data).first():
            error = "Такой логин уже есть! Придумайте другой"
            return render_template("user.html", error=error, form=form)
        if not check(form.email.data):
            error = "Это не email!"
            return render_template("user.html", error=error, form=form)
        if db.session.query(User).filter(User.email == form.email.data).first():
            error = "Такой email уже есть! Может, вам стоит войти?"
            return render_template("user.html", error=error, form=form)
        user1 = User(username=form.username.data, email=form.email.data)
        user1.set_password(form.password.data)
        db.session.add(user1)
        db.session.commit()
        user = db.session.query(User).filter(User.username == form.username.data).first()
        login_user(user)
        return redirect(url_for('account'))
    return render_template("user.html", error=error, form=form)


@app.route('/login', methods=['POST', 'GET'])
def log():
    if current_user.is_authenticated:
        return redirect(url_for('account'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.query(User).filter(User.username == form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('account'))

        flash("Invalid username/password", 'error')
        return redirect(url_for('log'))
    return render_template('login.html', form=form)


validate_phone_number_pattern = "^\\+?[1-9][0-9]{7,14}$"


def check_ph(phone):
    if re.match(validate_phone_number_pattern, phone):
        return True
    else:
        return False


@app.route('/account', methods=['POST', 'GET'])
@login_required
def account():
    form = FurtherInfo()
    user = User.query.get_or_404(current_user.id)
    flag = (user.surname is None) and (user.name is None) and (user.famname is None) and (
                user.phone_number is None) and (user.location is None)

    if form.validate_on_submit():
        user.surname = form.surname.data
        user.name = form.name.data
        user.famname = form.famname.data
        if check_ph(form.phone_number.data):
            user.phone_number = form.phone_number.data
        else:
            flash("Invalid number")
            return render_template('account.html', form=form, flag=flag)
        user.location = form.location.data
        db.session.commit()
        flag = False
    #flag_for_orders = (Zakaz.books is None)
    #flag_for_orders = (user.id > 5)
    my_orders = Zakaz.query.filter(Zakaz.id_client == current_user.id).all()

    return render_template('account.html', form=form, flag=flag, order=my_orders)


@app.route('/update_acc', methods=['POST', 'GET'])
@login_required
def update_acc():
    form = FurtherInfo()
    user = User.query.get_or_404(current_user.id)

    if form.validate_on_submit():
        user.surname = form.surname.data
        user.name = form.name.data
        user.famname = form.famname.data
        if check_ph(form.phone_number.data):
            user.phone_number = form.phone_number.data
        else:
            flash("Invalid number")
            return render_template('update_acc.html', form=form)
        user.location = form.location.data
        db.session.commit()
        return redirect(url_for('account'))

    return render_template('update_acc.html', form=form)


# @app.route('/post_rating', methods=['POST', 'GET'])
# @login_required
# def post_rating():
#     choice = []
#     for i in Books.query.all():
#         choice.append((i.id_book, i.title))
#     form = RatingBook()
#     form.book.choices = choice
#     if form.validate_on_submit():
#         if form.comment.data is None:
#             rate_obj = Rating(id_book_to_rate=form.book.data, id_client_by=current_user.id, rating=form.rating.data)
#         else:
#             rate_obj = Rating(id_book_to_rate=form.book.data, id_client_by=current_user.id, rating=form.rating.data, comment=form.comment.data)

#         db.session.add(rate_obj)
#         db.session.commit()
#         return redirect(url_for('account'))
#     return render_template('post_rating.html', form=form)


@app.route('/busket', methods=['POST', 'GET'])
@login_required
def busket():
    #all_q = len(db.session.query(Books).all()) + 1
    s = []
    d = {}
    total = 0
    flag = False
    id_promo = 0
    for i in db.session.query(Books.id_book).all():
        #   print(i[0])
        i=i[0]
        if i in session:
            s.append(i)
            d[i] = session[i]
            id_b = Books.query.get(i)
            print(id_b)
            total += id_b.price * session[i]
    print(s)

    if len(s) > 0:
        books_chosen = Books.query.filter(Books.id_book.in_(s))
        flag = True
    else:
        books_chosen = None

    user = User.query.get_or_404(current_user.id)
    flag_log = (user.surname is None) or (user.name is None) or (user.famname is None) or (
            user.phone_number is None) or (user.location is None)
    form = CheckDiscount()
    error = None
    if form.validate_on_submit():
        exist = Promocode.query.filter(Promocode.promocode == form.promocode.data).first()
        if exist:
            total = total * ((100 - exist.discount) / 100)
            id_promo = exist.id_promocode
        else:
            error = "Такого промокода не существует"
            id_promo = 0
    return render_template('busket.html', book=books_chosen, flag=flag, dict=d, total=total, flag_log=flag_log, error=error, form=form, id_promo=id_promo)


@app.route('/busket/buy/<int:id>')
@login_required
def buy(id):
    if id == 0:
        new_order = Zakaz(id_client=current_user.id)
        print(type(Zakaz))
        print("new_order=",new_order)
    else:
        new_order = Zakaz(id_client=current_user.id, id_promocode_used=id)
    #all_q = len(db.session.query(Books).all()) + 1
    for i in db.session.query(Books.id_book).all():
        i=i[0]
        if i in session:
            b = Books.query.get(i)
            print('b=',b)
            print('b.quantity=',b.quantity)
            if b.quantity < 0:
                return "На складе нет такого кол-ва книг"
            b.quantity = b.quantity - session[i]
            print("sesion[i] = ", session[i])
            for n in range(0, session[i]):
                new_order.books.append(b)
                print(b)
        session.pop(i, None)

    print(new_order)
    #db.session.add(new_order)
    #db.session.commit()
    return render_template('buy.html')

@app.route('/busket/<string:id>/delete_item')
@login_required
def delete_item(id):
    if session[id] == 1:
        session.pop(id, None)
    else:
        session[id] = session[id] - 1
    return redirect(url_for('busket'))


@app.route('/logout')
@login_required
def logout():
    all_q = len(db.session.query(Books).all()) + 1
    for i in range(1, all_q):
        if str(i) in session:
            session.pop(str(i), None)
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for('log'))

class MyModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        if not current_user.is_authenticated:
            return False
        if current_user.id == 5:
            return True
        else: 
            print(current_user.id)
            flash("You are not the admin")
            return False
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('log'))

admin = Admin(app, index_view=MyAdminIndexView())
admin.add_view(ModelView(Books, db.session))
admin.add_view(ModelView(Promocode, db.session))
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Rating, db.session))

# @app.route('/admin')
# @login_required
# def admin():
#     id = current_user.id
#     if id == 5:
#        #return render_template('admin.html')

#         return redirect(url_for('admin'))
#     else:
#         flash("You are not admin")
#         return redirect(url_for('log'))


@app.route('/telegram',methods= ['POST'])
def telegram():
    Name = request.form['Name']
    Telegram = request.form['Telegram']
    msg_text = request.form['msg_text']
    output = 'Имя: ' + Name + '\nТелеграм: ' + Telegram + '\n\nОтзыв:\n' + msg_text
    if Name and Telegram and msg_text:
        token = os.environ['TOKEN'] 
        bot = telebot.TeleBot(token)
        chat_id = '1283589339' #moj
        chat_id_2 = '755390003'
        bot.send_message(chat_id, output)
        bot.send_message(chat_id_2, output)

        return jsonify({'output':'Спасибо за отзыв!'})

    return jsonify({'error' : 'Missing data!'})



if __name__ == '__main__':
    app.run(debug=True)
