"""
Flask Website Functions
"""

from datetime import datetime
from flask import Flask, session, render_template, request, g, redirect, url_for, flash
from flask_bcrypt import Bcrypt
import sqlite_db
import requisite_tree

DB_FILE = 'database.db'

# Initialise objects
app = Flask(__name__)
app.config['SECRET_KEY'] = b'b949e0ee62dcd1d4aa8f2cf1e8cc9a462ee81fa5a0a0fb9680aef1d2cfc73612'
bcrypt = Bcrypt(app)

### Database Methods
def get_db():
    """Retrieve database object with Singleton pattern"""
    if not hasattr(g, '_db'):
        g._db = sqlite_db.SqlDb(DB_FILE)
    return g._db

@app.teardown_appcontext
def close_connection(exception):
    """Close database when closing app"""
    if hasattr(g, '_db'):
        g._db.close()


### User Functions
def register_user(username, password):
    """Returns True if user successfully registered"""
    encrypted_password = bcrypt.generate_password_hash(password).decode('utf-8')
    return get_db().add_user(username, encrypted_password)

def login_user(username, password):
    """Returns True if login successful"""
    hash = get_db().get_password(username)
    if hash is not None and bcrypt.check_password_hash(hash, password):
        session['user'] = username
        return True
    return False

def logout_user():
    """Removes user from session"""
    session.pop('user', None)

def get_username():
    """Returns username of user in current session, or None if user is not logged in"""
    return session.get('user')

def add_review(course_id, rating, content):
    """Returns True if comment successfully added"""
    if (username := get_username()):
        return get_db().add_review(course_id, username, rating, content)
    return False

def edit_review(course_id, rating, content):
    """Returns True if comment successfully edited"""
    if (username := get_username()):
        return get_db().edit_review(course_id, username, rating, content)
    return False

def delete_review(course_id):
    """Returns True if comment successfully deleted"""
    if (username := get_username()):
        return get_db().delete_review(course_id, username)
    return False

def get_user_review(course_id):
    """Returns review made by user in course, or None if user is not logged in
    
    Return Schema:
    {
        "review_id": Unique id of Review,
        "timestamp": Timestamp of Review in Unix Epoch,
        "username": Username of Review Creator,
        "rating": Rating of Review, on a scale of 0-10 (inclusive)
        "content": Additional comments of review
    }
    """
    if (username := get_username()):
        return get_db().get_course_review(course_id, username)

def get_user_reviews():
    """Returns list of reviews posted by a user, or None if user is not logged in
    
    Return Schema:
    [
        {
            "review_id": Unique id of Review,
            "timestamp": Timestamp of Review in Unix Epoch,
            "course_id": Username of Review Creator,
            "rating": Rating of Review, on a scale of 0-10 (inclusive)
            "content": Additional comments of review
        }
    ]
    """
    if (username := get_username()):
        return get_db().get_user_reviews(username)

def get_requisite_tree_data(type, courses, secondary=None):
    """Returns data for requisite chart given parameters
    
    Return Schema:
    {
        'type': 'pre'/'post_partial'/'post_complete',
        'courses': [list of courses],
        'secondary': [list of courses] // Only if 'post' chosen
    }
    """
    db = get_db()

    # Get data for nodes
    tree = dict()
    if type == 'pre':
        tree = requisite_tree.create_prereq_tree(db, courses)
    elif type == 'post_partial':
        tree = requisite_tree.create_partial_postreq_tree(db, courses)
    elif type == 'post_complete':
        tree = requisite_tree.create_complete_postreq_tree(db, courses, secondary)

    # Remove edges to nodes that aren't in tree
    for from_course, course_list in tree.items():
        tree[from_course] = [to_course for to_course in course_list if to_course in tree.keys()]

    return tree

### API
@app.post('/api/course_chart')
def api_course_chart():
    return get_requisite_tree_data(request.form['type'], request.form.getlist('courses'), request.form.getlist('secondary')), 400

@app.post('/api/login')
def api_login():
    if not login_user(request.form['username'], request.form['password']):
        flash("Username or password is invalid!", 'warning')
        return redirect(url_for('page_login'))
    flash("Successfully logged in!", 'success')
    return redirect(url_for('page_index'))

@app.post('/api/register')
def api_register():
    if not register_user(request.form['username'], request.form['password']):
        flash("Username already taken!", 'warning')
        return redirect(url_for('page_login'))
    flash("Registered - Please login", 'success')
    return redirect(url_for('page_login'))

@app.post('/api/logout')
def api_logout():
    logout_user()
    flash("Successfully logged out!", 'success')
    return redirect(url_for('page_index'))

## User-Specific API
@app.post('/api/user/review/<course_id>')
def api_user_review(course_id):
    if session['user']:
        if request.form['action'] == 'Submit':
            # Add or edit review depending on if review already posted
            if get_user_review(course_id):
                if edit_review(course_id, request.form['rating'], request.form['comment']):
                    flash("Review successfully edited!", 'success')
            else:
                if add_review(course_id, request.form['rating'], request.form['comment']):
                    flash("Review successfully added!", 'success')
        elif request.form['action'] == 'Delete':
            if delete_review(course_id):
                flash("Review successfully deleted!", 'success')
    return redirect(url_for('page_course', course_id=course_id))

### Pages
@app.get('/')
def page_index():
    return render_template('index.html', reviews=get_user_reviews())

@app.get('/courses-tree')
def page_courses_tree():
    # Select only MAT, CSC, and STA courses
    courses = [course for course in get_db().get_courses() if course[:3] in ('MAT', 'CSC', 'STA')]
    return render_template('courses-tree.html', courses=courses)


@app.get('/courses-tree-visual')
def page_courses_tree_visual():
    data = get_requisite_tree_data(request.args['type'], request.args.getlist('courses'), request.args.getlist('secondary'))
    return render_template('courses-tree-visual.html', data=data)

@app.get('/login')
def page_login():
    if get_username() is not None:
        return redirect(url_for('page_index'))
    return render_template('login.html')

@app.get('/course/<course_id>')
def page_course(course_id):
    info = get_db().get_course_full_info(course_id)
    if info is not None:
        # Get information related to course to pass to template
        reviews = get_db().get_course_reviews(course_id)
        rating = get_db().get_course_average_rating(course_id)
        user_review = get_user_review(course_id)
        return render_template('course.html', course_id=course_id, info=info, reviews=reviews, rating=rating, user_review=user_review)
    return render_template('course-404.html', course=course_id)

@app.get('/courses')
def page_courses():
    match request.args.get('sort'):
        case 'rating':
            return render_template('courses.html', course_attribute="Average Rating", courses=get_db().get_courses_order_by_average_rating())
        case 'reviews':
            return render_template('courses.html', course_attribute="Reviews", courses=get_db().get_courses_order_by_reviews())
        case _:
            return render_template('courses.html', courses=get_db().get_courses())


@app.template_filter('format_unix')
def format_unix(timestamp, format="%d/%m/%Y at %H:%M"):
    """Returns unix epoch timestamp object formatted in a readable format"""
    return datetime.fromtimestamp(timestamp).strftime(format)

@app.template_filter('course_page')
def course_page(course_id):
    """Returns course page url given course id"""
    return url_for('page_course', course_id=course_id)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8001)
