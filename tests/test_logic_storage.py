import unittest
import pandas as pd

from career_logic import (materia_id, estados_por_materia, estado_materia,
                          mascara_materia, entorno_materia, vista_academica)
from graph_view import graph_data, graph_html
from storage import guardar_usuario, SaveError


PLAN = {
    "Matemática I": {"puntos": 8, "correlativas": []},
    "Matemática II": {"puntos": 8, "correlativas": ["Matemática I"]},
    "Estadística": {"puntos": 6, "correlativas": ["Matemática II"]},
    "Otra": {"puntos": 3, "correlativas": []},
}


def table(*rows):
    return pd.DataFrame(rows, columns=["Nombre", "Materia", "Estado", "Nota"])


class FakeConnection:
    def __init__(self, df, failure=None):
        self.df = df.copy(deep=True)
        self.failure = failure
        self.reads = 0
        self.writes = []

    def read(self, **kwargs):
        self.reads += 1
        if self.failure == "read" or (self.failure == "verify" and self.reads > 1):
            raise RuntimeError("read failed")
        return self.df.copy(deep=True)

    def update(self, worksheet, data):
        self.writes.append(worksheet)
        if worksheet == "backup":
            if self.failure == "backup":
                raise RuntimeError("no backup")
            return
        if self.failure == "write":
            raise RuntimeError("write failed")
        self.df = data.copy(deep=True)
        if self.failure == "mismatch":
            self.df.loc[0, "Nota"] = 2


class LogicTests(unittest.TestCase):
    def test_normalization_shared_with_graph(self):
        data = table(("Demo", "  MATEMATICA   i ", "Final", ""))
        states = estados_por_materia(data)
        self.assertEqual(estado_materia("Matemática II", PLAN, states), "Disponible")
        nodes = graph_data(PLAN, states)["nodes"]
        self.assertEqual(next(n for n in nodes if n["name"] == "Matemática II")["state"], "Disponible")
        self.assertTrue(mascara_materia(data, "Demo", "Matemática I").all())

    def test_cursando_does_not_unlock(self):
        states = estados_por_materia(table(("Demo", "Matemática I", "Cursando", "")))
        self.assertEqual(estado_materia("Matemática II", PLAN, states), "Bloqueada")

    def test_duplicate_metrics_without_storage_migration(self):
        raw = table(("Demo", "matematica i", "Cursando", ""), ("Demo", "Matemática I", "Aprobada", 8), ("Demo", "Ajena", "Aprobada", 9))
        original = raw.copy(deep=True)
        view = vista_academica(raw, PLAN)
        self.assertEqual(view["Materia"].tolist(), ["Matemática I"])
        self.assertEqual(view.iloc[0]["Estado"], "Aprobada")
        pd.testing.assert_frame_equal(raw, original)

    def test_focused_map_and_controls(self):
        self.assertEqual(entorno_materia("Matemática II", PLAN), {"Matemática I", "Matemática II", "Estadística"})
        html = graph_html(PLAN, {}, "Matemática II")
        self.assertNotIn("https://", html)
        for control in ["Acercar", "Alejar", "Centrar selección", "Ver todo", "tabindex", "aria-label", "pointercancel"]:
            self.assertIn(control, html)

    def test_script_data_is_escaped(self):
        plan = {"</script><script>alert(1)</script>": {"puntos": 1, "correlativas": []}}
        self.assertNotIn("</script><script>alert", graph_html(plan, {}))


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.base = table(("Demo", "Matemática I", "Cursando", ""), ("Otro", "Otra", "Aprobada", 8))
        self.local = self.base.copy(deep=True)
        self.local.loc[0, ["Estado", "Nota"]] = ["Aprobada", 9]

    def test_failed_read_never_writes(self):
        conn = FakeConnection(self.base, "read")
        with self.assertRaises(SaveError):
            guardar_usuario(conn, self.local, "Demo", self.base)
        self.assertEqual(conn.writes, [])

    def test_preserves_other_users_fresh_changes(self):
        fresh = self.base.copy(deep=True)
        fresh.loc[1, "Nota"] = 10
        conn = FakeConnection(fresh)
        result = guardar_usuario(conn, self.local, "Demo", self.base)
        self.assertTrue(result.backup_confirmed)
        self.assertEqual(conn.df[conn.df["Nombre"] == "Otro"].iloc[0]["Nota"], 10)
        self.assertEqual(conn.df[conn.df["Nombre"] == "Demo"].iloc[0]["Nota"], 9)
        self.assertEqual(conn.reads, 2)

    def test_stale_same_user_never_writes(self):
        conn = FakeConnection(self.local)
        with self.assertRaisesRegex(SaveError, "otra sesión"):
            guardar_usuario(conn, self.local, "Demo", self.base)
        self.assertEqual(conn.writes, [])

    def test_write_failure_not_success_or_retry(self):
        conn = FakeConnection(self.base, "write")
        with self.assertRaisesRegex(SaveError, "Puede haberse aplicado"):
            guardar_usuario(conn, self.local, "Demo", self.base)
        self.assertEqual(conn.writes, ["backup", 0])

    def test_verification_failure_not_success(self):
        for mode in ["verify", "mismatch"]:
            with self.subTest(mode=mode):
                conn = FakeConnection(self.base, mode)
                with self.assertRaises(SaveError):
                    guardar_usuario(conn, self.local, "Demo", self.base)

    def test_backup_missing_reported_but_confirmed_write_succeeds(self):
        conn = FakeConnection(self.base, "backup")
        self.assertFalse(guardar_usuario(conn, self.local, "Demo", self.base).backup_confirmed)

    def test_last_user_row_can_be_deleted(self):
        base = self.base.iloc[:1].copy()
        conn = FakeConnection(base)
        guardar_usuario(conn, base.iloc[:0], "Demo", base)
        self.assertTrue(conn.df.empty)

    def test_invalid_remote_schema_is_fail_closed(self):
        conn = FakeConnection(pd.DataFrame({"Nombre": ["Demo"]}))
        with self.assertRaises(SaveError):
            guardar_usuario(conn, self.local, "Demo", self.base)
        self.assertEqual(conn.writes, [])

    def test_legacy_optional_columns_and_numeric_readback(self):
        conn = FakeConnection(self.base)
        base = self.base.copy()
        base["Cursada"] = "Regular"
        guardar_usuario(conn, self.local, "Demo", base)
        self.assertEqual(conn.df[conn.df["Nombre"] == "Demo"].iloc[0]["Nota"], 9)

    def test_blank_legacy_modality_matches_loaded_default(self):
        remote = self.base.copy()
        remote["Cursada"] = float("nan")
        base = self.base.copy()
        base["Cursada"] = "Regular"
        conn = FakeConnection(remote)
        guardar_usuario(conn, self.local, "Demo", base)
        self.assertEqual(conn.df[conn.df["Nombre"] == "Demo"].iloc[0]["Nota"], 9)


if __name__ == "__main__":
    unittest.main()
