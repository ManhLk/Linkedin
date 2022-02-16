import undetected_chromedriver.v2 as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time
import requests
import os
import re
from datetime import datetime
import random
from bs4 import BeautifulSoup


def init_driver(proxy=None):
    options = uc.ChromeOptions()
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--start-maximized")
    driver = uc.Chrome(options= options, version_main=98)
    if proxy:
        options.add_argument(f'--proxy-server={proxy}')
    return driver

## Common method

def login(driver, username, password):
    driver.get('https://www.linkedin.com/login')
    time.sleep(random.randint(2,3))
    driver.find_element_by_xpath('//input[@id="username"]').send_keys(username)
    time.sleep(random.randint(1,2))
    driver.find_element_by_xpath('//input[@id="password"]').send_keys(password)
    time.sleep(1)
    driver.find_element_by_xpath('//button[@aria-label="Sign in"]').send_keys(Keys.RETURN)

def exist_element(driver, xpath):
    result = driver.find_elements_by_xpath(xpath)
    return True if len(result) >0 else False

def see_more(driver):
    try:
        btn_see_more = driver.find_element_by_xpath('.//button[contains(@class, "inline-show-more-text__button")]')
        while 'more' in btn_see_more.text:
            ActionChains(driver).click(btn_see_more).perform()
            time.sleep(0.5)
    except:
        try:
            btn_see_more.click()
        except:
            pass

def check_login(driver):
    if exist_element(driver= driver, xpath= '//a[@data-control-name="nav_homepage"]'):
        return True
    return False

def check_banned(driver):
    if 'checkpoint/challenge' in driver.current_url or 'linkedin.com/checkpoint/lg/login-submit' in driver.current_url:
        return True

    if not check_login(driver):
        login(driver, CREDENTIAL)
    else:
        return False
    
    if not check_login(driver):
        return True

def get_element_text(driver, xpath, more=False):
    if exist_element(driver, xpath):
        if more:
            see_more(driver.find_element_by_xpath(xpath))
        return driver.find_element_by_xpath(xpath).text
    else:
        return None

def preprocessing(text):
    try:
        text = text.split('\n')
        return [w for w in text if w.strip() != '']
    except:
        return None

def check_format_linked_url(url):
    if 'https://www.linkedin.com/in/' in url:
        return True
    return False

def get_item_relation(element):
    item = {}
    item['url'] = element.get_attribute('href')
    if item['url'][-1] == '/':
        item['url'] = item['url'][:-1]
    item['fullname'] = element.find_element_by_xpath('.//h3[contains(@class, "actor-name")]').text.split('\n')
    item['fullname'] = item['fullname'][0] if len(item['fullname']) > 0 else ''
    item['short_description'] = element.find_element_by_xpath('.//p[contains(@class, "pv-browsemap-section")]').text
    item['crawled_at'] = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
    item['avatar'] = get_image(element.find_element_by_xpath('.//img').get_attribute('src'))
    item['crawled'] = False
    return item

def get_image(img_url):
    try:
        return requests.get(img_url).content
    except:
        return None
## Type 1

def crawl_relation_url_1(driver, url):
    if not check_format_linked_url(url):
        return []
    
    xpath = '//ul[@class="browsemap"]/li[contains(@class, "pv-browsemap-section__member-container")]/a[@data-control-name="browsemap_profile"]'
    if not exist_element(driver, xpath):
        return None
    
    # Click show more
    xpath_btn_show_more = '//footer[@class="artdeco-card__actions"]/button'
    if exist_element(driver, xpath_btn_show_more):
        btn = driver.find_element_by_xpath(xpath_btn_show_more)
        ActionChains(driver).click(btn).perform()
    
    relation_urls = driver.find_elements_by_xpath(xpath)
    list_item = []
    for element in relation_urls:
        item = get_item_relation(element)
        list_item.append(item)
    return list_item

def download_avatar_1(driver, url):
    # Check image url
    driver.get(url + '/detail/photo/')
    xpath = '//img[contains(@class, "pv-member-photo-modal__profile-image")]'
    if not exist_element(driver= driver, xpath= xpath):
        return None
    
    # Download image
    img_url = driver.find_element_by_xpath(xpath).get_attribute('src')
    response = requests.get(img_url).content
    return response

