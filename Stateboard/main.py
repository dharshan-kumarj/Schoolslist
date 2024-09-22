import requests
from bs4 import BeautifulSoup
from fpdf import FPDF
import time

def get_soup(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except requests.RequestException as e:
        print(f"An error occurred while fetching {url}: {e}")
        return None

def extract_school_details(url):
    soup = get_soup(url)
    if not soup:
        return []

    schools = []
    school_links = soup.select('a.btn.pmd-btn-flat.btn-block.btn-primary.pmd-ripple-effect')
    
    for link in school_links:
        school_url = link['href']
        school_soup = get_soup(school_url)
        if school_soup:
            name = school_soup.find('h1', class_='school-name')
            address = school_soup.find('p', class_='school-address')
            schools.append({
                'name': name.text.strip() if name else 'N/A',
                'address': address.text.strip() if address else 'N/A',
                'url': school_url
            })
        time.sleep(1)  # Be respectful to the server
    
    return schools

def create_pdf(all_schools):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    for state, schools in all_schools.items():
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, f"State: {state}", ln=True)
        pdf.set_font("Arial", size=12)
        
        for school in schools:
            pdf.multi_cell(0, 10, f"Name: {school['name']}")
            pdf.multi_cell(0, 10, f"Address: {school['address']}")
            pdf.multi_cell(0, 10, f"URL: {school['url']}")
            pdf.ln(5)
        
        pdf.add_page()
    
    pdf.output("state_board_schools.pdf")

def main():
    url = "https://targetstudy.com/school/state-board-schools-in-india.html"
    soup = get_soup(url)
    if not soup:
        return

    target_div = soup.find('div', class_="list-group pmd-list pmd-list-bullet")
    if not target_div:
        print("Target div not found on the page.")
        return

    links = target_div.find_all('a')
    all_schools = {}

    for link in links:
        state_name = link.text.strip()
        state_url = link['href']
        print(f"Processing {state_name}...")
        
        schools = extract_school_details(state_url)
        all_schools[state_name] = schools
        
        print(f"Found {len(schools)} schools in {state_name}")

    create_pdf(all_schools)
    print("PDF has been generated: state_board_schools.pdf")

if __name__ == "__main__":
    main()