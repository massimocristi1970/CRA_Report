import io
import unittest

import pandas as pd

import app


class FakeUpload(io.BytesIO):
    def __init__(self, content: bytes, name: str):
        super().__init__(content)
        self.name = name


class AppHelpersTests(unittest.TestCase):
    def test_extract_status_code_ignores_untagged_titles(self):
        df = pd.DataFrame({"Status_Title": ["AMiss", "Mr", "VMr"]})

        result = app.extract_status_code(df)

        self.assertEqual(result["Status_Code"].tolist(), ["A", "", "V"])
        self.assertEqual(result["Title"].tolist(), ["Miss", "Mr", "Mr"])

    def test_filter_dataframe_returns_empty_result_for_invalid_regex(self):
        df = pd.DataFrame(
            {
                "Account_ID": ["100"],
                "Status_Code": ["A"],
                "First_Name": ["Sarah"],
                "Last_Name": ["Lawrence"],
                "Postcode_1": ["SS2"],
                "Postcode_2": ["6EB"],
            }
        )

        result = app.filter_dataframe(
            df,
            {
                "search_column": "First_Name",
                "search_value": "(",
                "regex_mode": True,
            },
        )

        self.assertTrue(result.empty)

    def test_normalize_match_keys_removes_blanks(self):
        series = pd.Series([" 123 ", "", None, "456 "])

        result = app.normalize_match_keys(series)

        self.assertEqual(result.tolist(), ["123", "456"])

    def test_load_match_file_reads_csv(self):
        uploaded = FakeUpload(b"Account_ID\n100\n101\n", "match.csv")

        df, error = app.load_match_file(uploaded)

        self.assertIsNone(error)
        self.assertEqual(df["Account_ID"].tolist(), [100, 101])

    def test_parse_text_content_keeps_trailing_fields_stable_with_extra_address_tokens(self):
        text = (
            "864652 2.24062E+32 0 0 0 0 AMiss Sarah Lawrence 70 VICTORIA AVENUE"
            " SOUTHEND-ON-SEA SS2 6EB 19051979 0 0000000M\n"
        )

        df = app.parse_text_content(text)

        self.assertEqual(df.loc[0, "Account_ID"], "864652")
        self.assertEqual(df.loc[0, "Status_Title"], "AMiss")
        self.assertEqual(df.loc[0, "Postcode_1"], "SS2")
        self.assertEqual(df.loc[0, "Postcode_2"], "6EB")
        self.assertEqual(df.loc[0, "Date_Field"], "19051979")
        self.assertEqual(df.loc[0, "Column_17"], "0")
        self.assertEqual(df.loc[0, "Column_18"], "0000000M")

    def test_parse_text_content_splits_postcode_date_token_when_separator_is_missing(self):
        text = (
            "864652 2.24062E+32 0 0 0 0 AMiss Sarah Lawrence 70 VICTORIA"
            " SOUTHEND-ON-SEA SS2 6EB19051979 0 0000000M\n"
        )

        df = app.parse_text_content(text)

        self.assertEqual(df.loc[0, "Postcode_1"], "SS2")
        self.assertEqual(df.loc[0, "Postcode_2"], "6EB")
        self.assertEqual(df.loc[0, "Date_Field"], "19051979")


if __name__ == "__main__":
    unittest.main()
