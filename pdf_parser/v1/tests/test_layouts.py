from pdf_parser.v1.detector.layout_detector import LayoutDetector


def test_sbi_layout_detection():
    text = "STATE BANK OF INDIA"
    layout = LayoutDetector().detect(text)
    assert layout == "SBI_V1"
