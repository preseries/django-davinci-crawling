.. _davinci_proxy_mesh:

.. highlight:: rst

.. role:: python(code)
    :language: python

.. role:: latex(code)
    :language: latex

ProxyMesh
=========

This guide will help you on how to use ProxyMesh to hide our ips when
crawling websites.

1.Authentication
----------------

ProxyMesh supports essentialy two major types of authentication that we
will cover below:

1.1 IP Authentication
~~~~~~~~~~~~~~~~~~~~~

With this technique we can whitelist some IPs to have access, on this
mode we don\`t need any authentication format. To learn more about it:
https://docs.proxymesh.com/article/10-proxy-authentication

1.2 User-Password authentication
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We also can use ProxyMesh using our user and password, the recommended
way is to use the Base64 encoded user:password, but for https requests
we will need another technique.

**1.2.1 Base64**

To use Base64 you just need to encode ``username:password`` using Base64 and
send it on a header just like this:

::

    Proxy-Authorization: Basic aWFucmlja2V5saZhcmlhYmxlZGF0YTEwMSE=

**1.2.2 Plain user:password**

When we need to make an HTTPS request we can\`t send the authentication
information through the header, we will need to use either IP Authentication
or Plain user password.

This is very simple, just add your ``user:password`` before the host of
the proxy and usu a ``@`` to separate them.

Example:

::

    http://user:password@HOST:PORT
    http://user:password@http://fr.proxymesh.com:31280

2. Using ProxyMesh
------------------

2.1 Simple request
~~~~~~~~~~~~~~~~~~

To make a simple web request we can use the ``requests`` python module,
on this example we will mount the proxies host/port and then request to
a api that simple return the ip that connected to the service.

.. code:: python

    import requests
    import random

    # the list of the proxies that will be used
    PROXY_CHOICES = ['us-wa.proxymesh.com:31280', 'fr.proxymesh.com:31280']
    # the header containing the authnetication to the service.
    HEADERS = {
        "Proxy-Authorization": "Basic aWFucmlja2V5OlZhcmlhYmxlZGF0YTEwMSE="
    }

    def check_ip():
        # choose betweehn the proxies available
        proxy = random.choice(PROXY_CHOICES)
        # mount the list of proxies, on the https we can`t use Base64 authentication, so that's why we need
        # a different authentication technique.
        proxies = {'http': 'http://%s' % proxy, 'https': 'http://user:password%s' % proxy}
        response = requests.get('http://api.myip.com', proxies=proxies, headers=HEADERS)

        return response.text

    for x in range(5):
        print("Called %d times" % x)
        print("Result: %s" % check_ip())

The response of the script should be something like this:

::

    Called 0 times
    Result: {"ip":"2001:19f0:8001:12b0:5400:2ff:fe61:82b0","country":"United States","cc":"US"}
    Called 1 times
    Result: {"ip":"2001:19f0:8001:12b0:5400:2ff:fe61:82b0","country":"United States","cc":"US"}
    Called 2 times
    Result: {"ip":"2001:19f0:6801:cf7:5400:2ff:fe61:7986","country":"United States","cc":"US"}
    Called 3 times
    Result: {"ip":"2001:19f0:6801:e35:5400:2ff:fe61:7b89","country":"United States","cc":"US"}
    Called 4 times
    Result: {"ip":"2001:19f0:8001:af2:5400:2ff:fe61:599b","country":"United States","cc":"US"}

You can run this script many times to check that the ip is changing
everytime.

2.2 Selenium WebDriver
~~~~~~~~~~~~~~~~~~~~~~

To use ProxyMesh with Selenium WebDriver you need to an argument to
chromium options called ``proxy-server`` specifying a single proxy.

We can use the random to select a new ProxyMesh everytime to raise the
ramge of available ips.

Below you can find an example of using ProxyMesh to request the
``https://www.whatismyip.com/my-ip-information/`` website, everytime we
hit this page the IP will change, indicating that the Proxy is working
properly.

.. code:: python

    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from bs4 import BeautifulSoup
    import time

    PROXY = "us-wa.proxymesh.com:31280"

    def call_selenium():
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-features=NetworkService")
        chrome_options.add_argument('--proxy-server=%s' % PROXY)
        chrome_options.binary_location = "/Applications/Chromium.app/Contents/MacOS/Chromium"

        driver = webdriver.Chrome(
            chrome_options=chrome_options)

        driver.get("https://www.whatismyip.com/my-ip-information/")
        time.sleep(10)
        bs = BeautifulSoup(driver.page_source, "html.parser")
        my_ip = bs.find("p", attrs={"class": "h3"})
        return my_ip

    for x in range(5):
        print("Called %d times" % x)
        print("Result: %s" % call_selenium())

This is an example of output:

::

    Result: <p class="h3">Your IPv6 Address Is: 2001:19f0:8001:1451:5400:2ff:fe61:82f1 <br/>
    </p>
    Called 1 times
    Result: <p class="h3">Your IPv6 Address Is: 2001:19f0:8001:af2:5400:2ff:fe61:599b <br/>
    </p>
    Called 2 times
    Result: <p class="h3">Your IPv6 Address Is: 2001:19f0:8001:c19:5400:2ff:fe61:82cd  <br/>
    </p>
    Called 3 times
    Result: <p class="h3">Your IPv6 Address Is: 2001:19f0:8001:1e67:5400:2ff:fe61:8252 <br/>
    </p>
    Called 4 times
    Result: <p class="h3">Your IPv6 Address Is: 2001:19f0:8001:159e:5400:2ff:fe61:8294 <br/>
    </p>

