from logging.handlers import RotatingFileHandler

from meta_agent.utils.logging import setup_logging


def test_setup_logging_stream(capfd):
    logger = setup_logging(name="test_logger", level="DEBUG")
    logger.debug("stream message")
    captured = capfd.readouterr()
    assert "stream message" in captured.out


def test_setup_logging_file(tmp_path):
    log_file = tmp_path / "test.log"
    logger = setup_logging(name="file_logger", level="INFO", log_file=str(log_file))
    logger.info("file message")
    assert log_file.exists()
    content = log_file.read_text()
    assert "file message" in content


def test_setup_logging_rotation(tmp_path):
    log_file = tmp_path / "rotate.log"
    logger = setup_logging(
        name="rotate_logger",
        level="INFO",
        log_file=str(log_file),
        max_bytes=10,
        backup_count=1,
    )
    assert isinstance(logger.handlers[0], RotatingFileHandler)
    logger.info("rotated message")
    assert log_file.exists()
    assert log_file.read_text()
