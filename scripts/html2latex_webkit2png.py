#!/usr/bin/python


#
# webkit2png.py
#
# Creates screenshots of webpages using by QtWebkit.
#
# Copyright (c) 2014 Roland Tapken <roland@dau-sicher.de>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
#
# Nice ideas "todo":
#  - Add QTcpSocket support to create a "screenshot daemon" that
#    can handle multiple requests at the same time.


# Standard Library
import logging
import os
import signal
import sys
import time
import urlparse
from optparse import OptionParser

# Third Party Stuff
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtNetwork import *
from PyQt4.QtWebKit import *


# Class for Website-Rendering. Uses QWebPage, which
# requires a running QtGui to work.
class WebkitRenderer(QObject):

    """
    A class that helps to create 'screenshots' of webpages using
    Qt's QWebkit. Requires PyQt4 library.

    Use "render()" to get a 'QImage' object, render_to_bytes() to get the
    resulting image as 'str' object or render_to_file() to write the image
    directly into a 'file' resource.
    """

    def __init__(self, **kwargs):
        """
        Sets default values for the properties.
        """

        if not QApplication.instance():
            raise RuntimeError(
                self.__class__.__name__ + " requires a running QApplication instance")
        QObject.__init__(self)

        # Initialize default properties
        self.width = kwargs.get('width', 0)
        self.height = kwargs.get('height', 0)
        self.timeout = kwargs.get('timeout', 0)
        self.wait = kwargs.get('wait', 2000)
        self.scaleToWidth = kwargs.get('scaleToWidth', 0)
        self.scaleToHeight = kwargs.get('scaleToHeight', 0)
        self.scaleRatio = kwargs.get('scaleRatio', 'crop')
        self.format = kwargs.get('format', 'png')
        self.logger = kwargs.get('logger', None)

        # Set this to true if you want to capture flash.
        # Not that your desktop must be large enough for
        # fitting the whole window.
        self.grabWholeWindow = kwargs.get('grabWholeWindow', False)
        self.renderTransparentBackground = kwargs.get(
            'renderTransparentBackground', False)
        self.ignoreAlert = kwargs.get('ignoreAlert', True)
        self.ignoreConfirm = kwargs.get('ignoreConfirm', True)
        self.ignorePrompt = kwargs.get('ignorePrompt', True)
        self.interruptJavaScript = kwargs.get('interruptJavaScript', True)
        self.encodedUrl = kwargs.get('encodedUrl', False)
        self.cookies = kwargs.get('cookies', [])

        # Set some default options for QWebPage
        self.qWebSettings = {
            QWebSettings.JavascriptEnabled: False,
            QWebSettings.PluginsEnabled: False,
            QWebSettings.PrivateBrowsingEnabled: True,
            QWebSettings.JavascriptCanOpenWindows: False
        }

    def render(self, url):
        """
        Renders the given URL into a QImage object
        """
        # We have to use this helper object because
        # QApplication.processEvents may be called, causing
        # this method to get called while it has not returned yet.
        helper = _WebkitRendererHelper(self)
        helper._window.resize(self.width, self.height)
        image = helper.render(url)

        # Bind helper instance to this image to prevent the
        # object from being cleaned up (and with it the QWebPage, etc)
        # before the data has been used.
        image.helper = helper

        return image

    def render_to_file(self, url, file_object):
        """
        Renders the image into a File resource.
        Returns the size of the data that has been written.
        """
        format = self.format  # this may not be constant due to processEvents()
        image = self.render(url)
        qBuffer = QBuffer()
        image.save(qBuffer, format)
        file_object.write(qBuffer.buffer().data())
        return qBuffer.size()

    def render_to_bytes(self, url):
        """Renders the image into an object of type 'str'"""
        format = self.format  # this may not be constant due to processEvents()
        image = self.render(url)
        qBuffer = QBuffer()
        image.save(qBuffer, format)
        return qBuffer.buffer().data()

# @brief The CookieJar class inherits QNetworkCookieJar to make a couple of functions public.


class CookieJar(QNetworkCookieJar):

    def __init__(self, cookies, qtUrl, parent=None):
        QNetworkCookieJar.__init__(self, parent)
        for cookie in cookies:
            QNetworkCookieJar.setCookiesFromUrl(
                self, QNetworkCookie.parseCookies(QByteArray(cookie)), qtUrl)

    def allCookies(self):
        return QNetworkCookieJar.allCookies(self)

    def setAllCookies(self, cookieList):
        QNetworkCookieJar.setAllCookies(self, cookieList)


