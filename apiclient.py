import webuiapi



def getApiClient(ip):
    # create API client with custom host, port and https
    #api = webuiapi.WebUIApi(host='webui.example.com', port=443, use_https=True)

    # create API client with default sampler, steps.
    #api = webuiapi.WebUIApi(sampler='Euler a', steps=20)
    # create API client
    api = webuiapi.WebUIApi(host=ip, port=7860)
    api.set_auth('username', 'password')
    return api

