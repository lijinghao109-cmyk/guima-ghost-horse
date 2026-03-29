"""工具定义 schema 校验。"""

import unittest

from aim.tools import ALL_TOOLS


class TestToolDefinitions(unittest.TestCase):
    """验证所有工具定义的结构完整性。"""

    def test_tool_count(self):
        """Phase 2.5 应有 29 个工具（23 Ableton + 6 分析）。"""
        self.assertEqual(len(ALL_TOOLS), 29)

    def test_no_duplicate_names(self):
        """工具名不能重复。"""
        names = [t["name"] for t in ALL_TOOLS]
        self.assertEqual(len(names), len(set(names)), f"重复工具名: {[n for n in names if names.count(n) > 1]}")

    def test_required_fields(self):
        """每个工具必须有 name, description, input_schema。"""
        for tool in ALL_TOOLS:
            with self.subTest(tool=tool.get("name", "UNNAMED")):
                self.assertIn("name", tool)
                self.assertIn("description", tool)
                self.assertIn("input_schema", tool)
                self.assertIsInstance(tool["name"], str)
                self.assertIsInstance(tool["description"], str)
                self.assertIsInstance(tool["input_schema"], dict)

    def test_input_schema_structure(self):
        """input_schema 必须是 type=object 的 JSON Schema。"""
        for tool in ALL_TOOLS:
            with self.subTest(tool=tool["name"]):
                schema = tool["input_schema"]
                self.assertEqual(schema.get("type"), "object")
                self.assertIn("properties", schema)

    def test_required_subset_of_properties(self):
        """required 中的字段必须在 properties 中定义。"""
        for tool in ALL_TOOLS:
            with self.subTest(tool=tool["name"]):
                schema = tool["input_schema"]
                required = schema.get("required", [])
                properties = schema.get("properties", {})
                for field in required:
                    self.assertIn(field, properties, f"{tool['name']}: required 字段 '{field}' 不在 properties 中")


if __name__ == "__main__":
    unittest.main()
