# Dependency + External Tooling Audit

Date: 2026-01-21
Scope: html2latex modernization (Python 3 + justhtml)

## Python Dependencies (current)

### Runtime (requirements/base.txt)
| Package | Current Pin | Notes | Python 3 plan |
| --- | --- | --- | --- |
| Jinja2 | 2.7.3 | Very old; templates + custom delimiters used. | Upgrade to latest Jinja; validate rendering. |
| MarkupSafe | 0.23 | Old; Jinja dependency. | Upgrade via Jinja. |
| argparse | 1.2.1 | Python 2 backport; unnecessary in Py3. | Remove. |
| html2text | 2015.6.12 | Very old. | Upgrade to latest compatible version. |
| lxml | 3.4.1 | Heavy dep; to be removed. | Replace with justhtml. |
| pyenchant | 1.6.6 | Old; needs system lib. | Upgrade; move to optional extra. |
| xamcheck-utils | git master | Git dependency. | Inline/remove function(s). |

### Dev (requirements/dev.txt)
| Package | Current Pin | Notes | Python 3 plan |
| --- | --- | --- | --- |
| Flask | 1.1.4 | Old. | Upgrade to latest supported (demo app). |
| ipdb | 0.8 | Old. | Optional dev tool. |
| ipython | 2.3.1 | Python 2 era. | Upgrade or drop. |
| redis | 2.9.1 | Old. | Upgrade to modern redis client. |

### Test (requirements/test.txt)
| Package | Current Pin | Notes | Python 3 plan |
| --- | --- | --- | --- |
| blessings | 1.6 | Old; nose plugin related. | Drop (pytest). |
| coverage | 3.7.1 | Old. | Use pytest-cov if needed. |
| nose | 1.3.4 | Deprecated. | Replace with pytest. |
| nose-progressive | 1.5.1 | Deprecated. | Drop. |
| python-termstyle | 0.1.10 | Old. | Drop unless needed. |
| rednose | 0.4.1 | Deprecated. | Drop. |
| wsgiref | 0.1.2 | Py2 stdlib backport. | Remove. |

## External Tools / System Dependencies

| Tool | Where referenced | Status | Plan |
| --- | --- | --- | --- |
| phantomjs | README (Requirements) | Deprecated/unmaintained | Remove or make optional; document replacement if needed. |
| bower | setup.py install hook | Deprecated | Remove install hook; no bower dependency in modern flow. |
| webkit2png script | setup.py install hook | Script missing in repo | Remove install hook; re-evaluate feature need. |
| libxml2/libxslt | lxml build deps | Heavy system deps | Remove with lxml. |
| enchant (system) | pyenchant | Required for spellcheck | Move to optional extra; document system package. |

## Observations
- The project is Python 2.7–era; many dependencies are obsolete or redundant in Python 3.
- The `setup.py` install hook attempts to copy a script that does not exist in the repo and runs `bower install` with `sudo`.
- `xamcheck-utils` is a git dependency; only one function is used (check_if_html_has_text).

## Recommendations (priority)
1. Remove lxml and adopt justhtml (MOD-06).
2. Remove all Python 2 backports (argparse, wsgiref).
3. Replace nose stack with pytest + ruff (MOD-11/13).
4. Upgrade Jinja + html2text + redis + Flask; move pyenchant to optional extra (MOD-08/17).
5. Delete all `sudo` install hooks and deprecated tooling (MOD-10).
