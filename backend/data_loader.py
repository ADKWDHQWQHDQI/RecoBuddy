import pandas as pd
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_music_data(file_path='spotify_tracks.csv'):
    try:
        df = pd.read_csv(file_path)
        # Map valence to emotions (0-0.3: sad, 0.3-0.7: neutral, 0.7-1.0: happy)
        df['emotion'] = df['valence'].apply(
            lambda x: 'sad' if x < 0.3 else 'happy' if x > 0.7 else 'neutral'
        )
        return df[['track_number', 'name', 'artists', 'emotion', 'danceability', 'energy', 'year', 'release_date']].to_dict('records')
    except Exception as e:
        logging.error(f"Error loading music data: {e}")
        return []

def load_movie_data(file_path='netflix_movies.csv'):
    try:
        df = pd.read_csv(file_path)
        # Infer emotions based on listed_in genres
        df['emotion'] = df['listed_in'].apply(
            lambda x: 'happy' if any(g in x.lower() for g in ['comedy', 'romance']) else
                      'sad' if any(g in x.lower() for g in ['drama', 'documentary']) else
                      'neutral'
        )
        return df[['title', 'director', 'cast', 'listed_in', 'description', 'emotion', 'release_year', 'rating']].to_dict('records')
    except Exception as e:
        logging.error(f"Error loading movie data: {e}")
        return []

def load_book_data(file_path='books.csv'):
    try:
        # Define expected data types for each column
        dtypes = {
            'book_id': int,
            'goodreads_book_id': int,
            'best_book_id': int,
            'work_id': int,
            'books_count': int,
            'isbn': str,
            'isbn13': str,  # ISBN13 might be in scientific notation (e.g., 9.78E+12), treat as string
            'authors': str,
            'original_publication_year': float,  # Use float to handle NaN
            'original_title': str,
            'title': str,
            'language_code': str,
            'average_rating': float
        }
        
        # Load the CSV with specified dtypes and handle missing values
        df = pd.read_csv(
            file_path,
            dtype=dtypes,
            na_values=['nan', 'NaN', ''],  # Treat these as missing values
            keep_default_na=True
        )
        
        # Log the initial shape of the DataFrame
        logging.info(f"Loaded books.csv with shape: {df.shape}")
        
        # Log rows with missing critical values before dropping
        missing_title = df[df['title'].isna()]
        if not missing_title.empty:
            logging.warning(f"Found {len(missing_title)} rows with missing title: {missing_title.to_dict('records')}")
        
        # Drop rows where critical columns are NaN
        df = df.dropna(subset=['title', 'authors', 'average_rating'])
        
        # Additional filter to remove 'nan' strings
        df = df[df['title'].str.lower() != 'nan']
        df = df[df['authors'].str.lower() != 'nan']
        
        # Ensure average_rating is numeric and within a valid range (0 to 5)
        df['average_rating'] = pd.to_numeric(df['average_rating'], errors='coerce')
        df = df.dropna(subset=['average_rating'])
        df = df[(df['average_rating'] >= 0) & (df['average_rating'] <= 5)]
        
        # Map new columns to expected fields
        df['book_title'] = df['title']
        df['book_author'] = df['authors']
        df['year_of_publication'] = df['original_publication_year'].fillna(0).astype(int)
        df['rating'] = df['average_rating']
        
        # Infer Category based on title (simplified heuristic)
        df['Category'] = df['title'].apply(
            lambda x: "['Young Adult', 'Dystopia']" if 'Hunger Games' in x else
                      "['Fantasy']" if 'Harry Potter' in x else
                      "['Young Adult', 'Romance']" if 'Twilight' in x or 'Fault in Our Stars' in x else
                      "['Classics', 'Fiction']" if 'To Kill a Mockingbird' in x or 'Great Gatsby' in x else
                      "['Fantasy', 'Adventure']" if 'Hobbit' in x else
                      "['Fiction']"
        )
        
        # Infer emotions based on inferred category
        df['emotion'] = df['Category'].apply(
            lambda x: 'happy' if any(g in x.lower() for g in ['comedy', 'romance']) else
                      'sad' if any(g in x.lower() for g in ['drama', 'tragedy']) else
                      'neutral'
        )
        
        # Add a default Summary (since it's not in the new dataset)
        df['Summary'] = df['title'].apply(lambda x: f"A story about {x}. (Summary not available in dataset.)")
        
        # Log the final shape after cleaning
        logging.info(f"Books data after cleaning: {df.shape}")
        
        return df[['book_title', 'book_author', 'Category', 'Summary', 'emotion', 'year_of_publication', 'rating']].to_dict('records')
    except Exception as e:
        logging.error(f"Error loading book data: {e}")
        return []

if __name__ == "__main__":
    music = load_music_data()
    movies = load_movie_data()
    books = load_book_data()
    print(f"Loaded {len(music)} music tracks, {len(movies)} movies, {len(books)} books")