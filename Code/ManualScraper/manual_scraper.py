#####################################################################
#                                                                   #
#                     Lennard Rose 5122737                          #
#                     Jochen Schmidt 5122xxx                        #
#                     Esther Ademola 5122xxx                        #
#                     Marius Benkert 5122xxx                        #
#       University of Applied Sciences Wuerzburg Schweinfurt        #
#                           SS2022                                  #
#                                                                   #
#####################################################################
from Code.Utils import utils
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests
from bs4 import BeautifulSoup
import re
from Code.Clients import client_factory
import logging
import ssl
import os
from tqdm import tqdm
import time
from Code.config import config


class ManualScraper:

    def __init__(self):
        self.manual_config = None
        ssl._create_default_https_context = ssl._create_unverified_context
        self.driver = None

    def initialize_scraper(self, manual_config):
        self.manual_config = manual_config
        self.driver = self._get_webdriver()

    def reset_scraper(self):
        self.manual_config = None
        self.driver.quit()

    def _get_webdriver(self):
        """
        returns a webdriver for selenium
        expects you to have the file in a directory named after your os (linux / windows / if you use mac, go buy linux)
        https://www.makeuseof.com/how-to-install-selenium-webdriver-on-any-computer-with-python/
        """
        path = None
        try:
            driver_options = Options()
            # driver_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            # trying to block logging from webdriver as it spams the log unnecessarily
            driver_options.headless = True

            if os.name == 'posix':
                path = os.path.join(config.WEBDRIVER_DIR, "linux", config.WEBDRIVER_FILE)
                return webdriver.Chrome(path, options=driver_options, service_log_path='/dev/null')
            else:
                path = os.path.join(config.WEBDRIVER_DIR, "windows", config.WEBDRIVER_FILE)
                return webdriver.Chrome(executable_path=path, options=driver_options, service_log_path='NUL')

        except Exception as e:
            logging.error("failed to initialize webdriver for selenium, /"
                          "make sure you downloaded a driver and wrote the correct path to config, /"
                          "current path: " + path)
            logging.error(e)

    def scrape(self, manual_config):
        """
        makes sure necessary properties are set in the manual_config
        """
        self.initialize_scraper(manual_config)

        if manual_config["base_url"] is None:
            logging.error("Missing url information to scrape from manual_config")

        else:
            logging.info("Start scraping from manuals source URL: %s", manual_config["base_url"])

            links = [manual_config["paths"]]
            requestLinks = []
            if "requests" in manual_config.keys():
                requestLinks = manual_config["requests"]["urls"]

            if manual_config["layers"] and len(manual_config["layers"]) != 0:

                # add a queue for every layer as well as one for the end
                for _ in range(0, len(manual_config["layers"])):
                    links.append([])

                # for each i, try the current layer to get new links, try these again with the current layer,
                # if they stop yielding results put them to the next i do not iterate over the last i
                for i in tqdm(range(0, len(links) - 1), desc="Search products by layers"):
                    while links[i]:
                        old_link = links[i].pop(0)
                        new_links = self._get_layer_links(old_link, manual_config["layers"][i])
                        # if the old link yielded new results append them and remove the old link (popped above)
                        if new_links:
                            links[i].extend(set(new_links))
                        # if the link does not yielded results, try in the next iteration with the next layer
                        else:
                            # to the next layer, ultimatively the last one gets filled only with "product pages" or
                            # the destination link on which the manuals are
                            links[i + 1].append(old_link)

                    # in case of request urls:
                    while requestLinks:
                        old_link = requestLinks.pop(0)
                        new_links = self._get_request_links(old_link, manual_config["requests"]["path"],
                                                            manual_config["requests"]["urlKey"],
                                                            manual_config["layers"][i])
                        if new_links:
                            links[i + 1].extend(set(new_links))

            # final duplicate filtering:
            links[-1] = list(set(links[-1]))
            # TODO links direkt als set machen? spart zusätzliches scrapen
            self._save_manuals(links[-1])

        # clear manual config for next one
        self.reset_scraper()

    def _save_manuals(self, URLs):
        """
        retrieves manuals from the product pages
        parses meta information
        saves all data
        :param URLs: An iterable with all the product pages URLs
        """
        for URL in tqdm(URLs, desc="scraping " + str(len(URLs)) + " products"):
            try:
                # all the different manuals
                manual_links = self._get_layer_links(URL, self.manual_config["pdf"])
                
                for i, manual_link in enumerate(manual_links):

                    most_recent_saved_articles_url = client_factory.get_meta_client().get_latest_entry_URL(
                        self.manual_config["base_url"],
                        self.manual_config["manufacturer_name"])

                    if not self._check_was_already_saved_by_url(most_recent_saved_articles_url, manual_link):

                        meta_data = self._get_meta_data(URL, manual_link, i)
                        if meta_data is None:
                            continue

                        if not self._check_was_already_saved_by_meta(meta_data):
                            fileBytes = self._get_pdf_bytes(manual_link)

                            logging.info("Save content of: " + manual_link)
                            self._save(meta_data, fileBytes)
            except Exception as e:
                logging.error("No metadata found for " + URL)
                logging.error(e)

    def _get_meta_data(self, URL, manual_link, number):
        """ TODO
            initializes meta_parser with necessary information, parses metadata and returns it
            :param URL: the url to get the metadata of
            :param soup: the soup of the url
            :return: the meta_data of the urls article
        """

        # has to be here for the first paths, may come up with a clever solution ... or not
        if self._is_relative_URL(URL):
            source_URL = self.manual_config["base_url"] + URL
        else:
            source_URL = URL

        meta_data = {}
        soup = self._get_soup(source_URL)

        if soup:
            product_name = soup.select(self.manual_config["meta"]["product_name"])
            manual_name = soup.select(self.manual_config["meta"]["manual_name"])

        # if static doesnt work try dynamic
        if product_name == [] or manual_name == []:
            soup = self._get_soup_of_dynamic_page(source_URL)

            if soup:
                product_name = soup.select(self.manual_config["meta"]["product_name"])
                manual_name = soup.select(self.manual_config["meta"]["manual_name"])

        filteredProductIndices = []
        filteredManualIndices = []
        if "filter" in self.manual_config["meta"].keys() and self.manual_config["meta"]["filter"] is not None:
            for idx, manualTag in enumerate(manual_name):
                if not self._is_valid(manualTag.text, self.manual_config["meta"]["filter"]):
                    filteredManualIndices.append(idx)
            for idx, productTag in enumerate(product_name):
                if not self._is_valid(productTag.text, self.manual_config["meta"]["filter"]):
                    filteredProductIndices.append(idx)

        if number not in filteredProductIndices:
            product_name = product_name[number % len(product_name)].text
        else:
            return None

        if number not in filteredManualIndices:
            try:
                manual_name = manual_name[number].text
            except IndexError:
                return None
        else:
            return None

        # If index higher than amount of manuals after filtering this manual got filtered by the manual name ("eu conformity pdf" for example) and thus should be skipped
        # -> index access returns Index error as flag for skipping
        # return None so upper logic knows to continue to next manual link

        if "transform" in self.manual_config["meta"].keys():
            result = re.search(self.manual_config["meta"]["transform"], product_name.lstrip())
            if result is not None:
                product_name = result.group(0)
            result = re.search(self.manual_config["meta"]["transform"], manual_name.lstrip())
            if result is not None:
                manual_name = result.group(0)

        meta_data["manufacturer_name"] = self.manual_config["manufacturer_name"]
        meta_data["product_name"] = utils.slugify(product_name)
        meta_data["manual_name"] = utils.slugify(manual_name)
        meta_data["filepath"] = str(meta_data["manufacturer_name"] + "/" + meta_data["product_name"] + "/")
        # clean url necessary for jura, example: 'https://www.jura.com/-/media/global/pdf/manuals-global/home/ENA/ENA
        # -4/download_manual_ena4.pdf?la=de&hash=7DA7BC6A1C4BD6C6CA040FBF955CA5F2C37FC8CA&em_force=true'
        filetype = utils.clean_url(os.path.splitext(manual_link)[1])
        if filetype == "" or filetype is None:
            filetype = ".pdf"
        if meta_data["product_name"] == meta_data["manual_name"] or meta_data["manual_name"].startswith(
                meta_data["product_name"]):
            meta_data["filename"] = str(meta_data["manual_name"]) + filetype
        else:
            meta_data["filename"] = str(meta_data["product_name"] + "_" + meta_data["manual_name"] + filetype)

        # windows filename (including path) length is restricted
        if len(meta_data["filepath"] + meta_data["filename"]) > 255:
            offset = 255 - len(meta_data["filepath"])
            meta_data["filename"] = meta_data["filename"][:offset-len(filetype)] + filetype

        meta_data["URL"] = manual_link
        meta_data["source_URL"] = source_URL
        meta_data["index_time"] = utils.date_now()

        return meta_data

    def _save(self, manual_meta_data, content):
        """
        saves the source pdf of the given URL
        also saves the meta data of the product
        only saved the content if meta_data was successfully indexed, if content saving raises an exception, deletes created meta_data
        :param manual_meta_data: the meta data to save
        :param content: the pdf to save
        """
        current_id = None
        try:
            current_id = client_factory.get_meta_client().index_manual_metadata(manual_meta_data)
            logging.info("Success -- Saved Metadata")

        except Exception as e:
            logging.error("failed to save Metadata with meta_client")
            logging.error(e)

        if current_id:
            try:
                client_factory.get_file_client().save_as_file(config.MANUALPATH + manual_meta_data["filepath"],
                                                              manual_meta_data["filename"],
                                                              content)
                logging.info("Success -- Saved content")

            except Exception as e:
                logging.error("failed to save Content with file_client")
                logging.error(e)
                client_factory.get_meta_client().delete_manual_metadata(current_id)

    def _get_request_links(self, url, dictPath, urlKey, layer):
        """
        creates a list with the links on the path with respect to the constraints of the given layer
        also completes every relative URL with the base_url if necessary
        checks every link if it matches the given conditions in the filter
        :param path: the path of the source, may be just the URL path or a complete URL
        :return: a list with all valid links on the page
        """

        links = []

        if self._is_relative_URL(url):
            source_URL = self.manual_config["base_url"] + url
        else:
            source_URL = url

        try:
            response = requests.get(source_URL)
            if response.status_code != 200:
                return []

            products = response.json()
            for key in dictPath:
                products = products[key]

            for product in products:
                link = product[urlKey]

                if self._is_valid(link, layer["filter"]):

                    if self._is_relative_URL(link):
                        link = self.manual_config["base_url"] + link[1:]

                    # bugfix for miele as it goes into infinity loop
                    if link != source_URL:
                        links.append(link)

        except Exception as e:
            logging.error("No response received for request: " + source_URL)

        return links

    def _get_layer_links(self, path, layer):
        """
        creates a list with the links on the path with respect to the constraints of the given layer
        also completes every relative URL with the base_url if necessary
        checks every link if it matches the given conditions in the filter
        :param path: the path of the source, may be just the URL path or a complete URL
        :return: a list with all valid links on the page
        """

        links = []

        if self._is_relative_URL(path):
            source_URL = self.manual_config["base_url"] + path
        else:
            source_URL = path

        for link in self._get_link_list(URL=source_URL,
                                        html_tag=layer["html_tag"],
                                        html_class=layer["html_class"],
                                        css_selector=layer["css_selector"]):

            if self._is_valid(link, layer["filter"]):

                if self._is_relative_URL(link):
                    link = self.manual_config["base_url"] + link[1:]

                # bugfix for miele as it goes into infinity loop
                if link != source_URL:
                    links.append(link)

        return links

    def _get_link_list(self, URL, html_tag=None, html_class=None, css_selector=None):
        """
        collects all links from the specified URL that fits the html_tag html_class combination or the css_selector
        If no href is found, the children will be searched for a href
        """

        link_list = []

        for link in self._get_tag_list(URL, html_tag, html_class, css_selector):

            if link.has_attr('href'):
                link_list.append(link['href'])

            else:
                link = self._search_direct_children_for_href(link)

                if link is not None:
                    link_list.append(link)

        return link_list

    def _get_tag_list(self, URL, html_tag=None, html_class=None, css_selector=None):
        """
        collects all tags that match html_tag and html_class or css_selector
        tries to do so by treating the page as static, if fails as dynamic page
        """

        tag_list = []

        # first try static page
        soup = self._get_soup(URL)

        if soup:
            if css_selector:
                tag_list = soup.body.select(css_selector)
            elif html_tag:
                tag_list = soup.body.find_all(html_tag, html_class)

        # if static doesnt work try dynamic
        onlyDynamic = False
        if "onlyDynamic" in self.manual_config.keys():
            onlyDynamic = self.manual_config["onlyDynamic"]
        if not tag_list and not onlyDynamic:
            soup = self._get_soup_of_dynamic_page(URL)
            if soup:
                if css_selector:
                    tag_list = soup.body.select(css_selector)
                elif html_tag:
                    tag_list = soup.body.find_all(html_tag, html_class)

        # if still no result something must be wrong with the html_tag and html_class
        if not tag_list:
            logging.error("No results found for html_class: " + str(html_class)
                          + ", html_tag: " + str(html_tag)
                          + ", css_selector: " + str(css_selector))

        return tag_list

    def _get_pdf_bytes(self, URL):
        return requests.get(URL).content

    def _get_soup(self, URL):
        """
        return soup by trying first to get it as a static page, after failure tries as a dynamic page
        :params URL: the url
        """
        # for example philipps needs to be dynamic soup by default as static only retrieves a few
        onlyDynamic = False
        if "onlyDynamic" in self.manual_config.keys():
            onlyDynamic = self.manual_config["onlyDynamic"]

        soup = None
        if not onlyDynamic:
            soup = self._get_soup_of_static_page(URL)

        if soup is None or onlyDynamic:
            soup = self._get_soup_of_dynamic_page(URL)

            if soup is None:
                logging.error("No soup could be cooked for" + URL + " !")

        return soup

    def _get_soup_of_static_page(self, URL):
        """
        extract content of static loaded page
        does some retries
        :param URL: the url to get the soup (Beatifulsoup) of
        :return: the soup, parsed with 'html5lib' parser
        """
        page = None
        retry_count = 0
        while page is None and retry_count < config.MAX_TRY:
            try:
                retry_count += 1
                page = requests.get(URL, timeout=5)
            except Exception as e:
                logging.warning("request unable to get: %s - retries left: %d", URL,
                                config.MAX_TRY - retry_count)
                logging.warning(e)
        if page:
            return BeautifulSoup(page.content, 'html5lib')
        else:
            return None

    def _get_soup_of_dynamic_page(self, URL):
        """
        extract content of dynamic loaded page
        does some retries
        :param URL: the url to get the soup (Beatifulsoup) of
        :return: the soup, parsed with 'html5lib' parser
        """
        page = None
        retry_count = 0
        while page is None and retry_count < config.MAX_TRY:
            try:
                retry_count += 1
                self.driver.get(URL)
                if "sleepTime" in self.manual_config.keys():
                    time.sleep(self.manual_config["sleepTime"])  # load page
                page = self.driver.page_source

            except Exception as e:
                logging.warning("selenium unable to get: %s - retries left: %d", URL,
                                config.MAX_TRY - retry_count)
                logging.warning(e)

        if page:
            return BeautifulSoup(page, 'html5lib')
        else:
            return None

    def _search_direct_children_for_href(self, tag):
        """
        searches all children of a tag for a href, returns the first
        """
        for child in tag.findAll(recursive=True):
            if child.has_attr('href'):
                return child['href']
        else:
            return None

    def _check_was_already_saved_by_url(self, most_recent_saved_articles_URLs, current_URL):
        """
        the first link in the list returned by the page is not always the most recent
        :param most_recent_saved_articles_url: the URLs of the most recent saved articles (in an earlier call)
        :param URL: the url of the current link
        :return: true if the URL matches one url in the most recent urls
        """
        if most_recent_saved_articles_URLs:
            return current_URL in most_recent_saved_articles_URLs
        else:
            return False

    def _is_relative_URL(self, URL):
        """
        checks if the given URL starts with http, to determine if it is a relative URL
        lots of webpages return only the path url on their own website
        :param URL: the URL to check
        :return: false if URL starts with http, otherwise true
        """
        return not bool(re.search("^http", URL))

    def _is_valid(self, URL, conditions):
        """
        checks if the given URL matches the given conditions, returns wether the url should be included in the list based on the include_condition value
        :param URL: the url to check
        :param conditions: list with the condition_string and include_condition combination to match in the url
        :return: true if url includes condition NXOR include_condition set true, else false 
        """
        valid = True

        if conditions is not None and conditions != []:

            for condition in conditions:

                is_included = bool(
                    re.search(condition["condition_string"], URL))  # if the condition_string is part of the URL

                if condition["include_condition"]:  # if the condition_string should be included in the URL
                    if is_included:
                        valid = valid
                    else:
                        valid = False

                else:  # if the condition_string should not be included in the URL
                    if is_included:
                        valid = False
                    else:
                        valid = valid

        return valid

    def _check_was_already_saved_by_meta(self, meta_data):

        doc_count = client_factory.get_meta_client().count_entries_by_product_and_manual(meta_data["manufacturer_name"],
                                                                                         meta_data["product_name"],
                                                                                         meta_data["manual_name"])
        if doc_count is None:
            return False
        return doc_count > 0
