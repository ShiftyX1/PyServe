def get_redirections(redirections: list):
    redirects_dict = {}
    
    for redirect_item in redirections:
        for path, url in redirect_item.items():
            redirects_dict[path] = url
    
    return redirects_dict