def get_experience_1(driver):
    xpath = '//section[@id="experience-section"]//ul[contains(@class, "pv-profile-section__section-info")]/li'
    if not exist_element(driver, xpath):
        return None
    
    item = []
    exps = driver.find_elements_by_xpath(xpath)
    for exp in exps:
        experience = {}
        xpath = './/div[@class="pv-entity__company-summary-info"]/h3'
        if exist_element(exp, xpath):
            experience['company'] = get_element_text(driver= exp, xpath= xpath)
            sub_exps = exp.find_elements_by_xpath('.//ul[contains(@class, "pv-entity__position-group")]/li')
            for sub_exp in sub_exps:
                see_more(sub_exp)
                # Position
                experience['position'] = preprocessing(get_element_text(driver=sub_exp, xpath='.//h3'))
                
                # Time
                time = preprocessing(get_element_text(driver= sub_exp, xpath= './/h4[contains(@class, "pv-entity__date-range")]'))
                experience['time'] = time if time == None else time[-1]
                
                # Detail
                experience['detail'] = preprocessing(get_element_text(driver= sub_exp, xpath= './/div[contains(@class, "pv-entity__extra-details")]'))
                item.append(experience)
        else:
            see_more(driver=exp)
            # Company
            experience['company'] = get_element_text(driver= exp, xpath='.//p[contains(@class, "pv-entity__secondary-title")]')
            
            # Position
            experience['position'] = get_element_text(driver= exp, xpath= './/div[contains(@class,"pv-entity__summary-info")]/h3')
            
            # Time
            time = preprocessing(get_element_text(driver= exp, xpath= './/h4[contains(@class, "pv-entity__date-range")]'))
            experience['time'] = time if time == None else time[-1]
            
            # Detail
            experience['detail'] = preprocessing(get_element_text(driver= exp, xpath='.//div[contains(@class, "pv-entity__extra-details")]'))
            item.append(experience)
    return item

def get_education_1(driver):
    item = []
    xpath = '//section[@id="education-section"]//ul/li[contains(@class, "pv-education-entity")]'
    if not exist_element(driver= driver, xpath=xpath):
        return None
    
    edus = driver.find_elements_by_xpath('//section[@id="education-section"]//ul/li[contains(@class, "pv-education-entity")]')
    for edu in edus:
        education = {}
        education['school'] = get_element_text(driver= edu, xpath= './/h3[contains(@class, "pv-entity__school-name")]')

        if exist_element(driver= edu, xpath= './/div[@class="pv-entity__degree-info"]/p'):
            for p in edu.find_elements_by_xpath('.//div[@class="pv-entity__degree-info"]/p'):
                try:
                    key , value = p.text.split('\n')
                    education[key] = value
                except:
                    continue
            # Time
            time = preprocessing(get_element_text(driver= edu, xpath= './/p[contains(@class, "pv-entity__dates")]'))
            education['time'] = time if time == None else time[-1]
            
            # Detail
            education['detail'] = get_element_text(driver= edu, xpath= './/p[contains(@class, "pv-entity__secondary-title")]') 
            item.append(education)
    return item

def crawl_profile_1(driver, url):

    profile = {}

    # Name
    profile['fullname'] = get_element_text(driver, xpath='//h1[contains(@class, "text-heading-xlarge")]')
    
    # Short description
    profile['short_description'] = get_element_text(driver, xpath= '//div[@class="text-body-medium break-words"]')

    # About
    profile['about'] = preprocessing(get_element_text(driver, xpath= '//section[contains(@class, "pv-about-section")]', more=True))
    if len(profile['about']) == 0:
        profile['about'] = None
    else:
        profile['about'] = '\n'.join(profile['about'])

    # Experience
    profile['experience'] = get_experience_1(driver)

    # Education 
    profile['education'] = get_education_1(driver)

    # Skill
    if exist_element(driver= driver, xpath= '//section[contains(@class, "pv-skill-categories-section")]//button[@data-control-name="skill_details"]'):
        btn = driver.find_element_by_xpath('//section[contains(@class, "pv-skill-categories-section")]//button[@data-control-name="skill_details"]')
        ActionChains(driver).click(btn).perform()
    
    try:
        skills = driver.find_elements_by_xpath('//section[contains(@class, "pv-skill-categories-section")]//ol/li[contains(@class, "pv-skill-category-entity")]//p')
        profile['skills'] = [skill.text for skill in skills]
        if len(profile['skills']) == 0:
            profile['skills'] = None
    except:
        profile['skills'] = None

    # Url
    profile['url'] = url

    # Datetime
    profile['crawled_at'] = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")

    # HTML
    html =  driver.page_source.encode()

    profile['html'] = html

    # Avatar
    profile['avatar'] = download_avatar_1(driver= driver, url= url)

    # Crawler
    profile['crawled'] = True
    return profile

