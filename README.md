### Get-GHPublicCommits.py

```python
# Example usage
start_date = '2023-05-01' # optional, empty by default
end_date = '2023-05-21' # optional, today by default
export_type = 'mysql'  # or 'json', 'mysql' by default
popularity_metric = 'stars'  # or 'followers', 'stars' by default
min_popularity = 100 # optional, 100 by defalt
language = 'python' #  optional, empty by default
auth_token = 'your_github_auth_token'  # optional, empty by default

fetch_popular_commits(start_date, end_date, export_type, popularity_metric, min_popularity, auth_token)
```
