"""
Tha main application logic
"""
from pathlib import Path
import mimetypes

from flask import Flask, request, jsonify, session, redirect, send_file, Response

from src.cert import Cert
from src.motionsensor import MotionSensor
from src.screen import Screen
from src.config import Config
from src.cron import CronFile
from src.system import System

PUBLIC_FUNCTION =  ['on_get_index','on_login','on_is_authenticated','on_logout', 'on_get_resource']

class App:
    """
    The main application logic.
    """

    def __init__(self, config: Config):
        """
        Creates a new instance.
        """
        self.__config = config
        self.__screen = Screen()
        self.__cert = Cert(root=config.get_root())
        self.__system = System()

        self.__motion_sensor = MotionSensor(
            self.__screen, self.__config.get_motion_sensor_delay())

        if self.__config.is_motion_sensor_enabled():
            self.__motion_sensor.enable()


    # Screen related function.
    def on_get_screenshot(self):
        """
        Takes a screenshot and returns it as png.
        """
        try:
            return Response(self.__screen.get_screenshot(), mimetype='image/png')
        except Exception as e:
            return f"Error occurred: {e}", 500

    def on_get_screen(self):
        """
        Gets the screen related configuration like dimensions, the url, the scale as well
        as the screen orientation.
        """

        return jsonify({
            "dimensions" : self.__screen.get_orientation(),
            "url" : self.__screen.get_url(),
            "scale" : self.__screen.get_scale()
        })

    def on_set_screen_off(self):
        """
        Turns the screen off.
        """
        self.__screen.off()
        return self.on_get_screen()


    def on_set_screen_on(self):
        """
        Turns the screen on.
        """
        self.__screen.on()
        return self.on_get_screen()

    def on_set_screen(self):
        """
        Sets the screen related configuration like the browser url, the scale 
        as well as the screen orientation.
        """
        data = request.json

        self.__screen.set_url(data.pop("url"))
        self.__screen.set_scale_factor(data.pop("scale"))
        self.__screen.set_orientation(data.pop("orientation"))

        self.__screen.reload()

        return self.on_get_screen()

    # Certificate Endpoint related functions
    def on_set_cert(self):
        """
        Sets a cert provided by the user
        """
        self.__cert.update_pfx(
            request.files['pfx'].read(),
            request.form['password'])

        return 'File updated successfully', 200

    def on_generate_cert(self):
        """
        Creates a new cert.
        """
        self.__cert.generate()
        return 'File updated successfully', 200

    def on_get_cert(self):
        """
        Returns the cert as der file.
        """
        return Response(
            self.__cert.get_cert(),
            content_type='application/x-x509-ca-cert',
            headers={'Content-Disposition': 'attachment; filename=cert.der'})

    # Schedule related functions
    def on_get_schedule(self):
        """
        Returns the schedule and the corresponding cron jobs.
        """

        return jsonify(CronFile().load_jobs())

    def on_set_schedule(self):
        """
        Sets the schedule and the corresponding cron jobs.
        """

        CronFile().save_jobs(request.json)
        return self.on_get_schedule()

    def on_get_motion_sensor(self):
        """
        Gets the motion sensors settings.
        """

        return jsonify({
            "enabled" : self.__motion_sensor.is_enabled(),
            "delay" : self.__motion_sensor.get_delay()
        })

    def on_enable_motion_sensor(self):
        """
        Enables the motion sensor.
        """
        if not self.__motion_sensor.is_enabled():
            self.__motion_sensor.enable()

        self.__config.enable_motion_sensor()

        return self.on_get_motion_sensor()

    def on_disable_motion_sensor(self):
        """
        Disables the motion sensor.
        """
        self.__motion_sensor.disable()
        self.__config.disable_motion_sensor()

        return self.on_get_motion_sensor()

    def on_set_motion_sensor_delay(self):
        """
        Sets the motion sensor's delay.
        """
        data = request.json

        self.__motion_sensor.set_delay(data["delay"])
        self.__config.set_motion_sensor_delay(data["delay"])

        return self.on_get_motion_sensor()

    # System related functions
    def on_reboot(self):
        """
        Triggers a restart.
        We need to defer the restart by just enough time to return a 
        success to the browser, otherwise it will be vary mad at us.
        """
        self.__system.reboot()
        return "Reboot in 5 seconds.", 200

    def on_get_hostname(self):
        """
        Returns the currently set hostname.
        """
        return jsonify({
            "hostname" : self.__system.get_hostname()})

    def on_set_hostname(self):
        """
        Sets the hostname and reboots the system.
        """
        self.__system.set_hostname(request.json["hostname"])
        self.__system.reboot()
        return 'Schedule updated successfully, rebooting', 200

    # SSH related functions
    def on_get_ssh(self):
        """
        Checks is SSH is active.
        """
        return jsonify(
            { "active" : self.__system.is_ssh_active() })

    def on_disable_ssh(self):
        """
        Disables SSH.
        """
        self.__system.disable_ssh()
        self.__system.reboot()
        return 'SSH is disabled.', 200

    def on_enable_ssh(self):
        """
        Enables SSH.
        """
        self.__system.enable_ssh()
        self.__system.reboot()
        return 'SSH is enabled.', 200

    def on_get_log_webservice(self):
        """
        Returns the web service's log.      
        """
        return self.__config.get_log("kiosk-webservice")

    def on_get_log_browser(self):
        """
        Returns the browser's log.      
        """
        return self.__config.get_log("kiosk-browser")

    # Authentication related Endpoints
    def on_set_password(self):
        """
        Called when ever the user wants to update the password.
        """

        data = request.json
        self.__config.set_password(data["password"])

        return 'Password set successfully.', 200

    def on_is_authenticated(self):
        """
        Called to check if the user is authenticated.
        """
        if 'authenticated' in session:
            return jsonify({'authenticated': True }), 200

        return jsonify({'authenticated': False }), 200

    def on_login(self):
        """
        Called when the user wants to login.
        """

        password = request.json.get('password')
        if not password:
            return jsonify({'error': 'Invalid password'}), 401

        if not self.__config.is_password(password):
            return jsonify({'error': 'Invalid password'}), 401

        session['authenticated'] = True
        return jsonify({'message': 'Login successful'}), 200

    def on_logout(self):
        """
        Called when the user wants to logout.
        """
        session.clear()
        return "Logout completed.", 200

    def on_status(self):
        """
        Called when the web application wants to check if the app is up and running.
        Alway returns 200.
        """
        return "Up and running.", 200

    def on_before_request(self):
        """
        Called before the request is processed.
        Used to check the authentication.
        """

        if request.headers.get('X-Forwarded-Proto') == 'http':
            url = request.url.replace('http://', 'https://', 1)
            return redirect(url, code=301)

        if not request.is_secure:
            # If the request is not secure (HTTP), redirect to HTTPS
            secure_url = request.url.replace('http://', 'https://', 1)
            return redirect(secure_url, code=301)

        if request.endpoint in PUBLIC_FUNCTION:
            return None

        if 'authenticated' in session:
            return None

        return jsonify({'error': 'Unauthorized'}), 401

    def on_after_request(self, r):
        """
        Called after the request is processed. 
        Used to inject the no proxy headers.
        """

        r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        r.headers["Pragma"] = "no-cache"
        r.headers["Expires"] = "0"

        return r

    def on_get_index(self):
        """
        Return the main html content.
        """
        return send_file("./../html/index.html")

    def on_get_resource(self, filename:str):
        """
        Resources needed by the html content. 
        """
        base = Path("./html/").resolve()
        target = (base / filename).resolve()

        # Ensure we do not escape our sandbox...
        if target.parts[:len(base.parts)] != base.parts:
            return f"File {filename} not found", 404

        if not target.exists():
            return f"File {filename} does not exist", 404

        mimetype, _ = mimetypes.guess_type(filename)

        if not mimetype:
            mimetype = 'application/octet-stream'

        return send_file(target, mimetype=mimetype)

    def run(self):
        """
        Tha main program loops which create the flask application.
        """
        app = Flask(__name__)
        app.secret_key = self.__config.get_secret_key()

        app.add_url_rule(
            '/log/browser', view_func=self.on_get_log_browser, methods=["GET"])
        app.add_url_rule(
            '/log/webservice', view_func=self.on_get_log_webservice, methods=["GET"])

        app.add_url_rule(
            '/screen/screenshot.png', view_func=self.on_get_screenshot, methods=['GET'])
        app.add_url_rule(
            '/screen/on',  view_func=self.on_set_screen_on, methods=['GET'])
        app.add_url_rule(
            '/screen/off',  view_func=self.on_set_screen_off, methods=['GET'])
        app.add_url_rule(
            '/screen',  view_func=self.on_get_screen, methods=['GET'])
        app.add_url_rule(
            '/screen',  view_func=self.on_set_screen, methods=['POST'])

        app.add_url_rule(
            '/cert', view_func=self.on_get_cert, methods=["GET"])
        app.add_url_rule(
            '/cert', view_func=self.on_set_cert, methods=["POST"])
        app.add_url_rule(
            '/cert/generate', view_func=self.on_generate_cert, methods=["POST"])

        app.add_url_rule(
            '/schedule', view_func=self.on_get_schedule, methods=["GET"])
        app.add_url_rule(
            '/schedule', view_func=self.on_set_schedule, methods=["POST"])

        app.add_url_rule(
            '/motionsensor', view_func=self.on_get_motion_sensor, methods=["GET"])
        app.add_url_rule(
            '/motionsensor/enable', view_func=self.on_enable_motion_sensor, methods=["GET", "POST"])
        app.add_url_rule(
            '/motionsensor/disable', view_func=self.on_disable_motion_sensor, methods=["GET", "POST"])
        app.add_url_rule(
            '/motionsensor/delay', view_func=self.on_set_motion_sensor_delay, methods=["POST"])        

        app.add_url_rule("/ssh", view_func=self.on_get_ssh, methods=["GET"])
        app.add_url_rule("/ssh/enable", view_func=self.on_enable_ssh, methods=["POST","GET"])
        app.add_url_rule("/ssh/disable", view_func=self.on_disable_ssh, methods=["POST","GET"])

        app.add_url_rule('/hostname', view_func=self.on_get_hostname, methods=["GET"])
        app.add_url_rule('/hostname', view_func=self.on_set_hostname, methods=["POST"])

        app.add_url_rule("/reboot", view_func=self.on_reboot, methods=["GET"])

        app.add_url_rule('/password', view_func=self.on_set_password, methods=['POST'])
        app.add_url_rule('/login', view_func=self.on_is_authenticated, methods=['GET'])
        app.add_url_rule('/login', view_func=self.on_login, methods=['POST'])
        app.add_url_rule("/logout", view_func=self.on_logout, methods=['GET', 'POST'])
        app.add_url_rule("/status", view_func=self.on_status, methods=['GET'])

        app.add_url_rule('/', view_func=self.on_get_index, methods=['GET'])
        app.add_url_rule('/resources/<filename>', view_func=self.on_get_resource, methods=['GET'])

        app.before_request(self.on_before_request)
        app.after_request(self.on_after_request)

        app.run(
            host='0.0.0.0', port=443,
            threaded=True,
            ssl_context=self.__cert.get_ssl_context())
