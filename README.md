RecoBuddy: Personalized Recommendation Chatbot
Overview
RecoBuddy is a smart chatbot that recommends books, movies, and music based on your mood and preferences. Built with React for the frontend and Flask for the backend, it uses Firebase for user data storage and AI tools for understanding your requests. Whether you're feeling happy, sad, or neutral, RecoBuddy suggests content tailored to you, supports multiple languages (English, Spanish, French, Hindi), and learns from your feedback.
Features

Personalized Recommendations: Suggests items based on your mood (e.g., happy songs for a positive vibe).
Multilingual Support: Chat in English, Spanish, French, or Hindi with seamless translations.
User Feedback: Like or dislike recommendations to improve future suggestions.
Context-Aware Responses: Understands your intent (e.g., asking for a book or saying hello).
Persistent Data: Saves your chat history and preferences using Firebase.
Responsive UI: Works on desktops and mobiles with light/dark themes and voice input.

Live Demo
Try RecoBuddy online at RecoBuddy Demo (replace with actual link after hosting).
Technologies Used

Frontend: React, Web Speech API, CSS
Backend: Flask, Firebase Firestore, googletrans, NLTK (VADER), Transformers (Hugging Face), Pandas, NumPy, Pickle, Regular Expressions
Datasets: Spotify Tracks, Netflix Movies, Books

Installation and Setup
Prerequisites

Node.js and npm for the frontend (Node.js)
Python 3.8+ for the backend (Python)
Git (Git SCM)
Firebase account for authentication and data storage (Firebase)

Datasets
The datasets (spotify_tracks.csv, netflix_movies.csv, books.csv) are too large to host on GitHub. Download them from this Google Drive link:
https://drive.google.com/drive/folders/1WUMlxrClSmdBPG78_3iFUNEhDXcqftZs?usp=drive_link
RecoBuddy Datasets. Place the data folder in the root directory of the project:
RecoBuddy/
└── data/
├── spotify_tracks.csv
├── netflix_movies.csv
└── books.csv

Frontend Setup

Navigate to the frontend folder:cd frontend

Install dependencies:npm install

Start the React app:npm start

The app will run at http://localhost:3000.

Backend Setup

Navigate to the backend folder:cd backend

Install dependencies:pip install -r requirements.txt

Set up Firebase:
Create a Firebase project and download the firebase-adminsdk.json file.
Place it in the backend folder (not included in this repository for security).

Start the Flask server:python app.py

The server will run at http://localhost:5000.

Usage

Open the live demo or run the app locally.
Log in or sign up using Firebase Authentication.
Type or speak a request (e.g., "recommend a book" or "I’m happy, suggest music").
Use the like/dislike buttons to provide feedback on recommendations.
Switch languages or themes using the dropdown menus.

Project Structure
RecoBuddy/
├── frontend/ # React frontend files
│ ├── App.js # Main React component
│ ├── App.css # Styles for the UI
│ └── package.json # Frontend dependencies
├── backend/ # Flask backend files
│ ├── app.py # Main Flask server
│ ├── data_loader.py # Dataset processing
│ └── requirements.txt # Backend dependencies
└── README.md # Project documentation

Contributing
Contributions are welcome! Please fork the repository, make changes, and submit a pull request.
License
This project is licensed under the Apache2.0 License.
Contact
For questions or feedback, reach out to sandeepkuruva0@gmail.com or open an issue on GitHub.
