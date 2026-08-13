"""Unit tests for the NeoRé NeoApi client.

These tests exercise `custom_components/neore/api.py` only. That module is
deliberately free of any Home Assistant import (see its module docstring),
so it can be tested with a plain `pytest` install and no network access —
every HTTP call is mocked. Nothing in `tests/` requires the `homeassistant`
package.
"""
