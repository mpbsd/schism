def create_app():
    # let the games begin ================================================= {{{
    from flask import Flask

    omeg = Flask(__name__)
    # ===================================================================== }}}

    # configurations ====================================================== {{{
    from omeg.conf.setup import Config

    omeg.config.from_object(Config)
    # ===================================================================== }}}

    # login management ==================================================== {{{
    from omeg.conf.boost import login_manager
    from omeg.mold.models import Professor

    login_manager.init_app(omeg)

    @login_manager.user_loader
    def load_user(cpfP):
        return Professor.query.get(cpfP)

    # ===================================================================== }}}

    # relational database ================================================= {{{
    from omeg.conf.boost import db

    db.init_app(omeg)
    # ===================================================================== }}}

    # flask-migrate ======================================================= {{{
    from omeg.conf.boost import migrate

    migrate.init_app(omeg, db)
    # ===================================================================== }}}

    # mail ================================================================ {{{
    from omeg.conf.boost import mail

    mail.init_app(omeg)
    # ===================================================================== }}}

    # blueprints ========================================================== {{{
    from omeg.home.routes import bp_home_routes

    omeg.register_blueprint(bp_home_routes, url_prefix="/home")

    from omeg.auth.routes import bp_auth_routes

    omeg.register_blueprint(bp_auth_routes, url_prefix="/auth")

    from omeg.user.routes import bp_user_routes

    omeg.register_blueprint(bp_user_routes, url_prefix="/user")
    # ===================================================================== }}}

    return omeg
