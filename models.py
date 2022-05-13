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


# Table for a single food truck
db.define_table(
    'food_truck',
    # food truck ID
    Field('availability', requires=IS_NOT_EMPTY()),
    Field('name', requires=IS_NOT_EMPTY()),
    Field('address', requires=IS_NOT_EMPTY()),
    Field('cuisine_type', requires=IS_NOT_EMPTY()),
    Field('phone_number'),  # optional
    Field('email'),  # optional
    Field('website')  # optional (can be link to website, instagram, etc)
)
db.food_truck.id.readable = db.food_truck.id.writable = False
# db.food_truck.availability.readable = db.food_truck.availability.writable = False
# db.food_truck.address.readable = db.food_truck.address.writable = False
# db.food_truck.cuisine_type.readable = db.food_truck.cuisine_type.writable = False


# Food truck hours for that single food truck
db.define_table(
    'food_truck_hours',
    Field('food_truck_id', 'reference food_truck', ondelete='CASCADE'),
    Field('dotw', requires=IS_NOT_EMPTY()),  # day of the week
    Field('open_time', requires=IS_NOT_EMPTY()),
    Field('close_time')
)

db.food_truck_hours.id.readable = db.food_truck_hours.id.writable = False

db.commit()