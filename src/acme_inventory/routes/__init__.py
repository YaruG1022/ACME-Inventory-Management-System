def register_routes(app):
    from . import account, auth, donations, home, inventory, media, orders, reports, stock

    for module in (account, auth, donations, home, inventory, media, orders, reports, stock):
        app.register_blueprint(module.bp)
