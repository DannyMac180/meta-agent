from meta_agent.utils.config import load_config, save_config


def test_save_and_load_config(tmp_path):
    cfg = {"key": "value", "num": 1}
    file_path = tmp_path / "config.json"
    save_config(cfg, str(file_path))
    loaded = load_config(str(file_path))
    assert loaded == cfg


def test_load_invalid_config(tmp_path):
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("not valid json")
    loaded = load_config(str(bad_file))
    assert loaded == {}
