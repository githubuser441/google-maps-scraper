import re as rex
import json
from datetime import datetime
# from botasaurus import *

def convert_timestamp_to_iso_date(timestamp):
    # Convert from microseconds to milliseconds
    milliseconds = int(timestamp) / 1000
    # Create a new Date object
    date = datetime.utcfromtimestamp(milliseconds)
    # Return the date in the specified format
    return date.isoformat() + "Z"



def clean_link(link):
    if link is not None:
        # Remove everything starting from "&opi"
        opi_index = link.find('&opi')
        if opi_index != -1:
            link = link[:opi_index]

        # Remove "/url?q=" if it's at the start of the link
        if link.startswith('/url?q='):
            link = link[len('/url?q='):]

    return link
def safe_get(data, *keys):
    for key in keys:
        try:
            data = data[key]
        except (IndexError, TypeError, KeyError):
            return None
    return data

def get_categories(data):
    return safe_get(data, 6, 13)

def get_thumbnail(data):
    return safe_get(data, 6, 72, 0, 1, 6, 0)

def get_place_id(data):
    return safe_get(data, 6, 78)

def get_description(data):
    return safe_get(data, 6, 32, 1, 1)

def get_open_state(data):
    return safe_get(data, 6, 34, 4, 4)

def get_plus_code(data):
    return safe_get(data, 6, 183, 2, 2, 0)

def get_gps_coordinates(data):
    return {'latitude': safe_get(data, 6, 9, 2), 'longitude': safe_get(data, 6, 9, 3)}

def get_images(data):
    images = safe_get(data, 6, 171, 0) or []
    ls = []
    for element in images:
        title = element[2]
        thumbnail = safe_get(element, 3, 0, 6, 0)
        if thumbnail:
            ls.append({'about': title, 'link': thumbnail})
    return ls

def get_reservations(data):
    images = safe_get(data, 6, 46) or []
    ls = []
    for element in images:
        link, source = element[0], element[1]
        ls.append({'link': clean_link(link), 'source': source})
    return ls

def get_order_online_link(data):
    images = safe_get(data, 6, 75, 0, 1, 2) or safe_get(data, 6, 75, 0, 0, 2) or []
    ls = []
    for element in images:
        source, link = safe_get( element,0,0), safe_get( element,1,2,0)
        ls.append({'link': clean_link(link), 'source': source})
    return ls

def get_hours(data):
    images = safe_get(data, 6, 34, 1) or []
    ls = []
    for element in images:
        day, times = element[0], element[1]
        ls.append({'day': day, 'times':  times})
    return ls


def get_review_keywords(data):
    images = safe_get(data, 6, 153, 0) or []
    ls = []
    for element in images:
        keyword, count = element[1], element[3][4]
        ls.append({'keyword': keyword, 'count':  count})
    return ls

def get_options(data):
    return [{'name': x[1], 'enabled': (safe_get(x, 2, 1, 0, 0) or x[4][0]) != 0} for x in data]

def get_about(data):
    rvs = safe_get(data, 6, 100, 1) or []
    ls = []
    for element in rvs:
        id, name, options = element[0], element[1], get_options(element[2] or [])
        ls.append({'id': id, 'name': name, 'options': options})
    return ls

def get_menu(data):
    link = safe_get(data, 6, 38, 0)
    source = safe_get(data, 6, 38, 1)
    return {'link': clean_link(link), 'source': source}

def get_review_images(data):
    return [x[6][0] for x in data]

def extract_google_maps_contributor_url(input_url):
    if input_url is not None:
        # Define a regular expression pattern to match the desired URL
        pattern = r'https://www\.google\.com/maps/contrib/\d+'
        
        # Use re.search to find the first match in the input_url
        match = rex.search(pattern, input_url)
        
        if match:
            # Extract the matched URL
            contributor_url = match.group(0)
            
            # Add "/reviews?entry=ttu" to the end of the URL
            contributor_url += '/reviews?entry=ttu'
            
            return contributor_url
        else:
            return None

def generate_google_reviews_url(placeid, query, authuser, hl, gl):
    base_url = "https://search.google.com/local/reviews"
    params = {
        "placeid": placeid,
        "q": query,
        "authuser": authuser,
        "hl": hl,
        "gl": gl
    }
    query_string = '&'.join(f"{key}={value}" for key, value in params.items())
    full_url = f"{base_url}?{query_string}"
    return full_url