## Type 2

def crawl_relation_url_2(driver, url):
    if not check_format_linked_url(url):
        return []
    
    xpath = '//ul[@class="mt4"]/li[contains(@class, "pv-browsemap-section__member-container")]/a'
    if not exist_element(driver, xpath):
        return None
    
    # Click show more
    try:
        btn_show_more = driver.find_element_by_xpath('//footer[@class = "artdeco-card__actions"]/button')
        ActionChains(driver).click(btn_show_more).perform()
    except:
        pass
    
    relation_urls = driver.find_elements_by_xpath(xpath)
    list_item = []
    for element in relation_urls:
        item = get_item_relation(element)
        list_item.append(item)
    return list_item

def get_experience_2(driver, id):
    xpath = f'//section[contains(@id, "{id}")]/div/ul[contains(@class, "pvs-list")]/li[contains(@class, "pvs-list__item")]'
    if not exist_element(driver, xpath):
        return None
    
    item = []
    exps = driver.find_elements_by_xpath(xpath)
    for exp in exps:
        experience = {}
        if exist_element(driver= exp, xpath= './/span[@class="pvs-entity__path-node"]'):
            experience['company'] = preprocessing(get_element_text(driver= exp, xpath= './/a[@data-field="experience_company_logo"]//span[contains(@class, "t-bold")]'))
            sub_exps = exp.find_elements_by_xpath('.//div[@class="pvs-list__outer-container"]/ul[contains(@class, "pvs-list")]/li')
            for sub_exp in sub_exps:
                see_more(sub_exp)
                # Position
                experience['position'] = get_element_text(driver=sub_exp, xpath='.//span[contains(@class, "t-bold")]/span[@aria-hidden="true"]')
                
                # Time
                xpath = './/span[contains(@class, "t-normal")]/span[@aria-hidden="true"]'
                if exist_element(driver= sub_exp, xpath= xpath):
                    times = sub_exp.find_elements_by_xpath(xpath)
                    experience['time'] = [t.text for t in times]

                
                # Detail
                experience['detail'] = preprocessing(get_element_text(driver= sub_exp, xpath= './/div[contains(@class, "pv-shared-text-with-see-more")]'))
                item.append(experience)
        else:
            see_more(driver=exp)
            # Company
            experience['company'] = get_element_text(driver= exp, xpath='.//span[@class="t-14 t-normal"]/span[@aria-hidden="true"]')
            
            # Position
            experience['position'] = get_element_text(driver= exp, xpath= './/span[contains(@class, "t-bold")]/span[@aria-hidden="true"]')
            
            # Time
            experience['time'] = get_element_text(driver= exp, xpath= './/span[@class="t-14 t-normal t-black--light"]/span[@aria-hidden="true"]')
            
            # Detail
            experience['detail'] = preprocessing(get_element_text(driver= exp, xpath='.//div[contains(@class, "pv-shared-text-with-see-more")]//span[@aria-hidden="true"]'))
            item.append(experience)
    return item