class _WebkitRendererHelper(QObject):

    """
    This helper class is doing the real work. It is required to
    allow WebkitRenderer.render() to be called "asynchronously"
    (but always from Qt's GUI thread).
    """

    def __init__(self, parent):
        """
        Copies the properties from the parent (WebkitRenderer) object,
        creates the required instances of QWebPage, QWebView and QMainWindow
        and registers some Slots.
        """
        QObject.__init__(self)

        # Copy properties from parent
        for key, value in parent.__dict__.items():
            setattr(self, key, value)

        # Create and connect required PyQt4 objects
        self._page = CustomWebPage(
            logger=self.logger, ignore_alert=self.ignoreAlert,
            ignore_confirm=self.ignoreConfirm, ignore_prompt=self.ignorePrompt,
            interrupt_js=self.interruptJavaScript)
        self._view = QWebView()
        self._view.setPage(self._page)
        self._window = QMainWindow()
        self._window.setCentralWidget(self._view)

        # Import QWebSettings
        for key, value in self.qWebSettings.iteritems():
            self._page.settings().setAttribute(key, value)

        # Connect required event listeners
        self.connect(
            self._page, SIGNAL("loadFinished(bool)"), self._on_load_finished)
        self.connect(
            self._page, SIGNAL("loadStarted()"), self._on_load_started)
        self.connect(self._page.networkAccessManager(), SIGNAL(
            "sslErrors(QNetworkReply *,const QList<QSslError>&)"), self._on_ssl_errors)
        self.connect(self._page.networkAccessManager(), SIGNAL(
            "finished(QNetworkReply *)"), self._on_each_reply)

        # The way we will use this, it seems to be unesseccary to have
        # Scrollbars enabled
        self._page.mainFrame().setScrollBarPolicy(
            Qt.Horizontal, Qt.ScrollBarAlwaysOff)
        self._page.mainFrame().setScrollBarPolicy(
            Qt.Vertical, Qt.ScrollBarAlwaysOff)
        self._page.settings().setUserStyleSheetUrl(
            QUrl("data:text/css,html,body{overflow-y:hidden !important;}"))

        # Show this widget
        self._window.show()

    def __del__(self):
        """
        Clean up Qt4 objects.
        """
        self._window.close()
        del self._window
        del self._view
        del self._page

    def render(self, url):
        """
        The real worker. Loads the page (_load_page) and awaits
        the end of the given 'delay'. While it is waiting outstanding
        QApplication events are processed.
        After the given delay, the Window or Widget (depends
        on the value of 'grabWholeWindow' is drawn into a QPixmap
        and postprocessed (_post_process_image).
        """
        self._load_page(url, self.width, self.height, self.timeout)
        # Wait for end of timer. In this time, process
        # other outstanding Qt events.
        if self.wait > 0:
            if self.logger:
                self.logger.debug("Waiting %d seconds " % self.wait)
            waitToTime = time.time() + self.wait
            while time.time() < waitToTime:
                if QApplication.hasPendingEvents():
                    QApplication.processEvents()

        if self.renderTransparentBackground:
            # Another possible drawing solution
            image = QImage(self._page.viewportSize(), QImage.Format_ARGB32)
            image.fill(QColor(255, 0, 0, 0).rgba())

            # http://ariya.blogspot.com/2009/04/transparent-qwebview-and-qwebpage.html
            palette = self._view.palette()
            palette.setBrush(QPalette.Base, Qt.transparent)
            self._page.setPalette(palette)
            self._view.setAttribute(Qt.WA_OpaquePaintEvent, False)

            painter = QPainter(image)
            painter.setBackgroundMode(Qt.TransparentMode)
            self._page.mainFrame().render(painter)
            painter.end()
        else:
            if self.grabWholeWindow:
                # Note that this does not fully ensure that the
                # window still has the focus when the screen is
                # grabbed. This might result in a race condition.
                self._view.activateWindow()
                image = QPixmap.grabWindow(self._window.winId())
            else:
                image = QPixmap.grabWidget(self._window)

        return self._post_process_image(image)

    def _load_page(self, url, width, height, timeout):
        """
        This method implements the logic for retrieving and displaying
        the requested page.
        """

        # This is an event-based application. So we have to wait until
        # "loadFinished(bool)" raised.
        cancelAt = time.time() + timeout
        self.__loading = True
        self.__loadingResult = False  # Default
        if self.encodedUrl:
            qtUrl = QUrl.fromEncoded(url)
        else:
            qtUrl = QUrl(url)
        # Set the required cookies, if any
        self.cookieJar = CookieJar(self.cookies, qtUrl)
        self._page.networkAccessManager().setCookieJar(self.cookieJar)
        # Load the page
        self._page.mainFrame().load(qtUrl)
        while self.__loading:
            if timeout > 0 and time.time() >= cancelAt:
                raise RuntimeError("Request timed out on %s" % url)
            while QApplication.hasPendingEvents() and self.__loading:
                QCoreApplication.processEvents()

        if self.logger:
            self.logger.debug("Processing result")

        if self.__loading_result == False:
            if self.logger:
                self.logger.warning("Failed to load %s" % url)

        # Set initial viewport (the size of the "window")
        size = self._page.mainFrame().contentsSize()
        if self.logger:
            self.logger.debug("contentsSize: %s", size)
        if width > 0:
            size.setWidth(width)
        if height > 0:
            size.setHeight(height)

        self._window.resize(size)

    def _post_process_image(self, qImage):
        """
        If 'scaleToWidth' or 'scaleToHeight' are set to a value
        greater than zero this method will scale the image
        using the method defined in 'scaleRatio'.
        """
        if self.scaleToWidth > 0 or self.scaleToHeight > 0:
            # Scale this image
            if self.scaleRatio == 'keep':
                ratio = Qt.KeepAspectRatio
            elif self.scaleRatio in ['expand', 'crop']:
                ratio = Qt.KeepAspectRatioByExpanding
            else:  # 'ignore'
                ratio = Qt.IgnoreAspectRatio
            qImage = qImage.scaled(
                self.scaleToWidth, self.scaleToHeight, ratio, Qt.SmoothTransformation)
            if self.scaleRatio == 'crop':
                qImage = qImage.copy(
                    0, 0, self.scaleToWidth, self.scaleToHeight)
        return qImage

    def _on_each_reply(self, reply):
        """
        Logs each requested uri
        """
        self.logger.debug("Received %s" % (reply.url().toString()))

    # Eventhandler for "loadStarted()" signal
    def _on_load_started(self):
        """
        Slot that sets the '__loading' property to true
        """
        if self.logger:
            self.logger.debug("loading started")
        self.__loading = True

    # Eventhandler for "loadFinished(bool)" signal
    def _on_load_finished(self, result):
        """Slot that sets the '__loading' property to false and stores
        the result code in '__loading_result'.
        """
        if self.logger:
            self.logger.debug("loading finished with result %s", result)
        self.__loading = False
        self.__loading_result = result

    # Eventhandler for "sslErrors(QNetworkReply *,const QList<QSslError>&)"
    # signal
    def _on_ssl_errors(self, reply, errors):
        """
        Slot that writes SSL warnings into the log but ignores them.
        """
        for e in errors:
            if self.logger:
                self.logger.warn("SSL: " + e.errorString())
        reply.ignoreSslErrors()


