import requests
from urllib.parse import quote_plus

def get_search_html(query):
    base_url = "https://www.edustoke.com/search/day-school"
    encoded_query = quote_plus(query)
    url = f"{base_url}?search={encoded_query}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.text
    else:
        return f"Error: {response.status_code}"

def main():
    search_query = "Ariyalur, Tamil Nadu, India"
    print(f"Fetching search results HTML for: {search_query}")
    
    html_content = get_search_html(search_query)
    
    # Save the HTML content to a file
    with open("ariyalur_search_results.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"Search results HTML has been saved to 'ariyalur_search_results.html'")
    print("\nFirst 1000 characters of the HTML content:")
    print(html_content[:100000])

if __name__ == "__main__":
    main()