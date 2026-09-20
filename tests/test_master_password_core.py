"""Tests unitaires pour master_password_core.py.

Comme tests/test_gcm4_core.py, ce fichier importe le module directement —
aucun stub GTK nécessaire, le module n'a aucune dépendance gi/Gtk (voir
CONSIGNES-AGENTS-IA.md §5).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import master_password_core as core  # noqa: E402


class TestIsProtected(unittest.TestCase):
    """is_protected() — distinction contenu protégé / legacy en clair."""

    def test_legacy_plain_key_is_not_protected(self):
        """Un KEY_FILE legacy (hex brut, produit par initialise_encyption_key) n'est pas protégé."""
        self.assertFalse(core.is_protected("1a2b3c4d5e6f"))

    def test_empty_content_is_not_protected(self):
        """Un contenu vide (première initialisation) n'est pas protégé."""
        self.assertFalse(core.is_protected(""))

    def test_protected_content_is_detected(self):
        """Le contenu produit par protect_key_file_content() est détecté comme protégé."""
        protected = core.protect_key_file_content("deadbeef", "hunter2")
        self.assertTrue(core.is_protected(protected))


class TestProtectAndUnlock(unittest.TestCase):
    """Round-trip protection/déverrouillage et détection de mot de passe incorrect."""

    def test_round_trip_returns_original_key(self):
        """unlock_key_file_content() renvoie exactement la clé passée à protect_key_file_content()."""
        raw_key = "cafef00ddeadbeef1234567890abcdef"
        protected = core.protect_key_file_content(raw_key, "correct horse battery staple")
        self.assertEqual(
            core.unlock_key_file_content(protected, "correct horse battery staple"), raw_key
        )

    def test_wrong_master_password_raises(self):
        """Un mot de passe maître incorrect lève InvalidMasterPasswordError, sans renvoyer de clé corrompue."""
        protected = core.protect_key_file_content("deadbeef", "right-password")
        with self.assertRaises(core.InvalidMasterPasswordError):
            core.unlock_key_file_content(protected, "wrong-password")

    def test_empty_master_password_rejected_at_protect_time(self):
        """protect_key_file_content() refuse un mot de passe maître vide (fausse sécurité)."""
        with self.assertRaises(ValueError):
            core.protect_key_file_content("deadbeef", "")

    def test_two_protections_of_same_key_produce_different_output(self):
        """Deux appels sur la même clé/mot de passe produisent des sorties différentes (sel aléatoire)."""
        protected_a = core.protect_key_file_content("deadbeef", "hunter2")
        protected_b = core.protect_key_file_content("deadbeef", "hunter2")
        self.assertNotEqual(protected_a, protected_b)
        # mais les deux se déverrouillent bien vers la même clé d'origine
        self.assertEqual(core.unlock_key_file_content(protected_a, "hunter2"), "deadbeef")
        self.assertEqual(core.unlock_key_file_content(protected_b, "hunter2"), "deadbeef")

    def test_unicode_master_password(self):
        """Un mot de passe maître contenant des caractères non-ASCII fonctionne (encodage UTF-8 explicite)."""
        protected = core.protect_key_file_content("deadbeef", "météo-42-éàü")
        self.assertEqual(core.unlock_key_file_content(protected, "météo-42-éàü"), "deadbeef")


class TestCorruptedContent(unittest.TestCase):
    """Détection d'un contenu protégé malformé, sans lever d'exception non gérée."""

    def test_missing_magic_prefix_raises_corrupted(self):
        """Un contenu sans préfixe magique lève CorruptedProtectedContentError, pas InvalidMasterPasswordError."""
        with self.assertRaises(core.CorruptedProtectedContentError):
            core.unlock_key_file_content("not-a-protected-content", "hunter2")

    def test_wrong_number_of_fields_raises_corrupted(self):
        """Un contenu avec le bon préfixe mais un nombre de champs incorrect est rejeté proprement."""
        with self.assertRaises(core.CorruptedProtectedContentError):
            core.unlock_key_file_content(f"{core.MASTER_PASSWORD_MAGIC}onlyonefield", "hunter2")

    def test_invalid_base64_salt_raises_corrupted(self):
        """Un sel qui n'est pas du base64 valide est rejeté proprement (pas de traceback binascii brut)."""
        malformed = f"{core.MASTER_PASSWORD_MAGIC}not-valid-base64!!:verifier:ciphertext"
        with self.assertRaises(core.CorruptedProtectedContentError):
            core.unlock_key_file_content(malformed, "hunter2")


class TestRewrapAndRemove(unittest.TestCase):
    """Changement de mot de passe maître et retrait de la protection."""

    def test_rewrap_with_correct_old_password(self):
        """rewrap_key_file_content() change le mot de passe maître sans changer la clé locale."""
        raw_key = "deadbeef"
        protected = core.protect_key_file_content(raw_key, "old-password")
        rewrapped = core.rewrap_key_file_content(protected, "old-password", "new-password")
        self.assertTrue(core.is_protected(rewrapped))
        self.assertEqual(core.unlock_key_file_content(rewrapped, "new-password"), raw_key)
        with self.assertRaises(core.InvalidMasterPasswordError):
            core.unlock_key_file_content(rewrapped, "old-password")

    def test_rewrap_with_wrong_old_password_raises(self):
        """rewrap_key_file_content() refuse de changer le mot de passe sans le bon mot de passe actuel."""
        protected = core.protect_key_file_content("deadbeef", "old-password")
        with self.assertRaises(core.InvalidMasterPasswordError):
            core.rewrap_key_file_content(protected, "wrong-password", "new-password")

    def test_remove_protection_returns_plain_raw_key(self):
        """remove_master_password_protection() renvoie la clé en clair, prête à réécrire telle quelle."""
        raw_key = "deadbeef"
        protected = core.protect_key_file_content(raw_key, "hunter2")
        plain = core.remove_master_password_protection(protected, "hunter2")
        self.assertEqual(plain, raw_key)
        self.assertFalse(core.is_protected(plain))

    def test_remove_protection_with_wrong_password_raises(self):
        """remove_master_password_protection() exige le bon mot de passe maître avant de retirer la protection."""
        protected = core.protect_key_file_content("deadbeef", "hunter2")
        with self.assertRaises(core.InvalidMasterPasswordError):
            core.remove_master_password_protection(protected, "wrong")


if __name__ == "__main__":
    unittest.main()
