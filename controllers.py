"""
This file defines actions, i.e. functions the URLs are mapped into
The @action(path) decorator exposed the function at URL:

    http://127.0.0.1:8000/{app_name}/{path}

If app_name == '_default' then simply

    http://127.0.0.1:8000/{path}

If path == 'index' it can be omitted:

    http://127.0.0.1:8000/

The path follows the bottlepy syntax.

@action.uses('generic.html')  indicates that the action uses the generic.html template
@action.uses(session)         indicates that the action uses the session
@action.uses(db)              indicates that the action uses the db
@action.uses(T)               indicates that the action uses the i18n & pluralization
@action.uses(auth.user)       indicates that the action requires a logged in user
@action.uses(auth)            indicates that the action requires the auth object

session, db, T, auth, and tempates are examples of Fixtures.
Warning: Fixtures MUST be declared with @action.uses({fixtures}) else your app will result in undefined behavior
"""

import re
from py4web import action, request, abort, redirect, URL, Field
from yatl.helpers import A

from py4web.utils.form import *
from .common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash
from py4web.utils.url_signer import URLSigner
from .models import get_user_email, get_user, cuisines, diets, dotws
from pydal.validators import *

# For search bar functionality
import uuid
import random

url_signer = URLSigner(session)


# Main webpage End points  ##############################
@action('index')
@action.uses('index.html', db, auth, url_signer)
def index():
    return dict(
        # COMPLETE: return here any signed URLs you need.
        load_trucks_url=URL('load-trucks', signer=url_signer),
        add_review_url=URL('add-review', signer=url_signer),
        view_reviews_url=URL('view-reviews'),
        delete_review_url=URL('delete-review', signer=url_signer),
        load_reviews_url=URL('load-reviews', signer=url_signer),
        search_url=URL('search', signer=url_signer),
        upload_thumbnail_url=URL('upload_thumbnail', signer=url_signer),
        load_truck_hours_url=URL('load_truck_hours', signer=url_signer),
    )


@action('about-us')
@action.uses('about-us.html', db, auth, url_signer)
def about_us():
    return dict()


# Food Truck Listing End Points #########################################
# Create food truck listing form
@action('add-listing', method=["GET", "POST"])
@action.uses('edit-listing.html', db, session, auth.user, url_signer)
def add_listing():
    # dotws = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
    # cuisines = ['Italian', 'Mediterranean', 'German', 'Mexican', 'Thai', 'Chinese', 'Indian', 'Japanese',
    #             'Korean', 'Vietnamese', 'American'
    #             ]
    # diets = ['None', 'Vegetarian', 'Vegan', 'Pescatarian', 'Gluten-free', 'Kosher', 'Halal', ]

    fields = [
        Field('name', requires=IS_NOT_EMPTY()),
        Field('thumbnail'),
        Field('address', requires=IS_NOT_EMPTY()),
        Field('lat', requires=IS_NOT_EMPTY()),
        Field('lng', requires=IS_NOT_EMPTY()),
        Field('cuisine_type', requires=IS_IN_SET(cuisines)),
        Field('dietary_options', requires=IS_IN_SET(diets)),
        Field('phone_number', requires=IS_NOT_EMPTY()),
        Field('email', requires=IS_EMAIL()),
        Field('website', requires=IS_URL())
    ]
    for dotw in dotws:
        fields.append(Field('hours_' + dotw + '_open'))
        fields.append(Field('hours_' + dotw + '_close'))
    FormStyleBootstrap4.widgets['cuisine_type'] = SelectWidget()
    form = Form(fields, csrf_session=session, formstyle=FormStyleBootstrap4)

    if form.accepted:
        food_truck_id = db.food_truck.insert(
            name=form.vars['name'],
            thumbnail=form.vars['thumbnail'],
            address=form.vars['address'],
            lat=form.vars['lat'],
            lng=form.vars['lng'],
            cuisine_type=form.vars['cuisine_type'],
            dietary_options=form.vars['dietary_options'],
            phone_number=form.vars['phone_number'],
            email=form.vars['email'],
            website=form.vars['website']
        )

        for dotw in dotws:
            open_time = form.vars['hours_' + dotw + '_open']
            close_time = form.vars['hours_' + dotw + '_close']

            if open_time == '' or close_time == '':
                continue

            db.food_truck_hours.insert(
                food_truck_id=food_truck_id,
                dotw=dotw,
                open_time=open_time,
                close_time=close_time
            )

        redirect(URL('manage-listings'))
    else: # debug
        print('FAILED TO ADD FORM')

    # Either this is a GET request, or this is a POST but not accepted = with errors.
    return dict(action_name='Add', form=form)


# End point to see all of your listings/food trucks
@action('manage-listings')
@action.uses('manage-listings.html', db, session, auth.user, url_signer)
def manage_listing():
    trucks = db(db.food_truck.created_by == get_user_email()).select()

    return dict(trucks=trucks, url_signer=url_signer)


