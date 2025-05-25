from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from transformers import pipeline
import firebase_admin
from firebase_admin import credentials, firestore, auth
from googletrans import Translator
from data_loader import load_music_data, load_movie_data, load_book_data
import numpy as np
import random
from datetime import datetime
import re
import pickle
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

# Initialize Firebase
cred = credentials.Certificate('firebase-adminsdk.json')
firebase_admin.initialize_app(cred)
db = firestore.client()
print("Firebase Connected!")

# Initialize NLP tools
nltk.download('vader_lexicon')
sia = SentimentIntensityAnalyzer()
translator = Translator()
intent_classifier = pipeline('zero-shot-classification', model='facebook/bart-large-mnli')

# Load recommendation data
music_data = load_music_data('spotify_tracks.csv')
movie_data = load_movie_data('netflix_movies.csv')
book_data = load_book_data('books.csv')

# Translation cache
translation_cache_file = 'translation_cache.pkl'
if os.path.exists(translation_cache_file):
    with open(translation_cache_file, 'rb') as f:
        translation_cache = pickle.load(f)
else:
    translation_cache = {}

def save_translation_cache():
    with open(translation_cache_file, 'wb') as f:
        pickle.dump(translation_cache, f)

# Knowledge base
knowledge_base = {
    "who is the father of RecoBuddy": "KURUVA SANDEEP",
    "who is the creator of RecoBuddy": "KURUVA SANDEEP",
    "what is the capital of france": "The capital of France is Paris.",
    "how to stay productive": "Try using the Pomodoro technique: work for 25 minutes, then take a 5-minute break.",
    "tell me a joke": "Why did the computer go to school? Because it wanted to improve its *byte*!",
    "who is elon musk": "Elon Musk is a billionaire entrepreneur, CEO of Tesla, SpaceX, and xAI, known for his work in electric vehicles, space travel, and AI.",
    "what is python": "Python is a high-level, interpreted programming language known for its readability and versatility, widely used in web development, data science, and AI.",
    "how does gravity work": "Gravity is a fundamental force that attracts objects towards each other, proportional to their mass and inversely proportional to the distance squared.",
    "what is the weather like": "I don’t have real-time weather data, but I can explain weather patterns or recommend indoor activities!",
    "what is ai": "Artificial Intelligence (AI) refers to computer systems that perform tasks requiring human intelligence, like learning or problem-solving.",
    "how to cook pasta": "Boil water with a pinch of salt, add pasta, cook for 8-12 minutes until al dente, then drain and serve with sauce.",
    "what is the meaning of life": "The meaning of life varies for everyone! Many find it in pursuing personal purpose or happiness.",
    "what is machine learning": "Machine learning is a subset of AI where computers learn from data to make predictions without explicit programming.",
    "what is the largest planet": "Jupiter is the largest planet in our solar system, with a diameter of about 139,820 kilometers.",
    "hello": "Hey there! How can I assist you today? Maybe a book, movie, or music recommendation? 😊",
    "how are you": "I'm great! Thanks for asking. Is there anything I can help you with?"
}

# Profanity filter
def contains_profanity(message):
    pattern = re.compile(r"\b(fuck|shit|damn|bitch|asshole)\b", re.IGNORECASE)
    return bool(pattern.search(message))

# Detect malformed input
def is_malformed_input(message):
    words = message.split()
    if len(words) > 3:
        for i in range(len(words) - 3):
            if words[i] == words[i+1] == words[i+2] == words[i+3]:
                return True
    for word in words:
        if len(word) > 5 and re.search(r'(.)\1{4,}', word):
            return True
    return False

# Translate with caching
def translate_text(text, src='en', dest='en'):
    cache_key = f"{text}:{src}:{dest}"
    if cache_key in translation_cache:
        return translation_cache[cache_key]
    try:
        translated = translator.translate(text, src=src, dest=dest).text
        translation_cache[cache_key] = translated
        save_translation_cache()
        print(f"🔹 Translated '{text}' from {src} to {dest}: '{translated}'")
        return translated
    except Exception as e:
        print(f"Translation error: {e}")
        return text

