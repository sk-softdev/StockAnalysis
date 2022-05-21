import os

from flask import Flask

"""The role of the __init__.py file is similar to the __init__ function in a Python class. The file essentially the constructor of your package or directory without it being called such. 
It sets up how packages or functions will be imported into your other files.Dec 29, 2020
"""

def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        # a default secret that should be overridden by instance config
        SECRET_KEY="key",
        # store the database in the instance folder
        DATABASE=os.path.join(app.instance_path, "StockAnalysis.sqlite"),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.update(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
        
    # register the database commands
    from StockAnalysis import db

    db.init_app(app)

    """ apply the blueprints to the app
    Each Flask Blueprint is an object that works very similarly to a Flask application. 
    They both can have resources, such as static files, templates, and views that are associated with routes.
    However, a Flask Blueprint is not actually an application. It needs to be registered in an application before you can run it. 
    When you register a Flask Blueprint in an application, you’re actually extending the application with the contents of the Blueprint.
    This is the key concept behind any Flask Blueprint. They record operations to be executed later when you register them on an application. 
    For example, when you associate a view to a route in a Flask Blueprint, it records this association to be made later in the application when the Blueprint is registered.
    """
    from StockAnalysis import auth, StockAnalysis

    app.register_blueprint(auth.bp)
    app.register_blueprint(StockAnalysis.bp)

    # make url_for('index') == url_for('blog.index')
    # in another app, you might define a separate main index here with
    # app.route, while giving the blog blueprint a url_prefix, but for
    # the tutorial the blog will be the main index
    app.add_url_rule("/", endpoint="home")

    return app