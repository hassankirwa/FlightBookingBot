from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests
from get_token import access_token  # Import the access_token variable from get_token.py
from fpdf import FPDF  # Import FPDF for creating PDFs


app = Flask(__name__)
app.config['ENV'] = 'production'


# Define the seat emoji
seat_emoji = "💺"

# Store user data temporarily
user_data = {}

@app.route('/', methods=['POST'])
def webhook():
    # Get the incoming message from WhatsApp
    incoming_msg = request.values.get('Body', '').strip()
    phone_number = request.values.get('From', '').strip()

    if incoming_msg.lower() == 'hi':
        # Initialize the conversation and ask for the user's name
        user_data[phone_number] = {'current_step': 'name'}
        resp = MessagingResponse()
        resp.message("Hi! Welcome to the flight booking bot. What's your name?")
        return str(resp)

    # Continue the conversation based on user's previous response
    user_info = user_data.get(phone_number)
    flight_data = user_info.get('flight_data', [])  # Move this line outside the if user_info block

    if user_info:
        current_step = user_info.get('current_step')

        if current_step == 'name':
            user_info['name'] = incoming_msg
            user_info['current_step'] = 'departure'
            resp = MessagingResponse()
            resp.message(f"Nice to meet you, {user_info['name']}! Where are you departing from?")
            return str(resp)

        elif current_step == 'departure':
            user_info['departure'] = incoming_msg
            user_info['current_step'] = 'destination'
            resp = MessagingResponse()
            resp.message("Great! Where is your destination?")
            return str(resp)

        elif current_step == 'destination':
            user_info['destination'] = incoming_msg
            user_info['current_step'] = 'departure_date'
            resp = MessagingResponse()
            resp.message("When do you want to depart? (e.g., 2023-09-15)")
            return str(resp)

        elif current_step == 'departure_date':
            user_info['departure_date'] = incoming_msg
            user_info['current_step'] = 'return_date'
            resp = MessagingResponse()
            resp.message("When will you return? (e.g., 2023-09-22)")
            return str(resp)

        elif current_step == 'return_date':
            user_info['return_date'] = incoming_msg
            user_info['current_step'] = 'adults'
            resp = MessagingResponse()
            resp.message("How many adults will be traveling?")
            return str(resp)

        elif current_step == 'adults':
            user_info['adults'] = incoming_msg
            user_info['current_step'] = 'travel_class'
            resp = MessagingResponse()
            resp.message("What travel class do you prefer? (e.g., ECONOMY)")
            return str(resp)

        elif current_step == 'travel_class':
            user_info['travel_class'] = incoming_msg
            flight_data = get_flight_offers(user_info)

            # Store the flight data in user_info
            user_info['flight_data'] = flight_data

            resp = MessagingResponse()
            resp.message("\n".join(flight_data))

            # Set the current step to 'select_flight'
            user_info['current_step'] = 'select_flight'
            return str(resp)
        # Add a new step to handle seat selection
        elif current_step == 'select_flight':
            try:
                selected_flight = int(incoming_msg)

                if 1 <= selected_flight <= len(flight_data) / 2:  # Divide by 2 to exclude separator lines
                    selected_flight_info = flight_data[(selected_flight - 1) * 2]
                    resp = MessagingResponse()
                    resp.message(selected_flight_info)

                    # Set the current step to 'select_seat'
                    user_info['current_step'] = 'select_seat'

                    # Generate a list of available seats with emojis in rows and columns
                    bookable_seats = int(selected_flight_info.split("Available Seats: ")[1])
                    num_rows = (bookable_seats + 2) // 3  # Calculate the number of rows (3 seats per row)

                    seat_message = "Available seats:\n"
                    for row in range(num_rows):
                        for seat_num in range(1, 4):
                            seat_index = row * 3 + seat_num
                            if seat_index <= bookable_seats:
                                seat_message += f"Seat {seat_index} {seat_emoji} "
                        seat_message += "\n"

                    resp.message(seat_message)

                    # Store the selected flight information
                    user_info['selected_flight_info'] = selected_flight_info

                    return str(resp)
                else:
                    resp = MessagingResponse()
                    resp.message("Invalid flight selection. Please select a valid flight number.")
                    return str(resp)
            except ValueError:
                resp = MessagingResponse()
                resp.message("Invalid input. Please enter the number of the flight you want to select.")
                return str(resp)

        # Add a new step to handle seat selection
        elif current_step == 'select_seat':
            selected_seat = incoming_msg.upper()  # Convert the user input to uppercase

            # Check if the selected seat is valid
            selected_flight_info = user_info.get('selected_flight_info', '')
            bookable_seats = int(selected_flight_info.split("Available Seats: ")[1])
            if selected_seat.startswith("SEAT ") and selected_seat[5:].isdigit():
                seat_number = int(selected_seat[5:])
                if 1 <= seat_number <= bookable_seats:
                    # Store the selected seat information
                    user_info['selected_seat'] = selected_seat
                    user_info['current_step'] = 'gather_info'
                    resp = MessagingResponse()
                    resp.message("Great! Please provide your full name and phone number in the format 'Full Name, Phone Number'.")
                    return str(resp)

            resp = MessagingResponse()
            resp.message("Invalid seat selection. Please select a valid seat (e.g., 'SEAT A1').")
            return str(resp)

        # Add a new step to gather user information
        elif current_step == 'gather_info':
            full_name, phone_number = incoming_msg.split(',')
            user_info['full_name'] = full_name.strip()
            user_info['phone_number'] = phone_number.strip()
            user_info['current_step'] = 'booking_confirmation'

            # Generate booking confirmation message
            booking_details = (
                f"Booking Details:\n"
                f"Name: {user_info['full_name']}\n"
                f"Phone Number: {user_info['phone_number']}\n"
                f"Selected Seat: {user_info['selected_seat']}\n"
                f"Flight Info: {user_info['selected_flight_info']}\n"
            )

            # Create and save the PDF ticket
            generate_pdf_ticket(user_info)

            resp = MessagingResponse()
            # Create a message with the PDF link using the 'media' attribute
            pdf_url = f"https://716e-105-160-56-39.ngrok-free.app/tickets/{phone_number}.pdf"  # Replace with your actual URL
            resp.message("Your booking details are as follows. You can download your PDF ticket below:")
            resp.message().media(pdf_url)

            # Return the response as a string
            return str(resp)

    return "Send 'Hi' to start booking a flight."

