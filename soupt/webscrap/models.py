from flask import url_for

from soupt import db
from soupt.auth.models import User



class Scrape(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.ForeignKey(User.id), nullable=False)
    created = db.Column(
        db.DateTime, nullable=False, server_default=db.func.current_timestamp()
    )
    urltitle = db.Column(db.String, nullable=False)
    pagetitle = db.Column(db.String, nullable=False)

    # User object backed by author_id
    # lazy="joined" means the user is returned with the post in one query
    author = db.relationship(User, lazy="joined", backref="scrapes")

    @property
    def update_url(self):
        return url_for("webscrap.scrape_update", id=self.id)

    @property
    def delete_url(self):
        return url_for("webscrap.delete", id=self.id)