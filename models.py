"""
This file defines the database models
"""

import datetime
from .common import db, Field, auth
from pydal.validators import *


def get_user_email():
    return auth.current_user.get('email') if auth.current_user else None


def get_user():
    return auth.current_user.get('id') if auth.current_user else None


def get_time():
    return datetime.datetime.utcnow()


cuisines = ['Italian', 'Mediterranean', 'German', 'Mexican', 'Thai', 'Chinese', 'Indian', 'Japanese',
            'Korean', 'Vietnamese', 'American']
diets = ['None', 'Vegetarian', 'Vegan', 'Pescatarian', 'Gluten-free', 'Kosher', 'Halal']

# Table for a single food truck
db.define_table(
    'food_truck',
    # food truck ID
    Field('name', requires=IS_NOT_EMPTY()),
    Field('thumbnail', default=''), # Image of food truck for listing
    Field('address', requires=IS_NOT_EMPTY()),
    Field('cuisine_type', requires=IS_IN_SET(cuisines, multiple=True)),
    Field('dietary_options', requires=IS_IN_SET(diets, multiple=True), default=''),
    Field('lat', 'double', requires=IS_FLOAT_IN_RANGE(-1e100, 1e100)),
    Field('lng', 'double', requires=IS_FLOAT_IN_RANGE(-1e100, 1e100)),
    Field('phone_number', requires=IS_NOT_EMPTY()),
    Field('email', requires=IS_EMAIL()),
    Field('website', requires=IS_URL()),
    Field('created_by', default=get_user_email),  # links the foodtruck to email it is created by
)

# Food truck hours for that single food truck
db.define_table(
    'food_truck_hours',
    Field('food_truck_id', 'reference food_truck', ondelete='CASCADE'),
    Field('dotw', requires=IS_NOT_EMPTY()),  # day of the week
    Field('open_time', requires=IS_NOT_EMPTY()),
    Field('close_time')
)

# Database table
db.define_table(
    'review',
    Field('food_truck_id', 'reference food_truck', ondelete='CASCADE'),
    Field('stars', 'integer', IS_INT_IN_RANGE(0, 5), requires=IS_NOT_EMPTY()),  # The star rating 0-5
    Field('text', requires=IS_NOT_EMPTY()),  # The review
    Field('name'),   #The name
    Field('encoded_image', default=''), # image linked to review
    Field('created_by', 'reference auth_user', requires=IS_NOT_EMPTY(), ondelete='CASCADE', default=get_user) # 'reference auth_user' causes my thing to break idk why
)

#DB: Food truck
db.food_truck.id.readable = db.food_truck.id.writable = False
db.food_truck.created_by.readable = db.food_truck.created_by.writable = False

# DB: Food Truck Hours
db.food_truck_hours.id.readable = db.food_truck_hours.id.writable = False
# db.food_truck_hours.food_truck_id.readable = db.food_truck_hours.food_truck_id.writable = False

# DB: Review
db.review.id.readable = db.review.id.writable = False
db.review.food_truck_id.readable = db.review.food_truck_id.writable = False
db.review.created_by.readable = db.review.created_by.writable = False

db.commit()
