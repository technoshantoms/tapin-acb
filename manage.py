#!/usr/bin/env python3

import sys
from flask import Flask
#from flask_script import Manager, Command
from app import app, db
from app import config
import threading
import os
from os import path

manager = Flask(__name__)

#manager = Manager(app)


@manager.cli.command
def install():
    database_dir = path.dirname(config.database)
    if len(database_dir) > 0 and not path.exists(database_dir):
        os.makedirs(database_dir)

    db.create_all()


@manager.cli.command
def run():
    app.run()


@manager.cli.command
def start():
    app.run(debug=True)


@manager.cli.command
def donations(start=None, end=None):
    import worker_donations
    worker_donations.run(start, end)


@manager.cli.command
def testmail():
    from flask_mail import Message
    from app import mail
    msg = Message("Hello",
                  sender=config.mail_from,
                  recipients=config.admins)
    mail.send(msg)


if __name__ == '__main__':
    #manager.run()
     pass