from flask import Flask, render_template, request, url_for, redirect,flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user,login_required,current_user
from sqlalchemy.sql import func
 
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
app.config["SECRET_KEY"] = "abc"
db = SQLAlchemy()
 
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)
 
 
class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    posts = db.relationship('Post',backref = 'user',passive_deletes=True)
    comments = db.relationship('Comment',backref = 'user',passive_deletes=True)
    likes = db.relationship('Like',backref = 'user',passive_deletes=True)
    
    
class Post(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  text = db.Column(db.Text,nullable=False)
  date_created = db.Column(db.DateTime(timezone = True),default = func.now())
  author = db.Column(db.Integer,db.ForeignKey('users.id',ondelete="CASCADE"),nullable=False)
  comments = db.relationship('Comment',backref = 'post',passive_deletes=True)
  likes = db.relationship('Like',backref = 'post',passive_deletes=True)
  
  
class Comment(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  text = db.Column(db.String(200),nullable=False)
  date_created = db.Column(db.DateTime(timezone = True),default = func.now())
  author = db.Column(db.Integer,db.ForeignKey('users.id',ondelete="CASCADE"),nullable=False)
  post_id = db.Column(db.Integer,db.ForeignKey('post.id',ondelete="CASCADE"),nullable=False)
  
  
class Like(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  date_created = db.Column(db.DateTime(timezone = True),default = func.now())
  author = db.Column(db.Integer,db.ForeignKey('users.id',ondelete="CASCADE"),nullable=False)
  post_id = db.Column(db.Integer,db.ForeignKey('post.id',ondelete="CASCADE"),nullable=False)
  
  
  
 
db.init_app(app)
 
 
with app.app_context():
    db.create_all()
 
 
@login_manager.user_loader
def loader_user(user_id):
  return Users.query.get(user_id)
 
 
@app.route('/sign_up', methods=["GET", "POST"])
def sign_up():
    if request.method == "POST":
        user = Users(username=request.form.get("username"),
                     password=request.form.get("password"))
        
        #username_exists = Users.query.filter_by(user.username).first()
        username_exists = Users.query.filter_by(username=request.form['username']).first()

        if username_exists:
          flash("Username Exists",category='error')
        elif len(user.username) < 3:
          flash("Username is too short",category="error")
        elif len(user.password) < 6 :
          flash("PassWord is too short",category="error")
        else:
          db.session.add(user)
          db.session.commit()
          flash("User Created",category='success')
          return redirect(url_for("login"))
    return render_template("sign_up.html")
 
 
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = Users.query.filter_by(
            username=request.form.get("username")).first()
        #password =Users.query.filter_by(password=request.form.get("password")).first()
        #if not user:
          #flash("User does not Exist",category="error")
        
        if user:
          
          if user.password == request.form.get("password"):
            #login_user(user)
            login_user(user,remember = True)
            flash("Logged in Successfully",category = 'success')
            return redirect(url_for("home",username="username"))
          else:
            flash("PassWord Is Incorrect",category="error")  
        else:  
          flash("User does not Exist",category="error")
        
        
    return render_template("login.html")
 
 
@app.route("/create_post",methods=["GET", "POST"])
@login_required
def create_post():
  if request.method == 'POST':
    text = request.form.get('text')
    if not text:
      flash("Post cannot be empty",category = 'error')
    else:
      post=Post(text = text,author = current_user.id)
      db.session.add(post)
      db.session.commit()
      flash("Post Created",category = 'success')
      return redirect(url_for('home'))
      
  return render_template('create_post.html',user = current_user)
 
@app.route("/delete-post/<id>")
@login_required
def delete_post(id):
  post = Post.query.filter_by(id=id).first()
  if not post:
    flash("Post does not exist",category='error')
  #elif current_user.id != post.id:
    #flash("You do not have permission to delete this post",category='error')
  else:
    db.session.delete(post)
    db.session.commit()
    flash("Post deleted",category="success")
  return redirect(url_for("home"))
  
 
@app.route("/logout")
def logout():
    logout_user()
    
    flash("You have been logged out",category='success')
    return redirect(url_for("login"))
 
@app.route("/posts/<username>")
@login_required
def posts(username):
  user = Users.query.filter_by(username=username).first()
  if not user:
    flash("No User with that Username exist",category="eror")
    return redirect(url_for("home"))
  #posts = user.posts
  posts = Post.query.filter_by(author=user.id).all()
  return render_template("posts.html",user = current_user,username=username,posts=posts)
  
  
@app.route("/create_comment/<post_id>",methods = ["POST","GET"])
@login_required
def create_comment(post_id):
  text = request.form.get("text")
  
  if not text:
    flash("Comment canot be empty",category='error')
  else:
    
    post = Post.query.filter_by(id=post_id)
    if post:
      comment = Comment(text = text,author = current_user.id,post_id=post_id)
      db.session.add(comment)
      db.session.commit()
      
    else:
      flash("Post does not exist",category='error')
  return render_template("home.html")
  

@app.route("/delete-comment/<comment_id>")
@login_required
def delete_comment(comment_id):
  comment = Comment.query.filter_by(id=comment_id).first() 
  if not comment:
    flash("Comment does not exist",category='error')
  elif current_user.id != comment.author and current_user.id != comment.post.author:
    flash("You do not have permission",category='error')
  else:
    db.session.delete(comment)
    db.session.commit()
  return redirect(url_for("home"))

@app.route("/like-post/<post_id>",methods=["GET"])
@login_required
def like(post_id):
  post = Post.query.filter_by(id=post_id)
  like = Like.query.filter_by(author = current_user.id, post_id = post_id).first()
  if not post:
    flash("Post does not Exist",category="error")
  elif like:
    db.session.delete(like)
    db.session.commit()
  else:
    like = Like(author=current_user.id,post_id =post_id)
    db.session.add(like)
    db.session.commit()
  
  return redirect(url_for("home"))
  #return jsonify({"likes": len(post.likes), "liked": current_user.id in map(lambda x: x.author, post.likes)})
    
    
    
@app.route("/")
@app.route("/home")
@login_required
def home():
  posts = Post.query.all()
  
  return render_template("home.html",posts=posts,user=current_user)
 
 
if __name__ == "__main__":
    app.run(debug=True)