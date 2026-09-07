"""T-26: Felddeklaration und generische Speicherung ohne Betriebsdatenbank."""

import pytest
from stockinfo_plugin import FieldSpec, MetadataSource, Unit

from app.details import definitions_for, merge_definitions


class SampleSource(MetadataSource):
    name = 'sample'
    SUPPORTED_TYPES = frozenset({'crypto', 'etf'})
    SUPPORTED_KINDS = frozenset({'listed', 'pair'})
    FIELDS = (FieldSpec('risk', kind='number', label_en='Risk', overridable=False),)


def test_unbekanntes_feld_hat_namespace_und_schreibrecht():
    definition = definitions_for(SampleSource())[0]
    assert definition.name == 'sample.risk'
    assert definition.overridable is False
    assert definition.applies('crypto', 'pair')


def test_fondsdaten_sind_nur_fuer_deklarierte_gattungen_anwendbar():
    class FundSource(SampleSource):
        FIELDS = (FieldSpec('provider', label_en='Provider', instrument_types=frozenset({'etf'})),)

    definition = definitions_for(FundSource())[0]
    assert definition.applies('etf', 'listed')
    assert not definition.applies('crypto', 'pair')


def test_widerspruechliche_kanonische_einheit_wird_abgelehnt():
    class InvalidSource(SampleSource):
        FIELDS = (FieldSpec('ter', kind='number', unit=Unit.ABSOLUTE, label_en='TER'),)

    with pytest.raises(ValueError):
        definitions_for(InvalidSource())


def test_schema_merge_behaelt_quellen_und_anwendbarkeit():
    first = definitions_for(SampleSource())
    assert merge_definitions([first, first])[0].sources == ['sample']


def test_persistenz_merge_und_kompatibilitaetsprojektion(tmp_path):
    from app.db import init_db
    from app.detail_models import DetailInput
    from app.repository import QuoteRepository
    from app.services.quote_cache import CachedQuoteService
    from tests.boundaries import empty_daily_sync
    from tests.test_quote_cache import FakeQuoteService, _now, _response

    path = str(tmp_path / 'details.db')
    init_db(path)
    repo = QuoteRepository(path)
    definitions = definitions_for(SampleSource())
    repo.detail_catalog(definitions)
    response = _response(_now())
    response.detail_readings = {'sample': {'sample.risk': {'value': 0}}}
    saved = repo.save_quote(response)
    service = CachedQuoteService(FakeQuoteService(response), repo, 6, empty_daily_sync(repo))
    row = service.get_instrument_summary(saved.instrument_id)
    assert row['details']['sample.risk']['value'] == 0
    assert row['details']['sample.risk']['source'] == 'sample'
    with pytest.raises(ValueError, match='bearbeitbar'):
        service.set_detail_overrides(row['listing_id'], {'sample.risk': DetailInput(value=4)})
    assert service.get_by_isin('IE00B3RBWM25').details['sample.risk'].value == 0


def test_katalogversion_steigt_nur_bei_schemawechsel(tmp_path):
    from app.db import init_db
    from app.repository import QuoteRepository

    path = str(tmp_path / 'schema.db')
    init_db(path)
    repo = QuoteRepository(path)
    definitions = definitions_for(SampleSource())
    _, first = repo.detail_catalog(definitions)
    assert repo.detail_catalog(definitions)[1] == first
    changed = [definition.model_copy(update={'label_de': 'Risiko'}) for definition in definitions]
    assert repo.detail_catalog(changed)[1] == first + 1
    assert repo.detail_catalog([])[1] == first + 2


def test_plausibilitaet_verwendet_die_deklarierte_einheit():
    from stockinfo_plugin import Reading
    from app.plugin_adapters import MetadataAdapter

    class RatioSource(SampleSource):
        FIELDS = (FieldSpec('ter', kind='number', unit=Unit.PERCENT, plausible=(0, 5)),)

        def handles(self, request):
            return True

        def fetch(self, request):
            return [Reading('ter', 20, unit=Unit.BASIS_POINTS, source=self.name)]

    result = MetadataAdapter(RatioSource(), 'XETR').fetch_etf('IE00B4L5Y983')
    assert result.detail_readings['sample']['ter']['value'] == 0.2
