import httpx


class httpxClient:
    """
    A class used to create an httpxClient.
    If an instance is created it should also be closed after use.

    Methods
    -------
    get(url, **params)
        Calls httpx get for given url with custom client and given parameters
        and returns the result
    post(url, **params)
        Calls httpx post for given url with custom client and given parameters
        and returns the result
    stream(method, url)
        Calls httpx stream for given url with custom client and given method
        parameter and returns the stream
    checkStatusCodeOK(statusCode)
        Uses httpx.codes.OK to check if given statusCode is OK
    """

    def __init__(self, timeout=30.0):
        """
        Parameters
        ----------
        timeout : float
            Default value: 30 seconds
            The timeout set on the client instance, used as the default
            timeout for get and post requests.
            Can be overwritten in individual calls in *params
        """
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)
        return None

    def close(self):
        self.client.close()
        return None

    def __del__(self):
        self.close()
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get(self, url: str, **params):
        if "attempt" in params:
            attempt = params.get("attempt")
            del params["attempt"]
        else:
            attempt = 0
        try:
            r = self.client.get(url, **params)
        except httpx.ReadTimeout as e:
            if attempt < 3:
                params["attempt"] = attempt + 1
                if "timeout" in params:
                    params["timeout"] = params["timeout"] * 2
                else:
                    params["timeout"] = self.timeout * 2
                r = self.get(url, **params)
            else:
                raise e
        return r

    def post(self, url: str, **params):
        r = self.client.post(url, **params)
        return r

    def stream(self, method, url):
        return self.client.stream(method, url)

    def checkStatusCodeOK(self, statusCode: int) -> bool:
        return statusCode == httpx.codes.OK
