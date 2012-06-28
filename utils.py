from pyquery.pyquery import PyQuery

__author__ = 'dude'

def serializeArray(form):
    form = PyQuery(form)
    if not form.is_('form'):
        return []

    source = form.find('input, select, textarea')

    data = []
    for input in source:
        input = PyQuery(input)
        if input.is_('[disabled]') or not input.is_('[name]'):
            continue
        if input.is_('[type=checkbox]') and not input.is_('[checked]'):
            continue

        data.append((input.attr('name'), input.val()))

    return data


#        testcookie = cookie._cookie_from_cookie_tuple(
#            ( 'testcookie', '', {'domain': '.aol.com', 'path': '/', 'version': 0}, None), Request('http://aol.com'))
#        cookie.set_cookie(testcookie)
#
