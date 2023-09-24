from flask import Flask, render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Giriş yapmanız gerekiyor.", "danger")
            return redirect(url_for("login"))
        
    return decorated_function

class Registerform(Form):
    name= StringField("isim giriniz",validators=[validators.Length(min = 3, max = 10)])
    username= StringField("Kullanıcı adı",validators=[validators.Length(min = 5, max = 26)])
    
    email = StringField("mail giriniz", validators=[validators.Email(message="Lütfen mail giriniz")])
    parola = PasswordField("parola giriniz", validators=
                           [validators.data_required(message="lütfen parola giriniz"),validators.EqualTo(fieldname="confirm",message="parola uyuşmuyor")])
    confirm = PasswordField("parloda doğrulama", validators=[validators.DataRequired()])

class Loginform(Form):
    username = StringField("kullanıcı adi")
    parola = PasswordField("parola")
app = Flask(__name__)
app.secret_key ="ybblog"

app.config["MYSQL_HOST"] = "localhost"
app.config['MYSQL_USER'] = "root"
app.config['MYSQL_PASSWORD'] = ""
app.config['MYSQL_DB'] = "ybblog"
app.config['MYSQL_CURSORCLASS'] = "DictCursor"
mysql = MySQL(app)



@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/dashboard")
@login_required
def dashboard():
   # flash("Hoş geldin " + session['username'],"success")
   cursor = mysql.connection.cursor()
   sorgu = "select * from articles where author=%s"
   result = cursor.execute(sorgu,(session["username"],))
   if result >0:
        articles = cursor.fetchall()
        return render_template("dashboard.html", articles = articles)
   else:
       return render_template("dashboard.html")
    
    
@app.route("/about")
@login_required
def about():
    return render_template("about.html")
@app.route("/article")
@login_required
def article():
    cursor = mysql.connection.cursor()
    sorgu = "select * from articles"
    result = cursor.execute(sorgu)
    if result > 0:
        articles = cursor.fetchall()
        return render_template("article.html", articles = articles)
    else:
        artc = [
            {"id":1, "title":"Bilim Dünyasi", "content": "Yunuslar"},
            {"id":2, "title":"Bilim Dünyasi2", "content": "Kaplumbağalar"},
            {"id":3, "title":"Bilim Dünyasi3", "content": "Yengeçler"}
             ]
        return render_template("article.html",artc = artc)

@app.route("/article/<string:id>")
def detail(id):
    cursor = mysql.connection.cursor()
    sorgu = "select * from articles where id = %s"
    result = cursor.execute(sorgu,(id,))
    if result >0:
        article = cursor.fetchone()
        return render_template("article1.html", article= article)
    else:
        return render_template("article1.html")

@app.route("/register", methods =["GET", "POST"])
def register():
    form = Registerform(request.form)

    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.parola.data)
        cursor = mysql.connection.cursor()
        sorgu = "insert into users(name,username,email,password) VALUES (%s,%s,%s,%s)"
        
        cursor.execute(sorgu,(name,username,email,password))
        mysql.connection.commit()
        cursor.close()
        flash("başarıyla kayıt oldunuz","success")

        return redirect(url_for("login"))
    else:
        return render_template("register.html", form = form)

@app.route("/login",methods = ["GET", "POST"])
def login():
    form = Loginform(request.form)
    if request.method == "POST":
        username = form.username.data
        passworde = form.parola.data
        cursor = mysql.connection.cursor()
        sorgu = "select * from users where username = %s"

        result = cursor.execute(sorgu,(username,)) 
        if result >0:
            data = cursor.fetchone()
            realpass= data["password"]
            if sha256_crypt.verify(passworde,realpass):
                flash("giriş yapılıyor...","success")
                session["logged_in"] = True
                session["username"] = username

                return redirect(url_for("index"))
            else:
                flash("yanlış şifre","danger")
                return redirect(url_for("login"))
        else:
            flash("kullanıcı bulunmuyor","warning")
            return redirect(url_for("login"))
        cursor.close()
        return redirect(url_for("index"))
    else: 
        return render_template("login.html", form = form)
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/edit/<string:id>", methods = ["GET","POST"])
@login_required
def update(id):
    
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        sorgu = "select * from articles where author = %s and id = %s"
        result = cursor.execute(sorgu,(session["username"],id))
        if result == 0:
            flash("Böyle bir makaleniz yok","warning")
            return redirect(url_for("index"))
        else:
            article = cursor.fetchone()
            form = ArticleForm()
            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html", form = form)
    else:
        form = ArticleForm(request.form)
        newTitle = form.title.data
        newContent = form.content.data
        sorgu2 = "update articles Set title = %s, content = %s where id = %s"
        cursor = mysql.connection.cursor()
        cursor.execute(sorgu2,(newTitle,newContent,id))
        mysql.connection.commit()
        cursor.close()
        flash("makale başarıyla güncellendi", "success")
        return redirect(url_for("dashboard"))
        
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    sorgu = "select * from articles where author = %s and id = %s"
    result = cursor.execute(sorgu,(session["username"],id))
    if result >0:
        sorgu2 = "delete from articles where id = %s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir makaleniz mevcut değil","warning")
        return redirect(url_for("index"))


@app.route("/addarticle", methods = ["GET","POST"])
def addarticle():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data
        cursor = mysql.connection.cursor()
        sorgu = "insert into articles(title,author,content) VALUES (%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],content))
        mysql.connection.commit()
        cursor.close()
        flash("makale başarıyla eklendi", "success")
        return redirect(url_for("dashboard"))
    return render_template("addarticle.html", form = form)


class ArticleForm(Form):
    title = StringField("Makale Başlığı", validators=[validators.Length(min= 5, max = 100)])
    content = TextAreaField("İçerik", validators=[validators.length(min = 10)])

@app.route("/search",methods = ["GET","POST"])
def search():
   if request.method == "GET":
       return redirect(url_for("index"))
   else:
       keyword = request.form.get("keyword")

       cursor = mysql.connection.cursor()

       sorgu = "Select * from articles where title like '%" + keyword +"%'"

       result = cursor.execute(sorgu)

       if result == 0:
           flash("Aranan kelimeye uygun makale bulunamadı...","warning")
           return redirect(url_for("article"))
       else:
           articles = cursor.fetchall()

           return render_template("article.html",articles = articles)


if __name__ == "__main__":
    app.run(debug=True)
