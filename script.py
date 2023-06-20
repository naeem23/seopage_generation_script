import copy
import googlemaps
import io
import json
import openai
import os
import requests
import re
import time
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
from openai.error import APIConnectionError, RateLimitError, Timeout

load_dotenv() #load environment variables from .env file

openai.api_key = os.getenv("OPENAI_API_KEY")
googlemaps_api_key = os.getenv("GOOGLEMAPS_API_KEY")
guardian_api_key = os.getenv("GUARDIAN_API_KEY")
guardian_url = 'https://content.guardianapis.com/search'
newsapi_api_key = os.getenv("NEWSAPI_API_KEY")
newsapi_url = 'https://newsapi.org/v2/everything'
globaldatabase_api_key = 'your_api_key_here'
globaldatabase_url = 'https://api.globaldatabase.com/companies'


def generate_text(location):
    """Generate content for a location using chat gpt api 

    Args:
        location: The name of location for which the content will be generated.
    """
    
    prompt = f"""Write a 350-word SEO-optimized article on the benefits of leaflet distribution for businesses in {location}. Discuss the impact on specific industries, local challenges, and unique aspects of {location}. Include varied aspects of leaflet distribution and different article formats. Ensure natural, human language, occassional accepted grammar and syntax errors keyword usage, and readability. Use keyphrase a maximum of 5 times throughout the article. Generates content in such a way that it always follow the following format: 
Meta Title
Meta Description
Meta Keywords
H1 Heading - Use Keyphrase synonym
Paragraph
H2 Heading - Use Keyphrase
Paragraph
H3 Heading - Use Keyphrase synonym
Paragraph
H4 Heading - Use Keyphrse synonym
Paragraph
H5 Heading - Use Keyphrase 
Paragraph

It's not mandatory to have all 5 heading but they should appear in ascending order. Multiple paragraph can appear under one heading if necessary. Please ensure you follow ALL the instructions correctly."""
    print('call api.......')

    retries = 3
    base_delay = 5

    for i in range(retries):
        try:
            response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}], timeout=120)
            break
        except RateLimitError:
            print("Rate limit exceeded.")
        except Timeout:
            print("API call timed out.")
        except APIConnectionError:
            print("Error communicating with OpenAI.")

        if i == retries - 1:
            response = None
            print("API call failed after multiple retries.")
            break

        delay = base_delay * (2 ** i)
        print(f"Retrying in {delay} seconds...")
        time.sleep(delay)
    
    # Check that the response is not None.
    if response is None:
        print("API call failed.")
        print(f'Could not create content for --- {location}')
        return None
    else:
        print(response)
        return response.choices[0].message.content


def get_breadcrumbs_and_map_src(location):
    """Generate google maps static iframe src and breadcrumbs 

    Args:
        location: The name of the location for which the map src and breadcrumbs will be generated.
    """

    gmaps = googlemaps.Client(key=googlemaps_api_key)
    geocode_result = gmaps.geocode(location + ', UK')

    if geocode_result:
        # Extract the address components
        address_components = geocode_result[0]['address_components']
        print(address_components)
        # Extract the hierarchical order
        breadcrumbs = [component['long_name'] for component in address_components if 'sublocality' in component['types'] or 'locality' in component['types'] or 'administrative_area_level_2' in component['types'] or 'administrative_area_level_1' in component['types']]

        # get lat lng and create map src 
        lat = geocode_result[0]['geometry']['location']['lat']
        lng = geocode_result[0]['geometry']['location']['lng']
        map_src = f'''https://maps.google.com/maps?q={lat},{lng}&hl=es&z=14&output=embed'''
           
        return map_src, breadcrumbs
    else:
        london_src = "https://maps.google.com/maps?q=51.5072178,-0.1275862&hl=es&z=6&output=embed"
        return london_src, None


# get ONS UK demographic data for a location
"""def get_ons_uk_demographic_data():
    area_code = 'E06000023'  # Bristol local authority code
    data_type = '2019POP'    # Population data for 2019 
    url = f'https://api.beta.ons.gov.uk/v1/population-types/UR/census-observations?area-type=ctry,E92000001&dimensions=health_in_general,highest_qualification'

    response = requests.get(url)
    if response.ok:
        data = response.json()
        print(data)
        # population = data['features'][0]['attributes'][data_type]
        # print(f"Population of {area_code}: {population}")
    else:
        print('Error retrieving data')"""


def get_local_news(location):
    """Get local news by location from newsapi  

    Args:
        location: The name of the location for which the news will be generated.
    """

    params = {
        'apiKey': newsapi_api_key,
        'q': f"{location}, UK local business",
        'sortBy': 'publishedAt',
        'pageSize': 10
    }

    response = requests.get(newsapi_url, params=params)

    if response.status_code == 200:
        data = json.loads(response.text)
        articles = data['articles']
        return articles
    else:
        return None


