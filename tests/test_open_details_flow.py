"""T-26: Datei-Plugin → Registry → Beschaffung → SQLite → REST, mit echtem Lifespan."""

from pathlib import Path

import pytest

from tests import test_yaml_profile as yaml_profile

client = yaml_profile.client
_profile = yaml_profile._profile

PLUGIN = '''
import json
from pathlib import Path
from stockinfo_plugin import MetadataSource, FieldSpec, Reading

class RiskSource(MetadataSource):
    name = 'risk-demo'
    api_version = 2
    SUPPORTED_KINDS = frozenset({'listed', 'pair'})
    SUPPORTED_TYPES = frozenset({'etf', 'crypto'})
    FIELDS = (
        FieldSpec('score', kind='number', label_en='Risk score', label_de='Risikoscore', plausible=(0, 100)),
        FieldSpec('verified', kind='boolean', label_en='Verified', label_de='Bestätigt', overridable=False),
    )
    def handles(self, request):
        return True
    def fetch(self, request):
        value = json.loads((Path(__file__).parent.parent / 'risk.json').read_text())
        return [Reading('score', value, source=self.name), Reading('verified', False, source=self.name)]

SOURCES = [RiskSource]
'''


@pytest.fixture
def volume(tmp_path: Path) -> Path:
    (tmp_path / 'plugins').mkdir()
    (tmp_path / 'plugins' / 'risk.py').write_text(PLUGIN)
    (tmp_path / 'risk.json').write_text('null')
    return tmp_path


def test_offene_details_durch_die_ganze_kette(volume, client):
    _profile(volume, {
        'resolvers': ['yaml-file'], 'quotes': ['yaml-file'], 'daily': ['yaml-file'],
        'fx': ['yaml-file'], 'etf_meta': ['risk-demo', 'yaml-file'],
    })
    catalog = client.get('/fields')
    assert catalog.status_code == 200, catalog.text
    definitions = {entry['name']: entry for entry in catalog.json()['details']}
    assert definitions['risk-demo.score']['overridable'] is True
    assert definitions['risk-demo.verified']['overridable'] is False
    assert definitions['ter']['unit'] == 'percent'
    assert catalog.json()['generation_id']
    response = client.get('/quote/IE00B4L5Y983')
    assert response.status_code == 200, response.text
    quote = response.json()
    assert quote['details']['risk-demo.verified']['value'] is False
    assert quote['details']['ter']['value'] == quote['ter'] == 0.2
    assert quote['details']['ter']['source'] == 'yaml-file'
    item = client.get('/instruments').json()[0]
    path = f"/instruments/by-id/{item['listing_id']}/details"
    assert client.patch(path, json={'risk-demo.score': {'value': 0}}).status_code == 200
    assert client.get('/quote/IE00B4L5Y983').json()['details']['risk-demo.score']['value'] == 0
    before = client.get('/instruments').json()
    for patch in (
        {'risk-demo.verified': {'value': True}},
        {'risk-demo.score': {'value': 101}},
        {'risk-demo.score': {'value': True}},
        {'risk-demo.score': {'value': 7}, 'missing.field': {'value': 4}},
    ):
        assert client.patch(path, json=patch).status_code == 422
        assert client.get('/instruments').json() == before
    (volume / 'risk.json').write_text('17')
    refreshed = client.post('/refresh/IE00B4L5Y983')
    assert refreshed.status_code == 200, refreshed.text
    value = refreshed.json()['details']['risk-demo.score']
    assert value['value'] == 17 and value['manual_value'] == 0 and value['shadowed']
    assert value['source'] == 'risk-demo'
    assert client.patch(path, json={'risk-demo.score': {'value': None}}).status_code == 200
    assert client.get('/quote/IE00B4L5Y983').json()['details']['risk-demo.score']['manual_value'] is None
    crypto = client.get('/quote', params={'symbol': 'BTC-EUR'})
    assert crypto.status_code == 200, crypto.text
    assert 'fund_domicile' not in crypto.json()['details']
    assert 'ter' not in crypto.json()['details']
    assert 'risk-demo.score' in crypto.json()['details']


def test_quellenausfall_aendert_weder_schema_noch_version(volume, client):
    chains = {'resolvers': ['yaml-file'], 'quotes': ['yaml-file'],
              'etf_meta': ['risk-demo', 'yaml-file']}
    _profile(volume, chains)
    before = client.get('/fields').json()
    # Dieselbe validierte Quelle wird beim nächsten Aufbau als gestört gemeldet.
    from app.plugin_adapters import unwrap
    from app.sources_registry import build_chain
    from app.container import get_sources_config
    from app.config import get_settings

    source = unwrap(build_chain('etf_meta', get_sources_config(), get_settings())[0])
    source.__class__.configuration_problem = lambda self: 'Testausfall'
    try:
        _profile(volume, chains)
        assert client.get('/fields').json() == before
    finally:
        del source.__class__.configuration_problem


def test_schemaentfernung_erhoeht_version_im_rest_vertrag(volume, client):
    chains = {'resolvers': ['yaml-file'], 'quotes': ['yaml-file'],
              'etf_meta': ['risk-demo', 'yaml-file']}
    _profile(volume, chains)
    before = client.get('/fields').json()
    _profile(volume, {**chains, 'etf_meta': ['yaml-file']})
    after = client.get('/fields').json()
    assert after['generation_id'] == before['generation_id']
    assert after['details_version'] == before['details_version'] + 1
    assert all(not entry['name'].startswith('risk-demo.') for entry in after['details'])


def test_konstruktorfehler_behaelt_schema_und_manuelle_werte(volume, client, monkeypatch):
    from app.plugin_adapters import unwrap
    from app.sources_registry import build_chain
    from app.container import get_sources_config
    from app.config import get_settings

    chains = {'resolvers': ['yaml-file'], 'quotes': ['yaml-file'],
              'etf_meta': ['risk-demo', 'yaml-file']}
    _profile(volume, chains)
    before = client.get('/fields').json()
    assert client.get('/quote/IE00B4L5Y983').status_code == 200
    item = client.get('/instruments').json()[0]
    path = f"/instruments/by-id/{item['listing_id']}/details"
    assert client.patch(path, json={'risk-demo.score': {'value': 0}}).status_code == 200
    source = unwrap(build_chain('etf_meta', get_sources_config(), get_settings())[0])
    attempts = []

    def fail_construction(self, config):
        attempts.append(config)
        raise RuntimeError('Dienst beim Konstruktor nicht erreichbar')

    monkeypatch.setattr(type(source), '__init__', fail_construction)
    _profile(volume, chains)
    assert attempts
    assert client.get('/fields').json() == before
    during = client.get('/instruments').json()[0]['details']
    assert during['risk-demo.score']['value'] == 0
    assert during['risk-demo.score']['origin'] == 'manual'


def test_feldauskunft_funktioniert_mit_nur_lesender_verbindung(volume, client, monkeypatch):
    from app import repository

    _profile(volume, {'quotes': ['yaml-file'], 'etf_meta': ['risk-demo', 'yaml-file']})
    before = client.get('/fields').json()
    connect = repository.get_connection

    def read_only(path):
        connection = connect(path)
        connection.execute('PRAGMA query_only=ON')
        return connection

    monkeypatch.setattr(repository, 'get_connection', read_only)
    response = client.get('/fields')
    assert response.status_code == 200
    assert response.json() == before
