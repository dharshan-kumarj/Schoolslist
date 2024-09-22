import aiohttp
import asyncio
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.google.com/',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

async def fetch(session, url):
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            return await response.text()
        return None

async def get_soup(session, url):
    html = await fetch(session, url)
    if html:
        return BeautifulSoup(html, 'html.parser')
    return None

async def extract_contact_info(session, url):
    soup = await get_soup(session, url)
    if not soup:
        return None
    
    contact_info = {
        'Name': 'null',
        'Address': 'null',
        'Phone': 'null',
        'Email': 'null',
        'Website': 'null'
    }
    
    # Extract school name from both possible locations
    name_div1 = soup.find('div', class_='media-body align-items-center align-self-md-end')
    name_div2 = soup.find('div', class_='align-self-end col-lg-12')
    
    if name_div1:
        name_h1 = name_div1.find('h1', class_='d-inline-block')
        if name_h1:
            contact_info['Name'] = name_h1.text.strip()
    elif name_div2:
        name_h1 = name_div2.find('h1', class_='text-white d-inline-block')
        if name_h1:
            contact_info['Name'] = name_h1.text.strip()
    
    contact_ul = soup.find('ul', class_='list-group pmd-list')
    if contact_ul:
        for li in contact_ul.find_all('li'):
            key = li.find('i', class_='material-icons')
            value = li.find('div', class_='media-body')
            if key and value:
                key_text = key.text.strip()
                value_text = value.text.strip()
                if 'location_on' in key_text:
                    contact_info['Address'] = value_text
                elif 'call' in key_text:
                    contact_info['Phone'] = value_text
                elif 'email' in key_text:
                    img = value.find('img')
                    if img and 'src' in img.attrs:
                        email_img_url = urljoin(url, img['src'])
                        contact_info['Email'] = email_img_url
                    else:
                        contact_info['Email'] = value_text if value_text else 'null'
                elif 'web_asset' in key_text:
                    website_link = value.find('a')
                    if website_link and 'href' in website_link.attrs:
                        contact_info['Website'] = website_link['href']
                    else:
                        contact_info['Website'] = value_text if value_text else 'null'

    logging.info(f"Extracted info for {contact_info['Name']}")
    return contact_info

async def process_state_page(session, state_url, state_name):
    logging.info(f"Processing {state_name} page: {state_url}")
    
    soup = await get_soup(session, state_url)
    if not soup:
        return []
    
    school_links = soup.select('a.btn.pmd-btn-flat.btn-block.btn-primary.pmd-ripple-effect')
    
    all_schools_data = []
    for school_link in school_links:
        school_url = urljoin(state_url, school_link['href'])
        school_data = await extract_contact_info(session, school_url)
        if school_data:
            school_data['State'] = state_name
            all_schools_data.append(school_data)
    
    return all_schools_data

async def process_state(session, base_state_url, state_name):
    all_schools_data = []
    rec_no = 0
    
    while True:
        if rec_no == 0:
            state_url = base_state_url
        else:
            state_url = f"{base_state_url}?recNo={rec_no}"
        
        page_data = await process_state_page(session, state_url, state_name)
        
        if not page_data:
            break
        
        all_schools_data.extend(page_data)
        rec_no += 25
    
    return all_schools_data

async def get_remaining_states(session, main_url):
    soup = await get_soup(session, main_url)
    if not soup:
        return {}

    states = {}
    state_links = soup.select('div.list-group.pmd-list.pmd-list-bullet a')
    start_processing = False
    for link in state_links:
        state_name = link.text.strip().split(' in ')[-1]
        if state_name == 'Chhattisgarh':
            start_processing = True
        if start_processing:
            state_url = urljoin(main_url, link['href'])
            states[state_name] = state_url
        if state_name == 'Ladakh':
            break
    
    return states

def read_existing_excel(file_name):
    if os.path.exists(file_name):
        return pd.read_excel(file_name)
    return pd.DataFrame(columns=['State', 'Name', 'Address', 'Phone', 'Email', 'Website'])

async def main():
    main_url = 'https://targetstudy.com/school/state-board-schools-in-india.html'
    excel_file = "first_five_states_schools_info.xlsx"
    
    # Read existing data
    existing_df = read_existing_excel(excel_file)
    
    async with aiohttp.ClientSession(headers=headers) as session:
        states = await get_remaining_states(session, main_url)
        
        if not states:
            logging.error("Failed to fetch state links. Exiting.")
            return

        all_schools_data = []
        
        for state_name, state_url in states.items():
            logging.info(f"Processing state: {state_name}")
            state_data = await process_state(session, state_url, state_name)
            all_schools_data.extend(state_data)

    if all_schools_data:
        new_df = pd.DataFrame(all_schools_data)
        new_df = new_df[['State', 'Name', 'Address', 'Phone', 'Email', 'Website']]  # Reorder columns
        
        # Combine existing and new data
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        
        combined_df.to_excel(excel_file, index=False)
        logging.info(f"Data saved to {excel_file}")
        print(f"Data saved to {excel_file}")
        print(f"Extracted data for {len(all_schools_data)} new schools across {len(states)} states:")
        print(new_df.groupby('State').size())
        print(f"Total schools in the file: {len(combined_df)}")
    else:
        logging.error("No new data collected. Excel file not updated.")
        print("No new data collected. Excel file not updated.")

if __name__ == "__main__":
    asyncio.run(main())