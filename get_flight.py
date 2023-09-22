# Import necessary modules
import requests
from get_token import access_token  # Import the access_token variable from get_token.py

# Define user information (you can replace this with actual user input)
user_info = {
    'departure': 'NBO',  # Replace with the departure airport code
    'destination': 'MBA',  # Replace with the destination airport code
    'departure_date': '2023-09-18',  # Replace with the departure date
    'return_date': '2023-09-18',  # Replace with the return date
    'adults': 1,  # Replace with the number of adults
    'travel_class': 'ECONOMY',  # Replace with the desired travel class
}

# Define the function to get flight offers
def get_flight_offers(user_info):
    # Define the API endpoint URL
    url = "https://test.api.amadeus.com/v2/shopping/flight-offers"

    # Prepare query parameters based on user input
    params = {
        "originLocationCode": user_info['departure'],
        "destinationLocationCode": user_info['destination'],
        "departureDate": user_info['departure_date'],
        "returnDate": user_info['return_date'],
        "adults": user_info['adults'],
        "travelClass": user_info['travel_class'],
    }

    # Make the API request to get flight offers with the specified query parameters
    headers = {
        "Authorization": f"Bearer {access_token}",  # Use the imported access_token variable
    }
    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200:
        flight_offers = response.json()

        # Extract and format flight data with additional information
        flight_data = []
        for i, offer in enumerate(flight_offers['data'], start=1):
            airline = offer['itineraries'][0]['segments'][0]['carrierCode']
            price = offer['price']['total']
            departure_time = offer['itineraries'][0]['segments'][0]['departure']['at']
            arrival_time = offer['itineraries'][0]['segments'][-1]['arrival']['at']
            plane_number = offer['itineraries'][0]['segments'][0]['number']
            duration = offer['itineraries'][0]['duration']

            # Get the number of available seats
            num_seats = offer['numberOfBookableSeats']

            flight_info = (
                f"{i}. Flight Airline: {airline} {plane_number}:\n"
                f"Origin: {user_info['departure']}, Destination: {user_info['destination']}, "
                f"Departure Time: {departure_time} Arrival Time: {arrival_time}\n"
                f"Duration: {duration} minutes\n"
                f"Price: {price} USD\n"
                f"Number of Available Seats: {num_seats}\n"
            )
            flight_data.append(flight_info)

        return flight_data
    else:
        return [f"Error in flight offers request: {response.status_code} - {response.text}"]

if __name__ == "__main__":
    flight_offers = get_flight_offers(user_info)
    for offer in flight_offers:
        print(offer)