class CustomWebPage(QWebPage):

    def __init__(self, **kwargs):
        """
        Class Initializer
        """
        super(CustomWebPage, self).__init__()
        self.logger = kwargs.get('logger', None)
        self.ignore_alert = kwargs.get('ignore_alert', True)
        self.ignore_confirm = kwargs.get('ignore_confirm', True)
        self.ignore_prompt = kwargs.get('ignore_prompt', True)
        self.interrupt_js = kwargs.get('interrupt_js', True)

    def javaScriptAlert(self, frame, message):
        if self.logger:
            self.logger.debug('Alert: %s', message)
        if not self.ignore_alert:
            return super(CustomWebPage, self).javaScriptAlert(frame, message)

    def javaScriptConfirm(self, frame, message):
        if self.logger:
            self.logger.debug('Confirm: %s', message)
        if not self.ignore_confirm:
            return super(CustomWebPage, self).javaScriptConfirm(frame, message)
        else:
            return False

    def javaScriptPrompt(self, frame, message, default, result):
        """
        This function is called whenever a JavaScript program running inside frame tries to prompt
        the user for input. The program may provide an optional message, msg, as well as a default value
        for the input in defaultValue.

        If the prompt was cancelled by the user the implementation should return false;
        otherwise the result should be written to result and true should be returned.
        If the prompt was not cancelled by the user, the implementation should return true and
        the result string must not be null.
        """
        if self.logger:
            self.logger.debug('Prompt: %s (%s)' % (message, default))
        if not self.ignore_prompt:
            return super(CustomWebPage, self).javaScriptPrompt(frame, message, default, result)
        else:
            return False

    def shouldInterruptJavaScript(self):
        """
        This function is called when a JavaScript program is running for a long period of time.
        If the user wanted to stop the JavaScript the implementation should return true; otherwise false.
        """
        if self.logger:
            self.logger.debug("WebKit ask to interrupt JavaScript")
        return self.interrupt_js


