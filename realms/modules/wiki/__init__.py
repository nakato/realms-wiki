from realms.modules.wiki import routes

class WikiRoutes(object):

    def __init__(self, app):
        _commit = routes.Commit()
        _compare = routes.Compare()
        _history = routes.History()
        _edit = routes.Edit()
        _index = routes.Index()
        _create = routes.Create()
        _page = routes.Page()
        _revert = routes.Revert()
        get = routes.Get()
        app.add_route('/_commit/{sha}/{path}', _commit)
        app.add_route('/_compare/{path}/{fsha}..{lsha}', _compare)
        app.add_route('/_history/{path}', _history)
        app.add_route('/_edit/{path}', _edit)
        app.add_route('/_index', _index)
        app.add_route('/_index/{path}', _index)
        app.add_route('/_create', _create)
        app.add_route('/_create/{path}', _create)
        app.add_route('/_revert', _revert)
        app.add_route('/', _page)
        app.add_route('/{path}', _page)
        app.add_route('/get/{path}', get)
