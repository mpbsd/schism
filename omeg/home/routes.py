from flask import Blueprint, render_template

from omeg.data.load import payload

bp_home_routes = Blueprint("bp_home_routes", __name__)


@bp_home_routes.route("/")
def home():
    return render_template("home/home.html", edition=payload["edition"])


@bp_home_routes.route("dates")
def dates():
    return render_template(
        "home/dates.html",
        edition=payload["edition"],
        save_the_date=payload["save_the_date"],
        days_until=payload["days_until"],
    )
