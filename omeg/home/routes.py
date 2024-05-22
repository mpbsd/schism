from flask import Blueprint, render_template

from omeg.data.load import payload

bp_home_routes = Blueprint(
    "bp_home_routes",
    __name__,
    static_folder="static",
    template_folder="templates",
)


@bp_home_routes.route("/")
def home():
    return render_template("home.html", payload=payload)


@bp_home_routes.route("dates")
def dates():
    return render_template("dates.html", payload=payload)
