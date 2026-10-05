"""
Tests untuk services/prompt_builder.py
"""
import pytest
from models import Business, FAQ
from services.prompt_builder import (
    build_system_prompt,
    _get_tone_guidance,
    _build_faq_section,
    validate_message_length,
    detect_order_intent
)


class TestPromptBuilder:
    """Test system prompt building"""

    @pytest.fixture
    def sample_business(self):
        """Fixture untuk sample business"""
        return Business(
            id=1,
            name="Toko Kopi Asik",
            category="Kafe",
            tone="ramah",
            opening_hours="08:00 - 17:00 (Senin-Jumat)",
            address="Jl. Sudirman No. 123, Jakarta",
            order_flow="Pesan via WA, kami akan konfirmasi dalam 1 jam. Bayar via transfer bank atau cash on delivery.",
            whatsapp_number="628123456789",
            is_active=True
        )

    @pytest.fixture
    def sample_faqs(self):
        """Fixture untuk sample FAQs"""
        return [
            FAQ(
                id=1,
                business_id=1,
                question="Apa saja menu kopi yang tersedia?",
                answer="Kami punya: Espresso, Americano, Cappuccino, Latte, Macchiato, dan Flat White.",
                order=1
            ),
            FAQ(
                id=2,
                business_id=1,
                question="Berapa harga kopi?",
                answer="Harga mulai dari Rp 15.000 untuk Americano hingga Rp 35.000 untuk specialty drinks.",
                order=2
            ),
            FAQ(
                id=3,
                business_id=1,
                question="Apakah ada minuman lain selain kopi?",
                answer="Ada! Kami juga punya teh, smoothie, dan jus segar.",
                order=3
            )
        ]

    def test_build_system_prompt_contains_business_name(self, sample_business, sample_faqs):
        """Test bahwa system prompt contain nama bisnis"""
        prompt = build_system_prompt(sample_business, sample_faqs)
        assert "Toko Kopi Asik" in prompt
        assert "Kafe" in prompt

    def test_build_system_prompt_contains_faqs(self, sample_business, sample_faqs):
        """Test bahwa system prompt contain FAQ"""
        prompt = build_system_prompt(sample_business, sample_faqs)
        assert "Apa saja menu kopi" in prompt
        assert "Espresso, Americano" in prompt
        assert "Berapa harga kopi" in prompt

    def test_build_system_prompt_contains_address(self, sample_business, sample_faqs):
        """Test bahwa system prompt contain alamat"""
        prompt = build_system_prompt(sample_business, sample_faqs)
        assert "Jl. Sudirman No. 123" in prompt

    def test_build_system_prompt_contains_opening_hours(self, sample_business, sample_faqs):
        """Test bahwa system prompt contain jam operasional"""
        prompt = build_system_prompt(sample_business, sample_faqs)
        assert "08:00 - 17:00" in prompt

    def test_build_system_prompt_contains_order_flow(self, sample_business, sample_faqs):
        """Test bahwa system prompt contain alur pemesanan"""
        prompt = build_system_prompt(sample_business, sample_faqs)
        assert "Pesan via WA" in prompt

    def test_build_system_prompt_no_placeholders(self, sample_business, sample_faqs):
        """Test bahwa tidak ada placeholder yang tersisa"""
        prompt = build_system_prompt(sample_business, sample_faqs)
        assert "{{" not in prompt
        assert "}}" not in prompt

    def test_tone_guidance_ramah(self):
        """Test tone guidance untuk ramah"""
        guidance = _get_tone_guidance("ramah")
        assert "Ramah" in guidance
        assert "hangat" in guidance

    def test_tone_guidance_formal(self):
        """Test tone guidance untuk formal"""
        guidance = _get_tone_guidance("formal")
        assert "Formal" in guidance
        assert "profesional" in guidance

    def test_tone_guidance_professional(self):
        """Test tone guidance untuk profesional"""
        guidance = _get_tone_guidance("profesional")
        assert "Profesional" in guidance

    def test_tone_guidance_santai(self):
        """Test tone guidance untuk santai"""
        guidance = _get_tone_guidance("santai")
        assert "Santai" in guidance

    def test_build_faq_section_empty(self):
        """Test FAQ section dengan empty list"""
        section = _build_faq_section([])
        assert "(Belum ada FAQ)" in section

    def test_build_faq_section_with_faqs(self, sample_faqs):
        """Test FAQ section dengan FAQs"""
        section = _build_faq_section(sample_faqs)
        assert "1. **Q:** Apa saja menu kopi" in section
        assert "2. **Q:** Berapa harga kopi" in section
        assert "3. **Q:** Apakah ada minuman lain" in section


class TestMessageValidation:
    """Test message validation"""

    def test_validate_message_length_valid(self):
        """Test valid message"""
        is_valid, error = validate_message_length("Hello world", max_length=100)
        assert is_valid is True
        assert error is None

    def test_validate_message_length_empty(self):
        """Test empty message"""
        is_valid, error = validate_message_length("", max_length=100)
        assert is_valid is False
        assert "kosong" in error.lower()

    def test_validate_message_length_too_long(self):
        """Test message yang terlalu panjang"""
        long_message = "a" * 5000
        is_valid, error = validate_message_length(long_message, max_length=100)
        assert is_valid is False
        assert "terlalu panjang" in error.lower()

    def test_validate_message_length_exactly_at_limit(self):
        """Test message exactly at limit"""
        message = "a" * 100
        is_valid, error = validate_message_length(message, max_length=100)
        assert is_valid is True


class TestOrderIntentDetection:
    """Test order intent detection"""

    def test_detect_order_intent_pesan(self):
        """Test detect 'pesan' keyword"""
        assert detect_order_intent("Saya ingin pesan kopi") is True

    def test_detect_order_intent_order(self):
        """Test detect 'order' keyword"""
        assert detect_order_intent("Can I order a coffee?") is True

    def test_detect_order_intent_beli(self):
        """Test detect 'beli' keyword"""
        assert detect_order_intent("Berapa harga? Saya mau beli") is True

    def test_detect_order_intent_harga(self):
        """Test detect 'harga' keyword"""
        assert detect_order_intent("Berapa harganya?") is True

    def test_detect_order_intent_no_intent(self):
        """Test no order intent"""
        assert detect_order_intent("Apa itu kopi?") is False

    def test_detect_order_intent_faq_match_no_intent(self):
        """Test FAQ match overrides keywords"""
        faqs = [
            FAQ(id=1, business_id=1, question="Berapa harga kopi?", answer="Rp 20.000", order=1)
        ]
        # "Berapa harga kopi" matches FAQ, so should return False
        assert detect_order_intent("Berapa harga kopi?", faqs) is False
