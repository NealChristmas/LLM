"""Semantic regressions; simulated report confirmations are not actual performance evidence."""
import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("capacity_sizing", ROOT / "scripts" / "sizing.py")
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)
client_spec = importlib.util.spec_from_file_location("capacity_client", ROOT / "scripts" / "client_report.py")
client = importlib.util.module_from_spec(client_spec)
client_spec.loader.exec_module(client)


class SizingTests(unittest.TestCase):
    def test_config_budget_uses_declared_counts_without_theory_file(self):
        d, missing = s.demand(json.loads((ROOT / 'examples/request.json').read_text(encoding='utf-8')))
        d['quant'] = 'W8A8C16'
        config = {'model_type': 'llama', 'num_parameters': 1000000000,
                  'num_active_parameters': 500000000, 'num_hidden_layers': 2,
                  'hidden_size': 128, 'num_attention_heads': 4, 'num_key_value_heads': 2,
                  'max_position_embeddings': 100000}
        item = {'config': config, 'modelName': d['model'], 'source': {'path': 'synthetic', 'sha256': 'demo'}}
        e = s.model_config_evidence(item, d, missing)
        self.assertEqual(e['derived']['weightTensorBytes'], 1000000000)
        self.assertEqual(e['derived']['linearFlopsPerToken'], 1000000000)
        self.assertEqual(e['derived']['standardKv']['bytesPerToken'], 512)
        del config['num_parameters']
        del config['num_active_parameters']
        e = s.model_config_evidence(item, d, missing)
        self.assertNotIn('weightTensorBytes', e['derived'])
        self.assertNotIn('linearFlopsPerToken', e['derived'])

    def test_theory_command_generates_results_and_rejects_pd_separation(self):
        original = s.read_json(ROOT / 'examples/theory.json')['inputs']
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'generated.json'
            cmd = [sys.executable, str(ROOT / 'scripts/sizing.py'), 'theory-calculate']
            keys = ['total', 'active', 'parallel', 'bytes', 'cache', 'cacheLength', 'memory', 'usable',
                    'peak', 'prefillEfficiency', 'decodeEfficiency', 'timeBudget', 'group', 'slots',
                    'concurrency', 'input', 'output', 'ttft', 'tpot', 'growth', 'weightExtra', 'runtime',
                    'spare', 'model', 'server', 'quant', 'kv', 'cachePrecision']
            for key in keys:
                cmd += ['--' + key, str(original[key])]
            cmd += ['--basis', 'synthetic unit-test assumptions, not measured', '--out', str(output), '--config-form']
            result = subprocess.run(cmd + ['shared'], capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(result.returncode, 0, result.stderr)
            generated = s.read_json(output)
            self.assertEqual(generated['results'], s.theory_compute(original))
            self.assertTrue(generated['basis'])
            before = output.read_bytes()
            blocked = subprocess.run(cmd + ['PD分离'], capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(blocked.returncode, 2)
            self.assertEqual(before, output.read_bytes())

    def setUp(self):
        self.raw = json.loads((ROOT / "examples" / "baselines.json").read_text(encoding="utf-8"))[0]
        self.request = json.loads((ROOT / "examples" / "request.json").read_text(encoding="utf-8"))
        self.meta = s.meta_defaults() | dict(ttftStat="p95", tpotStat="p95", load="closed", kBase="1024",
                                           lengthStat="fixed", reasoning="included", verified=True,
                                           source="模拟单元测试依据，非实际验收")
        self.record = dict(key=s.record_key(self.raw), raw=self.raw, meta=self.meta, source={"path": "test", "sha256": "test"})

    def evaluate(self, **changes):
        d, missing = s.demand(self.request | changes)
        self.assertFalse(missing)
        return s.evaluate(self.record, d)

    def test_unknown_is_not_p95(self):
        self.record["meta"] = s.meta_defaults()
        self.assertEqual(self.evaluate()["state"], "pending")
        self.assertIsNone(self.evaluate()["result"])

    def test_exact_rounding_growth_and_spare(self):
        self.assertEqual(self.evaluate()["result"]["totalCards"], 32)
        self.assertEqual(self.evaluate(concurrency=64)["result"]["totalCards"], 16)
        self.assertEqual(self.evaluate(concurrency=65)["result"]["totalCards"], 32)
        self.assertEqual(self.evaluate(growth=50, spare=1)["result"]["totalCards"], 64)

    def test_latency_failure_cannot_be_fixed_by_copying(self):
        e = self.evaluate(ttft=2000, concurrency=1000)
        self.assertEqual(e["state"], "failed")
        self.assertIsNone(e["result"])

    def test_no_cross_model_or_statistics(self):
        self.assertEqual(self.evaluate(model="DeepSeek-V4-Flash")["state"], "reference")
        self.assertEqual(self.evaluate(ttftStat="mean")["state"], "reference")

    def test_optional_config_not_fabricated(self):
        e = self.evaluate(chip="", quant="", framework="", form="", cpu="")
        self.assertEqual(e["state"], "measured_match")
        self.assertEqual(e["baseline"]["cards"], 16)

    def test_near_does_not_inflate_capacity(self):
        d, _ = s.demand(self.request | {"input": 8192})
        e = s.evaluate(self.record, d)
        self.assertEqual(e["state"], "near_reference")
        self.assertIsNone(e["result"])
        self.assertEqual(s.evaluate(self.record, d, True)["result"]["totalCards"], 32)
        self.assertIsNone(self.evaluate(input=32768)["result"])

    def test_k_and_prefix_mismatch(self):
        self.meta["kBase"] = "1000"
        self.assertEqual(self.evaluate()["state"], "reference")
        self.meta["kBase"] = "1024"
        self.assertEqual(self.evaluate(prefix=20)["state"], "reference")

    def test_rate_needs_real_qps(self):
        self.assertEqual(self.evaluate(rate=10)["state"], "pending")
        self.meta["qps"] = "3"
        self.assertEqual(self.evaluate(rate=10)["result"]["totalCards"], 64)

    def test_conflicting_fields_block(self):
        self.raw["keyConcurrency"] = "32"
        self.assertEqual(self.evaluate()["state"], "pending")

    def test_request_missing_not_guessed(self):
        _, missing = s.demand(s.request_template())
        self.assertIn("ttftStat", missing)
        with self.assertRaises(ValueError):
            s.demand(self.request | {"concurrency": 1.5})

    def test_prepare_transactional(self):
        with tempfile.TemporaryDirectory() as tmp:
            p, out = Path(tmp) / "input.json", Path(tmp) / "library.json"
            out.write_text("unchanged", encoding="utf-8")
            s.write_json(p, [self.raw, {"modelName": "bad"}])
            with self.assertRaises(ValueError):
                s.prepare(SimpleNamespace(baselines=[str(p)], annotations=None, theory=None, out=str(out)))
            self.assertEqual(out.read_text(), "unchanged")

    def test_prepare_wrapper_and_reimport_resets_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            p1, p2, out = [Path(tmp) / x for x in ("a.json", "b.json", "library.json")]
            s.write_json(p1, {"type": "baseline-sizing-project", "records": [self.record]})
            s.write_json(p2, {"data": {"records": [self.raw]}})
            s.prepare(SimpleNamespace(baselines=[str(p1), str(p2)], annotations=None, theory=None, out=str(out)))
            lib = s.read_json(out)
            self.assertEqual(len(lib["records"]), 1)
            self.assertFalse(lib["records"][0]["meta"]["verified"])

    def test_theory_recompute_and_integer_assignment(self):
        raw = s.read_json(ROOT / "examples" / "theory.json")
        self.assertEqual(s.theory_compute(raw["inputs"])["cards"], 16)
        self.assertEqual(s.theory_compute(raw["inputs"] | {"concurrency": 27})["cards"], 24)

    def test_theory_is_separate_and_detects_inconsistency(self):
        raw = s.read_json(ROOT / "examples" / "theory.json")
        d, _ = s.demand(self.request)
        e = s.theory_evidence({"source": {"path": "test"}, "raw": raw}, d, [])
        self.assertEqual(e["state"], "reference")
        self.assertNotIn("candidate", e)
        raw["results"]["cards"] = 999
        self.assertEqual(s.theory_evidence({"source": {}, "raw": raw}, d, [])["state"], "inconsistent")

    def test_theory_only_requires_matching_assumptions(self):
        raw = s.read_json(ROOT / "examples" / "theory.json")
        v = raw["inputs"]
        request = self.request | {"model": v["model"], "input": v["input"], "output": v["output"],
                                  "concurrency": 20, "ttft": v["ttft"], "tpot": v["tpot"],
                                  "chip": "", "cpu": "", "framework": "", "form": "", "quant": "",
                                  "lengthStat": "max", "load": "burst"}
        lib = {"type": "capacity-evidence-library", "version": s.VERSION, "records": [],
               "theories": [{"source": {"path": "test", "sha256": "test"}, "raw": raw}]}
        report = s.assess(lib, request)
        self.assertEqual(report["evidenceLevel"], "theory_only")
        self.assertIsNone(report["selected"])
        self.assertEqual(report["theoryEvidence"][0]["candidate"]["totalCards"], 16)

    def test_malformed_theory_is_reference_not_process_failure(self):
        raw = s.read_json(ROOT / "examples" / "theory.json")
        raw["inputs"] = []
        d, _ = s.demand(self.request)
        self.assertEqual(s.theory_evidence({"source": {}, "raw": raw}, d, [])["state"], "unusable")

    def test_missing_request_still_produces_report(self):
        library = {"type": "capacity-evidence-library", "version": s.VERSION, "records": [self.record], "theories": []}
        report = s.assess(library, s.request_template())
        self.assertEqual(report["evidenceLevel"], "insufficient")
        self.assertTrue(report["missingRequirements"])
        self.assertIn("补齐用户规格", s.markdown(report))

    def test_report_basis_is_traceable_and_includes_numeric_qps(self):
        self.meta["qps"] = "3"
        library = {"type": "capacity-evidence-library", "version": s.VERSION, "records": [self.record], "theories": []}
        r = s.assess(library, self.request | {"rate": 10})
        evidence = r["calculationBasis"]["measuredEvidence"][0]
        self.assertEqual(evidence["rawHash"], s.digest(self.raw))
        self.assertEqual(evidence["source"]["path"], "test")
        md = s.markdown(r)
        self.assertIn("## 测算依据", md)
        self.assertIn("3886.1 ms / p95", md)
        self.assertIn("速率组数 = ceil(10.0 / 3)", md)

    def test_report_keeps_unused_theory_assumptions(self):
        raw = s.read_json(ROOT / "examples" / "theory.json")
        library = {"type": "capacity-evidence-library", "version": s.VERSION, "records": [],
                   "theories": [{"source": {"path": "test", "sha256": "test"}, "raw": raw}]}
        md = s.markdown(s.assess(library, self.request))
        self.assertIn("原公式版本：1.1.0", md)
        self.assertIn("缓存", md)
        self.assertIn("prefillEfficiency=30", md)

    def config_item(self, **changes):
        config = {"model_type": "llama", "max_position_embeddings": 32768,
                  "num_hidden_layers": 32, "hidden_size": 4096, "num_attention_heads": 32,
                  "num_key_value_heads": 8, "head_dim": 128} | changes
        return {"modelName": self.request["model"], "revision": "unit-test-fixture-not-real-config",
                "source": {"path": "unit-test-config", "sha256": "test"}, "config": config}

    def library_with_config(self, config):
        return {"type": "capacity-evidence-library", "version": s.VERSION, "records": [self.record],
                "theories": [], "modelConfigs": [config]}

    def test_standard_config_kv_and_provenance(self):
        item = self.config_item()
        report = s.assess(self.library_with_config(item), self.request)
        e = report["modelConfigEvidence"][0]
        self.assertEqual(report["selected"]["result"]["totalCards"], 32)
        self.assertEqual(e["derived"]["standardKv"]["bytesPerToken"], 131072)
        self.assertTrue(e["checks"]["context"]["withinDeclaredLimit"])
        self.assertIn("## 模型配置依据", s.markdown(report))
        self.assertIn("unit-test-config", s.markdown(report))

    def test_context_conflict_pauses_candidate(self):
        r = s.assess(self.library_with_config(self.config_item(max_position_embeddings=16384)), self.request)
        self.assertIsNone(r["selected"])
        self.assertEqual(r["evaluations"][0]["state"], "config_conflict")
        self.assertEqual(r["modelConfigEvidence"][0]["state"], "context_conflict")

    def test_unbound_or_wrong_model_config_does_not_block(self):
        for name in ("", "another-model"):
            item = self.config_item(max_position_embeddings=1024)
            item["modelName"] = name
            r = s.assess(self.library_with_config(item), self.request)
            self.assertEqual(r["selected"]["result"]["totalCards"], 32)
            self.assertEqual(r["modelConfigEvidence"][0]["state"], "reference")

    def test_compressed_window_and_unknown_kv_not_guessed(self):
        d, _ = s.demand(self.request)
        for changes in ({"compress_ratios": [0, 4, 128]}, {"kv_lora_rank": 512},
                        {"sliding_window": 128}, {"model_type": "unknown"}):
            e = s.model_config_evidence(self.config_item(**changes), d, [])
            self.assertNotIn("standardKv", e["derived"])
        d["quant"] = ""
        e = s.model_config_evidence(self.config_item(torch_dtype="float16"), d, [])
        self.assertNotIn("standardKv", e["derived"])

    def test_multiple_revisions_require_selection(self):
        first, second = self.config_item(), self.config_item(max_position_embeddings=65536)
        lib = self.library_with_config(first)
        lib["modelConfigs"].append(second)
        self.assertIsNone(s.assess(lib, self.request)["selected"])
        r = s.assess(lib, self.request | {"modelConfigHash": s.digest(first["config"])})
        self.assertEqual(r["selected"]["result"]["totalCards"], 32)

    def test_config_import_keeps_identity_and_optional_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            s.write_json(path, {"model_type": "unknown"})
            item = s.import_model_config(path)
            self.assertEqual(item["modelName"], "")
            self.assertEqual(len(item["source"]["sha256"]), 64)
            out = Path(tmp) / "library.json"
            summary = s.prepare(SimpleNamespace(baselines=None, theory=None, annotations=None,
                                               model_config=[str(path)], config_model="demo", config_revision="r1", out=str(out)))
            self.assertEqual(summary["modelConfigs"], 1)
            self.assertEqual(s.read_json(out)["modelConfigs"][0]["revision"], "r1")

    def test_customer_report_same_numbers_and_offline_diagrams(self):
        lib = {"type": "capacity-evidence-library", "version": s.VERSION, "records": [self.record], "theories": []}
        r = s.assess(lib, self.request | {"growth": 20, "spare": 1})
        self.assertEqual(r["selected"]["result"]["totalCards"], 48)
        md, html = client.client_markdown(r), client.client_html(r)
        self.assertIn("32张工作卡+16张备用卡=48张", "".join(md.split()))
        self.assertIn("120÷64", "".join(md.split()))
        self.assertIn("```mermaid", md)
        self.assertIn("<svg", html)
        self.assertNotIn("<script src=", html)
        self.assertIn(">48 张<", html)

    def test_customer_report_safe_and_no_internal_paths(self):
        self.record["source"] = {"path": r"C:\private\internal\baseline.json", "sha256": "test"}
        self.meta["source"] = '<img src=x onerror="alert(1)">'
        lib = {"type": "capacity-evidence-library", "version": s.VERSION, "records": [self.record], "theories": []}
        r = s.assess(lib, self.request | {"project": "<script>alert(1)</script>"})
        h = client.client_html(r)
        self.assertNotIn('<img src=x', h)
        self.assertNotIn('<script>alert(1)</script>', h)
        self.assertNotIn(r'C:\private', h)
        self.assertIn('baseline.json', h)

    def test_customer_incomplete_report_does_not_invent_zero_cards(self):
        self.record["meta"] = s.meta_defaults()
        lib = {"type": "capacity-evidence-library", "version": s.VERSION, "records": [self.record], "theories": []}
        r = s.assess(lib, self.request)
        md = client.client_markdown(r)
        self.assertIn("当前不能给出", md)
        self.assertNotIn("|合计|0", md)
        self.assertNotIn("|合计|32", md)

    def test_customer_simulation_and_near_not_presented_as_measured(self):
        self.raw["id"] = "DEMO-001"
        self.record["key"] = s.record_key(self.raw)
        self.raw["tuningStatus"] = "合成夹具，非实测"
        lib = {"type": "capacity-evidence-library", "version": s.VERSION, "records": [self.record], "theories": []}
        r = s.assess(lib, self.request | {"input": 8192}, True)
        md = client.client_markdown(r)
        self.assertIn("仅流程演示", md)
        self.assertIn("存在差异，按保守近似处理", md)

    def test_three_stage_flow_does_not_fabricate_theory(self):
        lib = {"type": "capacity-evidence-library", "version": "1.2.0", "records": [self.record], "theories": []}
        r = s.assess(lib, self.request | {"growth": 20, "spare": 1})
        w = r["workflow"]
        self.assertEqual(w["order"], ["theory", "baseline", "integration"])
        self.assertEqual(w["theory"]["status"], "incomplete")
        self.assertEqual(w["integration"]["status"], "baseline_only")
        self.assertEqual(w["integration"]["provisionalCards"], 48)
        self.assertIsNone(w["integration"]["finalCards"])
        doc = client.document(r)
        titles = [x["title"] for x in doc["sections"]]
        self.assertTrue(titles[2].startswith("第一步"))
        self.assertTrue(titles[3].startswith("第二步"))
        self.assertTrue(titles[4].startswith("第三步"))
        self.assertFalse(any(x["deep"] for x in doc["sections"][:5]))
        html = client.client_html(r)
        self.assertIn("理论卡数：暂不能确定", html)
        self.assertIn("理论校核待完成", html)

    def test_theory_runs_before_baseline_and_integration_does_not_average(self):
        from unittest.mock import patch
        lib = {"type": "capacity-evidence-library", "version": s.VERSION, "records": [self.record], "theories": [{}]}
        theory = {"candidate": {"totalCards": 64, "workCards": 48, "spareCards": 16}, "source": {"path": "toy.json"}}
        calls = []
        original = s.evaluate
        def baseline(*args):
            calls.append("baseline")
            return original(*args)
        def theoretical(*args):
            calls.append("theory")
            return theory
        with patch.object(s, "theory_evidence", theoretical), patch.object(s, "evaluate", baseline):
            r = s.assess(lib, self.request | {"growth": 20, "spare": 1})
        self.assertEqual(calls, ["theory", "baseline"])
        i = r["workflow"]["integration"]
        self.assertEqual(i["status"], "review_required")
        self.assertEqual(i["comparison"][0]["theoryMinusBaseline"], 16)
        self.assertEqual(i["provisionalCards"], 48)
        self.assertIsNone(i["finalCards"])

    def test_customer_revision_removes_zero_branch_and_labels_simulation(self):
        self.record["key"] = "id:DEMO-001"
        lib = {"type": "capacity-evidence-library", "version": s.VERSION, "records": [self.record], "theories": []}
        r = s.assess(lib, self.request | {"growth": 20, "spare": 1})
        html = client.client_html(r)
        self.assertIn('整体计算模型与总公式', html)
        self.assertIn('候选总卡数＝（工作组数＋备用组数）×每组卡数', html)
        self.assertIn('理论工作组数＝向上取整', html)
        self.assertIn('<mfrac>', html)
        self.assertIn('２×每词元激活参数量', html)
        overview = client.document(r)['sections'][0]
        equations = ''.join(b[1] for b in overview['blocks'] if b[0] == 'formula')
        self.assertNotIn('10¹²', equations)
        self.assertNotIn('1024', equations)
        self.assertNotIn('Pa', equations)
        self.assertIn('>48 张<', html)
        self.assertNotIn('本次基线代入', html)
        self.assertNotIn('最大值［2；0］', html)
        self.assertIn('模拟基线记录 id:DEMO-001', html)
        self.assertNotIn('实测记录 id:DEMO-001', html)

    def test_formula_layers_keep_large_dimensions_before_details(self):
        lib = {"type": "capacity-evidence-library", "version": s.VERSION, "records": [self.record], "theories": []}
        r = s.assess(lib, self.request)
        overview = client.document(r)["sections"][0]
        root = next(b[1] for b in overview["blocks"] if b[0] == "onion")
        self.assertEqual(len(root["formulas"]), 1)
        self.assertNotIn("权重", root["formulas"][0])
        second = root["child"]
        self.assertTrue(second["title"].startswith("第二层"))
        self.assertTrue(second["child"]["title"].startswith("第三层"))
        self.assertNotIn("child", second["child"])
        html = client.onion_html(root)
        self.assertEqual(html.count('<details class="formula-layer">'), 2)
        self.assertNotIn('<details class="formula-layer" open', html)

    def test_standard_import_preserves_confirmed_unknown_and_old_library(self):
        schema = s.read_json(ROOT / "schemas/baseline-import-v1.schema.json")
        bundle = s.read_json(ROOT / "examples/baselines.standard-v1.json")
        s.validate_import_schema(bundle, schema)
        item = bundle["records"][0]
        s.validate_standard_conditions(item["raw"], item["meta"])
        self.assertEqual(item["meta"]["ttftStat"], "mean")
        self.assertEqual(item["meta"]["load"], "unknown")
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "lib.json"
            s.prepare(SimpleNamespace(baselines=[str(ROOT / "examples/baselines.standard-v1.json")], annotations=None,
                                     theory=None, model_config=None, out=str(out)))
            lib = s.read_json(out)
            self.assertEqual(lib["records"][0]["inputSchema"], "llm-capacity-baselines/1.0")
            self.assertFalse(lib["records"][0]["meta"]["verified"])
            self.assertIsNone(s.assess(lib, self.request)["selected"])
        old = {"type": "capacity-evidence-library", "version": "1.3.0", "records": [self.record], "theories": []}
        self.assertEqual(s.assess(old, self.request)["selected"]["result"]["totalCards"], 32)

    def test_standard_schema_rejects_typos_types_units_and_unknown_versions(self):
        original = s.read_json(ROOT / "examples/baselines.standard-v1.json")
        schema = s.read_json(ROOT / "schemas/baseline-import-v1.schema.json")
        cases = []
        def changed(mutator):
            copy_bundle = copy.deepcopy(original)
            mutator(copy_bundle)
            cases.append(copy_bundle)
        changed(lambda b: b.update(schemaVersion="99"))
        changed(lambda b: b["records"][0]["meta"].update(ttftStat="P95"))
        changed(lambda b: b["records"][0]["meta"].update(qps="110.1"))
        changed(lambda b: b["records"][0]["meta"].update(ttftStats="mean"))
        changed(lambda b: b["records"][0]["raw"]["deployConfig"].update({"部署卡数": "16"}))
        changed(lambda b: b["records"][0]["raw"]["perfData"].update({"Prefix Cache命中率": 101}))
        changed(lambda b: b["records"][0]["meta"].pop("load"))
        for bundle in cases:
            with self.assertRaises(ValueError):
                s.validate_import_schema(bundle, schema)

    def test_card_scope_blocks_standard_candidate_and_detects_conflicts(self):
        d, _ = s.demand(self.request)
        record = copy.deepcopy(self.record)
        record["inputSchema"] = "llm-capacity-baselines/1.0"
        record["meta"].update(cardCountScope="unknown")
        self.assertIsNone(s.evaluate(record, d)["result"])
        record["meta"]["cardCountScope"] = "total"
        self.assertEqual(s.evaluate(record, d)["result"]["totalCards"], 32)
        record["meta"].update(prefillCards=16, decodeCards=16)
        self.assertIsNone(s.evaluate(record, d)["result"])
        item = s.read_json(ROOT / "examples/baselines.standard-v1.json")["records"][0]
        item["meta"].update(prefillCards=16, decodeCards=16)
        with self.assertRaises(ValueError):
            s.validate_standard_conditions(item["raw"], item["meta"])


if __name__ == "__main__":
    unittest.main()
