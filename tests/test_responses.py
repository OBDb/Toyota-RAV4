import glob
import os
import pytest
from pathlib import Path
from typing import Dict, Any

# These will be imported from the schemas repository
from schemas.python.can_frame import CANIDFormat
from schemas.python.json_formatter import format_file
from schemas.python.signals_testing import obd_testrunner

REPO_ROOT = Path(__file__).parent.parent.absolute()

TEST_CASES = [
    {
        "model_year": "2014",
        "signalset": "0000-2018.json",
        "tests": [
            # Tire pressures
            ("7582A10076130AAA9A8\n7582A21AC0000000000", {
                "RAV4_TP_FL": 2.4310344827586206,
                "RAV4_TP_FR": 2.413793103448276,
                "RAV4_TP_RL": 2.396551724137931,
                "RAV4_TP_RR": 2.4655172413793105,
                "RAV4_TP_SPARE": 0,
            }),

            # Fuel level volume
            ("7C803612947", {"RAV4_FLI_VOL": 35.5}),
            ("7C803612966", {"RAV4_FLI_VOL": 51}),

            # General stats
            ("7E810216151000005FE\n7E82101003D7D413E76\n7E822302D00001E8A04\n7E8234100008052918C\n7E82480C4806A000000", {
                "RAV4_PREV_TRIP_DST": 0.61,
                "RAV4_VVTOT": 125.0,
                "RAV4_EOT": 62,
            }),

            # Cruise control speeds
            ("7E80761210000008000", {"RAV4_CC_S": 0}),
            ("7E80761216F6F14FC00", {"RAV4_CC_S": 111.0}),

            # Transmission temperature (pan)
            ("7E80461822D00", {"RAV4_ATF_PAN_T": 5}),
            ("7E80461827800", {"RAV4_ATF_PAN_T": 80}),

            # Gear
            ("7E8056185010010", {"RAV4_GEAR": 1, "RAV4_GEAR_LOCKUP": 0}),
            ("7E8056185012010", {"RAV4_GEAR": 1, "RAV4_GEAR_LOCKUP": 0}),
            ("7E8056185012018", {"RAV4_GEAR": 1, "RAV4_GEAR_LOCKUP": 0}),
            ("7E8056185030010", {"RAV4_GEAR": 3, "RAV4_GEAR_LOCKUP": 0}),
            ("7E8056185040010", {"RAV4_GEAR": 4, "RAV4_GEAR_LOCKUP": 0}),
            ("7E8056185042018", {"RAV4_GEAR": 4, "RAV4_GEAR_LOCKUP": 0}),
            ("7E8056185050010", {"RAV4_GEAR": 5, "RAV4_GEAR_LOCKUP": 0}),
            ("7E8056185052018", {"RAV4_GEAR": 5, "RAV4_GEAR_LOCKUP": 0}),
            ("7E8056185060010", {"RAV4_GEAR": 6, "RAV4_GEAR_LOCKUP": 0}),
            ("7E8056185062018", {"RAV4_GEAR": 6, "RAV4_GEAR_LOCKUP": 0}),
            ("7E805618506A018", {"RAV4_GEAR": 6, "RAV4_GEAR_LOCKUP": 1}),

            # Tire speeds
            ("7B806610300000000", {
                "RAV4_TS_FR": 0,
                "RAV4_TS_FL": 0,
                "RAV4_TS_RR": 0,
                "RAV4_TS_RL": 0,
            }),
            ("7B806610365656464", {
                "RAV4_TS_FR": 129.28,
                "RAV4_TS_FL": 129.28,
                "RAV4_TS_RR": 128,
                "RAV4_TS_RL": 128,
            }),
        ]
    },
    {
        "model_year": "2021",
        "signalset": "default.json",
        "tests": [
            # Tire pressures
            ("7582A10076130ACAAA7\n7582A21AC0000000000", {
                "RAV4_TP_FL": 2.4655172413793105,
                "RAV4_TP_FR": 2.4310344827586206,
                "RAV4_TP_RL": 2.3793103448275863,
                "RAV4_TP_RR": 2.4655172413793105,
                "RAV4_TP_SPARE": 0,
            }),
        ]
    },
]

def load_signalset(filename: str) -> str:
    """Load a signalset JSON file from the standard location."""
    signalset_path = REPO_ROOT / "signalsets" / "v3" / filename
    with open(signalset_path) as f:
        return f.read()

@pytest.mark.parametrize(
    "test_group",
    TEST_CASES,
    ids=lambda test_case: f"MY{test_case['model_year']}"
)
def test_signals(test_group: Dict[str, Any]):
    """Test signal decoding against known responses."""
    signalset_json = load_signalset(test_group["signalset"])

    # Run each test case in the group
    for response_hex, expected_values in test_group["tests"]:
        try:
            obd_testrunner(
                signalset_json,
                response_hex,
                expected_values,
                can_id_format=CANIDFormat.ELEVEN_BIT,
                extended_addressing_enabled=response_hex.startswith('7582A')
            )
        except Exception as e:
            pytest.fail(
                f"Failed on response {response_hex} "
                f"(Model Year: {test_group['model_year']}, "
                f"Signalset: {test_group['signalset']}): {e}"
            )

def get_json_files():
    """Get all JSON files from the signalsets/v3 directory."""
    signalsets_path = os.path.join(REPO_ROOT, 'signalsets', 'v3')
    json_files = glob.glob(os.path.join(signalsets_path, '*.json'))
    # Convert full paths to relative filenames
    return [os.path.basename(f) for f in json_files]

@pytest.mark.parametrize("test_file",
    get_json_files(),
    ids=lambda x: x.split('.')[0].replace('-', '_')  # Create readable test IDs
)
def test_formatting(test_file):
    """Test signal set formatting for all vehicle models in signalsets/v3/."""
    signalset_path = os.path.join(REPO_ROOT, 'signalsets', 'v3', test_file)

    formatted = format_file(signalset_path)

    with open(signalset_path) as f:
        assert f.read() == formatted

if __name__ == '__main__':
    pytest.main([__file__])