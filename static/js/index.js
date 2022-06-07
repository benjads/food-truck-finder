// This will be the object that will contain the Vue attributes
// and be used to initialize it.
let app = {};


// Given an empty app object, initializes it filling its attributes,
// creates a Vue instance, and then initializes the Vue instance.
let init = (app) => {

    // This is the Vue data.
    app.data = {
        trucks: [],
        query: "",
        q_truck_results: [],
        q_cuisine_results: [],
        expanded: -1,
        
        // Upload Images
        selection_done: false,
        selected_image: null,

        uploaded_file: "",
        uploaded: false,
        encoded_image: "",
        review_add_text: "",
        review_add_rating: 0,
        review_rating_display: 0,
        review_add_mode: false,
        current_user: null,
    };

    app.enumerate = (a) => {
        // This adds an _idx field to each element of the array.
        let k = 0;
        a.map((e) => {
            e._idx = k++;
        });
        return a;
    };

    // Function for the search bar, returns the list of food truck names that the person searches for
    app.search = function () {
        // If the user searches for something, then this would return the result
        if (app.vue.query.length > 1) {
            axios.get(search_url, {params: {q: app.vue.query}}).then(function (result) {
                // This returns [truck name, truck id]
               app.vue.q_truck_results = result.data.truck_results;
               app.vue.q_cuisine_results = result.data.cuisine_results;
            });
        // If the user doesn't search for anything, then don't result anything
        } else {
            app.vue.q_truck_results = [];
            app.vue.q_cuisine_results = [];
        }
    };


    /*
    Reviews
     */

    app.add_review = function (t_idx) {
        let truck = app.vue.trucks[t_idx];
        app.upload_complete();
        axios.post(add_review_url,
            {
                food_truck_id: truck.id,
                text: app.vue.review_add_text,
                stars: app.vue.review_add_rating,
                encoded_image: app.vue.encoded_image,
                // rating: num_stars,
            }).then(function (response) {
                truck.reviews.push({
                    id: response.data.id,
                    name: response.data.name,
                    created_by: response.data.created_by,
                    encoded_image: app.vue.encoded_image,
                    text: app.vue.review_add_text,
                    stars: app.vue.review_add_rating,
                    _idx: truck.reviews.length
                });
                app.enumerate(truck.reviews);
                truck.avg_rating = app.get_avg_rating(truck._idx);
                app.reset_form();
                app.set_add_status(false);
            });
    };
    // Upload Images (w/ preview)
    app.select_file = function (event) {
        // Reads the file.
        let input = event.target;
        app.vue.selected_image = input.files[0];
        if (app.vue.selected_image) {
            app.vue.selection_done = true;
            // We read the file.
            let reader = new FileReader();
            reader.addEventListener("load", function () {
                app.vue.encoded_image = reader.result;
            });
            reader.readAsDataURL(app.vue.selected_image);
        }
    };

    app.upload_complete = function () {
        app.vue.uploaded = true;
    };
    app.set_stars = (num_stars) => {
        app.vue.review_add_rating = num_stars;
    };
    app.stars_out = () => {
        app.vue.review_rating_display = app.vue.review_add_rating;
    };
    app.stars_over = (num_stars) => {
        if(num_stars != undefined){
            app.vue.review_rating_display = num_stars;
        }

    };
    app.get_avg_rating = (t_idx) => {
        let reviews = app.vue.trucks[t_idx].reviews;
        if(reviews.length == 0){
            return 0
        }
        let avg = 0;

        for(let review of reviews){
            avg += review.stars;
        }
        return (avg/(reviews.length))
    };
    app.reset_form = function () {
        app.vue.review_add_text = "";
        app.vue.review_add_rating = 0;
        app.vue.review_rating_display = 0;
        app.vue.uploaded = false;
        app.vue.encoded_image = "";
        app.vue.selection_done= false;
    };
    app.set_add_status = function (new_status) {
        app.vue.review_add_mode = new_status;
    };

    app.delete_review = function(t_idx, r_idx) {
        let truck = app.vue.trucks[t_idx];
        let id = truck.reviews[r_idx].id;
        axios.get(delete_review_url, {params: {id: id}}).then(function (response) {
            for (let i = 0; i < truck.reviews.length; i++) {
                if (truck.reviews[i].id === id) {
                    truck.reviews.splice(i, 1);
                    app.enumerate(truck.reviews);
                    truck.avg_rating = app.get_avg_rating(truck._idx);
                    break;
                }
            }
        });
    };
    /*
    Food Truck AJAX
     */

    app.complete_truck = (trucks) => {
        trucks.map((truck) => {
            truck.reviews = [];
            truck.images = [];
            truck.hours = {};
            truck.expanded = false;
            truck.avg_rating = 0;
            truck.marker = null;
        });
        app.vue.current_user = null;
    }

    // This is for the search bar map expanding
    app.search_toggle_expand_truck = (index) => {
        let truck = app.vue.trucks[index - 1];
        if (truck.expanded == false) {
            truck.expanded = true;
            map.setZoom(16);
            map.panTo(truck.marker.position);
            // Once the user clicks on a food truck, get rid of the results, but keep the search term
            app.vue.q_truck_results = [];
            app.vue.q_cuisine_results = [];
        } else {
            truck.expanded = false;
            map.setZoom(14);
            // Remove this if you just want to zoom out
            // map.panTo({lat: 36.968, lng: -122.057}); // Centers the map back to original position
        }
        // truck.expanded = !truck.expanded;
        // map.setZoom(16);
        // map.panTo(truck.marker.position);
    };

    // This is for the sidebar to expand the map when clicked on
    app.toggle_expand_truck = (idx) => {
        let truck = app.vue.trucks[idx];
        // If we weren't zoomed in, now we want to zoom in, otherwise zoom out
        if (truck.expanded == false) {
            truck.expanded = true;
            map.setZoom(16);
            map.panTo(truck.marker.position);
        } else {
            truck.expanded = false;
            map.setZoom(14);
            // Remove this if you just want to zoom out
            // map.panTo({lat: 36.968, lng: -122.057}); // Centers the map back to original position
        }
        // The original function to just zoom in
        // truck.expanded = !truck.expanded; // TODO figure out how to toggle only when clicking outside of card
        // map.setZoom(16);
        // map.panTo(truck.marker.position);
    };

    

    // This contains all the methods.
    app.methods = {
        add_review: app.add_review,
        delete_review: app.delete_review,
        select_file: app.select_file,
        set_stars: app.set_stars,
        stars_out: app.stars_out,
        stars_over: app.stars_over,
        get_avg_rating: app.get_avg_rating,
        set_add_status: app.set_add_status,
        toggle_expand_truck: app.toggle_expand_truck,
        search: app.search,
        select_file: app.select_file,
        search_toggle_expand_truck: app.search_toggle_expand_truck,
    };

    // This creates the Vue instance.
    app.vue = new Vue({
        el: "#vue-target",
        data: app.data,
        methods: app.methods
    });

    // And this initializes it.
    app.init = () => {

    };

    // Call to the initializer.
    app.init();
};


