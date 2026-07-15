# Build results

## 2026-07-15 release-candidate verification

- Python 3.12 unit suite: 10/10 passed.
- `compileall` over `src` and `tests`: passed.
- `uv build`: produced the 0.1.0 wheel and source distribution.
- Clean Python 3.12 virtual environment: wheel installed with no runtime dependencies.
- Installed CLI fixture listing, fixture creation, and expected failing score of an unedited fixture: passed.
- Targeted obvious-secret filename scan: no matches.

The system `python3` is Python 3.9 and correctly rejected the package's declared Python `>=3.10` requirement; clean-install verification was repeated successfully with installed Python 3.12.

Remote Ubuntu, macOS, and Windows CI remains pending private publication.