def get_education_2(driver, id):
    item = []
    xpath = f'//section[contains(@id, "{id}")]/div/ul[contains(@class, "pvs-list")]/li[contains(@class, "pvs-list__item")]'
    if not exist_element(driver= driver, xpath=xpath):
        return None
    
    edus = driver.find_elements_by_xpath(xpath)
    for edu in edus:
        education = {}
        education['school'] = get_element_text(driver= edu, xpath= './/span[contains(@class, "t-bold")]/span[@aria-hidden="true"]')

        keys = ["Degree Name", "Field Of Study", "See more"]
        if exist_element(driver=edu, xpath='.//span[@class="t-14 t-normal"]/span[@aria-hidden="true"]'):
            title = edu.find_element_by_xpath('.//span[@class="t-14 t-normal"]/span[@aria-hidden="true"]').text.split(',')
            for i in range(len(title)):
                if i < 3:
                    education[keys[i]] = title[i]

            # Time
            education['time'] = get_element_text(driver= edu, xpath= './/span[@class="t-14 t-normal t-black--light"]/span[@aria-hidden="true"]')
            
            # Detail
            education['detail'] = get_element_text(driver= edu, xpath= './/div[contains(@class, "pv-shared-text-with-see-more")]//span[@aria-hidden="true"]') 
            item.append(education)
    return item

def download_avatar_2(driver, url):
    # Check image url
    driver.get(url + '/overlay/photo/')
    xpath = '//img[contains(@class, "pv-member-photo-modal__profile-image")]'
    if not exist_element(driver= driver, xpath= xpath):
        return None
    
    # Conver img to bytes
    img_url = driver.find_element_by_xpath(xpath).get_attribute('src')
    response = requests.get(img_url).content
    
    return response

def crawl_profile_2(driver, url):

    profile = {}

    # Name
    profile['fullname'] = get_element_text(driver, xpath='//h1[contains(@class, "text-heading-xlarge")]')
    
    # Short description
    profile['short_description'] = get_element_text(driver, xpath= '//div[@class="text-body-medium break-words"]')

    # BeautifulSoup
    html =  driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    html = html.encode()
    
    main = soup.find(id="main")
    
    # About
    id_education, id_experience, id_skill = None, None, None
    for section in main.children:
        try:
            if section.div.get('id') == "about":
                about = section.text
                profile['about'] = about
            
            elif section.div.get('id') == 'education':
                id_education = section.get('id')
            elif section.div.get('id') == 'experience':
                id_experience = section.get('id')
            elif section.div.get('id') == "skills":
                id_skill = section.get('id')
        except:
            continue
    # about = preprocessing(get_element_text(driver, xpath= '//section[contains(@id, "ABOUT")]', more=True))
    # profile['about'] = list(set(about)) if about != None else about

    # Experience
    profile['experience'] = get_experience_2(driver, id_experience)

    # Education 
    profile['education'] = get_education_2(driver, id_education)

    # Skill
    try:
        skills = driver.find_elements_by_xpath(f'//section[contains(@id, "{id_skill}")]/div/ul/li[contains(@class, "pvs-list__item")]//span[contains(@class, "t-bold")]/span[@aria-hidden="true"]')
        profile['skills'] = [skill.text for skill in skills]
        if len(profile['skills']) == 0:
            profile['skills'] = None
    except:
        profile['skills'] = None
    
    profile['crawled_at'] = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")

    # Url
    profile['url'] = url

    # Datetime
    profile['crawled_at'] = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")

    # HTML
    profile['html'] = html

    # Avatar
    profile['avatar'] = download_avatar_2(driver= driver, url= url)

    # Crawler
    profile['crawled'] = True
    return profile

## Crawler

def crawl_profile(driver, url):
    # driver.get(url)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    if driver.find_element_by_xpath('//div[@id="profile-content"]').get_attribute('class') == 'extended':
        profile = crawl_profile_1(driver, url)
    else:
        profile = crawl_profile_2(driver, url)
    return profile

def crawl_relation_url(driver, url):
    # driver.get(url)
    if driver.find_element_by_xpath('//div[@id="profile-content"]').get_attribute('class') == 'extended':
        list_result = crawl_relation_url_1(driver, url)
    else:
        list_result = crawl_relation_url_2(driver, url)
    return list_result

if __name__ == '__main__':
    driver = init_driver()
    login(driver=driver, username='quanhanh.pn0910@gmail.com', password='CIST2o20')
    url = 'https://www.linkedin.com/in/frankluong/'
    driver.get(url)
    profile = crawl_profile(driver= driver, url=url)
    relation = crawl_relation_url(driver=driver, url=url)