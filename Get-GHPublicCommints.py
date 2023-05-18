import requests
import mysql.connector

# GitHub API endpoint for searching commits
SEARCH_API_URL = 'https://api.github.com/search/commits'

# MySQL database configuration
DB_HOST = 'your_database_host'
DB_USER = 'your_database_user'
DB_PASSWORD = 'your_database_password'
DB_NAME = 'your_database_name'

# Function to save commit and conversation to MySQL database
def save_commit_and_conversation(commit_sha, conversation):
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )

        cursor = connection.cursor()

        # Save commit to database
        insert_commit_query = "INSERT INTO commits (commit_sha) VALUES (%s)"
        cursor.execute(insert_commit_query, (commit_sha,))
        connection.commit()

        commit_id = cursor.lastrowid

        # Save conversation to database
        for comment in conversation:
            insert_comment_query = "INSERT INTO comments (commit_id, comment) VALUES (%s, %s)"
            cursor.execute(insert_comment_query, (commit_id, comment))
            connection.commit()

        cursor.close()
        connection.close()
    except mysql.connector.Error as error:
        print("Error connecting to MySQL database:", error)

# Function to fetch popular commits from GitHub and save them to the database
def fetch_and_save_commits(query, sort='stars', order='desc', per_page=10):
    # Build the search query
    params = {
        'q': query,
        'sort': sort,
        'order': order,
        'per_page': per_page
    }

    try:
        # Make the API request
        response = requests.get(SEARCH_API_URL, params=params)
        data = response.json()

        # Extract commits and conversations from the API response
        for item in data['items']:
            commit_sha = item['sha']
            conversation_url = item['comments_url']

            # Fetch the conversation for the commit
            conversation_response = requests.get(conversation_url)
            conversation_data = conversation_response.json()

            conversation = [comment['body'] for comment in conversation_data]

            # Save the commit and conversation to the database
            save_commit_and_conversation(commit_sha, conversation)

        print("Commits saved to the database successfully!")
    except requests.exceptions.RequestException as error:
        print("Error making the API request:", error)
