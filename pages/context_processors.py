from .site_info import SITE_INFO


def site_info(request):
    return {"SITE": SITE_INFO}
