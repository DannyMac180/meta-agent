from datetime import datetime

from meta_agent.models.bundle_metadata import BundleMetadata, BUNDLE_SCHEMA_VERSION


def test_bundle_metadata_defaults():
    meta = BundleMetadata()
    assert meta.schema_version == BUNDLE_SCHEMA_VERSION
    assert isinstance(meta.created_at, datetime)
    assert meta.custom == {}


def test_bundle_metadata_custom_fields_preserved():
    data = {
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "meta_agent_version": "0.1.0",
        "foo": "bar",
        "custom": {"x": 1},
    }
    meta = BundleMetadata(**data)
    assert meta.meta_agent_version == "0.1.0"
    assert meta.custom == {"x": 1}
    assert getattr(meta, "foo") == "bar"