def content_format_checker(content):
    """Check the format of the content   

    Args:
        content: content generated by openai 
    """

    keywords = {
        "title": r"(?i)(Meta Title:|Title:)",
        "description": r"(?i)(Meta Description:|Description:)",
        "keywords": r"(?i)(Meta Keywords:|Meta Keyword:|Keywords:|Keyword:)",
        "h1": r"(?i)(H1:|Heading H1:|H1 Heading:|Subheading 1:)",
        "h2": r"(?i)(H2:|Heading H2:|H2 Heading:|Subheading 2:)",
        "h3": r"(?i)(H3:|Heading H3:|H3 Heading:|Subheading 3:)",
        "h4": r"(?i)(H4:|Heading H4:|H4 Heading:|Subheading 4:)",
        "h5": r"(?i)(H5:|Heading H5:|H5 Heading:|Subheading 5:)",
        "h6": r"(?i)(H6:|Heading H6:|H6 Heading:|Subheading 6:)"
    }
    
    results = {}
    
    for keyword, pattern in keywords.items():
        match = re.search(pattern, content)
        if match:
            results[keyword] = True
        else:
            results[keyword] = False
    
    return results


def get_meta_tags(content, looking_for="title"):
    """Extract title, meta description and meta keywords from content

    Args:
        content: content generated by openai 
        looking_for: this flag is used to find either title, or description or keywords
    """

    if looking_for == 'description':
        pattern = r"(?i)(?:Meta Description:|Description:|Description Meta:)(.*?)(?=\n\n|\n)"
    elif looking_for == 'keywords':
        pattern = r"(?i)(?:Meta Keyword:|Meta Keywords:|Keywords:|Keyword:)(.*?)(?=\n|\n\n|\.)"
    else:
        pattern = r"(?i)(?:Meta Title:|Title:|Title Meta:)(.*?)(?=\n|\n\n|\.)"
    
    match = re.search(pattern, content)
    
    if match:
        response = match.group(1)
        return response.strip()
    else:
        return None


def extract_heading_and_paragraphs(content):
    """Extract all heading and following paragraph 

    Args:
        content: content generated by openai 
    """

    matches = re.findall(r'(?i)(?:\**H\d Heading\**\s*:*-*–*\**|\**H\d\**\s*:*-*–*\**)(.*?)(?=\n\**H\d Heading\**\s*:-*–*\**|\**H\d\**\s*:*-*–*\**|$)', content, re.DOTALL)

    # matches = re.findall(r'(?i)(?:\**H\d\**\s*:\**|\**H\d Heading\**\s*:\**|\**H\d\**\s*-\**|\**H\d Heading\**\s*-\**)(.*?)(?=\n\**H\d\**\s*:\**|\**H\d Heading\**\s*:\**|\**H\d\**\s*-\**|\**H\d Heading\**\s*-\**|$)', content, re.DOTALL)

    response = []
    for match in matches:
        result = match.strip()
        # heading_with_paragraph = result.split('\n\n', 1)
        heading_with_paragraph = re.split(r'\n\n|\n', result, 1)
        try:
            heading = heading_with_paragraph[0]
        except:
            heading = None
        
        try:
            paragraph = heading_with_paragraph[1]
        except: 
            paragraph = None
        
        response.append((heading, paragraph))

    return response