def get_user_reviews(data):
    rvs = safe_get(data, 6, 52, 0) or []
    ls = []
    for element in rvs:
        
        name, profile_picture, when, rating, description = element[0][1], element[0][2], element[1], element[4], element[3]
        # ChdDSUhNMG9nS0VJQ0FnSUNKeHJUYzJnRRAB
        review_id = element[3]


        review_translated_text = element[47]
        response_from_owner_translated_text = safe_get(element,9, 5) or None
        reviewer_url = extract_google_maps_contributor_url(safe_get(element,60, 0))

        response_from_owner_text = safe_get(element,9, 1) or None

        response_from_owner_ago = safe_get(element,9, 0) or None
        response_from_owner_date = safe_get(element,9, 3) or safe_get(element,9, 4) or None
        if response_from_owner_date:
            response_from_owner_date = convert_timestamp_to_iso_date(response_from_owner_date)

        # 1688528496522

        published_at_date = safe_get(element,27) or safe_get(element,57) or None
        if published_at_date:
            published_at_date = convert_timestamp_to_iso_date(published_at_date)
        
        # if "ChZDSUhNMG9nS0VJQ0FnSUR4Z0xERGJBEAE" == review_id:
        # bt.write_json(element, name)

        images = get_review_images(element[14] or [])
        
        total_number_of_reviews_by_reviewer = element[12][1][1]
        total_number_of_photos_by_reviewer = element[12][1][2]
        
        review_likes_count = element[16]
        
        is_local_guide = safe_get( element, 12, 1, 0, 2)
        if is_local_guide is not None:
            is_local_guide = is_local_guide > 0
        else:
             is_local_guide = False
            
        # > 0
        
        ls.append({
             'review_id':review_id,
             'reviewer_name':name,
             'rating': rating,
             'review_text': description,
             "published_at": when,
             "published_at_date": published_at_date,
             "response_from_owner_text":response_from_owner_text,
             "response_from_owner_ago": response_from_owner_ago, 
             "response_from_owner_date": response_from_owner_date, 
             "review_likes_count": review_likes_count, 
             "total_number_of_reviews_by_reviewer": total_number_of_reviews_by_reviewer, 
             "total_number_of_photos_by_reviewer": total_number_of_photos_by_reviewer, 
             "reviewer_url": reviewer_url, 
             "reviewer_profile_picture":profile_picture,
             "is_local_guide": is_local_guide, 
             "review_translated_text": review_translated_text, 
             "response_from_owner_translated_text":response_from_owner_translated_text , 
             "review_photos": images,
            })

    return ls

def get_owner(data):
    name = safe_get(data, 6, 57, 1)
    id = safe_get(data, 6, 57, 2)
    link = f"https://www.google.com/maps/contrib/{id}" if id else None
    return {'id': id, 'name': name, 'link': clean_link(link) if link else None }
    # if id else {'name': name}

def get_complete_address(data):
    ward = safe_get(data, 6, 183, 1, 0)
    street = safe_get(data, 6, 183, 1, 1)
    city = safe_get(data, 6, 183, 1, 3)
    postal_code = safe_get(data, 6, 183, 1, 4)
    state = safe_get(data, 6, 183, 1, 5)
    country_code = safe_get(data, 6, 183, 1, 6)

    result = {
        'ward': ward,
        'street': street,
        'city': city,
        'postal_code': postal_code,
        'state': state,
        'country_code': country_code
    }
    return result

def get_time_zone(data):
    return safe_get(data, 6, 30)

def get_reviews_link(data):
    return clean_link(safe_get(data, 6, 4, 3, 0))

def get_rating(data):
    return safe_get(data, 6, 4, 7)

def get_reviews(data):
    return safe_get(data, 6, 4, 8)

def get_phone(data):
    return safe_get(data, 6, 178, 0, 0)

def get_price_range(data):
    rs = safe_get(data, 6, 4, 2)
    
    if rs is not None:
        return len(rs) * "$" 

def get_title(data):
    return safe_get(data, 6, 11)

def get_address(data):
    return safe_get(data, 6, 18)

def get_website(data):
    return clean_link(safe_get(data, 6, 7, 0))

def get_features(data):
    out = {}
    features = safe_get(data, 6, 100, 1)
    if features is not None:
        for feature in features:
            out[feature[0]] = [f[1] for f in feature[2]]
    return out

def get_main_category(data):
    return safe_get(data, 6, 13, 0)

def get_cid(data):
    return safe_get(data, 25, 3, 0, 13, 0, 0, 1)

def get_data_id(data):
    return safe_get(data, 6, 10)

def get_reviews_per_rating(data):
    return {i: safe_get(data, 6, 52, 3, i - 1) for i in range(1, 6)}

def parse(data):
    # Assuming 'input_string' is provided to the function in some way
    input_string = json.loads(data)[3][6]  # Replace with actual input
    substring_to_remove = ")]}'"

    modified_string = input_string
    if input_string.startswith(substring_to_remove):
        modified_string = input_string[len(substring_to_remove):]

    return json.loads(modified_string)

def get_hl_from_link(link):
    # Regular expression to find the 'hl' parameter in the URL
    match = rex.search(r"[?&]hl=([^&]+)", link)
    
    # If found, return the value, otherwise return 'en'
    return match.group(1) if match else 'en'

def extract_business_name(url):
    # Regular expression to match the pattern in the URL
    match = rex.search(r"maps/place/([^/]+)", url)
    if match:
        return match.group(1)
    return None


