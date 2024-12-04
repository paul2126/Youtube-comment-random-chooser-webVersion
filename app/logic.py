import os
import re
import json
from datetime import datetime
from bs4 import BeautifulSoup
# import tkinter as tk
# from tkinter import ttk, scrolledtext, messagebox
import random

from flask import current_app
from .exception import SuccessException


class CommentAnalyzer:
    def __init__(self, settings_file="settings.json"):
        if not os.path.exists("settings.json"):
            self._create_settings()
        self._get_settings()

    def _create_settings(self):
        """
        Create settings.json file
        """
        settings = {
            "html_name": "comments.html",
            "email_types": [
                "\uc9c0\uba54\uc77c",
                "\ub124\uc774\ubc84",
                "\ud56b\uba54\uc77c",
                "\uc544\uc6c3\ub8e9",
                "\ud55c\uba54\uc77c",
                "\ub2e4\uc74c",
            ],
            "pick_number": 3,
            "show_process": True,
            "grace_period": 1,
        }
        with open("settings.json", "w", encoding="utf-8") as file:
            json.dump(settings, file, indent=4)

    def _get_settings(self):
        """
        Load settings from settings.json file
        html_name: 댓글들이 달린 HTML 파일 저장 이름
        email_types: 댓글에서 이메일을 추출할 때 분류되는 이메일 종류
        pick_number: 추첨할 댓글의 개수
        show_process: 중간 과정을 출력할지 여부 (콘솔에 출력이라 gui에서는 사용하지 않음)
        grace_period: 종료일자 이후 며칠까지 댓글 가져올지
        """
        try:
            with open("settings.json", "r", encoding="utf-8") as file:
                self.settings = json.load(file)
        except UnicodeDecodeError:
            with open("settings.json", "r", encoding="cp949") as file:
                self.settings = json.load(file)
        self.html_name = self.settings["html_name"]
        self.email_types = self.settings["email_types"]
        self.pick_number = self.settings["pick_number"]
        self.show_process = self.settings["show_process"]
        self.grace_period = self.settings["grace_period"]

    def get_comments(self):
        """
        Get comments from the HTML file
        :return: comments[time, comment, email type]
        """
        try:
            with open(f"./uploads/{self.html_name}", "r", encoding="utf-8") as file:
                html_content = file.read()
        except UnicodeDecodeError:
            with open(f"./uploads/{self.html_name}", "r", encoding="cp949") as file:
                html_content = file.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"{self.html_name}을 찾을 수 없습니다.\n실행파일과 같은 폴더에 저장했는지 확인 부탁드립니다.")

        soup = BeautifulSoup(html_content, "html.parser")
        comment_elements = soup.find_all("yt-attributed-string", id="content-text")
        time_elements = soup.find_all("span", id="published-time-text")

        comments = [
            re.sub(r"\s+", " ", comment.get_text(strip=True))
            for comment in comment_elements
        ]
        times = [time.get_text(strip=True) for time in time_elements]
        emails = []
        for comment in comments:
            found = False
            for email_type in self.email_types:
                if email_type in comment:
                    emails.append(email_type)
                    found = True
                    break
            if not found:
                emails.append("기타")

        result = []
        for i in range(len(comments)):
            result.append([times[i], comments[i], emails[i]])

        return result, len(comments)

    # 웹에서는 사용하지 않음
    # 자바스크립트로 처리
    # def save_data(self, datas, filename):
    #     """
    #     Save data to a text file
    #     :param comments: 데이터 리스트, 파일이름
    #     """
    #     current_date = datetime.now().strftime("%Y-%m-%d")
    #     directory = "data"
    #     os.makedirs(directory, exist_ok=True)
    #     try:
    #         with open(
    #             f"./{directory}/{current_date}_{filename}.txt", "w", encoding="utf-8"
    #         ) as file:
    #             for data in datas:
    #                 file.write(", ".join(data) + "\n")
    #             # raise SuccessException(f"{directory}에 {current_date}_{filename}.txt를 성공적으로 저장했습니다.")
    #             return f"./{directory}/{current_date}_{filename}.txt" # 파일 경로 반환
    #     except SuccessException as e:
    #         raise e
    #     except Exception as e:
    #         raise Exception(f"파일 저장 중 오류가 발생했습니다: {str(e)}")
    def save_data(self, datas, filename):
        """
        Save data to a text file
        :param comments: 데이터 리스트, 파일이름
        """
        current_date = datetime.now().strftime("%Y-%m-%d")
        directory = os.path.join(current_app.static_folder, 'data')
        os.makedirs(directory, exist_ok=True)
        filepath = os.path.join(directory, f"{current_date}_{filename}.txt")
        try:
            with open(filepath, "w", encoding="utf-8") as file:
                for data in datas:
                    file.write(", ".join(data) + "\n")
            return os.path.relpath(filepath, current_app.static_folder)
        except Exception as e:
            raise Exception(f"파일 저장 중 오류가 발생했습니다: {str(e)}")
        
    def overdue_comments(self, comments, end_date):
        """
        Remove comments that are posted after the end date
        :param comments: comments[time, comment, email type], end_date
        :return: comments[time, comment, email type] that are posted before the end date, comments[time, comment, email type] that are posted after the end date, number of overdue comments, number of not overdue comments
        """
        try:
            threshold = self.__time_conversion(end_date)
            cnt_overdue = 0
            cnt_not_overdue = 0
            result = []
            overdue_comments = []
            for comment in comments:
                if (
                    int(re.match(r"\d+", comment[0]).group())
                    >= threshold - self.grace_period
                ):
                    if self.show_process:
                        print(f"종료일자 이전 댓글: {comment[0]}, {comment[1]}")
                    result.append(comment)
                    cnt_not_overdue += 1
                else:
                    print(f"종료일자 이후 댓글: {comment[0]}, {comment[1]}")
                    overdue_comments.append(comment)
                    cnt_overdue += 1
            print(f"종료일자 이후 댓글: {cnt_overdue}개")
            print(f"종료일자 이전 댓글: {cnt_not_overdue}개")
            print()

            return result, overdue_comments, cnt_overdue, cnt_not_overdue
        except ValueError as e:
            raise ValueError(str(e))
        
    def find_email(self, comments):
        """
        Find emails from comments
        :param comments: comments[time, comment, email type]
        :return: emails[time, comment, email type], number of comments that contain email, number of comments that do not contain email
        """
        result = []
        cnt_email = 0
        cnt_not_email = 0
        email_pattern = r"[a-zA-Z0-9_-]+"
        for comment in comments:
            emails = re.findall(email_pattern, comment[1])
            for email in emails:
                if not email.isdigit():
                    cnt_email += 1
                    result.append([email, comment[2]])
                    break
                else:
                    cnt_not_email += 1
        return result, cnt_email

    def find_duplicate_comments(self, emails):
        """
        Find duplicate emails from emails
        :param emails: emails[time, comment, email type]
        :return: emails[time, comment, email type] that do not contain duplicate emails, duplicate emails, number of duplicate emails, number of emails that do not contain duplicate emails
        """
        email_list = [email[0] for email in emails]
        duplicate_emails = set(
            [email for email in email_list if email_list.count(email) > 1]
        )
        filtered_emails = [
            email for email in emails if email[0] not in duplicate_emails
        ]
        if duplicate_emails:
            print(f"중복된 이메일: {duplicate_emails}")
        else:
            print("중복된 이메일이 없습니다.")

        return (
            filtered_emails,
            list(duplicate_emails),
            len(duplicate_emails),
            len(filtered_emails),
        )

    def random_picker(self, emails, pick_number):
        """
        Pick random emails from emails
        :param emails: emails[time, comment, email type], pick_number
        :return: random_emails[picked emails]
        """
        if not emails: # If there is no comment
            raise ValueError("추첨할 이메일이 없습니다")
        random_emails = random.sample(emails, int(pick_number))
        for email in random_emails:
            print(f"{email[0]}@{email[1]}")

        print("마스킹된 이메일 주소:")
        # 마스킹된 이메일 주소 출력
        for email in random_emails:
            print(f"{email[0][:-4]}****@{email[1]}")
        print()

        return random_emails

    def all_in_one(self, end_date):
        """
        Run all the methods in order
        """
        try:
            comments, _ = self.get_comments()
            comments_remove_overdue, _, _, _ = self.overdue_comments(comments, end_date)
            comments_emails, _ = self.find_email(comments_remove_overdue)
            (
                comments_remove_duplicate,
                _,
                _,
                _,
            ) = self.find_duplicate_comments(comments_emails)
            random_emails = self.random_picker(
                comments_remove_duplicate, self.pick_number
            )
        except Exception as e:  # Catch all exceptions
            raise Exception(e)
        return random_emails

    def __time_conversion(self, end_date):
        """
        Convert end date to the number of days from the current date
        :param end_date: end date
        :return: the number of days from the current date
        """
        try:
            current_year = datetime.now().year
            end_date_with_year = f"{current_year}/{end_date}"
            date_diff = datetime.now() - datetime.strptime(end_date_with_year, "%Y/%m/%d")
            print(f"종료일({end_date})으로부터 {date_diff.days}일 지났습니다.")
            print()
            return date_diff.days
        except ValueError:
            raise ValueError("날짜 형식이 잘못되었습니다. 날짜를 다시 입력해주세요.")
    def save_settings(self, html_name, email_types, pick_number, grace_period):
        """
        Save settings to settings.json file
        :param html_name: HTML file name, email_types: email types, pick_number: number of picked emails, grace_period: grace period
        """
        self.settings["html_name"] = html_name
        self.settings["email_types"] = [
            email_type.strip() for email_type in email_types.split(",")
        ]
        try:
            self.settings["pick_number"] = int(pick_number)
            self.settings["grace_period"] = int(grace_period)
            if self.settings["pick_number"] <= 0 or self.settings["grace_period"] <= 0:
                raise ValueError
        except ValueError:
            raise ValueError("뽑기 수와 grace period는 양수로 입력해주세요.")
        with open("settings.json", "w", encoding="utf-8") as file:
            json.dump(self.settings, file, indent=4)
        self._get_settings()  # Update settings
        raise SuccessException("정상적으로 저장되었습니다.")