VERSION = "20091224"
LOG_FILENAME = 'webkit2png.log'
logger = logging.getLogger('webkit2png')


def init_qtgui(display=None, style=None, qtargs=None):
    """Initiates the QApplication environment using the given args."""
    if QApplication.instance():
        logger.debug("QApplication has already been instantiated. \
                        Ignoring given arguments and returning existing QApplication.")
        return QApplication.instance()

    qtargs2 = [sys.argv[0]]

    if display:
        qtargs2.append('-display')
        qtargs2.append(display)
        # Also export DISPLAY var as this may be used
        # by flash plugin
        os.environ["DISPLAY"] = display

    if style:
        qtargs2.append('-style')
        qtargs2.append(style)

    qtargs2.extend(qtargs or [])

    return QApplication(qtargs2)


if __name__ == '__main__':
    # This code will be executed if this module is run 'as-is'.

    # Enable HTTP proxy
    if 'http_proxy' in os.environ:
        proxy_url = urlparse.urlparse(os.environ.get('http_proxy'))
        proxy = QNetworkProxy(
            QNetworkProxy.HttpProxy, proxy_url.hostname, proxy_url.port)
        QNetworkProxy.setApplicationProxy(proxy)

    # Parse command line arguments.
    # Syntax:
    # $0 [--xvfb|--display=DISPLAY] [--debug] [--output=FILENAME] <URL>

    description = "Creates a screenshot of a website using QtWebkit." \
        + "This program comes with ABSOLUTELY NO WARRANTY. " \
        + "This is free software, and you are welcome to redistribute " \
        + "it under the terms of the GNU General Public License v2."

    parser = OptionParser(usage="usage: %prog [options] <URL>",
                          version="%prog " + VERSION +
                          ", Copyright (c) Roland Tapken",
                          description=description, add_help_option=True)
    parser.add_option("-x", "--xvfb", nargs=2, type="int", dest="xvfb",
                      help="Start an 'xvfb' instance with the given desktop size.", metavar="WIDTH HEIGHT")
    parser.add_option(
        "-g", "--geometry", dest="geometry", nargs=2, default=(0, 0), type="int",
        help="Geometry of the virtual browser window (0 means 'autodetect') [default: %default].", metavar="WIDTH HEIGHT")
    parser.add_option("-o", "--output", dest="output",
                      help="Write output to FILE instead of STDOUT.", metavar="FILE")
    parser.add_option("-f", "--format", dest="format", default="png",
                      help="Output image format [default: %default]", metavar="FORMAT")
    parser.add_option("--scale", dest="scale", nargs=2, type="int",
                      help="Scale the image to this size", metavar="WIDTH HEIGHT")
    parser.add_option(
        "--aspect-ratio", dest="ratio", type="choice", choices=["ignore", "keep", "expand", "crop"],
        help="One of 'ignore', 'keep', 'crop' or 'expand' [default: %default]")
    parser.add_option(
        "-F", "--feature", dest="features", action="append", type="choice",
        choices=["javascript", "plugins"],
        help="Enable additional Webkit features ('javascript', 'plugins')", metavar="FEATURE")
    parser.add_option("-c", "--cookie", dest="cookies", action="append",
                      help="Add this cookie. Use multiple times for more cookies. Specification is value of a Set-Cookie HTTP response header.", metavar="COOKIE")
    parser.add_option("-w", "--wait", dest="wait", default=0, type="int",
                      help="Time to wait after loading before the screenshot is taken [default: %default]", metavar="SECONDS")
    parser.add_option("-t", "--timeout", dest="timeout", default=0, type="int",
                      help="Time before the request will be canceled [default: %default]", metavar="SECONDS")
    parser.add_option("-W", "--window", dest="window", action="store_true",
                      help="Grab whole window instead of frame (may be required for plugins)", default=False)
    parser.add_option(
        "-T", "--transparent", dest="transparent", action="store_true",
        help="Render output on a transparent background (Be sure to have a transparent background defined in the html)", default=False)
    parser.add_option("", "--style", dest="style",
                      help="Change the Qt look and feel to STYLE (e.G. 'windows').", metavar="STYLE")
    parser.add_option(
        "", "--encoded-url", dest="encoded_url", action="store_true",
        help="Treat URL as url-encoded", metavar="ENCODED_URL", default=False)
    parser.add_option("-d", "--display", dest="display",
                      help="Connect to X server at DISPLAY.", metavar="DISPLAY")
    parser.add_option("--debug", action="store_true", dest="debug",
                      help="Show debugging information.", default=False)
    parser.add_option(
        "--log", action="store", dest="logfile", default=LOG_FILENAME,
        help="Select the log output file",)

    # Parse command line arguments and validate them (as far as we can)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error("incorrect number of arguments")
    if options.display and options.xvfb:
        parser.error("options -x and -d are mutually exclusive")
    options.url = args[0]

    logging.basicConfig(filename=options.logfile, level=logging.WARN,)

    # Enable output of debugging information
    if options.debug:
        logger.setLevel(logging.DEBUG)

    if options.xvfb:
        # Start 'xvfb' instance by replacing the current process
        server_num = int(os.getpid() + 1e6)
        newArgs = ["xvfb-run", "--auto-servernum", "--server-num", str(
            server_num), "--server-args=-screen 0, %dx%dx24" % options.xvfb, sys.argv[0]]
        skipArgs = 0
        for i in range(1, len(sys.argv)):
            if skipArgs > 0:
                skipArgs -= 1
            elif sys.argv[i] in ["-x", "--xvfb"]:
                skipArgs = 2  # following: width and height
            else:
                newArgs.append(sys.argv[i])
        logger.debug("Executing %s" % " ".join(newArgs))
        try:
            os.execvp(newArgs[0], newArgs[1:])
        except OSError:
            logger.error("Unable to find '%s'" % newArgs[0])
            print >> sys.stderr, "Error - Unable to find '%s' for -x/--xvfb option" % newArgs[
                0]
            sys.exit(1)

    # Prepare output ("1" means STDOUT)
    filename = options.output
    if options.output is None:
        options.output = sys.stdout
    else:
        options.output = open(options.output, "w")

    logger.debug("Version %s, Python %s, Qt %s",
                 VERSION, sys.version, qVersion())

    # Technically, this is a QtGui application, because QWebPage requires it
    # to be. But because we will have no user interaction, and rendering can
    # not start before 'app.exec_()' is called, we have to trigger our "main"
    # by a timer event.
    def __main_qt():
        # Render the page.
        # If this method times out or loading failed, a
        # RuntimeException is thrown
        try:
            # Initialize WebkitRenderer object
            renderer = WebkitRenderer()
            renderer.logger = logger
            renderer.width = options.geometry[0]
            renderer.height = options.geometry[1]
            renderer.timeout = options.timeout
            renderer.wait = options.wait
            renderer.format = options.format
            renderer.grabWholeWindow = False
            renderer.renderTransparentBackground = False
            renderer.encodedUrl = options.encoded_url
            if options.cookies:
                renderer.cookies = options.cookies

            if options.scale:
                renderer.scaleRatio = options.ratio
                renderer.scaleToWidth = options.scale[0]
                renderer.scaleToHeight = options.scale[1]

            if options.features:
                if "javascript" in options.features:
                    renderer.qWebSettings[
                        QWebSettings.JavascriptEnabled] = True
                if "plugins" in options.features:
                    renderer.qWebSettings[QWebSettings.PluginsEnabled] = True

            renderer.render_to_file(
                url=options.url, file_object=options.output)
            options.output.close()
            QApplication.exit(0)

            from PIL import Image, ImageChops

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

            image = Image.open(filename)
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
            nx, ny = image.size
            # image = image.resize((int(nx * 2), int(ny * 2)), Image.BICUBIC)
            image.save(filename)
        except RuntimeError, e:
            logger.error("main: %s" % e)
            print >> sys.stderr, e
            QApplication.exit(1)

    # Initialize Qt-Application, but make this script
    # abortable via CTRL-C
    app = init_qtgui(display=options.display, style=options.style)
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    QTimer.singleShot(0, __main_qt)
    sys.exit(app.exec_())