def reorder_hours_list(hours_list):
    # Get the current weekday (0 for Monday, 1 for Tuesday, etc.)
    today_weekday = datetime.today().weekday()
    ls = []
    if today_weekday == 0:
        ls = [0,1,2,3,4,5,6]
    if today_weekday == 1:
        ls = [6,0,1,2,3,4,5]
    if today_weekday == 2:
        ls = [5,6,0,1,2,3,4]
    if today_weekday == 3:
        ls = [4,5,6,0,1,2,3]
    if today_weekday == 4:
        ls = [3,4,5,6,0,1,2]
    if today_weekday == 5:
        ls = [2,3,4,5,6,0,1]
    if today_weekday == 6:
        ls = [1,2,3,4,5,6,0]

    rs = []
    
    
    
    for i in ls:
        rs.append(hours_list[i])
    return rs

def find_close_days(schedule):
    """
    Finds days that are closed based on the provided schedule.

    :param schedule: A list of dictionaries with 'day' and 'times' keys.
    :return: A list of days that are closed.
    """
    closed_days = []
    number_pattern = rex.compile(r'\d')

    for day_info in schedule:

        # Check if 'times' is empty or contains strings like 'closed' or 'not available'
        times = day_info["times"]
        times_str = "".join(times)
        if not number_pattern.search(times_str):
            closed_days.append(day_info["day"])

    return closed_days

def find_most_common_element(ls):
    if not ls:
        return None  # Handle empty list case

    # Dictionary to count occurrences of each element
    element_count = {}
    for element in ls:
        if element in element_count:
            element_count[element] += 1
        else:
            element_count[element] = 1

    # Find the most common element
    max_count = max(element_count.values())
    common_elements = [k for k, v in element_count.items() if v == max_count]

    # Return the first element if all occur equally, else return the most common one
    return common_elements[0]

def extract_work_day_time(schedule):
    """
    Finds days that are closed based on the provided schedule.

    :param schedule: A list of dictionaries with 'day' and 'times' keys.
    :return: A list of days that are closed.
    """
    days = []
    number_pattern = rex.compile(r'\d')

    for day_info in schedule:
        # Check if 'times' is empty or contains strings like 'closed' or 'not available'
        times = day_info["times"]
        times_str = ", ".join(times)
        if number_pattern.search(times_str):
            days.append(times_str)

    return find_most_common_element(days)


def extract_data(input_str, link):
    data = parse(input_str)
    categories = get_categories(data)
    place_id = get_place_id(data)
    order_online_links = get_order_online_link(data)
    thumbnail = get_thumbnail(data)
    coordinates = get_gps_coordinates(data)
    images = get_images(data)
    description = get_description(data)
    status = get_open_state(data)
    plus_code = get_plus_code(data)
    reservations = get_reservations(data)
    menu = get_menu(data)
    owner = get_owner(data)
    time_zone = get_time_zone(data)
    complete_address = get_complete_address(data)
    reviews_link = get_reviews_link(data)
    if reviews_link is None:
        gl = complete_address['country_code']
        hl = get_hl_from_link(link)
        query = extract_business_name(link)
        reviews_link = generate_google_reviews_url(place_id,query , 0, hl, gl)
        pass

    price_range = get_price_range(data)
    reviews_per_rating = get_reviews_per_rating(data)
    cid = get_cid(data)
    data_id = get_data_id(data)
    about = get_about(data)
    title = get_title(data)

    hours = get_hours(data)
    if hours:
        hours = reorder_hours_list(hours)
    else:
        hours = []
    openinghours = {}
    for hour in hours:
        openinghours[hour['day']] = hour['times'][0]
    
    rating = get_rating(data)
    reviews = get_reviews(data)
    phone = get_phone(data)
    address = get_address(data)
    website = get_website(data)
    features = get_features(data)
    main_category = get_main_category(data)
    user_reviews = get_user_reviews(data)
    
    review_keywords = get_review_keywords(data)
    # bt.write_json(data, title)

    # Add more as needed
    # skipped questions_and_answers
    # popular_times
    # people also search for

    return {
        'place_id': place_id,
        'name': title,
        'description': description,
        'reviews': reviews,

        'website': website,
        'owner': owner,
        'featured_image': thumbnail,
        'main_category': main_category,
        'categories': categories,
        'rating': rating,
        "workday_timing": extract_work_day_time(hours),
        "closed_on": find_close_days(hours),
        'openinghours': openinghours,
        'features': features,
        'phone': phone,
        'address': address,
        'review_keywords':review_keywords,
        'link':link,

        'status': status,
        'price_range': price_range,
        'reviews_per_rating': reviews_per_rating,
        'reviews_link': reviews_link,
        'coordinates': coordinates,
        'plus_code': plus_code,
        'detailed_address': complete_address,
        'time_zone': time_zone,
        'cid': cid,
        'data_id': data_id,

        'menu': menu,
        'reservations': reservations,
        'order_online_links': order_online_links,

        'about': about,
        'images': images,
        'hours': hours,

        'featured_reviews': user_reviews,
    }