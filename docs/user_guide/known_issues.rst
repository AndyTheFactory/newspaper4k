Known issues with newssites and parsing
==========================================
.. toctree::
   :maxdepth: 2

Type of sites that will probably never work
--------------------------------------------

* Sites that use a  javascript to generate the page. There is no planned browser integration at the moment.
* Sites that are behind a paywall. For paying customers, this case might work with the caveats mentioned below for the "sites that need you to login" case.
* Publishing dates written as div contents without any special class or markup
* Sites protected b Cloudflair or similar services. This will probably not work without a browser integration (Selenium or similar).
* Sites with scanned newsarticles. At the moment, there is no OCR integration planned.
* Sites that have their own "reader" and look like a pfd or ebook.


Sites that need you to login
----------------------------

These won't work out of the box. You might attempt to make the scraping work by providing the cookies set by the login process.
This means that you have to login in a browser and then copy the cookies from the browser to the script.

Hopefully I will manage to write a small tutorial on how to do this as soon as possible.


fox13now.com
-------------

Some articles, such as `this one <https://www.fox13now.com/2013/12/30/new-year-new-laws-obamacare-pot-guns-and-drones>`_
do not have the correct authors in the meta tags.
The one mentioned has "CNN Wire" as author, but the article is written by "Leigh Ann Caldwell". It seams that
articles that are taken over from external sites have the site as author.
This is not a problem with the script, but with the site itself. This can be overridden by creating
a custom parsing function for this site. You have to parse the article.html and get the author from there.

finance.yahoo.com
-----------------

This site has a "read more" button.


Sites that we know don't work
-----------------------------

.. csv-table:: Known websites that don't work
   :file: known_sites_not_working.csv
   :widths: 30, 60, 10
   :header-rows: 1