# Generate emotion-based recommendation
def generate_recommendation(user_message, user_lang, user_data, requested_rating=None, emotion='neutral'):
    category = 'book' if 'book' in user_message or 'livre' in user_message or 'पुस्तक' in user_message else \
               'movie' if 'movie' in user_message or 'film' in user_message or 'फिल्म' in user_message else \
               'music' if 'music' in user_message or 'song' in user_message or 'संगीत' in user_message else 'book'
    data = {'book': book_data, 'movie': movie_data, 'music': music_data}.get(category, book_data)
    
    if not data:
        return "Sorry, I don’t have recommendations for that category yet. Try asking for a book, movie, or music!"

    disliked = user_data.get('preferences', {}).get('disliked', [])
    previously_recommended = user_data.get('previously_recommended', {}).get(category, [])
    # Use 'book_title' for books, 'title' for movies, and 'name' for music
    key = 'book_title' if category == 'book' else 'title' if category == 'movie' else 'name'
    # Filter available recommendations
    available = [rec for rec in data if rec[key] not in disliked and 
                 rec[key] not in previously_recommended and 
                 rec['emotion'] == emotion]
    
    # Apply rating filter if specified
    if requested_rating is not None:
        # First try exact match (rating >= requested_rating)
        exact_matches = [rec for rec in available if float(rec.get('rating', 0)) >= requested_rating]
        if exact_matches:
            available = exact_matches
        else:
            # Fallback: allow ratings within 0.5 of the requested rating
            threshold = max(0, requested_rating - 0.5)
            available = [rec for rec in available if float(rec.get('rating', 0)) >= threshold]
            if not available:
                return f"No {emotion} {category}s found with a rating of {requested_rating} or higher. Try a lower rating or a different category!"
    
    # Additional validation for books: ensure book_title is not 'nan'
    if category == 'book':
        available = [rec for rec in available if rec['book_title'] and rec['book_title'].lower() != 'nan']
    
    if not available:
        # Clear previously recommended if no matches found
        user_data.setdefault('previously_recommended', {}).setdefault(category, []).clear()
        available = [rec for rec in data if rec[key] not in disliked and 
                     rec['emotion'] == emotion]
        if category == 'book':
            available = [rec for rec in available if rec['book_title'] and rec['book_title'].lower() != 'nan']
    
    if not available:
        return f"I’ve run out of {emotion} {category} recommendations. Try another category or emotion!"

    random.shuffle(available)
    rec = available[0]
    user_data.setdefault('previously_recommended', {}).setdefault(category, []).append(rec[key])
    
    if category == 'book':
        response = f"I recommend '{rec['book_title']}' by {rec['book_author']} ({rec['year_of_publication']}, Rating: {rec['rating']}).\n" \
                   f"Category: {rec['Category']}\nSummary: {rec['Summary']}\nEmotion: {rec['emotion'].capitalize()}"
    elif category == 'movie':
        response = f"I recommend '{rec['title']}' directed by {rec['director']} ({rec['release_year']}, Rating: {rec['rating']}).\n" \
                   f"Genres: {rec['listed_in']}\nDescription: {rec['description']}\nEmotion: {rec['emotion'].capitalize()}"
    else:
        response = f"I recommend '{rec['name']}' by {rec['artists']} ({rec['year']}, Valence: {rec['emotion']}).\n" \
                   f"Emotion: {rec['emotion'].capitalize()}"
    
    return response

# Store global behavior data
global_behavior_data = db.collection('global_behavior').document('shared_data').get().to_dict() or {'queries': []}

