// This will be the object that will contain the Vue attributes
// and be used to initialize it.
let app = {};


// Given an empty app object, initializes it filling its attributes,
// creates a Vue instance, and then initializes the Vue instance.
let init = (app) => {

    // This is the Vue data.
    app.data = {
        // Complete as you see fit.
        trucks: [],
        review_add_text: "",
        review_add_mode: false,
    };

    app.enumerate = (a) => {
        // This adds an _idx field to each element of the array.
        let k = 0;
        a.map((e) => {
            e._idx = k++;
        });
        return a;
    };

    /*
    Reviews
     */

    app.add_review = function (t_idx) {
        let truck = app.vue.trucks[t_idx];
        axios.post(add_review_url,
            {   
                food_truck_id: truck.id,
                text: app.vue.review_add_text,
                // rating: num_stars,
            }).then(function (response) {
                truck.reviews.push({
                    id: response.data.id,
                    name: response.data.name,
                    text: app.vue.review_add_text,
                    _idx: truck.reviews.length
                });
                app.enumerate(truck.reviews);
                app.reset_form();
                app.set_add_status(false);
            });
    };
    
    app.delete_review = function(t_idx, r_idx) {
        let truck = app.vue.trucks[t_idx];
        let id = truck.reviews[r_idx].id;
        axios.get(delete_review_url, {params: {id: id}}).then(function (response) {
            for (let i = 0; i < truck.reviews.length; i++) {
                if (truck.reviews[i].id === id) {
                    truck.reviews.splice(i, 1);
                    app.enumerate(truck.reviews);
                    break;
                }
            }
        });
    };
    app.reset_form = function () {
        app.vue.review_add_text = "";
    };
    app.set_add_status = function (new_status) {
        app.vue.review_add_mode = new_status;
    };
    // app.init_reviews = (review) => {
    //     // Initialize the review to have 0 stars and display
    //     review.map((rev) => {
    //         rev.rating = 0;
    //         rev.num_stars_display = 0;
    //     })
    // };
    //
    // // This function will set the star rating for the
    // // app.set_star_rating = (review_idx, num_stars) => {
    // //     // Get the review in question
    // //     let review = app.vue.reviews[review_idx];
    // //     review.rating = num_stars;
    // //     // Update the tables in models with this post request with the info
    // //     axios.post(vue_set_review_url, {review_id: review.id, rating: num_stars});
    // // };
    //
    // app.stars_out = (review_idx) => {
    //     let rev = app.vue.reviews[review_idx];
    //     rev.num_stars_display = rev.rating;
    // };
    // // Function to display how many stars when hovered over the rating
    // app.stars_over = (review_idx, num_stars) => {
    //     let rev = app.vue.reviews[review_idx];
    //     rev.num_stars_display = num_stars;
    // };

    /*
    Food Truck AJAX
     */

    app.complete_truck = (trucks) => {
        trucks.map((truck) => {
            truck.reviews = [];
            truck.expanded = false;
        });
    }

    app.toggle_expand_truck = (idx) => {
        let truck = app.vue.trucks[idx];
        truck.expanded = true;
    };

    // This contains all the methods.
    app.methods = {
        // stars_out: app.stars_out,
        // stars_over: app.stars_over,
        add_review: app.add_review,
        set_add_status: app.set_add_status,
        delete_review: app.delete_review,
        toggle_expand_truck: app.toggle_expand_truck,
    };

    // This creates the Vue instance.
    app.vue = new Vue({
        el: "#vue-target",
        data: app.data,
        methods: app.methods
    });

    // And this initializes it.
    app.init = () => {
        // Put here any initialization code.
        // Typically this is a server GET call to load the data.

        // Load the food trucks, then for each food truck, load the reviews
        axios.get(load_trucks_url).then((result) => {
            let trucks = result.data.trucks;
            app.enumerate(trucks);
            app.complete_truck(trucks);
            app.vue.trucks = trucks;
            //console.log(app.vue.trucks);
        }).then(() => {
            for (let truck of app.vue.trucks) {
                // load review for that truck
                let food_truck_id = truck.id;
                axios.get(load_reviews_url, {params: {food_truck_id: food_truck_id}}).then((response) => {
                    if (response.data.reviews != []){
                        console.log(response.data.reviews)
                    }
                    truck.reviews = response.data.reviews;
                    
                })
            }
        });
    };

    // Call to the initializer.
    app.init();
};

// This takes the (empty) app object, and initializes it,
// putting all the code i
init(app);

/* Google Map */

let map;

function initMap() {
    let map = new google.maps.Map(document.getElementById("map"), {
        center: {lat: 36.968, lng: -122.057},
        zoom: 14,
    });

    let marker1 = new google.maps.Marker({
        position: {lat: 36.960134, lng: -122.0177475},
        map,
        title: "Hello World!",
    });
}

window.initMap = initMap;