# End point to edit 1 specific listing/food truck
@action('edit-listing/<food_truck_id:int>', method=["GET", "POST"])
@action.uses('edit-listing.html', db, session, auth.user, url_signer)
def edit_listing(food_truck_id=None):
    assert food_truck_id is not None

    curr = db.food_truck[food_truck_id]
    if curr is None:
        redirect(URL('index'))

    # dotws = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
    # list of cuisine types here
    # cuisines = ['Italian', 'Mediterranean', 'German', 'Mexican', 'Thai', 'Chinese', 'Indian', 'Japanese',
    #             'Korean', 'Vietnamese', 'American'
    #             ]
    # diets = ['None', 'Vegetarian', 'Vegan', 'Pescatarian', 'Gluten-free', 'Kosher', 'Halal']

    fields = [
        Field('name', requires=IS_NOT_EMPTY()),
        Field('thumbnail'),
        Field('address', requires=IS_NOT_EMPTY()),
        Field('cuisine_type', requires=IS_IN_SET(cuisines)),
        Field('dietary_options', requires=IS_IN_SET(diets)),
        Field('lat', requires=IS_NOT_EMPTY()),
        Field('lng', requires=IS_NOT_EMPTY()),
        Field('phone_number', requires=IS_NOT_EMPTY()),
        Field('email', requires=IS_EMAIL()),
        Field('website', requires=IS_URL())
    ]
    for dotw in dotws:
        fields.append(Field('hours_' + dotw + '_open'))
        fields.append(Field('hours_' + dotw + '_close'))
    # iterate over our cuisine list, append
    # for cuisine in cuisines:
    #     fields.append(Field(cuisine))

    record = curr
    hours_records = db(db.food_truck_hours.food_truck_id == curr.id).select()
    for hours_record in hours_records:
        record['hours_' + hours_record.dotw + '_open'] = hours_record.open_time
        record['hours_' + hours_record.dotw + '_close'] = hours_record.close_time
    FormStyleBootstrap4.widgets['cuisine_type'] = SelectWidget()
    form = Form(fields, record=curr, deletable=False, csrf_session=session, formstyle=FormStyleBootstrap4)
    if form.accepted:
        db.food_truck.update_or_insert(
            curr.id,
            name=form.vars['name'],
            thumbnail=form.vars['thumbnail'],
            address=form.vars['address'],
            lat=form.vars['lat'],
            lng=form.vars['lng'],
            cuisine_type=form.vars['cuisine_type'],
            dietary_options=form.vars['dietary_options'],
            phone_number=form.vars['phone_number'],
            email=form.vars['email'],
            website=form.vars['website']
        )

        for dotw in dotws:
            open_time = form.vars['hours_' + dotw + '_open']
            close_time = form.vars['hours_' + dotw + '_close']

            if open_time == '' or close_time == '':
                continue

            db.food_truck_hours.update_or_insert(
                ((db.food_truck_hours.food_truck_id == curr.id) & (db.food_truck_hours.dotw == dotw)),
                food_truck_id=curr.id,
                dotw=dotw,
                open_time=open_time,
                close_time=close_time
            )

        redirect(URL('manage-listings'))
    # Either this is a GET request, or this is a POST but not accepted = with errors.
    return dict(action_name='Edit', form=form)


# The endpoint for the customer to delete a food truck listing
@action('delete-listing/<food_truck_id:int>')
@action.uses(db, session, auth.user, url_signer.verify())
def delete_listing(food_truck_id=None):
    assert food_truck_id is not None
    db(db.food_truck.id == food_truck_id).delete()
    # How do we get the POST body?
    redirect(URL('manage-listings'))


@action('load-trucks')
@action.uses(db, auth)
def load_trucks():
    trucks = db(db.food_truck).select().as_list()
    return dict(trucks=trucks, current_user=get_user())


# This is our very first API function.
@action('load-reviews')
@action.uses(url_signer.verify(), db, auth)
def load_reviews():
    truck_id = request.params.get('food_truck_id')
    reviews = db(db.review.food_truck_id == truck_id).select().as_list()

    return dict(reviews=reviews)


# This is our very first API function.
@action('load-images')
@action.uses(url_signer.verify(), db, auth)
def load_images():
    truck_id = request.params.get('food_truck_id')
    images = db(db.image.food_truck_id == truck_id).select().as_list()

    return dict(images=images)


# The endpoint for the customer to add a review
@action('add-review', method=["POST"])
@action.uses(db, auth.user, url_signer.verify())
def add_review():
    r = db(db.auth_user.id == get_user()).select().first()
    name = r.first_name + " " + r.last_name if r is not None else "Unknown"

    id = db.review.insert(
        food_truck_id=request.json.get('food_truck_id'),
        text=request.json.get('text'),
        encoded_image= request.json.get('encoded_image'),
        stars=request.json.get('stars'),
        created_by=get_user(),
        name=name,
    )
    return dict(id=id, name=name, created_by=get_user())

    # Either this is a GET request, or this is a POST but not accepted = with errors.
    # return dict(form=form, url_signer=url_signer)