@app.route('/')
def home():
    return "Welcome to RecoBuddy!"

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "Invalid JSON format", "is_translating": False}), 400

        user_message = data.get('message', '').lower()
        user_lang = data.get('language', 'en')
        user_id = data.get('user_id', 'anonymous')

        print("🔹 Received User Input:", user_message)

        # Get user email
        try:
            user_email = auth.get_user(user_id).email if user_id != 'anonymous' else 'anonymous'
        except Exception as e:
            print(f"Error fetching user email: {e}")
            user_email = 'anonymous'

        # Load user data
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        user_data = user_doc.to_dict() or {
            'email': user_email,
            'chat_history': [],
            'preferences': {'liked': [], 'disliked': [], 'categories': []},
            'previously_recommended': {'book': [], 'movie': [], 'music': []}
        }

        # Check if user is new
        is_new_user = len(user_data['chat_history']) == 0

        # Handle empty message
        if not user_message.strip():
            welcome_message = "Welcome to RecoBuddy! I'm here to recommend books, movies, and music. What would you like a recommendation for? 😊" if is_new_user else "Welcome back to RecoBuddy! Ready for some great recommendations? 🤗"
            return jsonify({'response': welcome_message, 'chat_history': user_data['chat_history'], 'is_translating': False})

        # Validate input
        if len(user_message.split()) > 50 or not any(c.isalnum() for c in user_message) or is_malformed_input(user_message):
            response = "Sorry, your query seems unclear or contains repetitive text. Please ask for a specific recommendation, like a book, movie, or music!"
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            user_data['chat_history'].append({
                'user': user_message,
                'bot': response,
                'mood': 'neutral',
                'tone': 'casual',
                'timestamp': timestamp,
                'topic': 'Invalid query',
                'intent': 'statement'
            })
            user_data['chat_history'] = user_data['chat_history'][-20:]
            user_ref.set(user_data)
            if user_lang != 'en':
                response = translate_text(response, src='en', dest=user_lang)
            return jsonify({'response': response, 'chat_history': user_data['chat_history'], 'is_translating': False})

        # Translate to English
        original_message = user_message
        is_translating = user_lang != 'en'
        if is_translating:
            user_message = translate_text(user_message, src=user_lang, dest='en').lower()

        # Sentiment and tone analysis
        sentiment = sia.polarity_scores(user_message)
        mood = 'positive' if sentiment['compound'] > 0.1 else 'negative' if sentiment['compound'] < -0.1 else 'neutral'
        tone = 'angry' if sentiment['neg'] > 0.3 else 'polite' if sentiment['pos'] > 0.3 else 'casual'
        has_profanity = contains_profanity(user_message)

        # Intent recognition with zero-shot classification
        candidate_labels = ['greeting', 'feedback', 'question', 'statement', 'complex_query', 'recommendation']
        intent_result = intent_classifier(user_message, candidate_labels, multi_label=False)
        intent = intent_result['labels'][0]
        
        # Override intent for recommendation requests
        recommendation_keywords = ['recommend', 'recommander', 'recommend a', 'suggest', 'अनुशंसा', 'सुझाव']
        if any(keyword in user_message for keyword in recommendation_keywords):
            intent = 'recommendation'

        # Override intent for complex queries
        if intent not in ['greeting', 'recommendation'] and len(user_message.split()) > 5:
            intent = 'complex_query'

        # Add to global behavior data
        global_behavior_data['queries'].append({
            'query': user_message,
            'intent': intent,
            'mood': mood,
            'tone': tone,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        db.collection('global_behavior').document('shared_data').set(global_behavior_data)

        # Check knowledge base
        response = None
        if intent in ['greeting', 'question']:
            for query, answer in knowledge_base.items():
                if query in user_message:
                    response = answer
                    break

        # Generate response
        responses = {
            'greeting': ["Hey there! What recommendation can I find for you today? 😊"],
            'question': ["That’s an interesting question! I can help with recommendations—would you like a book, movie, or music suggestion? 😊"],
            'statement': ["Thanks for sharing! How about a recommendation to explore something new? 🤗"],
            'feedback': ["Thanks for your feedback! It helps me improve. 😊"],
            'profanity': ["Let’s keep things friendly! Try asking for a book, movie, or music recommendation. 😊"],
            'negative_mood': ["I’m sorry you’re feeling down. How about a recommendation to cheer you up? 😊"],
            'complex_query': ["That sounds like a complex topic! I’m best at recommending books, movies, and music—would you like a suggestion? 😊"],
            'recommendation': None
        }

        if has_profanity:
            response = random.choice(responses['profanity'])
        elif response is None:
            if intent == 'recommendation':
                rating_match = re.search(r'(\d+\.?\d*)\s*rating', user_message)
                requested_rating = float(rating_match.group(1)) if rating_match else None
                emotion = 'happy' if mood == 'positive' else 'sad' if mood == 'negative' else 'neutral'
                response = generate_recommendation(user_message, user_lang, user_data, requested_rating, emotion)
            elif intent == 'complex_query':
                response = random.choice(responses['complex_query'])
            elif mood == 'negative':
                response = random.choice(responses['negative_mood'])
            else:
                response = random.choice(responses.get(intent, responses['statement']))

        # Adjust response
        if tone == 'angry':
            response = f"I’m sorry if I upset you! {response}"
        elif tone == 'polite':
            response = f"Thank you for your kind words! {response}"
        elif mood == 'negative' and intent != 'negative_mood':
            response = f"{response} How about a fun recommendation? 😊"

        # Translate response
        if user_lang != 'en':
            response = translate_text(response, src='en', dest=user_lang)

        # Update user data
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        topic = original_message[:50] + '...' if len(original_message) > 50 else original_message
        user_data['chat_history'].append({
            'user': original_message,
            'bot': response,
            'mood': mood,
            'tone': tone,
            'timestamp': timestamp,
            'topic': topic,
            'intent': intent
        })
        user_data['chat_history'] = user_data['chat_history'][-20:]
        user_ref.set(user_data)

        print("🔹 Buddy's Response:", response)
        return jsonify({'response': response, 'chat_history': user_data['chat_history'], 'is_translating': is_translating})

    except Exception as e:
        print("🔹 Server Error:", str(e))
        return jsonify({"error": "Internal Server Error", "details": str(e), 'is_translating': False}), 500

@app.route('/feedback', methods=['POST'])
def feedback():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "Invalid JSON format"}), 400

        user_id = data.get('user_id', 'anonymous')
        recommendation = data.get('recommendation')
        rating = data.get('rating')

        title_match = re.search(r"'([^']+)'", recommendation)
        if not title_match:
            return jsonify({"error": "Invalid recommendation format"}), 400
        recommendation_title = title_match.group(1)

        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        user_data = user_doc.to_dict() or {
            'email': 'anonymous',
            'chat_history': [],
            'preferences': {'liked': [], 'disliked': [], 'categories': []},
            'previously_recommended': {'book': [], 'movie': [], 'music': []}
        }

        if rating == 'like':
            user_data['preferences'].setdefault('liked', []).append(recommendation_title)
        elif rating == 'dislike':
            user_data['preferences'].setdefault('disliked', []).append(recommendation_title)

        user_ref.set(user_data)
        return jsonify({"status": "Feedback recorded"})
    except Exception as e:
        print("🔹 Feedback Error:", str(e))
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)