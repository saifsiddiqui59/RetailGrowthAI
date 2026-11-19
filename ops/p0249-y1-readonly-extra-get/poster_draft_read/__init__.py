"""#249 Y1 alternative hosting status GET only; not deployed."""
from p0249_readonly_jobs import serve


def main(req):
    return serve(req, "poster_draft")
