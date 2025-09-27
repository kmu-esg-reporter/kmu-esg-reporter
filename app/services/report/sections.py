# app/services/report/sections.py
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from .types import ESGSectionContext

BASE_DIR = Path(__file__).resolve().parent         # app/services/report
TPL_DIR = BASE_DIR / "templates"                   # app/services/report/templates


_env = Environment(
    loader=FileSystemLoader(str(TPL_DIR)),
    autoescape=select_autoescape(["html", "xml"])
)

def render_environment(ctx: ESGSectionContext) -> str:
    tpl = _env.get_template("section_environment.html")
    return tpl.render(section=ctx)

def render_social(ctx: ESGSectionContext) -> str:
    tpl = _env.get_template("section_social.html")
    return tpl.render(section=ctx)

def render_governance(ctx: ESGSectionContext) -> str:
    tpl = _env.get_template("section_governance.html")
    return tpl.render(section=ctx)
