from unfold.sites import UnfoldAdminSite


class LearnRiteAdminSite(UnfoldAdminSite):
    """Extends Unfold's site rather than Django's plain AdminSite - that's
    what swaps the default admin skin for the themed one. Everything
    registered against this site keeps working unchanged; appearance and
    sidebar grouping are configured by the UNFOLD dict in settings."""
    title_header = 'LearnRite Admin'
    site_header = 'LearnRite Administration'
    index_title = 'LearnRite Site Admin'
    logout_template = 'logged_out.html'
