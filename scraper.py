from time import sleep
import sys
from getpass import getpass

import pandas as pd
from selenium import webdriver
import selenium.common
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager


username = input("uspace username: ")
password = getpass("uspace password: ")

print("Trying to launch firefox")
driver = webdriver.Firefox(executable_path=GeckoDriverManager().install())
driver.implicitly_wait(5)


def login():

    driver.get("https://uspace.univie.ac.at/web/gast/login")

    username_input = driver.find_element_by_id("uspace_userid")
    password_input = driver.find_element_by_id("uspace_password")
    form = driver.find_element_by_tag_name("form")

    username_input.send_keys(username)
    password_input.send_keys(password)
    form.submit()


def expand_grade_page():

    driver.get("https://uspace.univie.ac.at/web/studium/pruefungspass")
    sleep(3)

    for i in range(2):
        labels = driver.find_elements_by_tag_name("label")
        for label in labels:
            sleep(0.1)
            try:
                i = label.find_element_by_xpath("./input")
                is_expanded = i.get_attribute("aria-expanded") == "true"
                if not is_expanded:
                    label.click()

            except selenium.common.exceptions.NoSuchElementException:
                break

        sleep(0.2)


def get_grades_and_ects():

    subjects = []

    courses = driver.find_elements_by_class_name("finalModule")
    if len(courses) == 0:
        print("No courses found. Aborting")
        raise RuntimeError()

    print(f"Gefundene Module: {len(courses)}")
    for course in courses:
        modul = course.find_element_by_tag_name("span").get_attribute("innerHTML")
        try:

            cols = course.find_elements_by_class_name("col-lg-1")
            grade = int(cols[-1].find_elements_by_tag_name("span")[-1].get_attribute("innerHTML"))
            ects = int(cols[-2].get_attribute("innerHTML").split("\n")[1].strip())

            element = {
                "subject": modul,
                "grade": grade,
                "ects": ects
                       }
            subjects.append(element)

        except Exception as e:
            print(f"fail: {modul}")

    subject_grades_df = pd.DataFrame.from_records(subjects)
    return subject_grades_df


if __name__ == '__main__':
    try:
        login()
        sleep(1.5)
        expand_grade_page()
        #sleep(1)
        subject_grades_df = get_grades_and_ects()

        # remove 5
        grades_neq_5 = subject_grades_df['grade'] != 5
        subject_grades_df = subject_grades_df[grades_neq_5]

        print(subject_grades_df)

        subject_grades_df['sumproduct'] = subject_grades_df['ects'] * subject_grades_df['grade']
        result = subject_grades_df['sumproduct'].sum() / subject_grades_df['ects'].sum()
        print(f"\nGewichtetes Mittel: {result}\n")
        input("Press Enter to exit")


    finally:
        driver.close()
