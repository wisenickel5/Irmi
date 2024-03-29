from flask import Flask

import config


app = Flask(__name__)
app.config.from_object(config)
app.config.from_mapping(SECRET_KEY='dev')
