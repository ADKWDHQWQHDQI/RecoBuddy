# RecoBuddy: Personalized Recommendation Chatbot

## Overview
RecoBuddy is an intelligent chatbot that recommends books, movies, and music based on your mood and preferences.  
Built with **React** for the frontend and **Flask** for the backend, it utilizes **Firebase** for user data storage and AI tools to understand your requests.  
Whether you're feeling happy, sad, or neutral, RecoBuddy suggests personalized content, supports multiple languages (**English, Spanish, French, Hindi**), and continuously improves through user feedback.

## Features
- **Personalized Recommendations** – Suggests content based on your mood (e.g., happy songs for a positive vibe).
- **Multilingual Support** – Chat in **English, Spanish, French, or Hindi** with seamless translations.
- **User Feedback System** – Like or dislike recommendations to refine future suggestions.
- **Context-Aware Responses** – Understands your intent (e.g., asking for a book or greeting).
- **Persistent Data** – Saves chat history and preferences using Firebase.
- **Responsive UI** – Works across desktop and mobile, featuring **light/dark themes** and **voice input**.

## Technologies Used
### Frontend  
- React  
- Web Speech API  
- CSS  

### Backend  
- Flask  
- Firebase Firestore  
- googletrans *(for translations)*  
- NLTK *(VADER for sentiment analysis)*  
- Transformers *(Hugging Face)*  
- Pandas, NumPy  
- Pickle, Regular Expressions  

### Datasets  
- **Spotify Tracks**  
- **Netflix Movies**  
- **Books**  

## Installation and Setup

### Prerequisites
Ensure you have the following installed:
- **Node.js & npm** (for frontend)  
- **Python 3.8+** (for backend)  
- **Git**  
- **Firebase account** (for authentication & data storage)  

### Datasets  
The datasets (`spotify_tracks.csv`, `netflix_movies.csv`, `books.csv`) are too large to host on GitHub.  
Download them from **Google Drive**: [RecoBuddy Datasets](https://drive.google.com/drive/folders/1WUMlxrClSmdBPG78_3iFUNEhDXcqftZs?usp=drive_link).  
```
Place the `data` folder in the project's root directory:
RecoBuddy/
└── data/
├── spotify_tracks.csv
├── netflix_movies.csv
└── books.csv
```
### Frontend Setup  
```bash
# Navigate to frontend folder
cd frontend

# Install dependencies
npm install

# To his is often needed when using old versions of Webpack or other packages that depend on older OpenSSL versions.
set NODE_OPTIONS=--openssl-legacy-provider

# Start the React app
npm start

The app runs at http://localhost:3000.
```
### Backend Setup
```
# Navigate to backend folder
cd backend

# Install dependencies
pip install -r requirements.txt

Set Up Firebase
- Create a Firebase project.
- Download firebase-adminsdk.json and place it in the backend folder (not included in this repository for security reasons).

# Start the Flask server
python app.py

The server runs at http://localhost:5000.
Usage
- Open the live demo or run the app locally.
- Log in / Sign up using Firebase Authentication.
- Enter or speak a request (e.g., "Recommend a book" or "I’m happy, suggest music").
- Provide feedback using like/dislike buttons.
- Switch languages or themes via dropdown menus.
Project Structure
RecoBuddy/
├── frontend/      # React frontend
│   ├── App.js      # Main React component
│   ├── App.css     # Styles for the UI
│   └── package.json # Frontend dependencies
├── backend/       # Flask backend
│   ├── app.py      # Main Flask server
│   ├── data_loader.py # Dataset processing
│   └── requirements.txt # Backend dependencies
└── README.md      # Project documentation
```
### Contributing
Contributions are welcome!
- Fork the repository
- Make changes
- Submit a pull request
### License
This project is licensed under the Apache 2.0 License.
### Contact
For questions or feedback, reach out to sandeepkuruva0@gmail.com or open an issue on GitHub.