def generate_html_page(location, content, map_src, breadcrumbs):
    """Creat html page with all necessary information

    Args:
        location: The name of the location 
        content: content generated by openai
        map_src: map src for iframe
        breadcrumbs: list of hierarchical locations for the specific location
    """

    formatter_response = content_format_checker(content)

    meta_title = get_meta_tags(content) if formatter_response.pop('title') else ''

    meta_desc = get_meta_tags(content, "description") if formatter_response.pop('description') else ''

    meta_keywords = get_meta_tags(content, 'keywords') if formatter_response.pop('keywords') else ''

    heading_with_paragraph = extract_heading_and_paragraphs(content)
    
    content_string = ''
    for i, item in enumerate(heading_with_paragraph):
        heading = item[0]
        paragraph = item[1]
        if i == 0:
            content_string += f'''<h{i+1} class="fw-semibold mb-4">{heading.replace("*", "")}</h{i+1}>'''
        elif i > 5:
            content_string += f'''<h6>{heading.replace("*", "").strip()}</h6>'''
        else:
            content_string += f'''<h{i+1}>{heading.replace("*", "").strip()}</h{i+1}>'''

        for para in paragraph.split('\n\n'):
            if para == 'Paragraph:' or para == 'Paragraph: ':
                continue
            p = re.sub(r"Paragraph\s*:*-*\s*?\n?", "", para).replace("\n", "<br>")
            content_string += f'''<p>{p.replace("*", "").strip()}</p>'''

    # print(content_string)

    # Load the HTML file
    with open("asademo.html", "r", encoding='utf-8') as f:
        html = f.read()

    # Parse the HTML file with BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")

    # find and update meta tags
    title_tag = soup.find('title')
    title_tag.string = meta_title.replace("*", "").strip()

    meta_description = soup.find('meta', attrs={'name': 'description'})
    meta_description['content'] = meta_desc.replace("*", "").strip()

    meta_keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
    meta_keywords_tag['content'] = meta_keywords.replace("*", "").strip()

    og_title = soup.find("meta", {'property': 'og:title'})
    og_title['content'] = meta_title
    og_desc = soup.find("meta", {'property': 'og:description'})
    og_desc['content'] = meta_desc
    og_url = soup.find("meta", {"property": "og:url"})
    url = f"https://www.asadistribution.co.uk/leaflets-{location.lower().replace(' ', '-')}/"
    og_url['content'] = url

    twitter_title = soup.find('meta', {'name': 'twitter:title'})
    twitter_title['content'] = meta_title
    twitter_desc = soup.find('meta', {'name': 'twitter:description'})
    twitter_desc['content'] = meta_desc
    twitter_url = soup.find('meta', {'name': 'twitter:url'})
    twitter_url['content'] = url
    
    structured_data = soup.find('script', {'type': 'application/ld+json'})
    structured_data.string = f'''{{
      "@context": "https://schema.org/",
      "@type": "LocalBusiness",
      "name": "ASA Distribution",
      "description": "{meta_desc}",
      "url": "{url}",
      "image": "https://www.asadistribution.co.uk/static/images/logo-asadirect.png",
      "telephone": "+44 0333 344 9456",
      "address": {{
        "@type": "PostalAddress",
        "streetAddress": "Millmead Business Centre, Mill Mead Rd",
        "addressLocality": "London",
        "postalCode": "N17 9QU",
        "addressCountry": "UK"
      }},
      "priceRange": "££"
    }}'''

    canonical_tag = soup.find('link', attrs={'rel': 'canonical'})
    canonical_tag['href'] = url

    # find breadcrumbs div and item 
    breadcrumbs_list = soup.find('ol', {'class': 'breadcrumb'})
    breadcrumbs_item = soup.find('li', {'class': 'breadcrumb-item'})
    if breadcrumbs is None or len(breadcrumbs) == 0 or len(breadcrumbs) == 1:
        active_breadcrumbs_item = location
    else:
        breadcrumbs.reverse()
        if location not in breadcrumbs:
            active_breadcrumbs_item = location
        else:
            active_breadcrumbs_item = breadcrumbs.pop()

        for item in breadcrumbs:
            new_item = copy.deepcopy(breadcrumbs_item)
            new_item.find('a').string = item 
            converted_value = item.replace(" ", "-").lower()
            new_item.find('a')['href'] = f'/leaflets-{converted_value}/' 
            breadcrumbs_list.append(new_item)

    # append active breadcrumb 
    active_breadcrumbs = f'<li class="breadcrumb-item active" aria-current="page">{active_breadcrumbs_item}</li>'
    active_breadcrumbs_tag = BeautifulSoup(active_breadcrumbs, 'html.parser')
    breadcrumbs_list.append(active_breadcrumbs_tag)

    # remove the demo breadcrumbs_item
    breadcrumbs_item.decompose()

    # update content 
    content_tag = BeautifulSoup(content_string, 'html.parser')

    # find main content div and append content tag 
    main_content_div = soup.find('div', {"id": "main-content"})
    main_content_div.append(content_tag)

    # find map iframe by it's id and change src value 
    map_iframe = soup.find("iframe", {"id": "map_iframe"})
    map_iframe["src"] = map_src

    # Find the JavaScript variable and update its value
    # js_variable = soup.find('script', {'id': 'news_script'})
    # js_variable.string = f'var area = "{location}";'
    
    # Write the modified HTML to a file
    pretty_html = soup.prettify(formatter=None)
    file_name = f"""{location}_{str(datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))}.html"""

    with open(file_name, "w", encoding="utf-8") as f:
        f.write(pretty_html)


def append_to_file(filename, text):
    """Appends new content to the specified file.

    Args:
        file_name: The name of the file to append to.
        new_content: The content to append to the file.

    """

    with io.open(filename, "a", encoding="utf-8") as f:
        f.write(text)



def main():
    """
        loop through all location and generate html page
    """

    locations = ["Nottinghamshire", "Kirkby-in-Ashfield", "Newark-on-Trent", "Sutton-in-Ashfield"]

    for location in locations:
        content = generate_text(location)
        
        print('write content in a file')
        if content:
            append_to_file("london-content.txt", content)
            print('wrote on file')
        print('take rest...........')
        time.sleep(3)

        map_src, breadcrumbs = get_breadcrumbs_and_map_src(location)

        try:
            generate_html_page(location, content, map_src, breadcrumbs)
            print('New file created')
        except:
            print("Couldn't create file")

        time.sleep(10)


if __name__ == "__main__":
    main()


