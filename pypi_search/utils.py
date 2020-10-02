from bs4 import BeautifulSoup
import requests
from requests.exceptions import HTTPError
import json
import html2text


class PyPiPage():
    def __init__(self, package_name: str) -> None:
        self.package_name = package_name.lower().strip()
        self.response = requests.get(
            f'http://pypi.org/project/{self.package_name}'
        )
        try:
            self.response.raise_for_status()
        except HTTPError as err:
            self.response = None

        if not self.response:
            self.soup = None
        else:
            self.soup = BeautifulSoup(self.response.text, 'html.parser')

    def found(self):
        if self.soup:
            return True
        else:
            return False

    def get_version_info(self):
        package_name_header = self.soup.find('h1', class_='package-header__name')
        version_no = package_name_header.text.split()[1]
        package_date_header = self.soup.find(
            'p', class_='package-header__date'
        ).time
        release_date = package_date_header.text.strip()
        return {
            'version_no': version_no,
            'release_date': release_date
        }

    def get_project_links(self):
        # project links are in the second sidebar section
        sidebar_sections = self._get_sidebar_sections()
        links_section = sidebar_sections[1]
        links = links_section.find_all('a')
        links = {
            link.text.strip(): link['href'] for
            link in links
        }
        return links

    def get_github_stats(self):
        # github stats are in the third sidebar section
        sidebar_sections = self._get_sidebar_sections()
        github_stats = sidebar_sections[2].find('div', class_='github-repo-info')
        if not github_stats:
            return None

        github_data_url = github_stats['data-url']
        github_stats_json = json.loads(
            requests.get(github_data_url).text
        )
        github_stats_dict = {
            'stars': github_stats_json['stargazers_count'],
            'forks': github_stats_json['forks_count'],
            'issues': github_stats_json['open_issues_count'],
        }
        return github_stats_dict

    def get_meta_info(self):
        # meta info is the fourth sidebar section
        sidebar_sections = self._get_sidebar_sections()
        meta_stats = sidebar_sections[3]
        meta_stats = meta_stats.find_all('p')
        results_dict = dict()
        for stat in meta_stats:
            key = stat.strong
            if not key:
                continue
            key.extract()
            key = key.text.replace(':', '').lower()
            value = stat.text.strip()
            if key == 'author':
                author_email = stat.a
                if author_email:
                    author_email = author_email.get('href').split(':')[1]
                value = {'name': value, 'email': author_email}

            results_dict[key] = value
        return results_dict


    def get_project_description(self):
        description_div = self.soup.find('div', id='description')
        return html2text.html2text(str(description_div)).strip()


    def _get_sidebar_sections(self):
        sidebar_sections = self.soup.find_all('div', class_='sidebar-section')
        return sidebar_sections
