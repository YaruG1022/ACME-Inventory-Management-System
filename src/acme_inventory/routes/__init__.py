def register_routes(app):
    from . import account, auth, donations, home, inventory, media, orders, reports

    for module in (account, auth, donations, home, inventory, media, orders, reports):
        app.register_blueprint(module.bp)
