from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.exceptions import abort
from urllib.request import urlopen
from bs4 import BeautifulSoup
from soupt import db
from soupt.auth.views import login_required
from soupt.webscrap.models import Scrape
import requests
import os
import io
import zipfile
from shutil import make_archive
import shutil
from flask import send_file





bp = Blueprint("webscrap", __name__)

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'js'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route("/")
def index():
    """Show all the posts, most recent first."""
    scrapes= Scrape.query.order_by(Scrape.created.desc()).all()
    # import pdb; pdb.set_trace()
    return render_template("webscrap/index.html", scrapes=scrapes)


def get_scarpe(id, check_author=True):
    """Get a post and its author by id.

    Checks that the id exists and optionally that the current user is
    the author.

    :param id: id of post to get
    :param check_author: require the current user to be the author
    :return: the post with author information
    :raise 404: if a post with the given id doesn't exist
    :raise 403: if the current user isn't the author
    """
    scrape_data = Scrape.query.get_or_404(id, f"scrape id {id} doesn't exist.")

    if check_author and scrape_data.author != g.user:
       abort(403)

    return scrape_data



@bp.route("/create", methods=("GET", "POST"))
@login_required
def scrape_title():
    """Create a new post for the current user."""
    if request.method == "POST":
        urltitle = str(request.form["urltitle"])
        r = requests.get(urltitle)
        soup = BeautifulSoup(r.text)
        pagetitle = soup.title.text
        file_path = "//tmp/"
        os.makedirs(file_path + pagetitle, exist_ok=True)
        javascript_list = soup.find_all('script')
        for num, script in enumerate(javascript_list, start=1):
            if script.text:
                filename = "/file" + str(num) + ".js"
                Jscript = open(file_path + pagetitle + filename , mode="w",encoding="utf-8")
                Jscript.write(script.text)
                Jscript.close()

                        
            Jscript = open(file_path + pagetitle + filename , mode="r",encoding="utf-8") 
           
            for line in Jscript:
                a_key = line.find('access key')
                key_val = line[a_key:-1]
                if a_key != -1:
                    flash(key_val)
                else:

                    flash("no key found")
            Jscript.close()


        dirname = file_path + pagetitle
        shutil.make_archive("/tmp/filename", 'zip', dirname)
        

        error = None

        if not urltitle:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            db.session.add(Scrape(urltitle=urltitle, pagetitle=pagetitle, author=g.user))
            db.session.commit()
            return send_file("/tmp/filename.zip",
            mimetype='application/zip',
            as_attachment=True,
            attachment_filename='data.zip'
            )
           
    return render_template("webscrap/create.html")


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def scrape_update(id):
    """Update a post if the current user is the author."""
    scrape_data = get_scarpe(id)

    if request.method == "POST":
        urltitle = str(request.form["urltitle"])
        r = requests.get(urltitle)
        soup = BeautifulSoup(r.text, 'html.parser')
        pagetitle = soup.title.text
        #import pdb; pdb.set_trace()
        error = None
        if not urltitle:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            scrape_data.urltitle = urltitle
            scrape_data.pagetitle = pagetitle
            db.session.commit()
            return redirect(url_for("webscrap.index"))

    return render_template("webscrap/update.html", scrape_data=scrape_data)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    """Delete a post.

    Ensures that the post exists and that the logged in user is the
    author of the post.
    """
    scrape = get_scarpe(id)
    db.session.delete(scrape)
    db.session.commit()
    return redirect(url_for("webscrap.index"))
