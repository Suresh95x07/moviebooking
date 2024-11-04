import streamlit as st
import pandas as pd
import requests

# Function to display splash screen
def splash_screen():
    st.title("Welcome to Movie Booking System")

# Function to register user or admin
def register(role):
    st.subheader(f"Register as {role.capitalize()}")
    name = st.text_input("Name")
    email = st.text_input("Email")
    mobile_number = st.text_input("Mobile Number")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Register"):
        user_data = {
            "name": name,
            "email": email,
            "mobile_number": mobile_number,
            "username": username,
            "password": password
        }
        response = requests.post(f'http://localhost:5000/{role}/register', json=user_data)
        if response.status_code == 201:
            st.success(f"{role.capitalize()} registered successfully!")
        else:
            st.error("Registration failed")

# Function to login user or admin
def login(role):
    st.subheader(f"Login as {role.capitalize()}")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        login_data = {"username": username, "password": password}
        response = requests.post(f'http://localhost:5000/{role}/login', json=login_data)

        if response.status_code == 200:
            st.success("Logged in successfully!")
            st.session_state["role"] = role
            st.session_state["username"] = username
            st.rerun()
        else:
            st.error("Login failed")

# Function to display login or register options
def auth_page():
    st.sidebar.title("Authentication")
    role = st.sidebar.radio("Choose role", ["user", "admin"])
    auth_option = st.sidebar.selectbox("Choose option", ["Login", "Register"])

    if auth_option == "Register":
        register(role)
    else:
        login(role)

# Function to display user details
def user_sidebar():
    st.sidebar.title(f"Welcome, {st.session_state['username']}!")
    st.sidebar.subheader("User Details")
    username = st.session_state["username"]

    try:
        response = requests.get(f'http://localhost:5000/users/{username}')
        if response.status_code == 200:
            user_details = response.json()
            st.sidebar.write(f"Name: {user_details['name']}")
            st.sidebar.write(f"Email: {user_details['email']}")
            st.sidebar.write(f"Mobile Number: {user_details['mobile_number']}")
        else:
            st.sidebar.write("No user details available.")
    except Exception as e:
        st.sidebar.write("Error fetching user details:", str(e))

    if st.sidebar.button("Logout"):
        del st.session_state["username"]
        del st.session_state["role"]
        st.rerun()

# Function to display admin details
def admin_sidebar():
    st.sidebar.title(f"Welcome, {st.session_state['username']}!")
    st.sidebar.subheader("Admin Details")
    admin_id = st.session_state.get("admin_id",2)  # Use the stored admin_id, default to 1

    try:
        # Fetch admin details based on admin_id
        response = requests.get(f'http://127.0.0.1:5000/admin?admin_id={admin_id}')
        if response.status_code == 200:
            admin_details = response.json()
            admin_details.pop('_id', None)  # Remove _id if it exists
            for key, value in admin_details.items():
                st.sidebar.write(f"**{key.capitalize()}:** {value}")
        else:
            st.sidebar.write("No admin details available.")
    except Exception as e:
        st.sidebar.write("Error fetching admin details:", str(e))

    if st.sidebar.button("Logout"):
        del st.session_state["username"]
        del st.session_state["role"]
        del st.session_state["theatre"]
        st.sidebar.header("Admin Actions")
        if "theatre" in st.session_state:
            del st.session_state["theatre"]  # Clear theatre on logout
        st.session_state.clear()  # Optionally clear all session state
        st.success("Logged out successfully.")
        # Clear admin_id on logout
        st.rerun()

# Function to display movie search and booking interface
def movie_search_and_book():
    st.header("Search Movies")

    # Fetch movies
    movies_response = requests.get('http://localhost:5000/movies')
    movies = movies_response.json()
    movies_df = pd.DataFrame(movies)

    # Dropdown for selecting movie, genre, and theatre
    search_movie = st.selectbox("Select Movie Title", [""] + list(movies_df['title'].unique()))
    search_genre = st.selectbox("Select Genre", [""] + list(movies_df['genre'].unique()))
    search_theatre = st.selectbox("Select Theatre", [""] + list(movies_df['theatre'].unique()))

    # Filter movies based on search criteria
    filtered_movies = movies_df
    if search_movie:
        filtered_movies = filtered_movies[filtered_movies['title'] == search_movie]
    if search_genre:
        filtered_movies = filtered_movies[filtered_movies['genre'] == search_genre]
    if search_theatre:
        filtered_movies = filtered_movies[filtered_movies['theatre'] == search_theatre]

    if not filtered_movies.empty:
        st.subheader("Filtered Movies")
        st.dataframe(filtered_movies[['title', 'genre', 'theatre']])
    else:
        st.write("No movies found for the selected criteria.")

    if search_theatre and search_movie:
        showtimes = ["Morning (10 AM)", "Afternoon (1 PM)", "Evening (4 PM)", "Night (7 PM)"]
        selected_showtime = st.selectbox("Select Show Time", showtimes)

        availability_response = requests.get(f'http://localhost:5000/availability/{search_theatre}/{search_movie}')
        if availability_response.status_code == 200:
            available_seats_count = availability_response.json().get('available_seats', 0)
            available_seats = list(range(1, available_seats_count + 1))

            st.write(f"Available Seats: {available_seats}")

            selected_seats = st.session_state.get('selected_seats', [])
            if available_seats:
                cols = st.columns(10)
                for seat_number in available_seats:
                    col = cols[(seat_number - 1) % 10]
                    if col.button(str(seat_number), key=f"seat_{seat_number}"):
                        if seat_number not in selected_seats:
                            selected_seats.append(seat_number)
                        else:
                            selected_seats.remove(seat_number)
                        st.session_state['selected_seats'] = selected_seats

                st.write("Selected Seats: ", selected_seats)

                # Request total price from the backend
                try:
                    total_price_response = requests.post('http://localhost:5000/book', json={
                        "seats": len(selected_seats),
                        "theatre": search_theatre,
                        "movie": search_movie,
                    })

                    if total_price_response.status_code == 200:
                        total_price = total_price_response.json().get('total_price', 0)
                        st.write(f"Total Price: {total_price} INR")
                    else:
                        st.error("Failed to retrieve total price.")
                        total_price = None
                except requests.exceptions.RequestException:
                    st.error("Error connecting to the backend.")
                    total_price = None

                payment_option = st.selectbox("Select Payment Option", ["Card", "Net Banking", "PayPal", "Pay Later"])

                if st.button("Book") and selected_seats and total_price is not None:
                    booking_response = requests.post('http://localhost:5000/book', json={
                        "movie": search_movie,
                        "seats": len(selected_seats),
                        "theatre": search_theatre,
                        "total_price": total_price,
                        "payment_method": payment_option
                    })

                    if booking_response.status_code == 200:
                        booking_data = booking_response.json()
                        st.success(f"Booking successful! You booked {len(selected_seats)} seats.")
                        st.write(f"Payment Method: {payment_option}")
                        display_booking_details(
                            booking_data['movie'],
                            booking_data['theatre'],
                            booking_data['seats'],
                            selected_showtime,
                            selected_seats,
                            booking_data['total_price']
                        )
                    else:
                        st.error("Booking failed.")
            else:
                st.write("No seats available for this show.")
        else:
            st.error("Error fetching seat availability.")

