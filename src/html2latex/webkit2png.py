# Standard Library
import time
from contextlib import contextmanager

# Third Party Stuff
import splinter
from PIL import Image, ImageChops
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support.expected_conditions import staleness_of


def check_if_mathjax_has_been_loaded_completely(driver):
    javascript_code = '''
    MathJax.Hub.Register.StartupHook("End",
        function () {
            window.MathJaxSetupDone = true;
        }
    );
    return window.MathJaxSetupDone === true;
    '''.strip()

    try:
        return driver.execute_script(javascript_code) is True
    except WebDriverException:
        return False

@contextmanager
def wait_for_mathjax_loading(driver, timeout=30):
    yield
    WebDriverWait(driver, timeout).until(check_if_mathjax_has_been_loaded_completely)


def is_transparent(image):
    """
    Check to see if an image is transparent.
    """
    if not isinstance(image, Image.Image):
        # Can only deal with PIL images, fall back to the assumption that that
        # it's not transparent.
        return False
    return (image.mode in ('RGBA', 'LA') or
            (image.mode == 'P' and 'transparency' in image.info))


def webkit2png(url, image_file_path, wait_time=10):
    with splinter.Browser('phantomjs') as browser:
        browser.visit(url)

        if browser.status_code.is_success():
            try:
                with wait_for_mathjax_loading(browser.driver):
                    pass
            except TimeoutException:
                pass

            if wait_time > 0:
                time.sleep(wait_time)

            browser.driver.save_screenshot(image_file_path)
            image = Image.open(image_file_path)
            image.load()
            if is_transparent(image) and False:
                no_alpha = Image.new('L', image.size, (255))
                no_alpha.paste(image, mask=image.split()[-1])
            else:
                no_alpha = image.convert('L')
            # Convert to black and white imageage.
            bw = no_alpha.convert('L')
            # bw = bw.filter(ImageFilter.MedianFilter)
            # White background.
            bg = Image.new('L', image.size, 255)
            bbox = ImageChops.difference(bw, bg).getbbox()
            if bbox:
                image = image.crop(bbox)
            image.save(image_file_path)
