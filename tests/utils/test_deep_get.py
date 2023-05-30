# Copyright (c) 2021-present Divinia, Inc.
"""Test deep_get function"""
from computing_toolbox.utils.deep_get import deep_get


class TestDeepGet:
    """Test DeepGet class"""
    data_dict = {
        "data": {
            "name":
            "Hotel1",
            "country":
            "US",
            "city":
            "NY",
            "locations": [{
                "central-park": [100, 100]
            }, {
                "statue-of-liberty": [200, 200, 200]
            }, None],
            "empty":
            None
        }
    }

    def test_deep_get_return_default_value(self):
        """Test all posibilities"""

        # get self.data_dict["data"]["empty"]
        assert deep_get(self.data_dict,
                        path=["data", "empty"],
                        default_value="EMPTY") == "EMPTY"

        # get self.data_dict["data"]["date"]
        assert deep_get(self.data_dict,
                        path=["data", "date"],
                        default_value="") == ""

        # get self.data_dict["data"]["locations"][0]["central-park"][2]
        assert deep_get(self.data_dict,
                        path=["data", "locations", 0, "central-park", 2],
                        default_value=0) == 0

        # get self.data_dict["data"]["locations"][2]["central-park"][0]
        assert deep_get(self.data_dict,
                        path=["data", "locations", 2, "central-park", 0],
                        default_value=0) == 0

        # get self.data_dict["data"]["locations"][2]["airport"][0]
        assert deep_get(self.data_dict,
                        path=["data", "location", 2, "airport", 0],
                        default_value=0) == 0

        # get self.data_dict["data"]["country"]["US"]["US"]
        assert deep_get(self.data_dict,
                        path=["data", "country", "US", "US"],
                        default_value="NA") == "NA"

        # get self.data_dict["data"]["location"][2]
        assert deep_get(self.data_dict,
                        path=["data", "location", 2],
                        default_value="NA") == "NA"

    def test_deep_get(self):
        """Test true values possibilities"""

        # get self.data_dict["data"]["name"]
        assert deep_get(self.data_dict,
                        path=["data", "name"],
                        default_value="") == "Hotel1"

        # get self.data_dict["data"]["locations"][0]["central-park"][1]
        assert deep_get(self.data_dict,
                        path=["data", "locations", 0, "central-park", 1],
                        default_value=0) == 100
