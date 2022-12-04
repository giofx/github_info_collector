import requests
import myutils

class HTTPreq:
    """
        Simple wrapper for HTTP requests
    """

    def __init__(self, reuse_session = True):
        # requests.Session() allows to reuse same session for every request to same domain 
        self.request = requests.Session() if reuse_session else requests


    def get(self, url, headers = {}):
        """
            Makes an http get request
            headers are optionals, if ommited empty headers are sent
        """

        try:
            http_response = self.request.get(url, headers = headers)
        except Exception as e:
            self.logger.error(f"{myutils.myfunc_name()} got {type(e).__name__} exception while trying to make get request to url {url}.\
                                Exception is at line {myutils.getLineLastException()}. Exception is {e}")
            raise e
        response = {}
        response["status_code"] = http_response.status_code
        response["encoding"] = http_response.encoding
        response["headers"] = http_response.headers

        if http_response.text: response["text"] = http_response.text

        return response

    def get_status_code(self, url, headers = {}):
        """
            Return just status code for get request
        """
        response = self.get(url, headers )
        return response["status_code"]

    def request_has_success( self, status_code ):
        return ( 300 > status_code >= 200 )

    def get_with_success(self, url, headers = {}):
        """
            Returns if get request to an url receives a status code in 2xx family
        """
        return self.request_has_success( self.get_status_code(url, headers) )