"""
This file defines the database models
"""

import datetime
from .common import db, Field, auth
from pydal.validators import *


def get_user_email():
    return auth.current_user.get('email') if auth.current_user else None


def get_time():
    return datetime.datetime.utcnow()


db.define_table(
    'food_truck',
    # food truck ID
    Field('availability', requires=IS_NOT_EMPTY()),
    Field('location', requires=IS_NOT_EMPTY()),
    Field('food_type', requires=IS_NOT_EMPTY()),
    Field('phone_number'),  # optional
    Field('email'),  # optional
    Field('website')  # optional (can be link to website, instagram, etc)
)
db.food_truck.id.readable = db.food_truck.id.writable = False

# Food truck hours
db.define_table(
    'food_truck_hours',
    Field('food_truck_id', 'reference food_truck', ondelete='CASCADE'),
    Field('dotw', requires=IS_NOT_EMPTY()),  # day of the week
    Field('open_time', requires=IS_NOT_EMPTY()),
    Field('close_time')
)

db.food_truck_hours.id.readable = db.food_truck_hours.id.writable = False

db.commit()