def generate_pdf_ticket(user_info):
    # Create a PDF document
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Flight Ticket", ln=True, align='C')
    pdf.ln(10)

    # Add user information to the PDF
    pdf.cell(200, 10, txt=f"Name: {user_info['full_name']}", ln=True)
    pdf.cell(200, 10, txt=f"Phone Number: {user_info['phone_number']}", ln=True)
    pdf.cell(200, 10, txt=f"Selected Seat: {user_info['selected_seat']}", ln=True)
    pdf.cell(200, 10, txt=f"Flight Info: {user_info['selected_flight_info']}", ln=True)

    # Save the PDF with the user's phone number as the filename
    pdf_filename = f"tickets/{user_info['phone_number']}.pdf"
    pdf.output(pdf_filename)


    return "Send 'Hi' to start booking a flight."

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

        # Extract and format flight data
        
        flight_data = []
        for i, offer in enumerate(flight_offers['data'], start=1):
            airline = offer['itineraries'][0]['segments'][0]['carrierCode']
            price = offer['price']['total']
            departure_time = offer['itineraries'][0]['segments'][0]['departure']['at']
            arrival_time = offer['itineraries'][0]['segments'][-1]['arrival']['at']
            plane_number = offer['itineraries'][0]['segments'][0]['number']
            bookable_seats = offer['numberOfBookableSeats']

            flight_info = (
                f"{i}. Airline: {airline} {plane_number}, "
                f"Price: {price} USD, "
                f"Departure Time: {departure_time}, "
                f"Arrival Time: {arrival_time}"
                f"Available Seats: {bookable_seats}"
            )
            flight_data.append(flight_info)
            flight_data.append('-' * 40)  # Add a line separator

        return flight_data
    else:
        return [f"Error in flight offers request: {response.status_code} - {response.text}"]


if __name__ == "__main__":
    app.run(debug=True)
