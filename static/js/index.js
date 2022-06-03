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
        uploading: false,
        uploaded_file: "",
        uploaded: false,
        img_url: "",
        review_add_text: "",
        review_add_rating: 0,
        review_rating_display: 0,
        review_add_mode: false,
        logged_in: false,
        current_user: null,
    };

    // Upload Images: This tis the file selected for upload
    app.file = null;

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
        axios.post(add_review_url,
            {
                food_truck_id: truck.id,
                text: app.vue.review_add_text,
                stars: app.vue.review_add_rating,
                // rating: num_stars,
            }).then(function (response) {
                truck.reviews.push({
                    id: response.data.id,
                    name: response.data.name,
                    created_by: response.data.created_by,
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
            truck.expanded = false;
            truck.avg_rating = 0;
        });
        app.vue.current_user = null;
    }

    app.toggle_expand_truck = (idx) => {
        let truck = app.vue.trucks[idx];
        truck.expanded = !truck.expanded; // TODO figure out how to toggle only when clicking outside of card
    };

    // Upload Images
    app.select_file = function (event) {
        // Reads the file.
        let input = event.target;
        app.file = input.files[0];
        if (app.file) {
            app.vue.selection_done = true;
            // We read the file.
            let reader = new FileReader();
            reader.addEventListener("load", function () {
                app.vue.img_url = reader.result;
            });
            reader.readAsDataURL(app.file);
        }
    };

    app.upload_complete = function (file_name, file_type) {
        app.vue.uploading = false;
        app.vue.uploaded = true;
    };

    app.upload_file = function () {
        if (app.file) {
            let file_type = app.file.type;
            let file_name = app.file.name;
            let full_url = file_upload_url + "&file_name=" + encodeURIComponent(file_name)
                + "&file_type=" + encodeURIComponent(file_type);
            // Uploads the file, using the low-level streaming interface. This avoid any
            // encoding.
            app.vue.uploading = true;
            let req = new XMLHttpRequest();
            req.addEventListener("load", function () {
                app.upload_complete(file_name, file_type)
            });
            req.open("PUT", full_url, true);
            req.send(app.file);
        }
    };


    // This contains all the methods.
    app.methods = {
        add_review: app.add_review,
        set_stars: app.set_stars,
        stars_out: app.stars_out,
        stars_over: app.stars_over,
        get_avg_rating: app.get_avg_rating,
        set_add_status: app.set_add_status,
        delete_review: app.delete_review,
        toggle_expand_truck: app.toggle_expand_truck,
        search: app.search,
        select_file: app.select_file,
        upload_file: app.upload_file,
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

                axios.get(load_reviews_url,
                    {params: {food_truck_id: food_truck_id}}
                ).then( (response) => {
                    truck.reviews = response.data.reviews;
                    app.enumerate(truck.reviews)
                    truck.avg_rating = app.get_avg_rating(truck._idx);
                    app.vue.current_user = response.data.current_user;
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