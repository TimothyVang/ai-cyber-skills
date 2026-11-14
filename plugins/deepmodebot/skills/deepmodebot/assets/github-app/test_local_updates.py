"""Real Git and file effects; only the canonical network endpoint is redirected to a local repository."""
import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import bot
import local_updates as updates


class LocalUpdatesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.home = self.root / "home"
        self.home.mkdir()
        # Repo-local temporary roots must not make the simulated home inherit the host checkout.
        (self.home / ".git").write_text("gitdir: absent-fixture-boundary\n", encoding="utf-8")
        self.remote = self.root / "remote"
        self.remote.mkdir()
        self.real_git = updates.git
        self.git(self.remote, "init", "-b", "main")
        self.git(self.remote, "config", "user.name", "Fixture")
        self.git(self.remote, "config", "user.email", "fixture@example.invalid")
        self.git(self.remote, "config", "core.autocrlf", "false")
        self.prefix = updates.SKILLS + "/deepmodebot"
        self.skill = self.remote / self.prefix
        (self.skill / "assets/github-app").mkdir(parents=True)
        (self.skill / "SKILL.md").write_bytes(b"canonical skill\n")
        (self.skill / "assets/github-app/bot.py").write_bytes(b"old bot\n")
        (self.skill / "retired.txt").write_bytes(b"prior managed file\n")
        self.marketplace_manifest = b'{\n  "name": "deepmodebot",\n  "plugins": []\n}\n'
        for folder in (".omp-plugin", ".claude-plugin"):
            (self.remote / folder).mkdir()
            (self.remote / folder / "marketplace.json").write_bytes(self.marketplace_manifest)
        self.git(self.remote, "add", ".")
        self.git(self.remote, "commit", "-m", "old")
        self.old = self.git(self.remote, "rev-parse", "HEAD")
        self.native = self.home / ".omp/agent/skills/deepmodebot"
        shutil.copytree(self.skill, self.native)
        self.checkout = self.home / "code/deep-mode"
        self.checkout.parent.mkdir()
        self.git(self.home, "clone", "-c", "core.autocrlf=false", str(self.remote), str(self.checkout))
        self.git(self.checkout, "remote", "set-url", "origin", updates.CANONICAL)
        self.git(self.checkout, "config", "core.autocrlf", "false")
        (self.skill / "assets/github-app/bot.py").write_bytes(b"new bot\n")
        (self.skill / "new.txt").write_bytes(b"new managed file\n")
        (self.skill / "retired.txt").unlink()
        self.git(self.remote, "add", "-A")
        self.git(self.remote, "commit", "-m", "new")
        self.new = self.git(self.remote, "rev-parse", "HEAD")
        self.cache = self.home / ".cache/deepmodebot/local-updates"
        patcher = mock.patch.object(updates, "git", side_effect=self.network)
        patcher.start()
        self.addCleanup(patcher.stop)
        metadata = mock.patch.object(updates, "repository_metadata", return_value={
            "id": 1449516491, "fork": False, "default_branch": "main"})
        metadata.start()
        self.addCleanup(metadata.stop)

    def git(self, path, *args):
        return self.real_git(path, *args).stdout.decode().strip()

    def network(self, path, *args, **kwargs):
        if updates.CANONICAL not in args:
            return self.real_git(path, *args, **kwargs)
        mapped = [str(self.remote) if arg == updates.CANONICAL else arg for arg in args]
        result = self.real_git(path, *mapped, **kwargs)
        if "clone" in args and not result.returncode:
            self.real_git(Path(args[-1]), "remote", "set-url", "origin", updates.CANONICAL)
        return result

    def sync(self, **kwargs):
        return updates.synchronize(self.home, self.cache, **kwargs)

    def row(self, result, path):
        return next(row for row in result["targets"] if Path(row["path"]) == path)

    def disk(self):
        return {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}

    def test_clean_canonical_checkout_advances_fast_forward(self):
        result = self.sync()
        self.assertEqual(self.git(self.checkout, "rev-parse", "HEAD"), self.new)
        self.assertEqual(self.row(result, self.checkout)["action"], "fast-forwarded")

    def test_renamed_canonical_origin_alias_is_accepted(self):
        self.git(self.checkout, "remote", "set-url", "origin", "git@github.com:TimothyVang/deep-mode.git")
        self.assertEqual(self.row(self.sync(), self.checkout)["action"], "fast-forwarded")

    def test_fork_origin_stays_unchanged_even_with_canonical_upstream(self):
        self.git(self.checkout, "remote", "set-url", "origin", "https://github.com/someone/deepmodebot.git")
        self.git(self.checkout, "remote", "add", "upstream", updates.CANONICAL)
        result = self.sync()
        self.assertEqual(self.git(self.checkout, "rev-parse", "HEAD"), self.old)
        self.assertIn("origin is a fork or unknown", self.row(result, self.checkout)["reason"])

    def test_dirty_checkout_is_preserved(self):
        path = self.checkout / self.prefix / "SKILL.md"
        path.write_bytes(b"my changes\n")
        result = self.sync()
        self.assertEqual(path.read_bytes(), b"my changes\n")
        self.assertEqual(self.git(self.checkout, "rev-parse", "HEAD"), self.old)
        self.assertIn("dirty", self.row(result, self.checkout)["reason"])

    def test_diverged_checkout_and_feature_branch_are_preserved(self):
        self.git(self.checkout, "config", "user.name", "Fixture")
        self.git(self.checkout, "config", "user.email", "fixture@example.invalid")
        self.git(self.checkout, "commit", "--allow-empty", "-m", "local commit")
        local = self.git(self.checkout, "rev-parse", "HEAD")
        result = self.sync()
        self.assertIn("local commits", self.row(result, self.checkout)["reason"])
        self.assertEqual(self.git(self.checkout, "rev-parse", "HEAD"), local)
        self.git(self.checkout, "checkout", "-b", "feature")
        self.assertIn("not on main", self.row(self.sync(), self.checkout)["reason"])

    def test_native_edited_copy_is_not_adopted_from_skill_md_alone(self):
        path = self.native / "assets/github-app/bot.py"
        path.write_bytes(b"my bot\n")
        result = self.sync()
        self.assertEqual(path.read_bytes(), b"my bot\n")
        self.assertIn("no complete canonical snapshot", self.row(result, self.native)["reason"])
        self.assertNotIn(str(self.native), result["manifests"])

    def test_stale_clean_native_is_adopted_and_old_files_backed_up(self):
        result = self.sync()
        self.assertEqual(self.row(result, self.native)["action"], "synchronized")
        self.assertEqual((self.native / "assets/github-app/bot.py").read_bytes(), b"new bot\n")
        backup = Path(result["manifests"][str(self.native)]["backup"])
        self.assertEqual((backup / "assets/github-app/bot.py").read_bytes(), b"old bot\n")
        self.assertEqual((backup / "retired.txt").read_bytes(), b"prior managed file\n")
        self.assertFalse((self.native / "retired.txt").exists())
        (self.native / "personal.txt").write_bytes(b"keep me\n")
        again = self.sync(manifests=result["manifests"])
        self.assertEqual(self.row(again, self.native)["action"], "current")
        self.assertEqual((self.native / "personal.txt").read_bytes(), b"keep me\n")

    def test_managed_native_edits_are_preserved(self):
        result = self.sync()
        (self.native / "SKILL.md").write_bytes(b"my skill\n")
        again = self.sync(manifests=result["manifests"])
        self.assertIn("locally edited", self.row(again, self.native)["reason"])
        self.assertEqual((self.native / "SKILL.md").read_bytes(), b"my skill\n")

    def test_newly_discovered_native_converges_on_unchanged_upstream(self):
        result = self.sync()
        other = self.home / ".claude/skills/deepmodebot"
        shutil.copytree(self.native, other)
        (other / "assets/github-app/bot.py").write_bytes(b"old bot\n")
        (other / "new.txt").unlink()
        (other / "retired.txt").write_bytes(b"prior managed file\n")
        again = self.sync(manifests=result["manifests"])
        self.assertEqual(again["remote"], result["remote"])
        self.assertEqual(self.row(again, other)["action"], "synchronized")

    def test_dry_run_preserves_entire_filesystem_and_state(self):
        updates.prepare_source(self.home, self.cache, False)
        before = self.disk()
        result = self.sync(dry=True)
        self.assertEqual(self.row(result, self.checkout)["action"], "would fast-forward")
        self.assertEqual(self.row(result, self.native)["action"], "would synchronize")
        self.assertEqual(self.disk(), before)
        self.assertEqual(result["manifests"], {})

    def test_unavailable_source_fails_closed_without_overwriting(self):
        before = self.disk()
        def unavailable(path, *args, **kwargs):
            if updates.CANONICAL in args:
                raise RuntimeError("source unavailable")
            return self.real_git(path, *args, **kwargs)
        with mock.patch.object(updates, "git", side_effect=unavailable):
            result = self.sync()
        self.assertEqual(result["error"], "source unavailable")
        self.assertTrue(all(row["action"] == "preserved" for row in result["targets"]))
        self.assertEqual(self.disk(), before)

    def test_rebranded_or_fork_repository_identity_cannot_retarget_updates(self):
        before = self.disk()
        with mock.patch.object(updates, "repository_metadata", return_value={
                "id": 987654, "fork": False, "default_branch": "main"}):
            result = self.sync()
        self.assertIn("fork or unsupported source", result["error"])
        self.assertEqual(self.disk(), before)
        self.assertFalse(self.cache.exists())
        self.assertTrue(all(row["action"] == "preserved" for row in result["targets"]))

    def test_invalid_manifest_does_not_authorize_overwrite(self):
        manifest = {"origin": "https://github.com/fork/deepmodebot.git", "sha": self.old, "prefix": self.prefix}
        result = self.sync(manifests={str(self.native): manifest})
        self.assertIn("provenance manifest", self.row(result, self.native)["reason"])
        self.assertEqual((self.native / "assets/github-app/bot.py").read_bytes(), b"old bot\n")

    def test_registered_checkout_outside_conventional_locations(self):
        registered = self.root / "custom-clone"
        shutil.move(str(self.checkout), registered)
        result = self.sync(registered=[str(registered)])
        self.assertEqual(self.row(result, registered)["action"], "fast-forwarded")

    def marketplace_install(self, metadata=None):
        marketplace = self.home / ".omp/plugins/cache/marketplaces/deepmodebot"
        marketplace.parent.mkdir(parents=True)
        shutil.move(str(self.checkout), marketplace)
        installed = self.root / "install"
        shutil.copytree(marketplace / updates.PLUGIN, installed)
        (marketplace / "marketplace.json").write_bytes(
            self.marketplace_manifest if metadata is None else metadata)
        return marketplace, {"marketplace": "deepmodebot", "link": installed}

    def test_generated_marketplace_metadata_allows_dry_run_and_verified_upgrade(self):
        metadata = self.marketplace_manifest.replace(b"\n", b"\r\n").removesuffix(b"\r\n")
        marketplace, install = self.marketplace_install(metadata)
        updates.prepare_source(self.home, self.cache, False)
        before = self.disk()
        upgrade = mock.Mock()
        preview = self.sync(dry=True, install=install, upgrade=upgrade)
        self.assertEqual(self.row(preview, install["link"])["action"], "would upgrade")
        upgrade.assert_not_called()
        self.assertEqual(self.disk(), before)

        def replace_installed_fixture():
            self.assertEqual(self.git(marketplace, "rev-parse", "HEAD"), self.new)
            shutil.rmtree(install["link"])
            shutil.copytree(self.remote / updates.PLUGIN, install["link"])

        upgrade.side_effect = replace_installed_fixture
        result = self.sync(install=install, upgrade=upgrade)
        upgrade.assert_called_once_with()
        self.assertEqual(self.row(result, install["link"])["action"], "upgraded")
        self.assertEqual(result["manifests"][str(install["link"])]["sha"], self.new)
        self.assertFalse(result["incomplete"])
        self.assertEqual((marketplace / "marketplace.json").read_bytes(), metadata)
        self.assertEqual(updates.inventory(install["link"]), updates.inventory(self.remote / updates.PLUGIN))

    def test_generated_marketplace_metadata_accepts_already_current_plugin(self):
        marketplace, install = self.marketplace_install()
        shutil.rmtree(install["link"])
        shutil.copytree(self.remote / updates.PLUGIN, install["link"])
        upgrade = mock.Mock()
        result = self.sync(install=install, upgrade=upgrade)
        self.assertEqual(self.row(result, install["link"])["action"], "current")
        self.assertEqual(result["manifests"][str(install["link"])]["sha"], self.new)
        self.assertEqual(self.git(marketplace, "rev-parse", "HEAD"), self.new)
        self.assertFalse(result["incomplete"])
        upgrade.assert_not_called()
        self.assertEqual((marketplace / "marketplace.json").read_bytes(), self.marketplace_manifest)

    def test_custom_marketplace_metadata_is_preserved_without_upgrade(self):
        marketplace, install = self.marketplace_install()
        upgrade = mock.Mock()
        for metadata in (b'{"name":"custom"}\n', self.marketplace_manifest.replace(b"  ", b" "),
                         self.marketplace_manifest + b"\n"):
            with self.subTest(metadata=metadata):
                (marketplace / "marketplace.json").write_bytes(metadata)
                result = self.sync(install=install, upgrade=upgrade)
                self.assertEqual(self.row(result, install["link"])["action"], "preserved")
                self.assertIn("dirty", self.row(result, install["link"])["reason"])
                self.assertEqual(self.git(marketplace, "rev-parse", "HEAD"), self.old)
                self.assertEqual((marketplace / "marketplace.json").read_bytes(), metadata)
                self.assertEqual((install["link"] / "skills/deepmodebot/assets/github-app/bot.py").read_bytes(),
                                 b"old bot\n")
        upgrade.assert_not_called()

    def test_generated_manifest_in_user_checkout_is_not_exempt(self):
        metadata = self.checkout / "marketplace.json"
        metadata.write_bytes(self.marketplace_manifest)
        result = self.sync()
        self.assertIn("dirty", self.row(result, self.checkout)["reason"])
        self.assertEqual(self.git(self.checkout, "rev-parse", "HEAD"), self.old)
        self.assertEqual(metadata.read_bytes(), self.marketplace_manifest)

    def test_other_marketplace_path_is_not_exempt(self):
        marketplace, install = self.marketplace_install()
        other = marketplace.with_name("custom")
        marketplace.rename(other)
        install["marketplace"] = "custom"
        upgrade = mock.Mock()
        result = self.sync(install=install, upgrade=upgrade)
        upgrade.assert_not_called()
        self.assertIn("dirty", self.row(result, install["link"])["reason"])
        self.assertEqual(self.git(other, "rev-parse", "HEAD"), self.old)
        self.assertEqual((other / "marketplace.json").read_bytes(), self.marketplace_manifest)

    def test_generated_metadata_requires_current_head_manifest_not_incoming_bytes(self):
        incoming = self.marketplace_manifest.replace(b"deepmodebot", b"new-name")
        for folder in (".omp-plugin", ".claude-plugin"):
            (self.remote / folder / "marketplace.json").write_bytes(incoming)
        self.git(self.remote, "add", ".")
        self.git(self.remote, "commit", "-m", "changed canonical manifests")
        marketplace, install = self.marketplace_install(incoming)
        upgrade = mock.Mock()
        result = self.sync(install=install, upgrade=upgrade)
        upgrade.assert_not_called()
        self.assertIn("dirty", self.row(result, install["link"])["reason"])
        self.assertEqual(self.git(marketplace, "rev-parse", "HEAD"), self.old)
        self.assertEqual((marketplace / "marketplace.json").read_bytes(), incoming)

    def test_generated_metadata_collision_with_incoming_file_or_directory_is_preserved(self):
        marketplace, install = self.marketplace_install()
        upgrade = mock.Mock()
        collision = self.remote / "marketplace.json"
        for kind in ("file", "directory"):
            with self.subTest(kind=kind):
                if kind == "file":
                    collision.write_bytes(self.marketplace_manifest)
                else:
                    collision.unlink()
                    collision.mkdir()
                    (collision / "nested.json").write_bytes(b"{}\n")
                self.git(self.remote, "add", "-A")
                self.git(self.remote, "commit", "-m", "colliding " + kind)
                result = self.sync(install=install, upgrade=upgrade)
                self.assertIn("collides", self.row(result, install["link"])["reason"])
                self.assertEqual(self.git(marketplace, "rev-parse", "HEAD"), self.old)
                self.assertEqual((marketplace / "marketplace.json").read_bytes(), self.marketplace_manifest)
                self.assertNotIn(str(install["link"]), result["manifests"])
        upgrade.assert_not_called()

    def test_linked_generated_marketplace_metadata_is_preserved(self):
        marketplace, install = self.marketplace_install()
        metadata = marketplace / "marketplace.json"
        metadata.unlink()
        target = self.root / "generated-manifest"
        target.write_bytes(self.marketplace_manifest)
        try:
            metadata.symlink_to(target)
        except OSError as err:
            self.skipTest(f"symlink creation unavailable: {err}")
        upgrade = mock.Mock()
        result = self.sync(install=install, upgrade=upgrade)
        upgrade.assert_not_called()
        self.assertIn("dirty", self.row(result, install["link"])["reason"])
        self.assertTrue(metadata.is_symlink())
        self.assertEqual(target.read_bytes(), self.marketplace_manifest)
        self.assertEqual(self.git(marketplace, "rev-parse", "HEAD"), self.old)

    def test_fork_marketplace_never_runs_omp_upgrade(self):
        marketplace = self.home / ".omp/plugins/cache/marketplaces/deepmodebot"
        marketplace.parent.mkdir(parents=True)
        shutil.move(str(self.checkout), marketplace)
        self.git(marketplace, "remote", "set-url", "origin", "https://github.com/fork/deepmodebot.git")
        install = {"marketplace": "deepmodebot", "link": self.root / "install"}
        upgrade = mock.Mock()
        result = self.sync(install=install, upgrade=upgrade)
        upgrade.assert_not_called()
        self.assertIn("marketplace: origin is a fork or unknown", self.row(result, install["link"])["reason"])

    def test_generated_cache_is_ignored_but_unknown_native_files_block_adoption(self):
        cache = self.native / "assets/github-app/__pycache__"
        cache.mkdir()
        (cache / "bot.pyc").write_bytes(b"generated")
        result = self.sync()
        self.assertEqual(self.row(result, self.native)["action"], "synchronized")
        unknown = self.home / ".agents/skills/deepmodebot"
        shutil.copytree(self.native, unknown)
        (unknown / "private.txt").write_bytes(b"keep")
        again = self.sync(manifests=result["manifests"])
        self.assertIn("no complete canonical snapshot", self.row(again, unknown)["reason"])
        self.assertEqual((unknown / "private.txt").read_bytes(), b"keep")

    def test_git_export_attributes_cannot_remove_or_rewrite_managed_blobs(self):
        (self.skill / ".gitattributes").write_bytes(b"new.txt export-ignore\nSKILL.md export-subst\n")
        self.git(self.remote, "add", ".")
        self.git(self.remote, "commit", "-m", "export attributes")
        result = self.sync()
        self.assertEqual(self.row(result, self.native)["action"], "synchronized")
        self.assertEqual((self.native / "new.txt").read_bytes(), b"new managed file\n")

    def test_omp_success_without_matching_contents_does_not_record_installed_sha(self):
        marketplace = self.home / ".omp/plugins/cache/marketplaces/deepmodebot"
        marketplace.parent.mkdir(parents=True)
        shutil.move(str(self.checkout), marketplace)
        installed = self.root / "install"
        shutil.copytree(marketplace / updates.PLUGIN, installed)
        install = {"marketplace": "deepmodebot", "link": installed}
        result = self.sync(install=install, upgrade=lambda: None)
        self.assertEqual(self.row(result, installed)["action"], "failed")
        self.assertIn("do not match", self.row(result, installed)["reason"])
        self.assertNotIn(str(installed), result["manifests"])
        self.assertFalse(result["upgraded"])
    def interrupt_copy(self, abrupt=False):
        original = updates.os.replace
        def replace(source, destination):
            if Path(destination) == self.native / "new.txt":
                if abrupt:
                    raise SystemExit("process stopped after first replacement")
                raise PermissionError("second replacement unavailable")
            return original(source, destination)
        with mock.patch.object(updates.os, "replace", side_effect=replace):
            if abrupt:
                with self.assertRaises(SystemExit):
                    self.sync()
                return None
            return self.sync()

    def test_second_replacement_failure_recovers_from_disk_journal(self):
        failed = self.interrupt_copy()
        self.assertEqual(self.row(failed, self.native)["action"], "failed")
        self.assertIn(str(self.native), failed["incomplete"])
        self.assertEqual((self.native / "assets/github-app/bot.py").read_bytes(), b"new bot\n")
        self.assertFalse((self.native / "new.txt").exists())
        result = self.sync()
        self.assertEqual(result["manifests"][str(self.native)]["sha"], self.new)
        self.assertEqual((self.native / "new.txt").read_bytes(), b"new managed file\n")
        self.assertFalse((self.native / "retired.txt").exists())
        self.assertFalse(list(self.native.rglob("*.update-*")))
        self.assertTrue(updates.pending_path(self.cache, self.native).exists())
        self.sync(manifests=result["manifests"])
        self.assertFalse(updates.pending_path(self.cache, self.native).exists())

    def test_abrupt_termination_resumes_without_in_memory_provenance(self):
        self.interrupt_copy(abrupt=True)
        result = self.sync()
        self.assertEqual(result["manifests"][str(self.native)]["sha"], self.new)
        self.assertEqual((self.native / "new.txt").read_bytes(), b"new managed file\n")
        self.assertFalse(result["incomplete"])

    def test_completed_files_without_saved_receipt_are_recovered(self):
        self.sync()  # Simulate losing the returned receipt before it can be persisted.
        result = self.sync()
        self.assertEqual(self.row(result, self.native)["action"], "recovered")
        self.assertEqual(result["manifests"][str(self.native)]["sha"], self.new)
        backup = Path(result["manifests"][str(self.native)]["backup"])
        self.assertEqual((backup / "assets/github-app/bot.py").read_bytes(), b"old bot\n")

    def test_failure_removing_retired_file_remains_recoverable(self):
        unlink = Path.unlink
        def refuse(path, *args, **kwargs):
            if path == self.native / "retired.txt":
                raise PermissionError("retired file is busy")
            return unlink(path, *args, **kwargs)
        with mock.patch.object(Path, "unlink", refuse):
            failed = self.sync()
        self.assertIn(str(self.native), failed["incomplete"])
        self.assertTrue((self.native / "retired.txt").exists())
        result = self.sync()
        self.assertFalse((self.native / "retired.txt").exists())
        self.assertEqual(result["manifests"][str(self.native)]["sha"], self.new)

    def test_pending_recovery_preserves_edits_and_missing_replacement_files(self):
        self.interrupt_copy()
        changed = self.native / "assets/github-app/bot.py"
        changed.write_bytes(b"my work after interruption\n")
        result = self.sync()
        self.assertEqual(changed.read_bytes(), b"my work after interruption\n")
        self.assertFalse((self.native / "new.txt").exists())
        self.assertIn(str(self.native), result["incomplete"])
        changed.write_bytes(b"new bot\n")
        (self.native / "SKILL.md").unlink()
        result = self.sync()
        self.assertFalse((self.native / "SKILL.md").exists())
        self.assertIn("local edit: SKILL.md", self.row(result, self.native)["reason"])

    def test_pending_target_finishes_before_newer_main_is_applied(self):
        self.interrupt_copy()
        (self.skill / "SKILL.md").write_bytes(b"third canonical skill\n")
        self.git(self.remote, "add", ".")
        self.git(self.remote, "commit", "-m", "third")
        third = self.git(self.remote, "rev-parse", "HEAD")
        result = self.sync()
        self.assertEqual(result["manifests"][str(self.native)]["sha"], self.new)
        self.assertEqual((self.native / "SKILL.md").read_bytes(), b"canonical skill\n")
        result = self.sync(manifests=result["manifests"])
        self.assertEqual(result["manifests"][str(self.native)]["sha"], third)
        self.assertEqual((self.native / "SKILL.md").read_bytes(), b"third canonical skill\n")

    def test_partial_plugin_upgrade_remains_incomplete_on_fresh_retry(self):
        marketplace = self.home / ".omp/plugins/cache/marketplaces/deepmodebot"
        shutil.copytree(self.checkout, marketplace)
        installed = self.home / ".omp/plugins/cache/plugins/fixture"
        shutil.copytree(self.checkout / updates.PLUGIN, installed)
        install = {"link": installed, "marketplace": "deepmodebot"}
        partial = installed / "skills/deepmodebot/assets/github-app/bot.py"

        def interrupted_upgrade():
            partial.write_bytes(b"new bot\n")
            raise RuntimeError("manager interrupted after its first write")

        first = self.sync(install=install, upgrade=interrupted_upgrade)
        self.assertIn(str(installed), first["incomplete"])
        upgrade = mock.Mock()
        retry = self.sync(install=install, upgrade=upgrade)
        upgrade.assert_not_called()
        self.assertIn(str(installed), retry["incomplete"])
        self.assertNotIn(str(installed), retry["manifests"])
        self.assertEqual(partial.read_bytes(), b"new bot\n")
        self.assertTrue((installed / "skills/deepmodebot/retired.txt").exists())
        # An external successful repair clears the barrier only after full-tree verification.
        shutil.copytree(self.remote / updates.PLUGIN, installed, dirs_exist_ok=True)
        (installed / "skills/deepmodebot/retired.txt").unlink()
        repaired = self.sync(install=install, upgrade=upgrade)
        self.assertNotIn(str(installed), repaired["incomplete"])
        self.assertEqual(repaired["manifests"][str(installed)]["sha"], self.new)


    def test_public_cli_update_without_omp_synchronizes_and_records(self):
        config = self.home / ".config/deepmodebot"
        output = io.StringIO()
        with mock.patch.object(bot.Path, "home", return_value=self.home), \
                mock.patch.object(bot, "WORK", self.cache.parent), \
                mock.patch.object(bot, "CONFIG_DIR", config), \
                mock.patch.object(bot, "BOT_CONFIG", config / "bot.json"), \
                mock.patch.object(bot, "UPDATE_PATH", config / "update.json"), \
                mock.patch.object(bot, "omp_install", return_value=None), \
                mock.patch.object(bot.sys, "argv", ["bot.py", "update"]), \
                contextlib.redirect_stdout(output):
            bot.main()
        receipt = json.loads((config / "update.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["copies"][str(self.native)]["sha"], self.new)
        self.assertEqual(receipt["copies"][str(self.checkout)]["sha"], self.new)
        self.assertNotIn("sha", receipt)
        self.assertFalse((config / "bot.json").exists())
        self.assertIn("synchronized", output.getvalue())

    def test_public_cli_dry_run_without_omp_does_not_create_config(self):
        updates.prepare_source(self.home, self.cache, False)
        config = self.home / ".config/deepmodebot"
        before = self.disk()
        output = io.StringIO()
        with mock.patch.object(bot.Path, "home", return_value=self.home), \
                mock.patch.object(bot, "WORK", self.cache.parent), \
                mock.patch.object(bot, "CONFIG_DIR", config), \
                mock.patch.object(bot, "BOT_CONFIG", config / "bot.json"), \
                mock.patch.object(bot, "UPDATE_PATH", config / "update.json"), \
                mock.patch.object(bot, "omp_install", return_value=None), \
                mock.patch.object(bot.sys, "argv", ["bot.py", "update", "--dry-run"]), \
                contextlib.redirect_stdout(output):
            bot.main()
        self.assertIn("would fast-forward", output.getvalue())
        self.assertIn("would synchronize", output.getvalue())
        self.assertFalse(config.exists())
        self.assertEqual(self.disk(), before)


if __name__ == "__main__":
    unittest.main()
