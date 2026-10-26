"""CPU AST-only tests. Input functions are never compiled, imported, or executed."""
import unittest
from alpha_diagnostic import compare

BASE="""def order_tasks(tasks, dependencies):
    seen = set()
    ordered = []
    for item in tasks:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return {"order": ordered, "blocked": [], "missing": []}
"""

class AlphaDiagnostic(unittest.TestCase):
    def label(self,a,b):return compare(a,b)["classification"]
    def test_three_renames(self):
        renamed=BASE.replace("seen","visited").replace("ordered","output").replace("item","task")
        self.assertEqual(self.label(BASE,renamed),"ALPHA_ONLY_MATCH")
        self.assertNotEqual(compare(BASE,renamed)["left_sha256"],compare(BASE,renamed)["right_sha256"])
    def test_operator_literal_and_free_call_preserved(self):
        a="def order_tasks(tasks, dependencies):\n    value = len(tasks) + 1\n    return value\n"
        for b in (a.replace("+","-"),a.replace("+ 1","+ 2"),a.replace("len(","sum(")):
            self.assertEqual(self.label(a,b),"DIFFERENT")
    def test_public_arg_not_renamed(self):
        self.assertEqual(self.label(BASE,BASE.replace("(tasks,","(jobs,").replace("in tasks:","in jobs:")),"UNKNOWN")
    def test_free_names_are_not_local_names(self):
        a="def order_tasks(tasks, dependencies):\n    value = external\n    return value\n"
        self.assertEqual(self.label(a,a.replace("external","different")),"DIFFERENT")
    def test_whole_function_binding(self):
        a="def order_tasks(tasks, dependencies):\n    saved = later\n    later = 1\n    return saved\n"
        b=a.replace("saved","first").replace("later","second")
        self.assertEqual(self.label(a,b),"ALPHA_ONLY_MATCH")
    def test_unsupported_scopes(self):
        bodies=("def nested():\n        return 1\n    return nested()",
                "return [x for x in tasks]","return lambda x: x","class Nested:\n        pass\n    return 1",
                "import os\n    return 1","global outside\n    return 1","nonlocal outside\n    return 1",
                "return (x := 1)","del tasks\n    return 1","try:\n        return 1\n    except:\n        return 0")
        for body in bodies:
            a="def order_tasks(tasks, dependencies):\n    "+body+"\n"
            with self.subTest(body=body):self.assertEqual(self.label(a,a),"UNKNOWN")
    def test_reflection_and_callable_shadowing_unknown(self):
        for statement in ("return locals()","return tasks.__class__","len = tasks\n    return len(dependencies)",
                          "return getattr(tasks, 'name')","return tasks.inspect()"):
            a="def order_tasks(tasks, dependencies):\n    "+statement+"\n"
            self.assertEqual(self.label(a,a),"UNKNOWN")
    def test_attribute_and_string_literals_preserved(self):
        self.assertEqual(self.label(BASE,BASE.replace("seen.add","seen.discard")),"DIFFERENT")
        self.assertEqual(self.label(BASE,BASE.replace('"order"','"ordered"')),"DIFFERENT")
    def test_rebinding_and_free_name_collision(self):
        a="def order_tasks(tasks, dependencies):\n    value = external\n    return value\n"
        b="def order_tasks(tasks, dependencies):\n    external = external\n    return external\n"
        self.assertEqual(self.label(a,b),"DIFFERENT")

if __name__=="__main__":unittest.main()
