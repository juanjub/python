import requests
import json
import mysql.connector
from datetime import datetime

# GitHub API URL for searching commits
API_URL = 'https://api.github.com/search/commits'

def fetch_popular_commits(start_date, end_date=date.today().isoformat(), export_type='mysql', popularity_metric='stars', min_popularity=100, language='', auth_token=''):
    # Setup query parameters for the API
    params = {
        'q': f'{popularity_metric}:{min_popularity}',
        'sort': popularity_metric,
        'per_page': 100
    }

    if start_date:
        params['q'] += f' committer-date:{start_date}..{end_date}'
        
    if language:
        params['q'] += f' language:{language}'

    headers = {}
    if auth_token:
        headers['Authorization'] = f'Token {auth_token}'

    # Send the request to the API
    try:
        response = requests.get(API_URL, params=params, headers=headers)
        response.raise_for_status()
        commits = response.json()['items']

        if export_type == 'mysql':
            save_to_mysql(commits)
        elif export_type == 'json':
            save_to_json(commits)
    except requests.exceptions.RequestException as err:
        log_info(f"An error occurred while fetching commits from GitHub: {err}", error=True)

def save_to_mysql(commits):
    # Database connection settings
    db_settings = {
        'host': 'localhost',
        'user': 'your_username',
        'password': 'your_password',
        'database': 'your_database'
    }

    try:
        # Connect to MySQL database
        db = mysql.connector.connect(**db_settings)
        cursor = db.cursor()

        # Create the repositories table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS repositories (
                id INT AUTO_INCREMENT PRIMARY KEY,
                repository_url VARCHAR(255),
                repository_stars INT,
                repository_followers INT,
                repository_owner VARCHAR(255)
            )
        """)

        # Create the commits table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS commits (
                id INT AUTO_INCREMENT PRIMARY KEY,
                repository_id INT,
                author VARCHAR(255),
                committer VARCHAR(255),
                commit_message TEXT,
                conversations TEXT,
                commit_url VARCHAR(255),
                FOREIGN KEY (repository_id) REFERENCES repositories(id)
            )
        """)

        for commit in commits:
            repository_url = commit['repository']['html_url']
            repository_stars = commit['repository']['stargazers_count']
            repository_followers = commit['repository']['followers']
            repository_owner = commit['repository']['owner']['login']
            author = repository_owner
            committer = commit['commit']['committer']['name']
            message = commit['commit']['message']
            conversations = get_commit_conversations(commit['url'])
            commit_url = commit['html_url']

            # Escape special characters
            message = message.replace("'", "''")
            conversations = conversations.replace("'", "''")

            # Check if the repository already exists
            cursor.execute(f"SELECT id FROM repositories WHERE repository_url = '{repository_url}'")
            repository_row = cursor.fetchone()

            if repository_row:
                repository_id = repository_row[0]
            else:
                # Insert the repository info
                cursor.execute(f"""
                    INSERT INTO repositories (repository_url, repository_stars, repository_followers, repository_owner)
                    VALUES ('{repository_url}', {repository_stars}, {repository_followers}, '{repository_owner}')
                """)

                # Get the last inserted ID
                repository_id = cursor.lastrowid

            # Insert the commit info
            cursor.execute(f"""
                INSERT INTO commits (repository_id, author, committer, commit_message, conversations, commit_url)
                VALUES ({repository_id}, '{author}', '{committer}', '{message}', '{conversations}', '{commit_url}')
            """)

        db.commit()
        db.close()
        log_info(f"{len(commits)} commits saved to the database")
    except mysql.connector.Error as err:
        log_info(f"An error occurred saving commits to the database: {err}", error=True)

def save_to_json(commits):
    file_name = f"GH_commits_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
    data = []

    for commit in commits:
        repository_url = commit['repository']['html_url']
        repository_stars = commit['repository']['stargazers_count']
        repository_followers = commit['repository']['followers']
        repository_owner = commit['repository']['owner']['login']
        author = repository_owner
        committer = commit['commit']['committer']['name']
        message = commit['commit']['message']
        conversations = get_commit_conversations(commit['url'])
        commit_url = commit['html_url']

        commit_data = {
            'repository_url': repository_url,
            'repository_stars': repository_stars,
            'repository_followers': repository_followers,
            'repository_owner': repository_owner,
            'author': author,
            'committer': committer,
            'commit_message': message,
            'conversations': conversations,
            'commit_url': commit_url
        }

        data.append(commit_data)

    try:
        with open(file_name, 'w') as json_file:
            json.dump(data, json_file, indent=2)
        log_info(f"{len(commits)} commits exported to file: {file_name}")
    except IOError as err:
        log_info(f"An error occurred saving commits to file: {err}", error=True)

def get_commit_conversations(commit_url):
    # Fetch conversations for the commit
    try:
        response = requests.get(commit_url)
        response.raise_for_status()
        commit_data = response.json()

        # Extract info
        conversations = [comment['body'] for comment in commit_data['comments']]

        return conversations
    except requests.exceptions.RequestException as err:
        log_info(f"An error occurred while fetching commit conversations: {err}", error=True)

def log_info(log_message, error=False):
    # Log script run information
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"Date: {timestamp} - {log_message}\n"

    with open('script_log.txt', 'a') as log_file:
        log_file.write(log_entry)

fetch_popular_commits()
