from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
import time
import ast
import random
import store_data as store

def create_driver(driver_path):
    chrome_options = webdriver.ChromeOptions()
    prefs = {"profile.default_content_setting_values.notifications" : 2}
    chrome_options.add_experimental_option("prefs",prefs)
    # chrome_options.headless = True
    driver = webdriver.Chrome(service = Service(driver_path), options=chrome_options)
    return driver

def login_navigate(driver, usr, pwd, url):
    driver.get("https://www.facebook.com")
    username = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='email']")))
    password = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='pass']")))

    username.clear()
    username.send_keys(usr)
    password.clear()
    password.send_keys(pwd)

    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))).click()
    time.sleep(4)
    url = url.replace("www", "touch")
    driver.get(url)

def get_elems(driver, numerofposts = 5):
        
    elems = driver.find_elements(By.CSS_SELECTOR , "article")

    while len(elems) < numerofposts:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(10)
        elems = driver.find_elements(By.CSS_SELECTOR , "article")

    return elems[0:numerofposts]

def post_info(dataft): 
    pageid = str(dataft['content_owner_id_new'])
    actorid = dataft["page_insights"][pageid]['targets'][0]['actor_id']
    postid = dataft["page_insights"][pageid]['targets'][0]['post_id']
    # publish_time = dataft["page_insights"][pageid]['post_context']['publish_time']
    dictionary = {"post_id" : f"{postid}", "page_id": f"{pageid}", "actor_id":f"{actorid}"}
    return dictionary

def get_posts_info(elems):
    post_data = []
    post_urls = []
    for elem in elems:
        dataft = ast.literal_eval(elem.get_attribute('data-ft'))
        dic = post_info(dataft)
        post_data.append(dic)
        post_urls.append(f'{dic["page_id"]}_{dic["post_id"]}')
    return post_data, post_urls

def get_post_content(driver):
    post = driver.find_element(By.CSS_SELECTOR, "._5rgt._5nk5")
    return post.text

def pre_crawl_cmt(driver):
    # click view more cmt until the end
    while True:
        try:
            viewmore_cmt = driver.find_element(By.CSS_SELECTOR, ".async_elem:not(.async_elem_preprocess) ._108_")
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "._108_")))
            viewmore_cmt.click()
            time.sleep(random.randint(30,50))
        except NoSuchElementException:
            break
    
    # click to all view more replies
    viewmore_reps = driver.find_elements(By.CSS_SELECTOR, "._2b1h.async_elem")

    for viewmore_rep in viewmore_reps:
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "._2b1h.async_elem")))
        viewmore_rep.click()
        time.sleep(random.randint(30,50))

def crawl_cmts_reps(driver,cursor, post_id):
    comments = driver.find_elements(By.CSS_SELECTOR, ":not(._2b1k) > ._2a_i")

    for comment in comments:
        try:
            cmt_id = comment.get_attribute("id")
            author = comment.find_element(By.CSS_SELECTOR, ":not(._2b1k) > ._2b05").text
            message = comment.find_element(By.CSS_SELECTOR, f'[data-commentid="{cmt_id}"]').text
            cmt_info = {"comment_id": f"{cmt_id}", "post_id":f"{post_id}", "author":f"{author}", "message":f"{message}"}
            # print(cmt_info)
            store.store_cmt(cursor, cmt_info)
            
            rep_cmts = comment.find_elements(By.CSS_SELECTOR, "._2a_i")
            for rep_cmt in rep_cmts:
                rep_id = rep_cmt.get_attribute("id")
                rep_author = rep_cmt.find_element(By.CSS_SELECTOR, "._2b05").text
                rep_message = rep_cmt.find_element(By.CSS_SELECTOR, f'[data-commentid="{rep_id}"]').text
                rep = {"rep_id": f"{rep_id}", "rep_to":f"{cmt_id}", "rep_author":f"{rep_author}", "rep_message":f"{rep_message}"}
                # print(rep)
                store.store_rep(cursor, rep)
            
        except Exception:
            continue

BASEURL = "https://www.facebook.com/"

username ="cs232khcl@gmail.com"
password = "definitelynotapassword"
desktop_user = "DESKTOP-NHATMIN\DELL"
server = 'DESKTOP-NHATMIN\SQLEXPRESS02'
database = 'FB'
frequently = 60*5

url = input("Nhập link page facebook cần crawl: ")
numberofpost = int(input("Số lượng bài viết: "))

driver = create_driver(driver_path)
store.check(server, database, desktop_user)
cursor, cnxn = store.create_cursor(server, database)
login_navigate(driver, username, password, url)
i = 0
while True:
    if i == 1:
        numberofpost = 5
    i = 1
    elems = get_elems(driver, numberofpost)
    posts_data, post_urls = get_posts_info(elems)

    for i, post_url in enumerate(post_urls):
        if not store.post_exists(cursor, posts_data[i]):    
            try:
                url = BASEURL+post_url
                touch_url = url.replace("www", "touch")
                driver.get(touch_url)
                posts_data[i]["content"] = get_post_content(driver)
                store.store_post(cursor, posts_data[i])
                pre_crawl_cmt(driver)
                post_id = posts_data[i]["post_id"]
                crawl_cmts_reps(driver, cursor, post_id)
                time.sleep(random.randint(60))
            except Exception:
                continue

    time.sleep(frequently)
