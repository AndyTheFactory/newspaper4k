# Change Log

## 0.9.2 (2024-01-14)
Some major changes in document parsing. In previous versions the chance that parts of the article body were missing was high. In addition, in some cases the order of the paragraphs was not correct. This release should fix these issues.

Highlichted features:
- You can now us the module as a command line interface (CLI). Usage: `python -m newspaper --url https://www.test.com`. More information in the [documentation](https://newspaper4k.readthedocs.io/).
- I have added an evaluation script against a dataset from [scrapinghub](https://github.com/scrapinghub/article-extraction-benchmark/). This will help keeping track of future improvements.
- Better handling of multithreaded requests. The previous version had a bug that could lead to a deadlock. I implemented ThreadPoolExecutor from the concurrent.futures module, which is more stable. The previously `news_pool` was replaced with a `fetch_news()` function.
- Caching is now much more flexible. You can disable it completely or for one request.
- You can now use `newspaper.article()` function for convenience. It will create, download and parse an article in one step. It takes all the parameters of the `Article` class.
- protected sites by cloudflare are better detected and raise an exception. The reason will be in the exception message.

### New feature:

- **category**: :sparkles: improved category link parsing / category link detection([`41677b0`](https://github.com/AndyTheFactory/newspaper4k/commit/41677b08e18459edb42114df3f8fa589fe5edba8)) (by Andrei)
- **category**: :zap: Added option to disable the category_url cache for Source objects. Refactored the cache_disk decorator([`670aad9`](https://github.com/AndyTheFactory/newspaper4k/commit/670aad9120eb2745f0b3ac4fed17487d4f6d43bf)) (by Andrei)
- **cli**: :sparkles: added command line interface (CLI) for the module. Usage: `python -m newspaper --url https://www.test.com`([`f46b443`](https://github.com/AndyTheFactory/newspaper4k/commit/f46b4430344e08136d54d29643f58f5168817a33)) (by Andrei)
- **cli**: added output format "text"([`31b9079`](https://github.com/AndyTheFactory/newspaper4k/commit/31b907900cf5d984c3c15d708e55d33c9c124ce2)) (by Andrei)
- **core** Article.download() and Article.parse() now returns self. Calls can be chained([`3be1e47`](https://github.com/AndyTheFactory/newspaper4k/commit/3be1e47ebd0a6b1ebcb52bb378dd672ab4ec5b56)) (by Andrei)
- **lang**: :art: automatically load nltk punkt if not present ([`d0fcdd8`](https://github.com/AndyTheFactory/newspaper4k/commit/d0fcdd8eac0af9f4f3669e414a82261e1a2910d4)) (by Andrei)
- **nlp** added the keyword scores as a dictionary attribute in Articles. Additionally, config.MAX_KEYWORDS is really taken into consideration when computing article keywords([`f51a04f`](https://github.com/AndyTheFactory/newspaper4k/commit/f51a04f9e58710f9f016cbb4ecb8bf4cf7d89da8)) (by Andrei)
- **parse**: :rocket: improvements in the article body extraction. some sections that were ignored are now added to the extracted text.([`1af12d2`](https://github.com/AndyTheFactory/newspaper4k/commit/1af12d24c054b1fffafb3c91dfd4a900666a0325)) (by Andrei)
- **parse**: :sparkles: better parametrization of top_node detection. magic constants moved out of the score computation([`6485c40`](https://github.com/AndyTheFactory/newspaper4k/commit/6485c40192c7a479ba0445b5622878f14c50aef1)) (by Andrei)
- **parse**: :triangular_flag_on_post: added some Author detection tags (Issue #347)([`4aebf29`](https://github.com/AndyTheFactory/newspaper4k/commit/4aebf293055e61cb18defa9c44c11c045fd75bd8)) (by Andrei)
- **parse**: added fine-grained score for top node article attribute booster([`0d41fc7`](https://github.com/AndyTheFactory/newspaper4k/commit/0d41fc713621f10d8224ff4fbe65af9aa35af829)) (by Andrei)
- **parse**: Added twitch as a video provider (Issue #349, #348)([`f4d8f0f`](https://github.com/AndyTheFactory/newspaper4k/commit/f4d8f0f4c568668774f72dffae81aed1cbe13b42)) (by Andrei)
- **parse**: minor improvement on top node detection([`95d5cfa`](https://github.com/AndyTheFactory/newspaper4k/commit/95d5cfae7f594585225ca9e411f49a93254dbaf7)) (by Andrei)
- **parse**: parsing rules improvements suggested by @aleksandar-devedzic in issue #577([`8677dbe`](https://github.com/AndyTheFactory/newspaper4k/commit/8677dbe60e482248ee56adbcfee90723e0f28d1e)) (by Andrei)
- **requests**: :bookmark: Added redirection history from the request calls in Article.download([`8ca3d40`](https://github.com/AndyTheFactory/newspaper4k/commit/8ca3d4013b8b298984f8f479b775ef23277dac36)) (by Andrei)
- **requests**: :chart_with_upwards_trend: added a binary file detection. Files that are known binary content-types or have in the first 1000 bytes more than 40% non-ascii characters will raise an exception in article.download.([`e7a60dd`](https://github.com/AndyTheFactory/newspaper4k/commit/e7a60ddb56e9a004befc019bc8febabd5216d174)) (by Andrei)
- **tests**: :sparkles: added evaluation script to test against the dataset from [https://github.com/scrapinghub/article-extraction-benchmark/](https://github.com/scrapinghub/article-extraction-benchmark/)([`737c226`](https://github.com/AndyTheFactory/newspaper4k/commit/737c2269878af67c3e1435d9b858821b95cd1037)) (by Andrei)


### Bugs fixed:


- **bug**: :lipstick: instead of memorize_articles the option / function / parameter was memoize_articles([`aaef712`](https://github.com/AndyTheFactory/newspaper4k/commit/aaef7120a205adb4c1117a52c302672dd919d0d2)) (by Andrei)
- **bug**: MEMO_DIR is now Path object. addition with str forgotten from refactoring([`0b98e71`](https://github.com/AndyTheFactory/newspaper4k/commit/0b98e71abf7a1f484f03c9c61fe4dc644a14ada9)) (by Andrei)
- **depend**: removed feedfinder2 as dependency. was not used([`c230aca`](https://github.com/AndyTheFactory/newspaper4k/commit/c230aca119d1cef2c462ca757002922a506c08cd)) (by Andrei)
- **doc**: some minor documentation changes([`764742a`](https://github.com/AndyTheFactory/newspaper4k/commit/764742ab14f04835d894f69530ac48cb8327feb3)) (by Andrei)
- **lang** added additional stopwords for "fa".  Issue #398([`3453538`](https://github.com/AndyTheFactory/newspaper4k/commit/3453538750f3f9d08fef7ea3ac7be5e1a39a83cc)) (by Andrei)

- **lang**: :speech_balloon: fixed serbian stopwords. added chirilic version (Issue #389)([`dfcb760`](https://github.com/AndyTheFactory/newspaper4k/commit/dfcb760ccd390e52ce65213df076bb40e7a1e66d)) (by Andrei)
- **parse** itemprop containing but not equal to articleBody([`510be0e`](https://github.com/AndyTheFactory/newspaper4k/commit/510be0e1238afc7c7179eb4f5c7f3f00418943e8)) (by Andrei)
- **parse**: :art: removed some additional advertising snippets([`bd30d48`](https://github.com/AndyTheFactory/newspaper4k/commit/bd30d486bb71def47c306604cf8b1c162c009a91)) (by Andrei Paraschiv)
- **parse**: :chart_with_upwards_trend: removed possible image caption remains from cleaned article text (Issue #44)([`7298140`](https://github.com/AndyTheFactory/newspaper4k/commit/7298140db081b336869813e5336afb5b1b7a504d)) (by Andrei)
- **parse**: :globe_with_meridians: image parsing and movie parsing improvements. get links from additional attributes such as "data-src".([`c02bb23`](https://github.com/AndyTheFactory/newspaper4k/commit/c02bb23dbd5088bfb108862b82ba2958fe0ee2ca)) (by Andrei)
- **parse**: :memo: exclude some tags from get_text. Tags such as script, option can add garbage to the text output([`f0e1965`](https://github.com/AndyTheFactory/newspaper4k/commit/f0e196597ec5785259689e3ebef14c5391696012)) (by Andrei Paraschiv)
- **parse**: :memo: Improved newline geeneration based on block level tags. <br>'s are better taken into account.([`22327d8`](https://github.com/AndyTheFactory/newspaper4k/commit/22327d8d874c077f9706f3fef64e961a47b6de9a)) (by Andrei)
- **parse**: added youtu.be to video sources([`bf516a1`](https://github.com/AndyTheFactory/newspaper4k/commit/bf516a190578bd880578f0fb04f85990155a4816)) (by Andrei)
- **parse**: additional fixes for caption([`3e7fdcc`](https://github.com/AndyTheFactory/newspaper4k/commit/3e7fdcc08084b3137bf5cdc65978e60b1003cf53)) (by Andrei)
- **refactor**: deprecated non pythonic configuration attributes (all caps vs lower caps). for the moment both approaches work([`691e12f`](https://github.com/AndyTheFactory/newspaper4k/commit/691e12f7c240f436872485deceb8a7fea50deecd)) (by Andrei)
- **sec**: bump nltk and requests min version([`553ef27`](https://github.com/AndyTheFactory/newspaper4k/commit/553ef27ddbc552a43fb173d25f56462f960c3a03)) (by Andrei)
- **sources**: :bug: fixed a problem with some type of articlelinks.([`9a5c0e2`](https://github.com/AndyTheFactory/newspaper4k/commit/9a5c0e2206e59b9aa72d1d00d8214dcc240acb94)) (by Andrei)

## 0.9.1 (2023-11-08)

### New feature:

- version bump([`f7107be`](https://github.com/AndyTheFactory/newspaper4k/commit/f7107beac9aa40d4cd7f95c8b1bec7ddb6a8ace6)) (by Andrei)
- **tests**: Add test case for([`592f6f6`](https://github.com/AndyTheFactory/newspaper4k/commit/592f6f63439727e8461184cfa80826a5ca848878)) (by Andrei)
- **parse**: added possibility to follow "read more" links in articles([`0720de1`](https://github.com/AndyTheFactory/newspaper4k/commit/0720de13888c54cb1001fa2d50d110a1a71178c2)) (by Andrei)
- **core**: Allow to pass any requests parameter to the Article constructor. You can now pass verify=False in order to ignore certificate errors (issue #462)([`5ff5d27`](https://github.com/AndyTheFactory/newspaper4k/commit/5ff5d27fa49b5c600b5fc938f7dbe9cfc94f4259)) (by Andrei)
- **lang** Macedonian file raises an error([`cadea6a`](https://github.com/AndyTheFactory/newspaper4k/commit/cadea6a97fb9e8933837c9b2c931a0b73993060e)) (by Murat Çorlu)
- **parse**: extended data parsing of json-ld metadata (issue #518)([`fc413af`](https://github.com/AndyTheFactory/newspaper4k/commit/fc413af8b42ebc8df8cfbf15221611ac8b3f1e7d)) (by Andrei)
- **tests**: added script to create test cases([`9df8c16`](https://github.com/AndyTheFactory/newspaper4k/commit/9df8c16cbe941bb4de705f87a14b3cff61c0f333)) (by Andrei)
- **parse**: added tag for date detection issue #835([`41152eb`](https://github.com/AndyTheFactory/newspaper4k/commit/41152eb74bb26e0f70bcd14e33eb535693ecae78)) (by Andrei)
- **parse**: added og:regDate to known date tags([`dc35e29`](https://github.com/AndyTheFactory/newspaper4k/commit/dc35e29472d3a7da993040b9b312a21c8a6963db)) (by Andrei)
- **tests**: convert unittest to pytest([`45c4e8d`](https://github.com/AndyTheFactory/newspaper4k/commit/45c4e8d3e0792c91a08101cb22c0dbf23823923d)) (by Andrei)
- **doc** add autodoc for readthedocs ([`22e9dca`](https://github.com/AndyTheFactory/newspaper4k/commit/22e9dcabac0f64af5722892eb9e785876c180141)) (by Andrei)
- **doc**: Added docstring to Article, Source and Configuration.([`8e54946`](https://github.com/AndyTheFactory/newspaper4k/commit/8e54946470b8c1ed6abc46f00f698b86d17abe3d)) (by Andrei)
- **doc**: some clarifications in the documentation([`e8126d5`](https://github.com/AndyTheFactory/newspaper4k/commit/e8126d55411e9fd5affdb14988b3f498e8d881a5)) (by Andrei)
- **doc**: some template changes([`0261054`](https://github.com/AndyTheFactory/newspaper4k/commit/0261054e74aae5b737477673529dd50188d29cc8), [`bfbac2c`](https://github.com/AndyTheFactory/newspaper4k/commit/bfbac2cf0be286563affcb394cd0c8f7f4f1fe83)) (by Andrei)

### Bugs fixed:

- **corec**: typing annotation for set python 3.8([`895343f`](https://github.com/AndyTheFactory/newspaper4k/commit/895343f46f759e0c48c3a22cd7e746aa2506e24e)) (by Andrei)
- **parse**: improve meta tag content for articles and pubdate([`37bb0b7`](https://github.com/AndyTheFactory/newspaper4k/commit/37bb0b7cfe90587105b74d852e2a410bc407d33a)) (by Andrei)
- **parse**: :memo: improved author detection. improved video links detection([`23c547f`](https://github.com/AndyTheFactory/newspaper4k/commit/23c547ff5f234993ceb6ba4784ff7b0f15f1e8ed)) (by Andrei)
- **parse**: ensured that clean_doc/doc to clean_top_node are on the same DOM.  And doc/top_node on the same DOM.([`6874d05`](https://github.com/AndyTheFactory/newspaper4k/commit/6874d052b3b87c8f1859d5ccb62a285ef8dd9317)) (by Andrei)
- **core**: small changes, replace os.path with pathlib([`5598d95`](https://github.com/AndyTheFactory/newspaper4k/commit/5598d95d46365158bfde7482f06fc584f5f87888)) (by Andrei)
- **parse**: use one file of stopwords for english, the one in the standard folder #503([`6bdf813`](https://github.com/AndyTheFactory/newspaper4k/commit/6bdf8133eae99e9a66c8269d17cb713995d45620)) (by Andrei)
- **parse**: better author parsing based on  issue #493([`f93a9c2`](https://github.com/AndyTheFactory/newspaper4k/commit/f93a9c2b0abc5fceff9586b7a8d3695aa98a3373)) (by Andrei)
- **parse**: make the url date parsing stricter. Issue #514([`0cc1e83`](https://github.com/AndyTheFactory/newspaper4k/commit/0cc1e833de5ef8799e60a2003bdb8428e447cc4d)) (by Andrei)
- **parse**: replace \n with space in  sentence split (Issue #506)([`3ccb87c`](https://github.com/AndyTheFactory/newspaper4k/commit/3ccb87c97fd8cf5134ce7ce7b2494f72c6a746eb)) (by Andrei)
- **parsing**: catch url errors resulting resulting from parsed image links([`9140a04`](https://github.com/AndyTheFactory/newspaper4k/commit/9140a04f03bd383efbcc2285dfa9b0904c424386)) (by Andrei)
- **repo**: correct python versions in pipeline([`7e671df`](https://github.com/AndyTheFactory/newspaper4k/commit/7e671dfeba35fdf6f3b234913d8068664d061d47)) (by Andrei)
- **repo**: gitignore update([`8855f00`](https://github.com/AndyTheFactory/newspaper4k/commit/8855f00ccc50adadfa9951797c4b527511ab1f8b)) (by Andrei)

## [0.9.0] (2023-10-29)
First release after the fork. This release is based on the 0.1.7 release of the original newspaper3k project. I jumped versions such that it is clear that this is a fork and not the original project.

### New feature:

- **tests**: starting moving tests to pytest([`f294a01`](https://github.com/AndyTheFactory/newspaper4k/commit/f294a012684134e859224ea85d7d3688bd7a7e01)) (by Andrei)
- **parser**: add yoast schema parse for date extraction([`39a5cff`](https://github.com/AndyTheFactory/newspaper4k/commit/39a5cff3b995a71ed14d8a9c0940c72bc5fb14d3)) (by Andrei)

### Bugs fixed:

- **docs**: update README.md([`d5f9209`](https://github.com/AndyTheFactory/newspaper4k/commit/d5f92092ad83525b06059c65b5d9409b1ac66651)) (by Andrei)
- **parse**: feed_url parsing, issue #915([`ec2d474`](https://github.com/AndyTheFactory/newspaper4k/commit/ec2d47498028490b6faeb17168491400e576f6df)) (by Andrei)
- **parse**: better content detection. added `<article>` and `<div>` tag as candidate for content parent_node([`447a429`](https://github.com/AndyTheFactory/newspaper4k/commit/447a429978e9757a880aacf8f69389dbfbc2b4f4)) (by Andrei)
- **core**: close pickle files - PR #938([`d7608da`](https://github.com/AndyTheFactory/newspaper4k/commit/d7608da3d1b05ca0609dd60968ca82b11bc0ba49)) (by Andrei)
- **parse**: improved publication date extraction([`4d137eb`](https://github.com/AndyTheFactory/newspaper4k/commit/4d137eb0b6d5b3df971a01f4aa8c1961af9da118)) (by Andrei)
- **core**: some linter errors, whitespaces and spelling([`79553f6`](https://github.com/AndyTheFactory/newspaper4k/commit/79553f6302cea1a6e36103fb4dc1c675ca704cd3)) (by Andrei)

################################### These are the original newspaper3k release notes ###################################
########################################################################################################################
## [0.1.7](https://github.com/codelucas/newspaper/tree/0.1.7) (2016-01-30)
[Full Changelog](https://github.com/codelucas/newspaper/compare/0.1.6...0.1.7)

**Closed issues:**

- ImportError: cannot import name 'Image' [\#183](https://github.com/codelucas/newspaper/issues/183)
- Won't let me import [\#182](https://github.com/codelucas/newspaper/issues/182)
- Install on Mac - El Capitan Failed - "Operation not permitted"  [\#181](https://github.com/codelucas/newspaper/issues/181)
- Downgrades to old versions of required packages upon installation [\#174](https://github.com/codelucas/newspaper/issues/174)
- Handling 404, 500, and other non-200 http response codes to prevent scraping error pages [\#142](https://github.com/codelucas/newspaper/issues/142)
- Library downgrading in installation [\#138](https://github.com/codelucas/newspaper/issues/138)

**Merged pull requests:**

- Don't scrape error pages [\#190](https://github.com/codelucas/newspaper/pull/190) ([yprez](https://github.com/yprez))
- Added Hebrew stop words for language support [\#188](https://github.com/codelucas/newspaper/pull/188) ([alon7](https://github.com/alon7))
- Fix installation and build [\#187](https://github.com/codelucas/newspaper/pull/187) ([yprez](https://github.com/yprez))
- Fix installation docs [\#184](https://github.com/codelucas/newspaper/pull/184) ([yprez](https://github.com/yprez))
- Travis CI integration [\#180](https://github.com/codelucas/newspaper/pull/180) ([yprez](https://github.com/yprez))
- requirements.txt - Use minimal instead of exact versions [\#179](https://github.com/codelucas/newspaper/pull/179) ([yprez](https://github.com/yprez))
- Handle lxml raising ValueError on node.itertext\(\) - Python 3 [\#178](https://github.com/codelucas/newspaper/pull/178) ([yprez](https://github.com/yprez))
- Handle lxml raising ValueError on node.itertext\(\) [\#144](https://github.com/codelucas/newspaper/pull/144) ([yprez](https://github.com/yprez))
- Parse byline fix [\#132](https://github.com/codelucas/newspaper/pull/132) ([davecrumbacher](https://github.com/davecrumbacher))

## [0.1.6](https://github.com/codelucas/newspaper/tree/0.1.6) (2016-01-10)
[Full Changelog](https://github.com/codelucas/newspaper/compare/0.1.5...0.1.6)

**Closed issues:**

- Critical leak in newspaper.mthreading.Worker [\#177](https://github.com/codelucas/newspaper/issues/177)
- HTMLParseError [\#165](https://github.com/codelucas/newspaper/issues/165)
- Take local paths to .html files [\#153](https://github.com/codelucas/newspaper/issues/153)
- Wall Street Journal Full Text is not Correctly Scraped [\#150](https://github.com/codelucas/newspaper/issues/150)
- Article HTML Returning Null [\#131](https://github.com/codelucas/newspaper/issues/131)
- No articles [\#130](https://github.com/codelucas/newspaper/issues/130)
- Loading Pages that use heavy javascript [\#127](https://github.com/codelucas/newspaper/issues/127)
- Login handling for premium websites [\#126](https://github.com/codelucas/newspaper/issues/126)
- Installation of nltk is failing [\#121](https://github.com/codelucas/newspaper/issues/121)

**Merged pull requests:**

- Support urls with dots [\#176](https://github.com/codelucas/newspaper/pull/176) ([alexanderlukanin13](https://github.com/alexanderlukanin13))
- upgrade beautifulsoup4 to 4.4.1 for python 3.5 [\#171](https://github.com/codelucas/newspaper/pull/171) ([AlJohri](https://github.com/AlJohri))
- Updated requests version [\#170](https://github.com/codelucas/newspaper/pull/170) ([adrienthiery](https://github.com/adrienthiery))
- Turkish Language added [\#169](https://github.com/codelucas/newspaper/pull/169) ([muratcorlu](https://github.com/muratcorlu))
- Add macedonian stopwords [\#166](https://github.com/codelucas/newspaper/pull/166) ([dimitrovskif](https://github.com/dimitrovskif))
- Issue\#95 added graceful string concatenation [\#157](https://github.com/codelucas/newspaper/pull/157) ([surajssd](https://github.com/surajssd))
- fix for "jpeg error with PIL, Can't convert 'NoneType' object to str implicitly" [\#154](https://github.com/codelucas/newspaper/pull/154) ([hnykda](https://github.com/hnykda))
- bugfix in article.py, is\_valid\_body [\#149](https://github.com/codelucas/newspaper/pull/149) ([ms8r](https://github.com/ms8r))
- Fixed typo [\#139](https://github.com/codelucas/newspaper/pull/139) ([Eleonore9](https://github.com/Eleonore9))
- Correct link for the Python 3 branch [\#136](https://github.com/codelucas/newspaper/pull/136) ([jtpio](https://github.com/jtpio))
- Add python3-pip install step for Ubuntu [\#135](https://github.com/codelucas/newspaper/pull/135) ([irnc](https://github.com/irnc))

## [0.1.5](https://github.com/codelucas/newspaper/tree/0.1.5) (2015-03-04)
[Full Changelog](https://github.com/codelucas/newspaper/compare/0.1.4...0.1.5)

**Closed issues:**

- is there any kind of documentation on centos 7? [\#114](https://github.com/codelucas/newspaper/issues/114)
- Add extraction publishing date from article. [\#3](https://github.com/codelucas/newspaper/issues/3)

**Merged pull requests:**

- bumping nltk to 2.0.5 - see \#824 in nltk [\#125](https://github.com/codelucas/newspaper/pull/125) ([hexelon](https://github.com/hexelon))

## [0.1.4](https://github.com/codelucas/newspaper/tree/0.1.4) (2015-02-04)
[Full Changelog](https://github.com/codelucas/newspaper/compare/0.1.3...0.1.4)

**Closed issues:**

- Getting rate limiting issue? [\#116](https://github.com/codelucas/newspaper/issues/116)
- newspaper.build\( \) error [\#111](https://github.com/codelucas/newspaper/issues/111)
- Allow lists in Parser.clean\_article\_html\(\) [\#108](https://github.com/codelucas/newspaper/issues/108)

**Merged pull requests:**

- Fix incorrect log call while generating articles [\#115](https://github.com/codelucas/newspaper/pull/115) ([curita](https://github.com/curita))
- Allow lists in clean\_article\_html\(\) - fixes \#108 [\#112](https://github.com/codelucas/newspaper/pull/112) ([ecesena](https://github.com/ecesena))
- Fixed nodeToString\(\) to return valid HTML [\#110](https://github.com/codelucas/newspaper/pull/110) ([ecesena](https://github.com/ecesena))
- Fixed empty return in top\_meta\_image [\#109](https://github.com/codelucas/newspaper/pull/109) ([ecesena](https://github.com/ecesena))

## [0.1.3](https://github.com/codelucas/newspaper/tree/0.1.3) (2015-01-15)
[Full Changelog](https://github.com/codelucas/newspaper/compare/0.1.2...0.1.3)

**Implemented enhancements:**

- Fulltext extraction improvement \#1 [\#105](https://github.com/codelucas/newspaper/issues/105)

**Closed issues:**

- Tags h1 in article\_html - indented behavior? [\#107](https://github.com/codelucas/newspaper/issues/107)

**Merged pull requests:**

- Fulltext extraction improvement \#1 [\#106](https://github.com/codelucas/newspaper/pull/106) ([codelucas](https://github.com/codelucas))

## [0.1.2](https://github.com/codelucas/newspaper/tree/0.1.2) (2015-01-01)
[Full Changelog](https://github.com/codelucas/newspaper/compare/0.1.1...0.1.2)

**Closed issues:**

- Metatags on Vice.com [\#103](https://github.com/codelucas/newspaper/issues/103)
- Can't extract images from german newspapers [\#96](https://github.com/codelucas/newspaper/issues/96)
- article\_html misses many of the images [\#89](https://github.com/codelucas/newspaper/issues/89)

**Merged pull requests:**

- Integrate UnicodeDammit, deprecate parser\_class, deprecate encodeValue, refactor, scaffolding for more unit tests [\#104](https://github.com/codelucas/newspaper/pull/104) ([codelucas](https://github.com/codelucas))

## [0.1.1](https://github.com/codelucas/newspaper/tree/0.1.1) (2014-12-27)
[Full Changelog](https://github.com/codelucas/newspaper/compare/0.1.0...0.1.1)

**Closed issues:**

- UnicodeDecodeError: 'utf8' codec can't decode byte 0xcc [\#99](https://github.com/codelucas/newspaper/issues/99)
- TypeError: Can't convert 'bytes' object to str implicitly [\#98](https://github.com/codelucas/newspaper/issues/98)
- \[Parse lxml ERR\] Unicode strings with encoding declaration are not supported. Please use bytes input or XML fragments without declaration. [\#78](https://github.com/codelucas/newspaper/issues/78)
- UnicodeDecodeError: 'ascii' codec can't decode byte 0xe2 in position 11: ordinal not in range\(128\) [\#77](https://github.com/codelucas/newspaper/issues/77)
- article.text  and keywords error [\#47](https://github.com/codelucas/newspaper/issues/47)

**Merged pull requests:**

- Huge bugfix to aid lxml DOM parsing + remove unhelpful and excess exception messages and added tracebacks to exception logging [\#102](https://github.com/codelucas/newspaper/pull/102) ([codelucas](https://github.com/codelucas))
- Decode bytestring returned from lxml's `toString` early on before sending it out to outer code [\#101](https://github.com/codelucas/newspaper/pull/101) ([codelucas](https://github.com/codelucas))
- Fixed \#78: Remove encoding tag because lxml won't accept it for unicode [\#97](https://github.com/codelucas/newspaper/pull/97) ([mhall1](https://github.com/mhall1))

## [0.1.0](https://github.com/codelucas/newspaper/tree/0.1.0) (2014-12-17)
[Full Changelog](https://github.com/codelucas/newspaper/compare/0.0.9...0.1.0)

## [0.0.9](https://github.com/codelucas/newspaper/tree/0.0.9) (2014-12-17)
[Full Changelog](https://github.com/codelucas/newspaper/compare/0.0.8...0.0.9)

**Closed issues:**

- object has no attribute clean Error when using parse method [\#90](https://github.com/codelucas/newspaper/issues/90)
- Questions [\#85](https://github.com/codelucas/newspaper/issues/85)
- \[nltk\_data\] Error loading brown: \<urlopen error \[Errno -2\] Name or \[nltk\_data\]     service not known\> [\#84](https://github.com/codelucas/newspaper/issues/84)
- newspaper unable to find embedded youtube video [\#82](https://github.com/codelucas/newspaper/issues/82)
- Bound for memory usage [\#81](https://github.com/codelucas/newspaper/issues/81)
- Hosted demo [\#80](https://github.com/codelucas/newspaper/issues/80)
- Having issues installing due to lxml [\#79](https://github.com/codelucas/newspaper/issues/79)
- Add a BeautifulSoup4 parser. [\#44](https://github.com/codelucas/newspaper/issues/44)
- python 3 support request [\#36](https://github.com/codelucas/newspaper/issues/36)

**Merged pull requests:**

- update jieba to 0.35 [\#94](https://github.com/codelucas/newspaper/pull/94) ([WingGao](https://github.com/WingGao))
- Parse was breaking in the method clean\_article\_html when keep\_article\_ht... [\#88](https://github.com/codelucas/newspaper/pull/88) ([phoenixwizard](https://github.com/phoenixwizard))
- split title with \_  [\#87](https://github.com/codelucas/newspaper/pull/87) ([deweydu](https://github.com/deweydu))
- Update to support python3 [\#86](https://github.com/codelucas/newspaper/pull/86) ([log0ymxm](https://github.com/log0ymxm))
- Added link to basic demo [\#83](https://github.com/codelucas/newspaper/pull/83) ([iwasrobbed](https://github.com/iwasrobbed))
- Add splitting of slash-separated titles [\#75](https://github.com/codelucas/newspaper/pull/75) ([igor-shevchenko](https://github.com/igor-shevchenko))

## [0.0.8](https://github.com/codelucas/newspaper/tree/0.0.8) (2014-10-13)
[Full Changelog](https://github.com/codelucas/newspaper/compare/0.0.7...0.0.8)

**Closed issues:**

- Parsing Raw HTML [\#74](https://github.com/codelucas/newspaper/issues/74)
- Can't install newspaper [\#72](https://github.com/codelucas/newspaper/issues/72)
- Refactor codebase so newspaper is actually pythonic [\#70](https://github.com/codelucas/newspaper/issues/70)
- Article.top\_node == Article.clean\_top\_node [\#65](https://github.com/codelucas/newspaper/issues/65)
- article.movies missing 'http:' [\#64](https://github.com/codelucas/newspaper/issues/64)
- KeyError when calling newspaper.languages\(\) [\#62](https://github.com/codelucas/newspaper/issues/62)
- Memoize Articles - Not Printing [\#61](https://github.com/codelucas/newspaper/issues/61)
- Add URL headers while building a "paper" [\#60](https://github.com/codelucas/newspaper/issues/60)
- AttributeError: 'module' object has no attribute 'build' [\#59](https://github.com/codelucas/newspaper/issues/59)
- Typo in newspaper.build argument "memoize\_articles" [\#58](https://github.com/codelucas/newspaper/issues/58)
- issue with stopwords-tr.txt [\#51](https://github.com/codelucas/newspaper/issues/51)
- Other language support.  [\#34](https://github.com/codelucas/newspaper/issues/34)
- Character encoding detection [\#2](https://github.com/codelucas/newspaper/issues/2)

**Merged pull requests:**

- Huge refactor: entire codebase in PEP8, imports alphabetized, bugfixes, core changes [\#71](https://github.com/codelucas/newspaper/pull/71) ([codelucas](https://github.com/codelucas))
- Meta tag extraction fixes [\#69](https://github.com/codelucas/newspaper/pull/69) ([karls](https://github.com/karls))
- Test suite improvements [\#68](https://github.com/codelucas/newspaper/pull/68) ([karls](https://github.com/karls))
- Test suite fixes [\#67](https://github.com/codelucas/newspaper/pull/67) ([karls](https://github.com/karls))
- Revert "Added published date to the extractor+article" [\#66](https://github.com/codelucas/newspaper/pull/66) ([codelucas](https://github.com/codelucas))
- Added published date to the extractor+article [\#63](https://github.com/codelucas/newspaper/pull/63) ([parhammmm](https://github.com/parhammmm))

## [0.0.7](https://github.com/codelucas/newspaper/tree/0.0.7) (2014-06-17)
[Full Changelog](https://github.com/codelucas/newspaper/compare/0.0.6...0.0.7)

**Closed issues:**

- no document on how to add language [\#57](https://github.com/codelucas/newspaper/issues/57)
- Retain \<a\> tags in top article node? [\#56](https://github.com/codelucas/newspaper/issues/56)
- DocumentCleaner is missing clean\_body\_classes [\#55](https://github.com/codelucas/newspaper/issues/55)
- You must download and parse an article before parsing it [\#52](https://github.com/codelucas/newspaper/issues/52)
- Not extracting UL LI text [\#50](https://github.com/codelucas/newspaper/issues/50)
- article does not release\_resources\(\) [\#42](https://github.com/codelucas/newspaper/issues/42)
- Doesn't work on http://www.le360.ma/fr [\#40](https://github.com/codelucas/newspaper/issues/40)
- How to assign html content without downloading it? [\#37](https://github.com/codelucas/newspaper/issues/37)
- Python venv only? [\#32](https://github.com/codelucas/newspaper/issues/32)
- .nlp\(\) could not work [\#27](https://github.com/codelucas/newspaper/issues/27)
- Doesn't work with Arabic news sites [\#23](https://github.com/codelucas/newspaper/issues/23)
- SyntaxError: invalid syntax [\#19](https://github.com/codelucas/newspaper/issues/19)
- Retain HTML markup for extracted article [\#18](https://github.com/codelucas/newspaper/issues/18)
- Portuguese is misspelled [\#14](https://github.com/codelucas/newspaper/issues/14)
- Multi-threading article downloads not working [\#12](https://github.com/codelucas/newspaper/issues/12)
- Timegm error? [\#10](https://github.com/codelucas/newspaper/issues/10)
- Problem in Brazilian sites [\#9](https://github.com/codelucas/newspaper/issues/9)
- Brazilian portuguese support [\#6](https://github.com/codelucas/newspaper/issues/6)

**Merged pull requests:**

- Fix typo in code and documentation [\#54](https://github.com/codelucas/newspaper/pull/54) ([jacquerie](https://github.com/jacquerie))
- removed quotes of 'filename' in utils\\_\_init\_\_.py [\#53](https://github.com/codelucas/newspaper/pull/53) ([jay8688](https://github.com/jay8688))
- Fixed long-form article issue w/ calculate\_best\_node [\#49](https://github.com/codelucas/newspaper/pull/49) ([jeffnappi](https://github.com/jeffnappi))
- Use first image from article top\_node [\#35](https://github.com/codelucas/newspaper/pull/35) ([otemnov](https://github.com/otemnov))
- Add a section with links to related projects [\#33](https://github.com/codelucas/newspaper/pull/33) ([cantino](https://github.com/cantino))
- Original [\#30](https://github.com/codelucas/newspaper/pull/30) ([otemnov](https://github.com/otemnov))
- Fix reddit top image [\#29](https://github.com/codelucas/newspaper/pull/29) ([otemnov](https://github.com/otemnov))
- Extract Meta Tags in structured way [\#28](https://github.com/codelucas/newspaper/pull/28) ([voidfiles](https://github.com/voidfiles))
- Replace instances of 'Portugease' with 'Portuguese' [\#26](https://github.com/codelucas/newspaper/pull/26) ([WheresWardy](https://github.com/WheresWardy))
- It's The Changelog not The ChangeLog :\) [\#24](https://github.com/codelucas/newspaper/pull/24) ([adamstac](https://github.com/adamstac))
- syntax errors [\#22](https://github.com/codelucas/newspaper/pull/22) ([arjun024](https://github.com/arjun024))
- Support for more HTML tags in parsers.py [\#21](https://github.com/codelucas/newspaper/pull/21) ([WheresWardy](https://github.com/WheresWardy))
- Fixed syntax error [\#20](https://github.com/codelucas/newspaper/pull/20) ([damilare](https://github.com/damilare))
- Minor Performance tweaks [\#17](https://github.com/codelucas/newspaper/pull/17) ([techaddict](https://github.com/techaddict))
- Update README.rst [\#15](https://github.com/codelucas/newspaper/pull/15) ([girasquid](https://github.com/girasquid))
- Minor Typo candidate\_words -\> candidate\_words [\#13](https://github.com/codelucas/newspaper/pull/13) ([techaddict](https://github.com/techaddict))

## [0.0.6](https://github.com/codelucas/newspaper/tree/0.0.6) (2014-01-18)
[Full Changelog](https://github.com/codelucas/newspaper/compare/0.0.5...0.0.6)

**Closed issues:**

- Port to Ruby [\#8](https://github.com/codelucas/newspaper/issues/8)
- Huge internationalization / API revamp underway! [\#7](https://github.com/codelucas/newspaper/issues/7)
- Multithread & gevent framework built into newspaper [\#4](https://github.com/codelucas/newspaper/issues/4)

**Merged pull requests:**

- Add article html extraction [\#11](https://github.com/codelucas/newspaper/pull/11) ([voidfiles](https://github.com/voidfiles))

## [0.0.5](https://github.com/codelucas/newspaper/tree/0.0.5) (2014-01-09)
[Full Changelog](https://github.com/codelucas/newspaper/compare/0.0.4...0.0.5)

## [0.0.4](https://github.com/codelucas/newspaper/tree/0.0.4) (2013-12-31)
[Full Changelog](https://github.com/codelucas/newspaper/compare/0.0.3...0.0.4)

**Closed issues:**

- Calling nlp\(\) on an article causes 'tokenizers/punkt/english.pickle' Not Found Error [\#1](https://github.com/codelucas/newspaper/issues/1)

**Merged pull requests:**

- Fix for keyword arg usage in print\(\) on Python 2.7 [\#5](https://github.com/codelucas/newspaper/pull/5) ([michaelhood](https://github.com/michaelhood))

## [0.0.3](https://github.com/codelucas/newspaper/tree/0.0.3) (2013-12-22)
[Full Changelog](https://github.com/codelucas/newspaper/compare/0.0.2...0.0.3)

## [0.0.2](https://github.com/codelucas/newspaper/tree/0.0.2) (2013-12-21)
[Full Changelog](https://github.com/codelucas/newspaper/compare/0.0.1...0.0.2)

## [0.0.1](https://github.com/codelucas/newspaper/tree/0.0.1) (2013-12-21)


\* *This Change Log was automatically generated by [github_changelog_generator](https://github.com/skywinder/Github-Changelog-Generator)*
