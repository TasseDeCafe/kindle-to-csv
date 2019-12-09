from flask import Flask, render_template, request, send_file, url_for, redirect, after_this_request, make_response, \
    flash, Markup, send_from_directory
from flask_debugtoolbar import DebugToolbarExtension
from werkzeug.utils import secure_filename
import sqlite3
from db_to_csv import *
from flask_dropzone import Dropzone
import uuid
import time
import threading

app = Flask(__name__, template_folder='templates')
app.config.update(
    SECRET_KEY='CHANGEME',

    # remove user database after X seconds
    DATABASE_PERSISTENCE=666,

    # Flask-Dropzone config:
    DROPZONE_ALLOWED_FILE_CUSTOM=True,
    DROPZONE_ALLOWED_FILE_TYPE='.db',
    DROPZONE_MAX_FILE_SIZE=50,
    DROPZONE_MAX_FILES=1,
    DROPZONE_REDIRECT_VIEW='book_list',
    DROPZONE_DEFAULT_MESSAGE='Drop your Kindle database here or click to upload.'

    # debugger config
    # DEBUG_TB_INTERCEPT_REDIRECTS=False
)

# create folder where files are uploaded
os.makedirs(os.path.join(app.instance_path, 'htmlfi'), exist_ok=True)

# # used for debugging
# toolbar = DebugToolbarExtension(app)

# create a dropzone
dropzone = Dropzone(app)


def style(css):
    """Add css to dropzone.
     :param css: style sheet code.
    """
    # return Markup('<style>\n.dropzone{%s}\n</style>' % css)
    return Markup('<style>\n%s\n</style>' % css)


# https://stackoverflow.com/questions/30640968/remove-old-temporary-files-when-user-is-logged-out

class TimeSet(set):
    def add(self, item, timeout):
        set.add(self, item)
        t = threading.Thread(target=timeout_set_remove, args=(self, item, timeout))
        t.start()


def timeout_set_remove(my_set, item, timeout):
    time.sleep(timeout)
    try:
        file_handle = open(item, 'r')
        os.remove(str(item))
        my_set.remove(item)
        file_handle.close()
    except FileNotFoundError as error:
        app.logger.error("Error removing database.", error)


@app.route('/')
def drop_file():
    resp = make_response(render_template('drop_file.html', style=style))
    resp.set_cookie("id", str(uuid.uuid4()))
    return resp


@app.route('/book_list', methods=["GET", "POST"])
def book_list():
    try:
        connection = sqlite3.connect(os.path.join(app.instance_path, 'htmlfi', f"{request.cookies['id']}.db"))
        c = connection.cursor()
        books = get_list_books(c)
        return render_template('book_list.html', books=books)
    except sqlite3.OperationalError:
        resp = redirect(url_for('drop_file'))
        # remove the cookie by changing its max_age to zero
        resp.set_cookie("id", "null", max_age=0)
        flash('Your session has expired. Please reupload your database.')
        return resp


@app.route("/sendfile", methods=["GET", "POST"])
def send_database_file():
    f = request.files['file']
    f.save(os.path.join(app.instance_path, 'htmlfi', secure_filename(f"{request.cookies['id']}.db")))
    my_set = TimeSet()
    my_set.add(os.path.join(app.instance_path, 'htmlfi', f"{request.cookies['id']}.db"), app.config['DATABASE_PERSISTENCE'])
    return redirect(url_for('book_list'))


@app.route('/<book_title>', methods=['GET', 'POST'])
def upload_file(book_title):
    if request.method == 'POST':
        user_book_index = int(request.form['book_index'])
        user_book_title = book_title
        try:
            connection = sqlite3.connect(os.path.join(app.instance_path, 'htmlfi', f"{request.cookies['id']}.db"))
            c = connection.cursor()
            create_csv(c, app, user_book_index, user_book_title)
            file_path = os.path.join(app.instance_path, 'csv_files', f'vocab_{user_book_title}.csv')
            file_handle = open(file_path, 'r')
        except (KeyError, sqlite3.OperationalError):
            # remove 0 byte file if user clicks on a button after the db has been removed
            os.remove(os.path.join(app.instance_path, 'htmlfi', f"{request.cookies['id']}.db"))
            resp = redirect(url_for('drop_file'))
            # remove the cookie by changing its max_age to zero
            resp.set_cookie("id", "null", max_age=0)
            flash('Your session has expired. Please reupload your database.')
            return resp

        @after_this_request
        def remove_file(response):
            try:
                os.remove(file_path)
                file_handle.close()
            except Exception as error:
                app.logger.error("Error removing or closing downloaded file handle", error)
            return response

        to_return = send_file(
            os.path.join(app.instance_path, 'csv_files', f'vocab_{user_book_title}.csv'),
            mimetype='text/csv',
            conditional=False)
        # uncomment this line to open the file as an attachment
        # to_return.headers["Content-Disposition"] = f"attachment; filename='words_and_sentences_{user_book_index}.csv"
        return to_return


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


if __name__ == '__main__':
    app.run(debug=True)
