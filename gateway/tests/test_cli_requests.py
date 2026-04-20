from __future__ import annotations

import argparse
import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

GATEWAY_ROOT = Path(__file__).resolve().parents[1]


def load_script_module(script_name: str):
    module_name = f"test_{script_name.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, GATEWAY_ROOT / f"{script_name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class SearchCliTests(unittest.TestCase):
    def test_search_main_reuses_request_payload_for_service(self) -> None:
        module = load_script_module("lkb_search")
        args = argparse.Namespace(
            target="both",
            query="passive linear optics",
            folder=None,
            endnote_library=None,
            limit=3,
            mode="semantic",
            years=None,
            show_config=False,
            explain=False,
            profile="balanced",
            auto_refresh=False,
            refresh_now=False,
            json=True,
            no_service=False,
        )
        expected = module.build_request(args)

        with (
            patch.object(module, "parse_args", return_value=args),
            patch.object(module, "load_config", return_value={}),
            patch.object(module, "request_json", return_value={"query": args.query, "hits": []}) as request_json,
            patch("builtins.print"),
        ):
            exit_code = module.main()

        self.assertEqual(exit_code, 0)
        request_json.assert_called_once_with({}, "/search", payload=expected.to_payload())


class AskCliTests(unittest.TestCase):
    def test_ask_main_uses_typed_request_for_local_execution(self) -> None:
        module = load_script_module("lkb_ask")
        args = argparse.Namespace(
            question="What is passive linear optics?",
            target="both",
            profile="fast",
            folder=None,
            endnote_library=None,
            years=None,
            json=True,
            mode="semantic",
            limit=4,
            auto_refresh=False,
            refresh_now=False,
            no_service=True,
        )
        expected = module.build_request(args)
        search_payload = {
            "query": expected.query,
            "target": expected.target,
            "profile": expected.profile,
            "mode": expected.mode,
            "hits": [],
            "total_hits": 0,
            "debug": {"effective_mode": expected.mode},
        }

        with (
            patch.object(module, "parse_args", return_value=args),
            patch.object(module, "load_config", return_value={}),
            patch.object(module, "search_local", return_value=search_payload) as search_local,
            patch.object(module, "build_answer_payload", return_value={"answer_markdown": "answer"}) as build_answer_payload,
            patch("builtins.print"),
        ):
            exit_code = module.main()

        self.assertEqual(exit_code, 0)
        search_local.assert_called_once_with({}, expected)
        build_answer_payload.assert_called_once_with(expected.question, search_payload)

    def test_ask_main_reuses_request_payload_for_service(self) -> None:
        module = load_script_module("lkb_ask")
        args = argparse.Namespace(
            question="What is passive linear optics?",
            target="both",
            profile="fast",
            folder=None,
            endnote_library=None,
            years=None,
            json=True,
            mode="lexical",
            limit=4,
            auto_refresh=False,
            refresh_now=False,
            no_service=False,
        )
        expected = module.build_request(args)

        with (
            patch.object(module, "parse_args", return_value=args),
            patch.object(module, "load_config", return_value={}),
            patch.object(module, "request_json", return_value={"answer_markdown": "answer"}) as request_json,
            patch("builtins.print"),
        ):
            exit_code = module.main()

        self.assertEqual(exit_code, 0)
        request_json.assert_called_once_with({}, "/ask", payload=expected.to_payload())
        payload = request_json.call_args.kwargs["payload"]
        self.assertEqual(payload["question"], args.question)
        self.assertEqual(payload["query"], args.question)
        self.assertEqual(payload["mode"], "lexical")


class ReportCliTests(unittest.TestCase):
    def test_report_main_uses_typed_request_for_local_execution(self) -> None:
        module = load_script_module("lkb_report")
        args = argparse.Namespace(
            query="passive linear optics",
            target="both",
            years=None,
            limit=5,
            folder=None,
            endnote_library=None,
            mode="semantic",
            read_top=2,
            profile="balanced",
            auto_refresh=False,
            refresh_now=False,
            json=True,
            no_service=True,
        )
        expected = module.build_request(args)
        search_payload = {
            "query": expected.query,
            "target": expected.target,
            "profile": expected.profile,
            "mode": expected.mode,
            "hits": [],
            "total_hits": 0,
            "debug": {"effective_mode": expected.mode},
        }

        with (
            patch.object(module, "parse_args", return_value=args),
            patch.object(module, "load_config", return_value={}),
            patch.object(module, "search_local", return_value=search_payload) as search_local,
            patch.object(module, "build_report_payload", return_value={"report_markdown": "report"}) as build_report_payload,
            patch("builtins.print"),
        ):
            exit_code = module.main()

        self.assertEqual(exit_code, 0)
        search_local.assert_called_once_with({}, expected)
        build_report_payload.assert_called_once_with(expected.query, search_payload, expected.read_top)

    def test_report_main_reuses_request_payload_for_service(self) -> None:
        module = load_script_module("lkb_report")
        args = argparse.Namespace(
            query="passive linear optics",
            target="both",
            years=None,
            limit=5,
            folder=None,
            endnote_library=None,
            mode="lexical",
            read_top=2,
            profile="balanced",
            auto_refresh=False,
            refresh_now=False,
            json=True,
            no_service=False,
        )
        expected = module.build_request(args)

        with (
            patch.object(module, "parse_args", return_value=args),
            patch.object(module, "load_config", return_value={}),
            patch.object(module, "request_json", return_value={"report_markdown": "report"}) as request_json,
            patch("builtins.print"),
        ):
            exit_code = module.main()

        self.assertEqual(exit_code, 0)
        request_json.assert_called_once_with({}, "/report", payload=expected.to_payload())
        payload = request_json.call_args.kwargs["payload"]
        self.assertEqual(payload["mode"], "lexical")
        self.assertEqual(payload["read_top"], 2)


if __name__ == "__main__":
    unittest.main()