# Function to display booking details
def display_booking_details(movie, theatre, seats, showtime, selected_seats, total_price):
    st.subheader("Your Booking Details")
    booking_df = pd.DataFrame([{
        "Movie": movie,
        "Theatre": theatre,
        "Seats Booked": seats,
        "Show Time": showtime,
        "Selected Seats": ", ".join(map(str, selected_seats)),
        "Total Price": total_price
    }])
    st.dataframe(booking_df)


# Sample movie data
movies_data = [
    {'title': 'The Shawshank Redemption', 'genre': 'Drama', 'language': 'English', 'theatre': 'AMC Mainstreet 6'},
    {'title': 'The Godfather', 'genre': 'Crime', 'language': 'English', 'theatre': 'AMC Mainstreet 6'},
    {'title': 'The Dark Knight', 'genre': 'Action', 'language': 'English', 'theatre': 'Alamo Drafthouse Cinema'},
    {'title': 'Pulp Fiction', 'genre': 'Crime', 'language': 'English', 'theatre': 'Union Station Extreme Screen'},
    {'title': 'Inception', 'genre': 'Sci-Fi', 'language': 'English', 'theatre': 'B&B Theatres Mainstreet KC'},
    {'title': 'Avengers: Endgame', 'genre': 'Action', 'language': 'English', 'theatre': 'Regal Kansas City'},
    {'title': 'The Matrix', 'genre': 'Sci-Fi', 'language': 'English', 'theatre': 'Cinetopia Overland Park 18'}
]

# Sample seat availability for each movie at each theater
seat_availability = {
    ('AMC Mainstreet 6', 'The Shawshank Redemption'): 100,
    ('AMC Mainstreet 6', 'The Godfather'): 50,
    ('Alamo Drafthouse Cinema', 'The Dark Knight'): 75,
    ('Alamo Drafthouse Cinema', 'Pulp Fiction'): 35,
    ('Rio Theatre', 'The Matrix'): 35,
    ('Regal Union Square', 'The Matrix'): 100,
    ('Cinemark Tinseltown', 'Inception'): 10,
}

# Sample dataset for theatres with base prices
theatre_data = [
    {"theatre": "AMC Mainstreet 6", "base_price": 12},
    {"theatre": "Regal Union Square", "base_price": 15},
    {"theatre": "Cinemark Tinseltown", "base_price": 10},
    {"theatre": "Alamo Drafthouse Cinema", "base_price": 15},
    {"theatre": "Rio Theatre", "base_price": 25},
]


def admin_dashboard():
    st.header("Admin Dashboard")

    # Extract theatre names for dropdown
    theatre_names = [theater['theatre'] for theater in theatre_data]
    selected_theatre = st.selectbox("Select Theatre", theatre_names)

    if selected_theatre:
        # Filter movies for the selected theatre
        filtered_movies = [movie for movie in movies_data if movie['theatre'] == selected_theatre]
        movie_titles = [movie['title'] for movie in filtered_movies]

        if movie_titles:
            selected_movie = st.selectbox("Select Movie", movie_titles)

            if selected_movie:
                # Get seat availability for the selected theatre and movie
                seats_available = seat_availability.get((selected_theatre, selected_movie), "N/A")
                # Get price for the selected theatre
                price_info = next((theater for theater in theatre_data if theater["theatre"] == selected_theatre), None)
                price = price_info['base_price'] if price_info else "N/A"

                # Display availability and pricing
                st.write(f"**Availability for {selected_movie}:** {seats_available} seats available.")
                st.write(f"**Price for {selected_movie} at {selected_theatre}:** ${price}")

        else:
            st.write("No movies available for this theatre.")

splash_screen()

if 'role' not in st.session_state:
    auth_page()  # Calls the authentication page function
else:
    role = st.session_state["role"]

    if role == "user":
        user_sidebar()
        movie_search_and_book()
    elif role == "admin":
        admin_sidebar()
        admin_dashboard()