// This takes the (empty) app object, and initializes it,
// putting all the code i
init(app);

/* Google Map */

let map;

function initGoogle() {
    map = new google.maps.Map(document.getElementById("map"), {
        center: {lat: 36.968, lng: -122.057},
        zoom: 14,
        styles: [
            {
                featureType: "poi",
                stylers: [
                    {visibility: "off"}
                ]
            }
        ]
    });

    axios.get(load_trucks_url).then((result) => {
            let trucks = result.data.trucks;
            app.enumerate(trucks);
            app.complete_truck(trucks);
            app.vue.trucks = trucks;
            app.vue.current_user = result.data.current_user;
        }).then(() => {
            for (let truck of app.vue.trucks) {
                // add marker
                 truck.marker = new google.maps.Marker({
                    position: {lat: truck.lat, lng: truck.lng},
                    map,
                    title: truck.name,
                    icon: 'img/ftf_marker.png',
                });

                // load review for that truck
                let food_truck_id = truck.id;

                axios.get(load_reviews_url,
                    {params: {food_truck_id: food_truck_id}}
                ).then( (response) => {
                    truck.reviews = response.data.reviews;
                    app.enumerate(truck.reviews)
                    truck.avg_rating = app.get_avg_rating(truck._idx);
                });
                // load the hours for the food truck
                axios.get(load_truck_hours_url, {params: {food_truck_id: food_truck_id}}).then( (result) => {
                    truck.hours = result.data.hours;
                });


            }
        });
}

window.initGoogle = initGoogle;