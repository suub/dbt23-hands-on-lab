import httpx


class httpxClient:
     """
     A class used to create a httpxClient.

     If an instance is created it should also be closed after use.

    ...

    Methods
    -------
    get(url, **params)
        Calls httpx get for given url with custom client and given parameters and retruns the result
    post(url, **params)
        Calls httpx post for given url with custom client and given parameters and retruns the result
    stream(method, url)
        Calls httpx stream for given url with custom client and given method parameter and retruns the stream
    checkStatusCodeOK(statusCode)
        Calls httpx.codes.OK and checks a given statusCode is included and returns an indicating bool
    """

    def __init__(self, timeout=30.0):
        """
        Parameters
        ----------
        timeout : float
             The timeout set on the client instance, used as the default timeout for get and post requests
             Can be overwritten in individual calls in *params
        """
        self.client = httpx.Client(timeout=timeout)
        return None

    async def close(self):
        self.client.close()
        return None

    def __del__(self):
        self.loop.close()
        return None

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
                params["timeout"] = params["timeout"] * 2 if "timeout" in params else timeout * 2
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