@action('delete-review')
@action.uses(db, auth.user, url_signer.verify())
def delete_review():
    db(db.review.id == request.params.get('id')).delete()
    return "ok"

@action('view-reviews/<food_truck_id:int>') # <food_truck_id:int>
@action.uses('view-reviews.html', db, auth)
def view_reviews(food_truck_id):
    # All the reviews for the currents food truck
    trucks = db(db.food_truck.id == food_truck_id).select()
    reviews = db(db.review.food_truck_id == food_truck_id).select()
    truck = trucks[0] # trucks is a list of 1 object so we are just getting the single truck item

    return dict(truck=truck, reviews=reviews)

@action('view-activity')
@action.uses('view-activity.html', db, session, auth.user)
def view_activity():
    reviews = db(db.review.created_by == get_user).select()
    trucks = db(db.food_truck).select()
    truck_ids = []
    truck_objects = []

    # list of all food truck ids that user left review for
    for review in reviews:
        if not (review.food_truck_id in truck_ids):
            truck_ids.append(review.food_truck_id)

    for truck in trucks:
        if truck.id in truck_ids:
            truck_objects.append(truck)

    return dict(trucks=truck_objects, reviews=reviews, url_signer=url_signer)

# Vue End Point : returns a list of food truck names if they match the user's search term
@action('search')
@action.uses(db)
def search():
    # Get the user's search word, and db
    q = request.params.get("q")
    food_trucks = db(db.food_truck).select().as_list()
    # cuisine_trucks = db(db.food_truck).select().as_list()

    truck_results = []  # List for food truck names if the truck name matches
    cuisine_results = []  # List for food truck names if the cuisine type matches
    for truck in food_trucks:
        # If search term is a substring in the name, then append it to the return list
        if q.lower() in truck['name'].lower():
            truck_results.append([truck['name'], truck['id']])
        # If the search term matches with the cuisine type, then append it to the list
        if q.lower() in truck['cuisine_type'].lower() or q.lower() in truck['dietary_options'].lower():
            cuisine_results.append([truck['name'], truck['id']])

    return dict(truck_results=truck_results, cuisine_results=cuisine_results)

# Vue End Point : returns a list of hours for display
@action('load_truck_hours')
@action.uses(db)
def load_truck_hours():
    id = request.params.get("food_truck_id")
    table = db(db.food_truck_hours.food_truck_id == id).select()

    # Store the dictionary with strings of the times they open and close
    hours = {"Monday": None, "Tuesday": None, "Wednesday": None, "Thursday": None, 
            "Friday": None, "Saturday": None, "Sunday": None}
    for day in table:
        d = day['dotw']
        open_time = day['open_time']
        close_time = day['close_time']
        
        # Create a time string
        time = create_time(open_time, close_time)
        # Associate the time
        if d == "mon":
            hours["Monday"] = time
        elif d == "tue":
            hours["Tuesday"] = time
        elif d == "wed":
            hours["Wednesday"] = time
        elif d == "thu":
            hours["Thursday"] = time
        elif d == "fri":
            hours["Friday"] = time
        elif d == "sat":
            hours["Saturday"] = time
        elif d == "sun":
            hours["Sunday"] = time

    # Iterate over the dict, if someone didn't specify a time, the string is "Closed"
    for x in hours:
        if hours[x] == None:
            hours[x] = "Closed"

    return dict(hours=hours)

# Regular Expression Pattern matching to display the food truck's opening/closing times nicely
def create_time(opening, closing):

    a = ""
    b = ""

    # 00:00 -> 12:59 am
    # 13:00 -> 23:59 pm
    am = "(0[0-9]|1[0-2]:[0-5][0-9])"
    am2 = "(0[1-9]:[0-5][0-9])"
    pm = "(1[2-9]|2[0-3]:[0-5][0-9])"

    # Pattern match for opening
    if re.match(am, opening) is not None:
        if re.match(am2, opening) is not None:
            a = opening[1:] + "am"
        else:
            a = opening + "am"
    if re.match(pm, opening) is not None:
        left = opening[:-3]
        right = opening[3:]
        left = int(left)
        if left != 12:
            left -= 12
        a = str(left) + ":" + right + "pm"

    # Pattern match for closing
    if re.match(am, closing) is not None:
        if re.match(am2, closing) is not None:
            b = closing[1:] + "am"
        else:
            b = closing + "am"
    if re.match(pm, closing) is not None:
        left = closing[:-3]
        right = closing[3:]
        left = int(left)
        if left != 12:
            left -= 12
        b = str(left) + ":" + right + "pm"
    
    return a + " - " + b

